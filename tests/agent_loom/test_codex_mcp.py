import tomllib

from agent_loom.adapters import codex
from agent_loom.schema import parse_mcp


def test_dump_toml_quotes_unsafe_keys_so_codex_can_reload():
    """路径 / @ 等不能当裸键；整文件 dump 后必须仍能被 tomllib 解析。"""
    doc = {
        "model": "gpt-5.6-sol",
        "desktop": {
            "open-in-target-preferences": {
                "global": "cursor",
                "perPath": {
                    "/Users/abnersun/Downloads/code/stock-view": "cursor",
                    'foo"bar': "quoted-key",
                },
            }
        },
        "hooks": {
            "state": {
                "/Users/abnersun/.codex/config.toml:post_tool_use:0:0": {
                    "enabled": True,
                }
            }
        },
        "plugins": {"build-web-apps@openai-curated": {"enabled": True}},
        "projects": {
            "/Users/abnersun/Downloads/code/stock-view": {
                "trust_level": "trusted",
            }
        },
        "inline": [{"/tmp/a": 1}],
    }
    text = codex.dump_toml(doc)
    assert tomllib.loads(text) == doc
    assert "\n/Users/" not in text
    assert '"/Users/abnersun/Downloads/code/stock-view"' in text
    assert 'plugins."build-web-apps@openai-curated"' in text
    assert (
        'hooks.state."/Users/abnersun/.codex/config.toml:post_tool_use:0:0"'
        in text
    )


def test_apply_mcp_roundtrip_keeps_quoted_path_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_LOOM_HOME", str(tmp_path))
    cfg = tmp_path / ".codex" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(
        "model = \"gpt\"\n"
        "[desktop.open-in-target-preferences.perPath]\n"
        '"/Users/abnersun/Downloads/code/stock-view" = "cursor"\n'
        '[plugins."build-web-apps@openai-curated"]\n'
        "enabled = true\n"
        '[projects."/Users/abnersun/Downloads/code/side-thread"]\n'
        'trust_level = "trusted"\n',
        encoding="utf-8",
    )
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
    text = cfg.read_text(encoding="utf-8")
    tomllib.loads(text)
    assert "\n/Users/" not in text
    assert '"/Users/abnersun/Downloads/code/stock-view"' in text
    assert 'plugins."build-web-apps@openai-curated"' in text
    assert 'projects."/Users/abnersun/Downloads/code/side-thread"' in text


def test_codex_keeps_unrelated_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_LOOM_HOME", str(tmp_path))
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
    assert "agent_loom_id" in text


def test_codex_missing_file_is_error(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_LOOM_HOME", str(tmp_path))
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
    monkeypatch.setenv("AGENT_LOOM_HOME", str(tmp_path))
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
    assert srv["agent_loom_id"] == "ctx"
    assert srv["env"]["K"] == "${K}"


def test_apply_skips_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_LOOM_HOME", str(tmp_path))
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
    monkeypatch.setenv("AGENT_LOOM_HOME", str(tmp_path))
    cfg = tmp_path / ".codex" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(
        '[mcp_servers.ctx]\ncommand = "npx"\nargs = []\nagent_loom_id = "ctx"\n\n'
        '[mcp_servers.hand]\ncommand = "npx"\nargs = []\n'
    )
    codex.apply_mcp([], prune=True)
    doc = tomllib.loads(cfg.read_text(encoding="utf-8"))
    assert "hand" in doc["mcp_servers"]
    assert "ctx" not in doc["mcp_servers"]
