import pytest
from agent_config.schema import SchemaError, parse_hooks, parse_mcp


def test_mcp_rejects_env_values():
    with pytest.raises(SchemaError):
        parse_mcp({"mcp": [{"id": "x", "hosts": ["cursor"], "transport": "stdio",
                            "command": "npx", "args": [], "env": {"K": "secret"}}]})


def test_mcp_stdio_ok():
    rows = parse_mcp({"mcp": [{"id": "x", "hosts": ["cursor"], "transport": "stdio",
                               "command": "npx", "args": ["-y", "pkg"], "env": ["K"]}]})
    assert rows[0].id == "x"
    assert rows[0].env == ["K"]


def test_hooks_require_adapter_for_each_host():
    with pytest.raises(SchemaError):
        parse_hooks({"hooks": [{"id": "h", "hosts": ["codex", "starFactory"],
                                "intent": "x", "adapters": {"codex": {"command": "git-ai"}}}]})
