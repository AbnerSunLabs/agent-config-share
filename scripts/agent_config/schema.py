from typing import Any

from agent_config.models import HookEntry, McpEntry

HOSTS = ("cursor", "codex", "starFactory")


class SchemaError(Exception):
    """清单 schema 校验失败。"""


def _require_mapping(data: Any, label: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise SchemaError(f"{label} 必须是对象")
    return data


def _require_list(data: Any, label: str) -> list[Any]:
    if not isinstance(data, list):
        raise SchemaError(f"{label} 必须是列表")
    return data


def _require_non_empty_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SchemaError(f"{label} 必须是非空字符串")
    return value


def _parse_hosts(value: Any, label: str) -> list[str]:
    hosts = _require_list(value, label)
    if not hosts:
        raise SchemaError(f"{label} 不能为空")
    seen: set[str] = set()
    result: list[str] = []
    for host in hosts:
        if not isinstance(host, str) or host not in HOSTS:
            raise SchemaError(f"{label} 含有非法宿主: {host!r}")
        if host in seen:
            raise SchemaError(f"{label} 含有重复宿主: {host!r}")
        seen.add(host)
        result.append(host)
    return result


def _parse_env(value: Any) -> list[str]:
    if isinstance(value, dict):
        raise SchemaError("env 只能是环境变量名列表，禁止写字面量")
    if not isinstance(value, list):
        raise SchemaError("env 必须是字符串列表")
    names: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise SchemaError("env 必须是字符串列表")
        names.append(item)
    return names


def _parse_headers_env(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise SchemaError("headers_env 必须是字符串到字符串的映射")
    result: dict[str, str] = {}
    for key, env_name in value.items():
        if not isinstance(key, str) or not isinstance(env_name, str):
            raise SchemaError("headers_env 必须是字符串到字符串的映射")
        result[key] = env_name
    return result


def _parse_mcp_entry(raw: Any, seen_ids: set[str]) -> McpEntry:
    if not isinstance(raw, dict):
        raise SchemaError("mcp 条目必须是对象")

    entry_id = _require_non_empty_str(raw.get("id"), "id")
    if entry_id in seen_ids:
        raise SchemaError(f"id 重复: {entry_id!r}")
    seen_ids.add(entry_id)

    hosts = _parse_hosts(raw.get("hosts"), "hosts")
    transport = _require_non_empty_str(raw.get("transport"), "transport")
    if transport not in ("stdio", "http"):
        raise SchemaError(f"transport 非法: {transport!r}")

    command: str | None = None
    args: list[str] | None = None
    url: str | None = None
    env: list[str] | None = None
    headers_env: dict[str, str] | None = None

    if transport == "stdio":
        command = _require_non_empty_str(raw.get("command"), "command")
        args_raw = raw.get("args")
        if not isinstance(args_raw, list):
            raise SchemaError("stdio transport 需要 args 列表")
        args = []
        for item in args_raw:
            if not isinstance(item, str):
                raise SchemaError("args 必须是字符串列表")
            args.append(item)
    else:
        url = _require_non_empty_str(raw.get("url"), "url")

    if "env" in raw:
        env = _parse_env(raw["env"])
    if "headers_env" in raw:
        headers_env = _parse_headers_env(raw["headers_env"])

    return McpEntry(
        id=entry_id,
        hosts=hosts,
        transport=transport,
        command=command,
        args=args,
        url=url,
        env=env,
        headers_env=headers_env,
    )


def parse_mcp(data: Any) -> list[McpEntry]:
    root = _require_mapping(data, "mcp 清单")
    items = _require_list(root.get("mcp"), "mcp")
    seen_ids: set[str] = set()
    return [_parse_mcp_entry(item, seen_ids) for item in items]


def _parse_hook_entry(raw: Any, seen_ids: set[str]) -> HookEntry:
    if not isinstance(raw, dict):
        raise SchemaError("hooks 条目必须是对象")

    entry_id = _require_non_empty_str(raw.get("id"), "id")
    if entry_id in seen_ids:
        raise SchemaError(f"id 重复: {entry_id!r}")
    seen_ids.add(entry_id)

    hosts = _parse_hosts(raw.get("hosts"), "hosts")
    intent = _require_non_empty_str(raw.get("intent"), "intent")

    adapters_raw = raw.get("adapters")
    if not isinstance(adapters_raw, dict):
        raise SchemaError("adapters 必须是对象")

    host_set = set(hosts)
    adapter_keys = set(adapters_raw.keys())
    if adapter_keys != host_set:
        raise SchemaError("adapters 键集合必须等于 hosts 集合")

    adapters: dict[str, dict] = {}
    for host in hosts:
        adapter = adapters_raw[host]
        if not isinstance(adapter, dict):
            raise SchemaError(f"adapters.{host} 必须是对象")
        adapters[host] = adapter

    return HookEntry(
        id=entry_id,
        hosts=hosts,
        intent=intent,
        adapters=adapters,
    )


def parse_hooks(data: Any) -> list[HookEntry]:
    root = _require_mapping(data, "hooks 清单")
    items = _require_list(root.get("hooks"), "hooks")
    seen_ids: set[str] = set()
    return [_parse_hook_entry(item, seen_ids) for item in items]
