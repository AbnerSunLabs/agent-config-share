import tomllib

from agent_config.adapters import codex
from agent_config.schema import parse_mcp


def test_codex_keeps_unrelated_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    cfg = tmp_path / ".codex" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text('model = "gpt"\n')
    entries = parse_mcp(
        {
            "mcp": [
                {
                    "id": "ctx",
                    "description": "用途",
                    "hosts": ["codex"],
                    "transport": "stdio",
                    "command": "npx",
                    "args": ["-y", "pkg"],
                }
            ]
        }
    )
    codex.apply_mcp(entries, prune=False)
    text = cfg.read_text()
    assert "model" in text
    assert "ctx" in text
    assert "agent_config_id" in text


def test_codex_missing_file_is_error(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    entries = parse_mcp(
        {
            "mcp": [
                {
                    "id": "ctx",
                    "description": "用途",
                    "hosts": ["codex"],
                    "transport": "stdio",
                    "command": "npx",
                    "args": [],
                }
            ]
        }
    )
    r = codex.check_mcp(entries)
    assert r.file_error is True


def test_apply_creates_marked_server_with_env_ref(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    cfg = tmp_path / ".codex" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text('model = "gpt"\n')
    entries = parse_mcp(
        {
            "mcp": [
                {
                    "id": "ctx",
                    "description": "用途",
                    "hosts": ["codex"],
                    "transport": "stdio",
                    "command": "npx",
                    "args": ["-y", "pkg"],
                    "env": ["K"],
                }
            ]
        }
    )
    codex.apply_mcp(entries, prune=False)
    doc = tomllib.loads(cfg.read_text(encoding="utf-8"))
    srv = doc["mcp_servers"]["ctx"]
    assert srv["agent_config_id"] == "ctx"
    assert srv["env"]["K"] == "${K}"


def test_apply_skips_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    entries = parse_mcp(
        {
            "mcp": [
                {
                    "id": "ctx",
                    "description": "用途",
                    "hosts": ["codex"],
                    "transport": "stdio",
                    "command": "npx",
                    "args": [],
                }
            ]
        }
    )
    codex.apply_mcp(entries, prune=False)
    assert not (tmp_path / ".codex" / "config.toml").exists()


def test_prune_skips_unmarked_extra(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    cfg = tmp_path / ".codex" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(
        '[mcp_servers.ctx]\ncommand = "npx"\nargs = []\nagent_config_id = "ctx"\n\n'
        '[mcp_servers.hand]\ncommand = "npx"\nargs = []\n'
    )
    codex.apply_mcp([], prune=True)
    doc = tomllib.loads(cfg.read_text(encoding="utf-8"))
    assert "hand" in doc["mcp_servers"]
    assert "ctx" not in doc["mcp_servers"]
