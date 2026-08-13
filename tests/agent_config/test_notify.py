import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "notify_approval", ROOT / "scripts" / "hooks" / "notify-approval.py"
)
assert SPEC is not None and SPEC.loader is not None
notify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(notify)


def test_custom_title_beats_first_user(tmp_path):
    transcript = tmp_path / "session.jsonl"
    transcript.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "user",
                        "message": {"role": "user", "content": "很长的第一句用户原话"},
                    }
                ),
                json.dumps(
                    {
                        "type": "custom-title",
                        "customTitle": "mcp-audit-log (Branch)",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    title, subtitle, body = notify.build_notification(
        {
            "hook_event_name": "Stop",
            "transcript_path": str(transcript),
        }
    )
    assert title == "mcp-audit-log"
    assert subtitle == "对话结束"
    assert body == ""


def test_first_user_prompt_when_no_custom_title(tmp_path):
    transcript = tmp_path / "session.jsonl"
    transcript.write_text(
        json.dumps(
            {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": "总结一下西安未来7天的天气"}],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    title, _, _ = notify.build_notification(
        {"hook_event_name": "Stop", "transcript_path": str(transcript)}
    )
    assert title == "总结一下西安未来7天的天气"


def test_fallback_session_file_under_starfactory_home(tmp_path):
    cwd = "/Users/demo/proj"
    session = "abc-123"
    encoded = cwd.replace("/", "-")
    path = tmp_path / ".starFactory" / "projects" / encoded
    path.mkdir(parents=True)
    (path / f"{session}.jsonl").write_text(
        json.dumps({"type": "custom-title", "customTitle": "短标题"}) + "\n",
        encoding="utf-8",
    )
    title, subtitle, body = notify.build_notification(
        {
            "hook_event_name": "Notification",
            "session_id": session,
            "cwd": cwd,
            "message": "需要批准 Bash",
        },
        home=tmp_path,
    )
    assert title == "短标题"
    assert subtitle == "等待处理"
    assert "Bash" in body
