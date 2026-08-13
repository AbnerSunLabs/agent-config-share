from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> Any:
    """读取 YAML 文件，空文件或仅含空白时返回空字典。"""
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    return data
