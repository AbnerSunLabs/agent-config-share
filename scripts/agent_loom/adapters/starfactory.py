"""starFactory 用户级 MCP 适配器。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_loom.envmerge import merge_env_map, ref_for
from agent_loom.envmerge import _ref_name  # noqa: PLC2701 — 复用引用解析
from agent_loom import hookbag, jsonc
from agent_loom.models import CheckResult, HookEntry, McpEntry
from agent_loom.paths import home

HOST = "starFactory"


def mcp_path() -> Path:
    return home() / ".starFactory.json"


def _host_entries(entries: list[McpEntry]) -> list[McpEntry]:
    return [e for e in entries if HOST in e.hosts]


def _merge_headers(
    existing: dict[str, str],
    headers_env: dict[str, str],
) -> dict[str, str]:
    """按 env merge 规则处理 HTTP headers 中的 env 引用。"""
    result = dict(existing)
    for header_name, env_name in headers_env.items():
        current = result.get(header_name, "")
        if not current:
            result[header_name] = ref_for(HOST, env_name)
            continue
        ref_name = _ref_name(current, HOST)
        if ref_name is not None:
            if ref_name != env_name:
                result[header_name] = ref_for(HOST, env_name)
    return result


def _upsert_server(entry: McpEntry, existing: dict[str, Any] | None) -> dict[str, Any]:
    base = dict(existing) if existing else {}
    hookbag.drop_legacy_markers(base)
    base["agentLoomId"] = entry.id
    if entry.transport == "stdio":
        base["command"] = entry.command
        base["args"] = entry.args or []
    else:
        base["url"] = entry.url
    if entry.env is not None:
        base["env"] = merge_env_map(base.get("env", {}), entry.env, HOST)
    if entry.headers_env is not None:
        base["headers"] = _merge_headers(base.get("headers", {}), entry.headers_env)
    return base


def _env_refs_ok(env: dict[str, str], wanted: list[str]) -> bool:
    for name in wanted:
        if name not in env:
            return False
        val = env[name]
        if not val:
            return False
        ref_name = _ref_name(val, HOST)
        if ref_name is not None and ref_name != name:
            return False
    return True


def _headers_refs_ok(headers: dict[str, str], headers_env: dict[str, str]) -> bool:
    for header_name, env_name in headers_env.items():
        if header_name not in headers:
            return False
        val = headers[header_name]
        if not val:
            return False
        ref_name = _ref_name(val, HOST)
        if ref_name is not None and ref_name != env_name:
            return False
    return True


def _server_matches(entry: McpEntry, actual: dict[str, Any]) -> bool:
    if actual.get("agentLoomId") != entry.id:
        return False
    if entry.transport == "stdio":
        if actual.get("command") != entry.command:
            return False
        if actual.get("args") != (entry.args or []):
            return False
    elif actual.get("url") != entry.url:
        return False
    if entry.env and not _env_refs_ok(actual.get("env", {}), entry.env):
        return False
    if entry.headers_env and not _headers_refs_ok(
        actual.get("headers", {}), entry.headers_env
    ):
        return False
    return True


def _load_data() -> tuple[dict[str, Any] | None, bool]:
    path = mcp_path()
    if not path.exists():
        return None, True
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None, True
    if not isinstance(raw, dict):
        return None, True
    servers = raw.get("mcpServers")
    if servers is not None and not isinstance(servers, dict):
        return None, True
    if "mcpServers" not in raw:
        raw["mcpServers"] = {}
    return raw, False


def _write_data(data: dict[str, Any]) -> None:
    path = mcp_path()
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def check_mcp(entries: list[McpEntry]) -> CheckResult:
    wanted = _host_entries(entries)
    path = mcp_path()
    if not path.exists():
        if not wanted:
            return CheckResult(gaps=[], drift=[], file_error=False)
        return CheckResult.fail(path)

    data, file_error = _load_data()
    if file_error:
        return CheckResult.fail(path)

    wanted = _host_entries(entries)
    wanted_ids = {e.id for e in wanted}
    gaps: list[str] = []
    drift: list[str] = []

    servers: dict[str, Any] = data.get("mcpServers", {}) if data is not None else {}

    for entry in wanted:
        actual = servers.get(entry.id)
        if actual is None or not isinstance(actual, dict):
            gaps.append(entry.id)
        elif not _server_matches(entry, actual):
            gaps.append(entry.id)

    for name, srv in servers.items():
        if not isinstance(srv, dict):
            continue
        marker = srv.get("agentLoomId")
        if not marker:
            continue
        if marker not in wanted_ids:
            drift.append(name)
            continue
        entry = next(e for e in entries if e.id == marker)
        if HOST not in entry.hosts:
            drift.append(name)

    return CheckResult(gaps=gaps, drift=drift, file_error=False)


def apply_mcp(entries: list[McpEntry], prune: bool) -> None:
    data, file_error = _load_data()
    if file_error or data is None:
        return

    servers: dict[str, Any] = data.setdefault("mcpServers", {})
    wanted = _host_entries(entries)
    wanted_ids = {e.id for e in wanted}

    for entry in wanted:
        existing = servers.get(entry.id)
        if existing is not None and not isinstance(existing, dict):
            existing = None
        servers[entry.id] = _upsert_server(entry, existing)

    if prune:
        to_remove = []
        for name, srv in servers.items():
            if not isinstance(srv, dict):
                continue
            marker = srv.get("agentLoomId")
            if not marker:
                continue
            if marker not in wanted_ids:
                to_remove.append(name)
                continue
            entry = next((e for e in entries if e.id == marker), None)
            if entry is None or HOST not in entry.hosts:
                to_remove.append(name)
        for name in to_remove:
            del servers[name]

    _write_data(data)


def hooks_path() -> Path:
    return home() / ".starFactory" / "settings.json"


def _host_hook_entries(entries: list[HookEntry]) -> list[HookEntry]:
    return [e for e in entries if HOST in e.hosts]


def _load_hooks_data() -> tuple[dict[str, Any] | None, bool]:
    path = hooks_path()
    if not path.exists():
        return None, True
    try:
        raw = jsonc.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return None, True
    if not isinstance(raw, dict):
        return None, True
    hooks = raw.get("hooks")
    if not hookbag.hooks_container_ok(hooks):
        return None, True
    if "hooks" not in raw:
        raw["hooks"] = []
    return raw, False


def _write_hooks_data(data: dict[str, Any]) -> None:
    path = hooks_path()
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def check_hooks(entries: list[HookEntry]) -> CheckResult:
    wanted = _host_hook_entries(entries)
    path = hooks_path()
    if not path.exists():
        if not wanted:
            return CheckResult(gaps=[], drift=[], file_error=False)
        return CheckResult.fail(path)

    data, file_error = _load_hooks_data()
    if file_error:
        return CheckResult.fail(path)

    wanted_ids = {e.id for e in wanted}
    gaps: list[str] = []
    drift: list[str] = []
    hooks: Any = data.get("hooks", []) if data is not None else []

    for entry in wanted:
        loc = hookbag.find_hook(hooks, entry, HOST)
        if loc is None:
            gaps.append(entry.id)
            continue
        bucket, _ = loc
        actual = hookbag.get_hook(hooks, loc)
        if not hookbag.hook_matches(entry, actual, HOST, bucket):
            gaps.append(entry.id)

    for bucket, i, hook in hookbag.iter_hooks(hooks):
        marker = hook.get("agentLoomId")
        if not marker:
            continue
        if marker not in wanted_ids:
            drift.append(marker if isinstance(marker, str) else str(i))
            continue
        entry = next(e for e in entries if e.id == marker)
        if HOST not in entry.hosts:
            drift.append(marker)

    return CheckResult(gaps=gaps, drift=drift, file_error=False)


def apply_hooks(entries: list[HookEntry], prune: bool) -> None:
    data, file_error = _load_hooks_data()
    if file_error or data is None:
        return

    hooks: Any = data.setdefault("hooks", [])
    map_mode = isinstance(hooks, dict)
    wanted = _host_hook_entries(entries)
    wanted_ids = {e.id for e in wanted}

    for entry in wanted:
        loc = hookbag.find_hook(hooks, entry, HOST)
        existing = hookbag.get_hook(hooks, loc) if loc is not None else None
        new_hook = hookbag.upsert_body(entry, existing, HOST, map_mode)
        if loc is not None:
            hookbag.put_hook(hooks, loc, new_hook)
        else:
            hookbag.append_hook(hooks, entry, HOST, new_hook)

    if prune:
        def _keep(h: dict[str, Any]) -> bool:
            marker = h.get("agentLoomId")
            if not marker:
                return True
            if marker not in wanted_ids:
                return False
            return HOST in next(e for e in entries if e.id == marker).hosts

        hookbag.prune_hooks(hooks, _keep)

    _write_hooks_data(data)
