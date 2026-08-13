"""跨宿主 MCP 同步编排（Task 4 仅 Cursor，其余 no-op）。"""

from __future__ import annotations

from agent_config.adapters import cursor
from agent_config.models import CheckResult, McpEntry


def check_mcp(entries: list[McpEntry]) -> CheckResult:
    return cursor.check_mcp(entries)


def apply_mcp(entries: list[McpEntry], prune: bool = False) -> None:
    cursor.apply_mcp(entries, prune=prune)
