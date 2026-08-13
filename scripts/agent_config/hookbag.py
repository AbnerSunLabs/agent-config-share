"""Cursor / starFactory 的 hooks 字段：数组或「事件名 → 数组」对象。"""

from __future__ import annotations

from typing import Any

from agent_config.models import HookEntry

_DEFAULT_MARKER = "agentConfigId"


def hooks_container_ok(hooks: Any) -> bool:
    if hooks is None or isinstance(hooks, list):
        return True
    return isinstance(hooks, dict)


def nested_command(hook: dict[str, Any]) -> str | None:
    cmd = hook.get("command")
    if isinstance(cmd, str):
        return cmd
    inner = hook.get("hooks")
    if isinstance(inner, list):
        for item in inner:
            if isinstance(item, dict) and isinstance(item.get("command"), str):
                return item["command"]
    return None


def iter_hooks(hooks: Any) -> list[tuple[str | None, int, dict[str, Any]]]:
    items: list[tuple[str | None, int, dict[str, Any]]] = []
    if isinstance(hooks, list):
        for i, hook in enumerate(hooks):
            if isinstance(hook, dict):
                items.append((None, i, hook))
        return items
    if isinstance(hooks, dict):
        for event, lst in hooks.items():
            if not isinstance(lst, list):
                continue
            for i, hook in enumerate(lst):
                if isinstance(hook, dict):
                    items.append((str(event), i, hook))
    return items


def find_hook(
    hooks: Any,
    entry: HookEntry,
    host: str,
    marker_key: str = _DEFAULT_MARKER,
) -> tuple[str | None, int] | None:
    adapter = entry.adapters[host]
    command = adapter.get("command") or nested_command(adapter)
    event = adapter.get("event")

    for bucket, i, hook in iter_hooks(hooks):
        if hook.get(marker_key) == entry.id:
            return bucket, i

    for bucket, i, hook in iter_hooks(hooks):
        hook_cmd = nested_command(hook)
        if command is not None and hook_cmd != command:
            continue
        hook_event = hook.get("event", bucket)
        if event is not None and hook_event != event:
            continue
        if command is not None or event is not None:
            return bucket, i
    return None


def get_hook(hooks: Any, loc: tuple[str | None, int]) -> dict[str, Any]:
    bucket, i = loc
    if bucket is None:
        return hooks[i]
    return hooks[bucket][i]


def put_hook(hooks: Any, loc: tuple[str | None, int], hook: dict[str, Any]) -> None:
    bucket, i = loc
    if bucket is None:
        hooks[i] = hook
        return
    hooks[bucket][i] = hook


def append_hook(hooks: Any, entry: HookEntry, host: str, hook: dict[str, Any]) -> None:
    if isinstance(hooks, list):
        hooks.append(hook)
        return
    event = entry.adapters[host].get("event") or "default"
    hooks.setdefault(event, []).append(hook)


def prune_hooks(hooks: Any, keep) -> None:
    """keep(hook) 为 True 则保留。"""
    if isinstance(hooks, list):
        hooks[:] = [h for h in hooks if not isinstance(h, dict) or keep(h)]
        return
    if isinstance(hooks, dict):
        for event, lst in list(hooks.items()):
            if not isinstance(lst, list):
                continue
            hooks[event] = [h for h in lst if not isinstance(h, dict) or keep(h)]


def upsert_body(
    entry: HookEntry,
    existing: dict[str, Any] | None,
    host: str,
    map_mode: bool,
    marker_key: str = _DEFAULT_MARKER,
) -> dict[str, Any]:
    base = dict(existing) if existing else {}
    adapter = dict(entry.adapters[host])
    if map_mode:
        adapter.pop("event", None)
    base.update(adapter)
    base[marker_key] = entry.id
    return base


def hook_matches(
    entry: HookEntry,
    actual: dict[str, Any],
    host: str,
    bucket: str | None,
    marker_key: str = _DEFAULT_MARKER,
) -> bool:
    marker = actual.get(marker_key)
    if marker is not None and marker != entry.id:
        return False
    adapter = entry.adapters[host]
    for key, val in adapter.items():
        if key == "event":
            actual_event = actual.get("event", bucket)
            if actual_event != val:
                return False
            continue
        if key == "command":
            if nested_command(actual) != val:
                return False
            continue
        if actual.get(key) != val:
            return False
    return True
