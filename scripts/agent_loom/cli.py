"""agentloom CLI 入口。"""

from __future__ import annotations

import argparse
import sys

from agent_loom import sync
from agent_loom.schema import HOSTS, SchemaError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentloom")
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
    sync_parser.add_argument(
        "--host",
        dest="hosts",
        action="append",
        choices=HOSTS,
        metavar="HOST",
        help="只同步到指定宿主（cursor / codex / starFactory），可重复。默认三家",
    )
    ui_parser = subparsers.add_parser("ui", help="打开本机配置面板")
    ui_parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="仅绑定 127.0.0.1 的端口",
    )
    ui_parser.add_argument(
        "--no-open",
        action="store_true",
        help="不调用系统浏览器",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "ui":
        from agent_loom.ui import serve

        return serve(args.port, open_browser=not args.no_open)

    if args.command != "sync":
        return 2

    if args.prune and not args.apply:
        return 2

    try:
        mcp_entries, hook_entries = sync.load_inventory()
    except SchemaError as exc:
        print(f"清单无效: {exc}", file=sys.stderr)
        return 2

    only: str | None = args.only
    hosts: list[str] | None = args.hosts

    if args.apply:
        paths = sync.collect_apply_paths(only, hosts=hosts)
        sync.backup_files(paths)
        sync.apply(
            mcp_entries, hook_entries, only=only, prune=args.prune, hosts=hosts
        )

    result = sync.check(mcp_entries, hook_entries, only=only, hosts=hosts)
    sync.print_result(result)
    return sync.exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
