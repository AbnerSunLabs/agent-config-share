import json

from agent_config.adapters import starfactory
from agent_config.schema import parse_mcp


def test_starfactory_missing_file_is_error(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    entries = parse_mcp(
        {
            "mcp": [
                {
                    "id": "ctx",
                    "description": "用途",
                    "hosts": ["starFactory"],
                    "transport": "stdio",
                    "command": "npx",
                    "args": [],
                }
            ]
        }
    )
    r = starfactory.check_mcp(entries)
    assert r.file_error is True


def test_apply_creates_marked_server_with_env_ref(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    p = tmp_path / ".starFactory.json"
    p.write_text(json.dumps({"other": 1}))
    entries = parse_mcp(
        {
            "mcp": [
                {
                    "id": "ctx",
                    "description": "用途",
                    "hosts": ["starFactory"],
                    "transport": "stdio",
                    "command": "npx",
                    "args": ["-y", "pkg"],
                    "env": ["K"],
                }
            ]
        }
    )
    starfactory.apply_mcp(entries, prune=False)
    data = json.loads(p.read_text())
    assert data["other"] == 1
    srv = data["mcpServers"]["ctx"]
    assert srv["agentConfigId"] == "ctx"
    assert srv["env"]["K"] == "${K}"


def test_apply_skips_when_file_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    entries = parse_mcp(
        {
            "mcp": [
                {
                    "id": "ctx",
                    "description": "用途",
                    "hosts": ["starFactory"],
                    "transport": "stdio",
                    "command": "npx",
                    "args": [],
                }
            ]
        }
    )
    starfactory.apply_mcp(entries, prune=False)
    assert not (tmp_path / ".starFactory.json").exists()


def test_prune_skips_unmarked_extra(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    p = tmp_path / ".starFactory.json"
    p.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "ctx": {"command": "npx", "args": [], "agentConfigId": "ctx"},
                    "hand": {"command": "npx", "args": []},
                }
            }
        )
    )
    starfactory.apply_mcp([], prune=True)
    data = json.loads(p.read_text())
    assert "hand" in data["mcpServers"]
    assert "ctx" not in data["mcpServers"]


def test_check_reports_drift_for_orphan_marked_server(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    p = tmp_path / ".starFactory.json"
    p.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "old": {"command": "npx", "args": [], "agentConfigId": "old"},
                }
            }
        )
    )
    result = starfactory.check_mcp([])
    assert result.file_error is False
    assert result.gaps == []
    assert "old" in result.drift


def test_check_file_error_on_invalid_json(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    p = tmp_path / ".starFactory.json"
    p.write_text("{")
    result = starfactory.check_mcp([])
    assert result.file_error is True
    assert result.gaps == []
    assert result.drift == []
