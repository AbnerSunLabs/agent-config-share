import json

from agent_config.schema import parse_hooks, parse_mcp
from agent_config import ui, ui_catalog


def _mcp(tmp_path, monkeypatch, text):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    inv = tmp_path / "inv"
    inv.mkdir()
    (inv / "mcp.yaml").write_text(text)
    (inv / "hooks.yaml").write_text("hooks: []\n")
    monkeypatch.setattr("agent_config.paths.inventory_dir", lambda: inv)
    return inv


def test_scan_skills_reads_description_and_splits_roots(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    a = tmp_path / ".agents" / "skills" / "playwright"
    a.mkdir(parents=True)
    (a / "SKILL.md").write_text("---\nname: playwright\ndescription: 浏览器自动化\n---\n# hi\n")
    c = tmp_path / ".cursor" / "skills" / "playwright"
    c.mkdir(parents=True)
    (c / "SKILL.md").write_text("# no frontmatter\n")
    cards = ui_catalog.scan_skills(tmp_path)
    assert len(cards) == 2
    by_root = {card["roots"][0]: card for card in cards}
    assert by_root[".agents"]["description"] == "浏览器自动化"
    assert by_root[".agents"]["hosts"] == ["cursor", "codex", "starFactory"]
    assert by_root[".cursor"]["description"] == ""
    assert by_root[".cursor"]["hosts"] == ["cursor"]
    assert by_root[".agents"]["path"] != by_root[".cursor"]["path"]


def test_file_error_marks_only_that_domain(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    entries = parse_mcp(
        {
            "mcp": [
                {
                    "id": "srv",
                    "description": "用途",
                    "hosts": ["cursor"],
                    "transport": "stdio",
                    "command": "echo",
                    "args": [],
                }
            ]
        }
    )
    hooks = parse_hooks(
        {
            "hooks": [
                {
                    "id": "h",
                    "description": "用途",
                    "hosts": ["cursor"],
                    "intent": "i",
                    "adapters": {"cursor": {"command": "true"}},
                }
            ]
        }
    )
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text("{")
    (tmp_path / ".cursor" / "hooks.json").write_text('{"hooks": []}')
    catalog = ui_catalog.build_catalog(entries, hooks, home=tmp_path)
    ui_catalog.annotate_status(catalog, entries, hooks, ["cursor"], None)
    assert catalog["mcp"][0]["per_host"]["cursor"] == "file_error"
    assert catalog["mcp"][0]["status"] == "file_error"
    assert catalog["hooks"][0]["per_host"]["cursor"] != "file_error"
    assert catalog["summary"]["cursor"]["file_error"] is True


def test_gap_status_and_unmatched_drift_not_a_card(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    entries = parse_mcp(
        {
            "mcp": [
                {
                    "id": "srv",
                    "description": "用途",
                    "hosts": ["cursor"],
                    "transport": "stdio",
                    "command": "echo",
                    "args": [],
                }
            ]
        }
    )
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text('{"mcpServers": {}}')
    catalog = ui_catalog.build_catalog(entries, [], home=tmp_path)
    ui_catalog.annotate_status(catalog, entries, [], ["cursor"], "mcp")
    assert catalog["mcp"][0]["per_host"]["cursor"] == "gap"
    assert catalog["mcp"][0]["status"] == "gap"
    assert [c["id"] for c in catalog["mcp"]] == ["srv"]


def test_dispatch_catalog_and_apply_requires_confirm(tmp_path, monkeypatch):
    _mcp(
        tmp_path,
        monkeypatch,
        "mcp:\n  - id: srv\n    description: 用途\n    hosts: [cursor]\n"
        "    transport: stdio\n    command: echo\n    args: []\n",
    )
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text('{"mcpServers": {}}')
    status, _, body = ui.dispatch("GET", "/api/catalog")
    assert status == 200
    data = json.loads(body)
    assert data["mcp"][0]["id"] == "srv"
    assert data["mcp"][0]["description"] == "用途"
    assert data["mcp"][0]["status"] == "unknown"
    status, _, body = ui.dispatch("POST", "/api/apply", b"{}")
    assert status == 400
    assert json.loads(body)["error"] == "confirm_required"
    assert json.loads((tmp_path / ".cursor" / "mcp.json").read_text()) == {
        "mcpServers": {}
    }


def test_dispatch_apply_writes(tmp_path, monkeypatch):
    _mcp(
        tmp_path,
        monkeypatch,
        "mcp:\n  - id: srv\n    description: 用途\n    hosts: [cursor]\n"
        "    transport: stdio\n    command: echo\n    args: []\n",
    )
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text('{"mcpServers": {}}')
    status, _, body = ui.dispatch(
        "POST",
        "/api/apply",
        json.dumps({"confirm": True, "hosts": ["cursor"], "only": "mcp"}).encode(),
    )
    assert status == 200
    data = json.loads((tmp_path / ".cursor" / "mcp.json").read_text())
    assert "srv" in data["mcpServers"]
    payload = json.loads(body)
    assert payload["mcp"][0]["per_host"]["cursor"] == "aligned"


def test_catalog_schema_error(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    inv = tmp_path / "inv"
    inv.mkdir()
    (inv / "mcp.yaml").write_text("mcp: not-a-list\n")
    (inv / "hooks.yaml").write_text("hooks: []\n")
    monkeypatch.setattr("agent_config.paths.inventory_dir", lambda: inv)
    status, _, body = ui.dispatch("GET", "/api/catalog")
    assert status == 400
    assert json.loads(body)["error"] == "schema"


def test_skills_open_allows_whitelist(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    skill = tmp_path / ".agents" / "skills" / "demo"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\ndescription: 示例\n---\n")
    called = []

    def fake_run(cmd, check, capture_output):
        called.append(cmd)
        return None

    monkeypatch.setattr(ui.subprocess, "run", fake_run)
    status, _, body = ui.dispatch(
        "POST",
        "/api/skills/open",
        json.dumps({"path": str(skill.resolve())}).encode(),
    )
    assert status == 200
    assert json.loads(body)["ok"] is True
    assert called and str(skill.resolve()) in called[0]


def test_skills_open_rejects_outside_whitelist(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    status, _, body = ui.dispatch(
        "POST",
        "/api/skills/open",
        json.dumps({"path": "/tmp/not-a-skill"}).encode(),
    )
    assert status == 400
    assert json.loads(body)["error"] == "not_allowed"


def test_bind_host_is_loopback():
    assert ui.BIND_HOST == "127.0.0.1"


def test_index_served():
    status, ctype, body = ui.dispatch("GET", "/")
    assert status == 200
    assert b"agent-config ui" in body
    assert "html" in ctype


def test_static_rejects_dotdot():
    status, _, _ = ui.dispatch("GET", "/static/../ui.py")
    assert status in (403, 404)
