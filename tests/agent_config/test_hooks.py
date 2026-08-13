import json

from agent_config.schema import parse_hooks
from agent_config.adapters import cursor, codex


def test_hook_skips_cursor_when_not_in_hosts(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "hooks.json").write_text(json.dumps({"hooks": []}))
    entries = parse_hooks({"hooks": [{"id": "git-ai-checkpoint", "hosts": ["codex"],
                                      "intent": "git-ai", "adapters": {"codex": {"command": "git-ai"}}}]})
    cursor.apply_hooks(entries, prune=False)
    data = json.loads((tmp_path / ".cursor" / "hooks.json").read_text())
    assert data["hooks"] == []


def test_codex_uses_toml_hooks_not_new_json(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    d = tmp_path / ".codex"
    d.mkdir()
    (d / "config.toml").write_text("[hooks]\nplaceholder = true\n")
    entries = parse_hooks({"hooks": [{"id": "h", "hosts": ["codex"], "intent": "i",
                                      "adapters": {"codex": {"command": "git-ai"}}}]})
    codex.apply_hooks(entries, prune=False)
    assert not (d / "hooks.json").exists()
    assert "git-ai" in (d / "config.toml").read_text()
