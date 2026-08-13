"""Cursor / starFactory 的 hooks 字段：数组或「事件名 → 数组」对象。"""

from __future__ import annotations

from typing import Any

from agent_config.models import HookEntry


def hooks_container_ok(hooks: Any) -> bool:
    if hooks is None or isinstance(hooks, list):
        return True
    if not isinstance(hooks, dict):
        return False
    return all(isinstance(v, list) for v in hooks.values())


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
    hooks: Any, entry: HookEntry, host: str
) -> tuple[str | None, int] | None:
    adapter = entry.adapters[host]
    command = adapter.get("command")
    event = adapter.get("event")

    for bucket, i, hook in iter_hooks(hooks):
        if hook.get("agentConfigId") == entry.id:
            return bucket, i

    for bucket, i, hook in iter_hooks(hooks):
        if command is not None and hook.get("command") != command:
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
        hooks[:] = [
            h for h in hooks if not isinstance(h, dict) or keep(h)
        ]
        return
    if isinstance(hooks, dict):
        for event, lst in list(hooks.items()):
            if not isinstance(lst, list):
                continue
            hooks[event] = [h for h in lst if not isinstance(h, dict) or keep(h)]


def upsert_body(
    entry: HookEntry, existing: dict[str, Any] | None, host: str, map_mode: bool
) -> dict[str, Any]:
    base = dict(existing) if existing else {}
    adapter = dict(entry.adapters[host])
    if map_mode:
        adapter.pop("event", None)
    base.update(adapter)
    base["agentConfigId"] = entry.id
    return base


def hook_matches(entry: HookEntry, actual: dict[str, Any], host: str, bucket: str | None) -> bool:
    if actual.get("agentConfigId") != entry.id:
        return False
    adapter = entry.adapters[host]
    for key, val in adapter.items():
        if key == "event":
            actual_event = actual.get("event", bucket)
            if actual_event != val:
                return False
            continue
        if actual.get(key) != val:
            return False
    return True
