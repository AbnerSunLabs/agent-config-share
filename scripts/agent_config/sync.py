"""跨宿主 MCP / Hooks 同步编排。"""

from __future__ import annotations

from agent_config.adapters import codex, cursor, starfactory
from agent_config.models import CheckResult, HookEntry, McpEntry


def check_mcp(entries: list[McpEntry]) -> CheckResult:
    return cursor.check_mcp(entries)


def apply_mcp(entries: list[McpEntry], prune: bool = False) -> None:
    cursor.apply_mcp(entries, prune=prune)


def check_hooks(entries: list[HookEntry]) -> CheckResult:
    return cursor.check_hooks(entries)


def apply_hooks(entries: list[HookEntry], prune: bool = False) -> None:
    cursor.apply_hooks(entries, prune=prune)


def apply_all(
    mcp_entries: list[McpEntry],
    hook_entries: list[HookEntry],
    prune: bool = False,
) -> None:
    cursor.apply_mcp(mcp_entries, prune=prune)
    cursor.apply_hooks(hook_entries, prune=prune)
    starfactory.apply_mcp(mcp_entries, prune=prune)
    starfactory.apply_hooks(hook_entries, prune=prune)
    codex.apply_all(mcp_entries, hook_entries, prune=prune)
