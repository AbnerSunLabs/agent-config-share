from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class McpEntry:
    id: str
    hosts: list[str]
    transport: str
    command: str | None = None
    args: list[str] | None = None
    url: str | None = None
    env: list[str] | None = None
    headers_env: dict[str, str] | None = None


@dataclass
class HookEntry:
    id: str
    hosts: list[str]
    intent: str
    adapters: dict[str, dict]


def load_yaml(path: Path) -> Any:
    """读取 YAML 文件，空文件或仅含空白时返回空字典。"""
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    return data
