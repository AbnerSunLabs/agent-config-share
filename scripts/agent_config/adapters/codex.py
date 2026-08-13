"""Codex 用户级 MCP 适配器。"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

from agent_config.envmerge import merge_env_map, ref_for
from agent_config.envmerge import _ref_name  # noqa: PLC2701 — 复用引用解析
from agent_config.models import CheckResult, HookEntry, McpEntry
from agent_config.paths import home

HOST = "codex"


def mcp_path() -> Path:
    return home() / ".codex" / "config.toml"


def dump_toml(doc: dict[str, Any]) -> str:
    """将 dict 序列化为 TOML 文本，覆盖 string / list / table。"""
    lines: list[str] = []

    for key, value in doc.items():
        if not isinstance(value, dict):
            lines.append(f"{key} = {_format_toml_value(value)}")

    for key, value in doc.items():
        if isinstance(value, dict):
            _dump_nested_tables(key, value, lines)

    if not lines:
        return "\n"
    return "\n".join(lines) + "\n"


def _format_toml_value(value: Any) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, list):
        if value and all(isinstance(item, dict) for item in value):
            inner = ", ".join(_format_inline_table(item) for item in value)
            return f"[{inner}]"
        inner = ", ".join(_format_toml_value(item) for item in value)
        return f"[{inner}]"
    raise TypeError(f"不支持的 TOML 值类型: {type(value)!r}")


def _format_inline_table(table: dict[str, Any]) -> str:
    parts = [f"{k} = {_format_toml_value(v)}" for k, v in table.items()]
    return "{" + ", ".join(parts) + "}"


def _dump_nested_tables(parent: str, table: dict[str, Any], lines: list[str]) -> None:
    scalars = {k: v for k, v in table.items() if not isinstance(v, dict)}
    nested = {k: v for k, v in table.items() if isinstance(v, dict)}

    if scalars:
        lines.append("")
        lines.append(f"[{parent}]")
        for k, v in scalars.items():
            lines.append(f"{k} = {_format_toml_value(v)}")

    for name, content in nested.items():
        _dump_nested_tables(f"{parent}.{name}", content, lines)


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
    base["agent_config_id"] = entry.id
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
    if actual.get("agent_config_id") != entry.id:
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
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError):
        return None, True
    if not isinstance(raw, dict):
        return None, True
    servers = raw.get("mcp_servers")
    if servers is not None and not isinstance(servers, dict):
        return None, True
    return raw, False


def _write_data(data: dict[str, Any]) -> None:
    path = mcp_path()
    path.write_text(dump_toml(data), encoding="utf-8")


def check_mcp(entries: list[McpEntry]) -> CheckResult:
    data, file_error = _load_data()
    if file_error:
        return CheckResult(gaps=[], drift=[], file_error=True)

    wanted = _host_entries(entries)
    wanted_ids = {e.id for e in wanted}
    gaps: list[str] = []
    drift: list[str] = []

    servers: dict[str, Any] = data.get("mcp_servers", {}) if data is not None else {}

    for entry in wanted:
        actual = servers.get(entry.id)
        if actual is None or not isinstance(actual, dict):
            gaps.append(entry.id)
        elif not _server_matches(entry, actual):
            gaps.append(entry.id)

    for name, srv in servers.items():
        if not isinstance(srv, dict):
            continue
        marker = srv.get("agent_config_id")
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

    _apply_mcp_to_data(data, entries, prune)
    _write_data(data)


def _apply_mcp_to_data(data: dict[str, Any], entries: list[McpEntry], prune: bool) -> None:
    servers: dict[str, Any] = data.setdefault("mcp_servers", {})
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
            marker = srv.get("agent_config_id")
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


def hooks_json_path() -> Path:
    return home() / ".codex" / "hooks.json"


def resolve_hooks_target() -> tuple[Path, str, bool]:
    """解析 Codex hooks 落点；config.toml 存在但不可解析时第三项为 True。"""
    hooks_json = hooks_json_path()
    config_toml = mcp_path()

    if hooks_json.exists():
        return hooks_json, "hooks_json", False

    if config_toml.exists():
        try:
            raw = tomllib.loads(config_toml.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError):
            # 禁止回落 hooks.json，避免在含 [hooks] 但损坏的 toml 旁路创建 json
            return config_toml, "config_toml", True
        if isinstance(raw, dict) and "hooks" in raw:
            return config_toml, "config_toml", False

    return hooks_json, "hooks_json", False


def _host_hook_entries(entries: list[HookEntry]) -> list[HookEntry]:
    return [e for e in entries if HOST in e.hosts]


def _find_hook_index(hooks: list[Any], entry: HookEntry) -> int | None:
    adapter = entry.adapters[HOST]
    command = adapter.get("command")
    event = adapter.get("event")

    for i, hook in enumerate(hooks):
        if not isinstance(hook, dict):
            continue
        if hook.get("agent_config_id") == entry.id:
            return i

    for i, hook in enumerate(hooks):
        if not isinstance(hook, dict):
            continue
        if command is not None and hook.get("command") != command:
            continue
        if event is not None and hook.get("event") != event:
            continue
        if command is not None or event is not None:
            return i
    return None


def _upsert_hook(entry: HookEntry, existing: dict[str, Any] | None) -> dict[str, Any]:
    base = dict(existing) if existing else {}
    base.update(entry.adapters[HOST])
    base["agent_config_id"] = entry.id
    return base


def _hook_matches(entry: HookEntry, actual: dict[str, Any]) -> bool:
    if actual.get("agent_config_id") != entry.id:
        return False
    adapter = entry.adapters[HOST]
    for key, val in adapter.items():
        if actual.get(key) != val:
            return False
    return True


def _prune_hooks_list(
    hooks: list[Any],
    wanted_ids: set[str],
    entries: list[HookEntry],
) -> list[Any]:
    result: list[Any] = []
    for hook in hooks:
        if not isinstance(hook, dict):
            result.append(hook)
            continue
        marker = hook.get("agent_config_id")
        if not marker:
            result.append(hook)
            continue
        if marker not in wanted_ids:
            continue
        entry = next((e for e in entries if e.id == marker), None)
        if entry is None or HOST not in entry.hosts:
            continue
        result.append(hook)
    return result


def _apply_hooks_to_data(data: dict[str, Any], entries: list[HookEntry], prune: bool) -> None:
    hooks_table = data.setdefault("hooks", {})
    if not isinstance(hooks_table, dict):
        return
    managed = hooks_table.get("managed", [])
    if not isinstance(managed, list):
        managed = []

    wanted = _host_hook_entries(entries)
    wanted_ids = {e.id for e in wanted}

    for entry in wanted:
        idx = _find_hook_index(managed, entry)
        existing = managed[idx] if idx is not None and isinstance(managed[idx], dict) else None
        new_hook = _upsert_hook(entry, existing)
        if idx is not None:
            managed[idx] = new_hook
        else:
            managed.append(new_hook)

    if prune:
        managed = _prune_hooks_list(managed, wanted_ids, entries)

    hooks_table["managed"] = managed


def _load_hooks_json() -> tuple[dict[str, Any] | None, bool]:
    path = hooks_json_path()
    if not path.exists():
        return None, False
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None, True
    if not isinstance(raw, dict):
        return None, True
    hooks = raw.get("hooks")
    if hooks is not None and not isinstance(hooks, list):
        return None, True
    if "hooks" not in raw:
        raw["hooks"] = []
    return raw, False


def _write_hooks_json(data: dict[str, Any]) -> None:
    path = hooks_json_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _get_managed_hooks(data: dict[str, Any]) -> list[Any]:
    hooks_table = data.get("hooks", {})
    if not isinstance(hooks_table, dict):
        return []
    managed = hooks_table.get("managed", [])
    if not isinstance(managed, list):
        return []
    return managed


def check_hooks(entries: list[HookEntry]) -> CheckResult:
    _, kind, target_error = resolve_hooks_target()
    if target_error:
        return CheckResult(gaps=[], drift=[], file_error=True)
    wanted = _host_hook_entries(entries)
    wanted_ids = {e.id for e in wanted}
    gaps: list[str] = []
    drift: list[str] = []

    if kind == "hooks_json":
        data, file_error = _load_hooks_json()
        if file_error:
            return CheckResult(gaps=[], drift=[], file_error=True)
        hooks: list[Any] = data.get("hooks", []) if data is not None else []
        if data is None and wanted:
            return CheckResult(gaps=[e.id for e in wanted], drift=[], file_error=False)

        for entry in wanted:
            idx = _find_hook_index(hooks, entry)
            if idx is None:
                gaps.append(entry.id)
                continue
            actual = hooks[idx]
            if not isinstance(actual, dict) or not _hook_matches(entry, actual):
                gaps.append(entry.id)

        for i, hook in enumerate(hooks):
            if not isinstance(hook, dict):
                continue
            marker = hook.get("agent_config_id")
            if not marker:
                continue
            if marker not in wanted_ids:
                drift.append(str(i))
                continue
            entry = next(e for e in entries if e.id == marker)
            if HOST not in entry.hosts:
                drift.append(str(i))

        return CheckResult(gaps=gaps, drift=drift, file_error=False)

    data, file_error = _load_data()
    if file_error:
        return CheckResult(gaps=[], drift=[], file_error=True)
    if data is None:
        if wanted:
            return CheckResult(gaps=[e.id for e in wanted], drift=[], file_error=False)
        return CheckResult(gaps=[], drift=[], file_error=False)

    hooks = _get_managed_hooks(data)
    for entry in wanted:
        idx = _find_hook_index(hooks, entry)
        if idx is None:
            gaps.append(entry.id)
            continue
        actual = hooks[idx]
        if not isinstance(actual, dict) or not _hook_matches(entry, actual):
            gaps.append(entry.id)

    for i, hook in enumerate(hooks):
        if not isinstance(hook, dict):
            continue
        marker = hook.get("agent_config_id")
        if not marker:
            continue
        if marker not in wanted_ids:
            drift.append(str(i))
            continue
        entry = next(e for e in entries if e.id == marker)
        if HOST not in entry.hosts:
            drift.append(str(i))

    return CheckResult(gaps=gaps, drift=drift, file_error=False)


def apply_hooks(entries: list[HookEntry], prune: bool) -> None:
    _, kind, target_error = resolve_hooks_target()
    if target_error:
        return
    if kind == "hooks_json":
        data, file_error = _load_hooks_json()
        if file_error:
            return
        if data is None:
            data = {"hooks": []}
        hooks: list[Any] = data.setdefault("hooks", [])
        wanted = _host_hook_entries(entries)
        wanted_ids = {e.id for e in wanted}

        for entry in wanted:
            idx = _find_hook_index(hooks, entry)
            existing = hooks[idx] if idx is not None and isinstance(hooks[idx], dict) else None
            new_hook = _upsert_hook(entry, existing)
            if idx is not None:
                hooks[idx] = new_hook
            else:
                hooks.append(new_hook)

        if prune:
            hooks[:] = _prune_hooks_list(hooks, wanted_ids, entries)

        _write_hooks_json(data)
        return

    data, file_error = _load_data()
    if file_error or data is None:
        return
    _apply_hooks_to_data(data, entries, prune)
    _write_data(data)


def apply_all(
    mcp_entries: list[McpEntry],
    hook_entries: list[HookEntry],
    prune: bool = False,
) -> None:
    _, kind, target_error = resolve_hooks_target()
    if target_error:
        return
    if kind == "config_toml":
        data, file_error = _load_data()
        if file_error or data is None:
            return
        _apply_mcp_to_data(data, mcp_entries, prune)
        _apply_hooks_to_data(data, hook_entries, prune)
        _write_data(data)
        return

    apply_mcp(mcp_entries, prune)
    apply_hooks(hook_entries, prune)
