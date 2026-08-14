"""面板目录：Skills 扫描与 MCP/Hooks 卡片装配。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agent_config import paths, sync
from agent_config.models import CheckResult, HookEntry, McpEntry
from agent_config.schema import HOSTS

SKILL_ROOTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (".agents", HOSTS),
    (".cursor", ("cursor",)),
    (".codex", ("codex",)),
    (".starFactory", ("starFactory",)),
)

_STATUS_RANK = {
    "file_error": 4,
    "gap": 3,
    "drift": 2,
    "aligned": 1,
    "unknown": 0,
    "readonly": 0,
}


def rollup_status(states: list[str]) -> str:
    """按 file_error > gap > drift > aligned 取最高优先级。"""
    if not states:
        return "unknown"
    return max(states, key=lambda item: _STATUS_RANK.get(item, 0))


def parse_skill_description(skill_md: Path) -> str:
    """读取 SKILL.md YAML frontmatter 的 description，缺省为空串。"""
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return ""
    if not text.startswith("---"):
        return ""
    rest = text[3:]
    end = rest.find("\n---")
    if end < 0:
        return ""
    data = yaml.safe_load(rest[:end]) or {}
    if not isinstance(data, dict):
        return ""
    value = data.get("description")
    if not isinstance(value, str):
        return ""
    return value.strip()


def scan_skills(home: Path | None = None) -> list[dict[str, Any]]:
    """扫描一层 Skills 目录，同名不同根拆成多张卡。"""
    root_home = home if home is not None else paths.home()
    cards: list[dict[str, Any]] = []
    for folder, hosts in SKILL_ROOTS:
        skills_root = root_home / folder / "skills"
        try:
            if not skills_root.is_dir():
                continue
            children = list(skills_root.iterdir())
        except OSError:
            continue
        for child in children:
            skill_md = child / "SKILL.md"
            try:
                is_skill = child.is_dir() and skill_md.is_file()
            except OSError:
                continue
            if not is_skill:
                continue
            cards.append(
                {
                    "id": child.name,
                    "path": str(child.resolve()),
                    "description": parse_skill_description(skill_md),
                    "roots": [folder],
                    "hosts": list(hosts),
                    "status": "readonly",
                }
            )
    return cards


def mcp_card(entry: McpEntry) -> dict[str, Any]:
    env_names = list(entry.env or [])
    if entry.headers_env:
        for name in entry.headers_env.values():
            if name not in env_names:
                env_names.append(name)
    return {
        "id": entry.id,
        "transport": entry.transport,
        "description": entry.description,
        "hosts": list(entry.hosts),
        "env_names": env_names,
        "per_host": {},
        "status": "unknown",
    }


def hook_card(entry: HookEntry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "intent": entry.intent,
        "description": entry.description,
        "hosts": list(entry.hosts),
        "per_host": {},
        "status": "unknown",
    }


def _apply_check(
    cards: list[dict[str, Any]], host: str, result: CheckResult
) -> None:
    """把一次 only=mcp|hooks 且单宿主的 CheckResult 写到卡片 per_host。"""
    for card in cards:
        if host not in card["hosts"]:
            continue
        if result.file_error:
            card["per_host"][host] = "file_error"
            continue
        card_id = card["id"]
        if card_id in result.gaps:
            card["per_host"][host] = "gap"
        elif card_id in result.drift:
            card["per_host"][host] = "drift"
        else:
            card["per_host"][host] = "aligned"


def _refresh_rollup(cards: list[dict[str, Any]], hosts: list[str]) -> None:
    for card in cards:
        states = [
            card["per_host"][host]
            for host in hosts
            if host in card["hosts"] and host in card["per_host"]
        ]
        card["status"] = rollup_status(states)


def build_catalog(
    mcp_entries: list[McpEntry],
    hook_entries: list[HookEntry],
    *,
    home: Path | None = None,
) -> dict[str, Any]:
    """未检查时的卡片列表。"""
    return {
        "error": None,
        "skills": scan_skills(home),
        "mcp": [mcp_card(entry) for entry in mcp_entries],
        "hooks": [hook_card(entry) for entry in hook_entries],
    }


def annotate_status(
    catalog: dict[str, Any],
    mcp_entries: list[McpEntry],
    hook_entries: list[HookEntry],
    hosts: list[str],
    only: str | None,
) -> dict[str, Any]:
    """按宿主分别 only=mcp / only=hooks 调用 sync.check，禁止合并结果直接上卡。"""
    summary: dict[str, Any] = {}
    mcp_cards: list[dict[str, Any]] = catalog["mcp"]
    hook_cards: list[dict[str, Any]] = catalog["hooks"]
    for host in hosts:
        row = {"mcp_gaps": 0, "hooks_gaps": 0, "drift": 0, "file_error": False}
        if only in (None, "mcp"):
            result = sync.check(
                mcp_entries, hook_entries, only="mcp", hosts=[host]
            )
            _apply_check(mcp_cards, host, result)
            row["mcp_gaps"] = len(result.gaps)
            row["drift"] += len(result.drift)
            row["file_error"] = row["file_error"] or result.file_error
        if only in (None, "hooks"):
            result = sync.check(
                mcp_entries, hook_entries, only="hooks", hosts=[host]
            )
            _apply_check(hook_cards, host, result)
            row["hooks_gaps"] = len(result.gaps)
            row["drift"] += len(result.drift)
            row["file_error"] = row["file_error"] or result.file_error
        summary[host] = row
    _refresh_rollup(mcp_cards, hosts)
    _refresh_rollup(hook_cards, hosts)
    catalog["summary"] = summary
    return catalog
