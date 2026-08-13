import json

from agent_config.adapters import cursor
from agent_config.schema import parse_mcp


def test_apply_creates_marked_server_with_env_ref(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    entries = parse_mcp(
        {
            "mcp": [
                {
                    "id": "ctx",
                    "hosts": ["cursor"],
                    "transport": "stdio",
                    "command": "npx",
                    "args": ["-y", "pkg"],
                    "env": ["K"],
                }
            ]
        }
    )
    cursor.apply_mcp(entries, prune=False)
    data = json.loads((tmp_path / ".cursor" / "mcp.json").read_text())
    srv = data["mcpServers"]["ctx"]
    assert srv["agentConfigId"] == "ctx"
    assert srv["env"]["K"] == "${env:K}"


def test_prune_skips_unmarked_extra(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    p = tmp_path / ".cursor" / "mcp.json"
    p.parent.mkdir(parents=True)
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
    cursor.apply_mcp([], prune=True)
    data = json.loads(p.read_text())
    assert "hand" in data["mcpServers"]
    assert "ctx" not in data["mcpServers"]


def test_check_reports_gap_when_env_value_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    p = tmp_path / ".cursor" / "mcp.json"
    p.parent.mkdir(parents=True)
    p.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "ctx": {
                        "command": "npx",
                        "args": [],
                        "agentConfigId": "ctx",
                        "env": {"K": ""},
                    },
                }
            }
        )
    )
    entries = parse_mcp(
        {
            "mcp": [
                {
                    "id": "ctx",
                    "hosts": ["cursor"],
                    "transport": "stdio",
                    "command": "npx",
                    "args": [],
                    "env": ["K"],
                }
            ]
        }
    )
    result = cursor.check_mcp(entries)
    assert result.file_error is False
    assert "ctx" in result.gaps
    assert result.drift == []


def test_check_reports_gap_when_server_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    entries = parse_mcp(
        {
            "mcp": [
                {
                    "id": "ctx",
                    "hosts": ["cursor"],
                    "transport": "stdio",
                    "command": "npx",
                    "args": [],
                }
            ]
        }
    )
    result = cursor.check_mcp(entries)
    assert result.file_error is False
    assert "ctx" in result.gaps
    assert result.drift == []


def test_check_reports_drift_for_orphan_marked_server(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    p = tmp_path / ".cursor" / "mcp.json"
    p.parent.mkdir(parents=True)
    p.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "old": {"command": "npx", "args": [], "agentConfigId": "old"},
                }
            }
        )
    )
    result = cursor.check_mcp([])
    assert result.file_error is False
    assert result.gaps == []
    assert "old" in result.drift


def test_check_file_error_on_invalid_json(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    p = tmp_path / ".cursor" / "mcp.json"
    p.parent.mkdir(parents=True)
    p.write_text("{")
    result = cursor.check_mcp([])
    assert result.file_error is True
    assert result.gaps == []
    assert result.drift == []


def test_apply_skips_write_on_invalid_json(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    p = tmp_path / ".cursor" / "mcp.json"
    p.parent.mkdir(parents=True)
    p.write_text("{")
    entries = parse_mcp(
        {
            "mcp": [
                {
                    "id": "ctx",
                    "hosts": ["cursor"],
                    "transport": "stdio",
                    "command": "npx",
                    "args": [],
                }
            ]
        }
    )
    cursor.apply_mcp(entries, prune=False)
    assert p.read_text() == "{"
