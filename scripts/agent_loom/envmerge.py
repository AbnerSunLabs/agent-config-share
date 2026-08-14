import re

_CURSOR_REF = re.compile(r"^\$\{env:([A-Za-z_][A-Za-z0-9_]*)\}$")
_CODEX_REF = re.compile(r"^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$")


def ref_for(host: str, name: str) -> str:
    if host == "cursor":
        return f"${{env:{name}}}"
    return f"${{{name}}}"


def is_env_ref(value: str, host: str) -> bool:
    return _ref_name(value, host) is not None


def _ref_name(value: str, host: str) -> str | None:
    if host == "cursor":
        match = _CURSOR_REF.match(value)
    else:
        match = _CODEX_REF.match(value)
    if not match:
        return None
    return match.group(1)


def merge_env_map(
    existing: dict[str, str],
    wanted_names: list[str],
    host: str,
) -> dict[str, str]:
    """按 spec §4.1 三步合并 env 映射，保留现场字面量。"""
    result = dict(existing)
    for name in wanted_names:
        current = result.get(name, "")
        if not current:
            result[name] = ref_for(host, name)
            continue
        ref_name = _ref_name(current, host)
        if ref_name is not None:
            if ref_name != name:
                result[name] = ref_for(host, name)
            continue
        # 非空字面量：原样保留
    return result
