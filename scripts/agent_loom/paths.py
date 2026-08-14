import os
from pathlib import Path


def repo_root() -> Path:
    """向上查找同时包含 inventory/ 与 scripts/ 的仓库根目录。"""
    override = os.environ.get("AGENT_LOOM_ROOT")
    if override:
        return Path(override)
    current = Path(__file__).resolve().parent
    for parent in [current, *current.parents]:
        if (parent / "inventory").is_dir() and (parent / "scripts").is_dir():
            return parent
    raise RuntimeError("无法定位仓库根目录（需同时存在 inventory/ 与 scripts/）")


def home() -> Path:
    """返回用户主目录，优先使用 AGENT_LOOM_HOME 环境变量。"""
    env_home = os.environ.get("AGENT_LOOM_HOME")
    if env_home:
        return Path(env_home)
    return Path.home()


def inventory_dir() -> Path:
    """返回 inventory 目录路径。"""
    return repo_root() / "inventory"
