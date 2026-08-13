#!/usr/bin/env python3
"""按当前对话短标题发送 macOS 通知中心横幅。不拦截操作。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def escape_applescript(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _clip(text: str, limit: int = 48) -> str:
    text = text.strip()
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def _normalize_title(text: str) -> str:
    text = " ".join(text.strip().split())
    if text.endswith(" (Branch)"):
        text = text[: -len(" (Branch)")].rstrip()
    if not text or text.startswith("/") or "<command-" in text:
        return ""
    if text == "[Request interrupted by user]":
        return ""
    return _clip(text)


def _user_text(obj: dict) -> str:
    message = obj.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text") or ""))
            return "\n".join(parts)
    return ""


def title_from_transcript(path: Path) -> str:
    latest_custom = ""
    first_user = ""
    try:
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict):
                    continue
                if obj.get("type") == "custom-title":
                    title = _normalize_title(str(obj.get("customTitle") or ""))
                    if title:
                        latest_custom = title
                    continue
                if first_user:
                    continue
                if obj.get("type") == "user":
                    title = _normalize_title(_user_text(obj))
                    if title:
                        first_user = title
    except OSError:
        return ""
    return latest_custom or first_user


def conversation_title(data: dict, home: Path | None = None) -> str:
    for key in ("customTitle", "title", "session_title"):
        raw = data.get(key)
        if isinstance(raw, str):
            title = _normalize_title(raw)
            if title:
                return title

    path = data.get("transcript_path")
    if isinstance(path, str) and path:
        title = title_from_transcript(Path(path))
        if title:
            return title

    home = home or Path.home()
    session = data.get("session_id")
    cwd = data.get("cwd")
    if isinstance(session, str) and isinstance(cwd, str) and session and cwd:
        encoded = cwd.replace("/", "-")
        fallback = home / ".starFactory" / "projects" / encoded / f"{session}.jsonl"
        title = title_from_transcript(fallback)
        if title:
            return title

    if isinstance(cwd, str) and cwd:
        name = Path(cwd).name.strip()
        if name:
            return _clip(name)
    return "未命名对话"


def build_notification(data: dict, home: Path | None = None) -> tuple[str, str, str]:
    """返回 (title, subtitle, body)，title 为当前对话短标题。"""
    event = data.get("hook_event_name", "unknown")
    heading = conversation_title(data, home=home)

    if event in ("Stop", "SessionEnd", "SubagentStop"):
        subtitle = {
            "Stop": "对话结束",
            "SessionEnd": "会话结束",
            "SubagentStop": "子任务结束",
        }[event]
        return heading, subtitle, ""

    if event == "Notification":
        body = _clip(str(data.get("message") or "请切回处理"), 80)
        return heading, "等待处理", body

    if event == "PermissionRequest":
        return heading, "权限请求", str(data.get("tool_name") or "工具")

    if event == "beforeShellExecution":
        command = _clip(str(data.get("command") or ""), 80)
        return heading, "终端命令等待批准", command or "（无命令内容）"

    if event == "beforeMCPExecution":
        return heading, "MCP 工具等待批准", str(data.get("tool_name") or "MCP 工具")

    if event == "preToolUse":
        return heading, "工具调用等待批准", str(data.get("tool_name") or "工具")

    return heading, "待处理", "请切回当前窗口"


def show_notification(title: str, subtitle: str, body: str) -> None:
    script = (
        f'display notification "{escape_applescript(body)}" '
        f'with title "{escape_applescript(title)}" '
        f'subtitle "{escape_applescript(subtitle)}" '
        'sound name "Glass"'
    )
    subprocess.Popen(
        ["osascript", "-e", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("{}")
        return 0

    title, subtitle, body = build_notification(data)
    show_notification(title, subtitle, body)
    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
