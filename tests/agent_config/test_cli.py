from pathlib import Path

from agent_config.cli import main


def test_only_hooks_ignores_broken_mcp_json(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    inv = tmp_path / "inv"
    inv.mkdir()
    (inv / "mcp.yaml").write_text("mcp: []\n")
    (inv / "hooks.yaml").write_text("hooks: []\n")
    monkeypatch.setattr("agent_config.paths.inventory_dir", lambda: inv)
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text("{")
    (tmp_path / ".cursor" / "hooks.json").write_text('{"hooks": []}')
    assert main(["sync", "--only", "hooks"]) == 0


def test_apply_requires_prune_flag_combo(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    inv = tmp_path / "inv"
    inv.mkdir()
    (inv / "mcp.yaml").write_text("mcp: []\n")
    (inv / "hooks.yaml").write_text("hooks: []\n")
    monkeypatch.setattr("agent_config.paths.inventory_dir", lambda: inv)
    assert main(["sync", "--prune"]) == 2


def test_schema_error_exits_2(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    inv = tmp_path / "inv"
    inv.mkdir()
    (inv / "mcp.yaml").write_text("mcp: not-a-list\n")
    (inv / "hooks.yaml").write_text("hooks: []\n")
    monkeypatch.setattr("agent_config.paths.inventory_dir", lambda: inv)
    assert main(["sync"]) == 2
    err = capsys.readouterr().err
    assert "清单无效" in err


def test_check_prints_ok_when_clean(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    inv = tmp_path / "inv"
    inv.mkdir()
    (inv / "mcp.yaml").write_text("mcp: []\n")
    (inv / "hooks.yaml").write_text("hooks: []\n")
    monkeypatch.setattr("agent_config.paths.inventory_dir", lambda: inv)
    assert main(["sync", "--only", "mcp"]) == 0
    assert "OK" in capsys.readouterr().out


def test_check_prints_unreadable_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    inv = tmp_path / "inv"
    inv.mkdir()
    (inv / "mcp.yaml").write_text("mcp: []\n")
    (inv / "hooks.yaml").write_text("hooks: []\n")
    monkeypatch.setattr("agent_config.paths.inventory_dir", lambda: inv)
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text("{")
    assert main(["sync", "--only", "mcp"]) == 2
    err = capsys.readouterr().err
    assert "文件无法解析" in err
    assert "mcp.json" in err


def test_gaps_exit_1(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    inv = tmp_path / "inv"
    inv.mkdir()
    (inv / "mcp.yaml").write_text(
        "mcp:\n"
        "  - id: srv\n"
        "    hosts: [cursor]\n"
        "    transport: stdio\n"
        "    command: echo\n"
        "    args: []\n"
    )
    (inv / "hooks.yaml").write_text("hooks: []\n")
    monkeypatch.setattr("agent_config.paths.inventory_dir", lambda: inv)
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text('{"mcpServers": {}}')
    assert main(["sync", "--only", "mcp"]) == 1


def test_apply_backups_existing_files(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    inv = tmp_path / "inv"
    inv.mkdir()
    (inv / "mcp.yaml").write_text(
        "mcp:\n"
        "  - id: srv\n"
        "    hosts: [cursor]\n"
        "    transport: stdio\n"
        "    command: echo\n"
        "    args: []\n"
    )
    (inv / "hooks.yaml").write_text("hooks: []\n")
    monkeypatch.setattr("agent_config.paths.inventory_dir", lambda: inv)
    cursor_dir = tmp_path / ".cursor"
    cursor_dir.mkdir()
    original = '{"mcpServers": {}}'
    mcp_file = cursor_dir / "mcp.json"
    mcp_file.write_text(original)
    backup_dirs: list[str] = []
    real_mkdtemp = __import__("tempfile").mkdtemp

    def capture_mkdtemp(**kwargs):
        d = real_mkdtemp(**kwargs)
        backup_dirs.append(d)
        return d

    monkeypatch.setattr("agent_config.sync.tempfile.mkdtemp", capture_mkdtemp)
    assert main(["sync", "--apply", "--only", "mcp"]) == 0
    assert backup_dirs
    backup_mcp = Path(backup_dirs[0]) / "mcp.json"
    assert backup_mcp.read_text() == original


def test_sync_check_mcp_aggregates_three_hosts(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    from agent_config import sync
    from agent_config.schema import parse_mcp

    (tmp_path / ".starFactory.json").write_text("{")
    entries = parse_mcp(
        {
            "mcp": [
                {
                    "id": "x",
                    "hosts": ["starFactory"],
                    "transport": "stdio",
                    "command": "echo",
                    "args": [],
                }
            ]
        }
    )
    result = sync.check_mcp(entries)
    assert result.file_error is True
