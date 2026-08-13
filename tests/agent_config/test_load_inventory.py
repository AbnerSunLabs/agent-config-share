from agent_config.paths import inventory_dir, repo_root
from agent_config.models import load_yaml
from agent_config.schema import parse_hooks, parse_mcp


def test_inventory_yaml_loads_and_parses():
    root = repo_root()
    assert (root / "inventory" / "mcp.yaml").is_file()
    mcp = load_yaml(inventory_dir() / "mcp.yaml")
    hooks = load_yaml(inventory_dir() / "hooks.yaml")
    mcp_rows = parse_mcp(mcp)
    hook_rows = parse_hooks(hooks)
    assert [e.id for e in mcp_rows] == [
        "figma",
        "playwright",
        "github",
        "supabase",
        "vercel",
        "tech-debt",
    ]
    assert [e.id for e in hook_rows] == [
        "git-ai-pre-tool-use",
        "git-ai-post-tool-use",
        "git-ai-stop",
        "macos-approval-notify",
        "macos-stop-notify",
    ]
