import os
import shutil
import subprocess
from pathlib import Path

from agent_loom.cli import _build_parser


def test_ui_help_lists_command():
    text = _build_parser().format_help()
    assert "ui" in text
    assert "sync" in text


def test_install_sh_syntax():
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["sh", "-n", str(root / "install.sh")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_local_install_writes_shim(tmp_path):
    src = Path(__file__).resolve().parents[2]
    repo = tmp_path / "repo"
    (repo / "inventory").mkdir(parents=True)
    (repo / "scripts").mkdir()
    (repo / "inventory" / "mcp.yaml").write_text("mcp: []\n")
    (repo / "scripts" / "agentloom").write_text("#!/usr/bin/env python3\nprint(0)\n")
    shutil.copy(src / "scripts" / "requirements-run.txt", repo / "scripts" / "requirements-run.txt")
    shutil.copy(src / "install.sh", repo / "install.sh")
    bin_dir = tmp_path / "bin"
    env = dict(os.environ)
    env["AGENT_LOOM_BIN_DIR"] = str(bin_dir)
    env["HOME"] = str(tmp_path)
    result = subprocess.run(
        ["sh", str(repo / "install.sh")],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(repo),
        env=env,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    shim = bin_dir / "agentloom"
    assert shim.is_file()
    text = shim.read_text()
    assert str(repo / ".venv" / "bin" / "python") in text
    assert str(repo / "scripts" / "agentloom") in text
