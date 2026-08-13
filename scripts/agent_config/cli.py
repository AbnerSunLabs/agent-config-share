"""agent-config CLI 入口。"""

from __future__ import annotations

import argparse
import sys

from agent_config import sync
from agent_config.schema import SchemaError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-config")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="同步 MCP / Hooks 配置")
    sync_parser.add_argument(
        "--check",
        action="store_true",
        help="只检查差异（默认行为）",
    )
    sync_parser.add_argument(
        "--apply",
        action="store_true",
        help="合并写入目标配置",
    )
    sync_parser.add_argument(
        "--prune",
        action="store_true",
        help="删除清单中已移除的托管条目（须与 --apply 同用）",
    )
    sync_parser.add_argument(
        "--only",
        choices=("mcp", "hooks"),
        default=None,
        help="仅处理 MCP 或 Hooks 域",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command != "sync":
        return 2

    if args.prune and not args.apply:
        return 2

    try:
        mcp_entries, hook_entries = sync.load_inventory()
    except SchemaError:
        return 2

    only: str | None = args.only

    if args.apply:
        paths = sync.collect_apply_paths(only)
        sync.backup_files(paths)
        sync.apply(mcp_entries, hook_entries, only=only, prune=args.prune)

    result = sync.check(mcp_entries, hook_entries, only=only)
    sync.print_result(result)
    return sync.exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
