"""跨宿主 MCP / Hooks 同步编排。"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from agent_config.adapters import codex, cursor, starfactory
from agent_config.models import CheckResult, HookEntry, McpEntry, load_yaml
from agent_config import paths
from agent_config.redact import safe_print
from agent_config.schema import HOSTS, parse_hooks, parse_mcp

_ADAPTERS = {
    "cursor": cursor,
    "codex": codex,
    "starFactory": starfactory,
}


def _selected_hosts(hosts: list[str] | None) -> list[str]:
    if not hosts:
        return list(HOSTS)
    return list(hosts)


def _merge_check_results(results: list[CheckResult]) -> CheckResult:
    gaps: list[str] = []
    drift: list[str] = []
    file_errors: list[str] = []
    file_error = False
    for result in results:
        gaps.extend(result.gaps)
        drift.extend(result.drift)
        file_errors.extend(result.file_errors)
        if result.file_error:
            file_error = True
    return CheckResult(
        gaps=gaps, drift=drift, file_error=file_error, file_errors=file_errors
    )


def check_mcp(entries: list[McpEntry], hosts: list[str] | None = None) -> CheckResult:
    results = []
    for name in _selected_hosts(hosts):
        results.append(_ADAPTERS[name].check_mcp(entries))
    return _merge_check_results(results)


def apply_mcp(
    entries: list[McpEntry], prune: bool = False, hosts: list[str] | None = None
) -> None:
    for name in _selected_hosts(hosts):
        _ADAPTERS[name].apply_mcp(entries, prune=prune)


def check_hooks(entries: list[HookEntry], hosts: list[str] | None = None) -> CheckResult:
    results = []
    for name in _selected_hosts(hosts):
        results.append(_ADAPTERS[name].check_hooks(entries))
    return _merge_check_results(results)


def apply_hooks(
    entries: list[HookEntry], prune: bool = False, hosts: list[str] | None = None
) -> None:
    for name in _selected_hosts(hosts):
        _ADAPTERS[name].apply_hooks(entries, prune=prune)


def apply_all(
    mcp_entries: list[McpEntry],
    hook_entries: list[HookEntry],
    prune: bool = False,
    hosts: list[str] | None = None,
) -> None:
    selected = _selected_hosts(hosts)
    if "cursor" in selected:
        cursor.apply_mcp(mcp_entries, prune=prune)
        cursor.apply_hooks(hook_entries, prune=prune)
    if "starFactory" in selected:
        starfactory.apply_mcp(mcp_entries, prune=prune)
        starfactory.apply_hooks(hook_entries, prune=prune)
    if "codex" in selected:
        # MCP 与 Hooks 可能写同一份 config.toml，必须一次读改写
        codex.apply_all(mcp_entries, hook_entries, prune=prune)


def load_inventory() -> tuple[list[McpEntry], list[HookEntry]]:
    """从 inventory 目录加载并校验清单。"""
    inv = paths.inventory_dir()
    mcp_data = load_yaml(inv / "mcp.yaml")
    hooks_data = load_yaml(inv / "hooks.yaml")
    return parse_mcp(mcp_data), parse_hooks(hooks_data)


def check(
    mcp_entries: list[McpEntry],
    hook_entries: list[HookEntry],
    only: str | None = None,
    hosts: list[str] | None = None,
) -> CheckResult:
    """对所选域、所选宿主执行 check 并汇总结果。"""
    results: list[CheckResult] = []
    if only in (None, "mcp"):
        results.append(check_mcp(mcp_entries, hosts=hosts))
    if only in (None, "hooks"):
        results.append(check_hooks(hook_entries, hosts=hosts))
    if not results:
        return CheckResult(gaps=[], drift=[], file_error=False)
    return _merge_check_results(results)


def apply(
    mcp_entries: list[McpEntry],
    hook_entries: list[HookEntry],
    only: str | None = None,
    prune: bool = False,
    hosts: list[str] | None = None,
) -> None:
    """对所选域、所选宿主执行 apply。"""
    if only is None:
        apply_all(mcp_entries, hook_entries, prune=prune, hosts=hosts)
        return
    if only == "mcp":
        apply_mcp(mcp_entries, prune=prune, hosts=hosts)
        return
    apply_hooks(hook_entries, prune=prune, hosts=hosts)


def _codex_hooks_path() -> Path | None:
    path, _, target_error = codex.resolve_hooks_target()
    if target_error:
        return None
    return path


def collect_apply_paths(
    only: str | None = None, hosts: list[str] | None = None
) -> list[Path]:
    """收集 apply 可能写入的目标文件路径（去重）。"""
    selected = set(_selected_hosts(hosts))
    paths: list[Path] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        if path not in seen:
            seen.add(path)
            paths.append(path)

    if only in (None, "mcp"):
        if "cursor" in selected:
            add(cursor.mcp_path())
        if "codex" in selected:
            add(codex.mcp_path())
        if "starFactory" in selected:
            add(starfactory.mcp_path())
    if only in (None, "hooks"):
        if "cursor" in selected:
            add(cursor.hooks_path())
        if "starFactory" in selected:
            add(starfactory.hooks_path())
        if "codex" in selected:
            hooks_path = _codex_hooks_path()
            if hooks_path is not None:
                add(hooks_path)
    return paths


def backup_files(paths: list[Path]) -> Path | None:
    """将存在的目标文件复制到临时备份目录。"""
    existing = [p for p in paths if p.is_file()]
    if not existing:
        return None
    backup_dir = Path(tempfile.mkdtemp(prefix="agent-config-"))
    for path in existing:
        dest = backup_dir / path.name
        if dest.exists():
            dest = backup_dir / f"{path.parent.name}-{path.name}"
        shutil.copy2(path, dest)
    return backup_dir


def exit_code(result: CheckResult) -> int:
    """根据 CheckResult 计算 CLI 退出码。"""
    if result.file_error:
        return 2
    if result.gaps:
        return 1
    return 0


def print_result(result: CheckResult) -> None:
    """打印缺口、漂移与无法解析的文件。"""
    import sys

    for path in result.file_errors:
        safe_print(f"文件无法解析: {path}", file=sys.stderr)
    for gap in result.gaps:
        safe_print(f"缺口: {gap}")
    for item in result.drift:
        safe_print(f"漂移: {item}")
    if not result.file_error and not result.gaps and not result.drift:
        safe_print("OK")
