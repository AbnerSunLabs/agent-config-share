from pathlib import Path
from agent_config.paths import inventory_dir, repo_root
from agent_config.models import load_yaml


def test_inventory_yaml_loads_empty_lists():
    root = repo_root()
    assert (root / "inventory" / "mcp.yaml").is_file()
    mcp = load_yaml(inventory_dir() / "mcp.yaml")
    hooks = load_yaml(inventory_dir() / "hooks.yaml")
    assert mcp.get("mcp") == []
    assert hooks.get("hooks") == []
