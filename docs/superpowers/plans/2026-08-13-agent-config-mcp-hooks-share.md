# MCP / Hooks 用户级清单同步 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在本仓库用两份 yaml 清单驱动 CLI，对 Codex / Cursor / starFactory 的用户级 MCP 与 Hooks 做 check / merge apply / prune。

**Architecture:** `scripts/agent-config` 为入口；可 import 包在 `scripts/agent_config/`（对应 spec 的 `agent-config.d`，因目录名无法作为 Python 模块）。清单在 `inventory/`。各宿主适配器只负责本宿主文件的读、期望片段、merge、写。测试通过 `AGENT_CONFIG_HOME` 把 `~` 指到临时目录，禁止写真实主目录。

**Tech Stack:** Python 3.11+（stdlib `tomllib`）、PyYAML、pytest。不改根目录 `package.json`。

## Global Constraints

- 范围仅用户级 MCP / Hooks；不同步 Skills、不调用 skillshare、不做 Web 面板（V1.1）。
- 不写项目级 `.cursor/mcp.json`、项目 `.mcp.json`、`.starFactory/settings.json`、项目 `.codex/`。
- 不创建 `~/.agents/mcp.json`；不读不写 `~/.starFactory/mcp.yaml`。
- 禁止整文件覆盖产品主配置；禁止把密钥字面量写入仓库或从 `.env` 读取。
- JSON 托管标记 `agentConfigId`；TOML 托管标记 `agent_config_id`。
- apply 默认只增不删；`--prune` 只删带标记且（清单无该 id 或当前宿主不在 `hosts`）的条目。
- 退出码：0 无缺口（未 prune 的托管漂移只警告）；1 有缺口；2 禁止创建的文件缺失或解析失败。
- `--only mcp|hooks` 不读取未选中域的文件。
- 日志只打印 id / 路径 / 缺或多，不打印疑似密钥值。
- 适配器按宿主拆分，禁止一个函数写三家格式。
- 每个任务结束用中文 Conventional Commit。

## File map

- Create: `scripts/requirements.txt`（PyYAML、pytest）
- Create: `scripts/agent-config`（入口）
- Create: `scripts/agent_config/`（`cli.py` `models.py` `schema.py` `paths.py` `envmerge.py` `redact.py` `sync.py`）
- Create: `scripts/agent_config/adapters/cursor.py` `codex.py` `starfactory.py`
- Create: `inventory/mcp.yaml` `inventory/hooks.yaml` `inventory/README.md`
- Create: `tests/agent_config/`（pytest，全部走 `AGENT_CONFIG_HOME`）
- Modify: `docs/superpowers/specs/2026-08-13-agent-config-mcp-hooks-share-design.md` 仅当实现时发现 Python 包名与 spec 目录名需加一句交叉引用（本计划已选定 `agent_config/`）

---

### Task 1: 路径、入口与空清单加载

**Files:**

- Create: `scripts/requirements.txt`
- Create: `scripts/agent_config/__init__.py`
- Create: `scripts/agent_config/paths.py`
- Create: `scripts/agent_config/models.py`
- Create: `scripts/agent-config`
- Create: `inventory/mcp.yaml`
- Create: `inventory/hooks.yaml`
- Create: `tests/agent_config/conftest.py`
- Create: `tests/agent_config/test_load_inventory.py`

**Interfaces:**

- Consumes: 无
- Produces: `paths.repo_root() -> Path`；`paths.home() -> Path`（`AGENT_CONFIG_HOME` 或 `Path.home()`）；`paths.inventory_dir() -> Path`；`McpEntry` / `HookEntry` dataclass（本任务只要求能把空 yaml 载成 `list[dict]` 的 `load_yaml(path) -> Any`，完整 dataclass 在 Task 2）

- [ ] **Step 1: Write the failing test**

```python
# tests/agent_config/conftest.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

# tests/agent_config/test_load_inventory.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/abnersun/Downloads/code/personal-ai-development-workflow && PYTHONPATH=scripts python3 -m pytest tests/agent_config/test_load_inventory.py -v`

Expected: FAIL（模块或文件不存在）

- [ ] **Step 3: Write minimal implementation**

`scripts/requirements.txt`:

```text
PyYAML>=6.0
pytest>=8.0
```

`inventory/mcp.yaml`:

```yaml
mcp: []
```

`inventory/hooks.yaml`:

```yaml
hooks: []
```

`scripts/agent_config/paths.py`：`repo_root()` 从 `paths.py` 向上找到同时含 `inventory/` 与 `scripts/` 的目录。`home()` 读 `AGENT_CONFIG_HOME`。

`scripts/agent_config/models.py`：`load_yaml` 用 `yaml.safe_load`，`None` 当 `{}`。

`scripts/agent-config`:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_config.cli import main
if __name__ == "__main__":
    raise SystemExit(main())
```

本任务 `cli.py` 可先 `def main(): return 0`。

- [ ] **Step 4: Run the tests and make sure they pass**

Run: `python3 -m pip install -r scripts/requirements.txt && PYTHONPATH=scripts python3 -m pytest tests/agent_config/test_load_inventory.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/requirements.txt scripts/agent-config scripts/agent_config inventory/mcp.yaml inventory/hooks.yaml tests/agent_config
git commit -m "$(cat <<'EOF'
feat: 增加 agent-config 空清单加载骨架

为后续 MCP/Hooks 同步提供仓库根路径与 yaml 读取入口。
EOF
)"
```

---

### Task 2: 清单 schema 校验

**Files:**

- Modify: `scripts/agent_config/models.py`
- Create: `scripts/agent_config/schema.py`
- Create: `tests/agent_config/test_schema.py`

**Interfaces:**

- Consumes: `load_yaml`
- Produces: `HOSTS = ("cursor", "codex", "starFactory")`；`parse_mcp(data) -> list[McpEntry]`；`parse_hooks(data) -> list[HookEntry]`；非法时 `raise SchemaError`。`McpEntry(id, hosts, transport, command=None, args=None, url=None, env=None, headers_env=None)`。`HookEntry(id, hosts, intent, adapters: dict[str, dict])`。`env` 若出现值（dict 而非 name 列表）则失败。

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=scripts python3 -m pytest tests/agent_config/test_schema.py -v`

Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

校验：`id` 文件内唯一且非空；`hosts` 非空且属于 `HOSTS`；`transport` 为 `stdio`（要 `command`+`args` 列表）或 `http`（要 `url`）；`env` 只能是字符串列表；`headers_env` 只能是 str→str；hooks 的 `adapters` 键集合必须等于 `hosts` 集合，每个值为 mapping。未知字段忽略。

- [ ] **Step 4: Run the tests and make sure they pass**

Run: `PYTHONPATH=scripts python3 -m pytest tests/agent_config/test_schema.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/agent_config/schema.py scripts/agent_config/models.py tests/agent_config/test_schema.py
git commit -m "$(cat <<'EOF'
feat: 校验 MCP/Hooks 清单 schema 并拒绝密钥字面量

保证 inventory 只含意图字段，env 只能写变量名。
EOF
)"
```

---

### Task 3: env 引用 merge 与脱敏

**Files:**

- Create: `scripts/agent_config/envmerge.py`
- Create: `scripts/agent_config/redact.py`
- Create: `tests/agent_config/test_envmerge.py`

**Interfaces:**

- Consumes: 无
- Produces: `is_env_ref(value: str, host: str) -> bool`（Cursor：匹配 `${env:NAME}`；Codex/starFactory：匹配 `${NAME}`）；`merge_env_map(existing: dict[str, str], wanted_names: list[str], host: str) -> dict[str, str]` 实现 spec §4.1 三步；`ref_for(host, name) -> str`；`looks_like_secret(text) -> bool`；`safe_print` 路径不输出 secret。

- [ ] **Step 1: Write the failing test**

```python
from agent_config.envmerge import merge_env_map

def test_keeps_live_literal():
    out = merge_env_map({"K": "sk-live"}, ["K"], "cursor")
    assert out["K"] == "sk-live"

def test_fills_missing_with_cursor_ref():
    out = merge_env_map({}, ["K"], "cursor")
    assert out["K"] == "${env:K}"

def test_rewrites_wrong_ref_name():
    out = merge_env_map({"K": "${env:OLD}"}, ["K"], "cursor")
    assert out["K"] == "${env:K}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=scripts python3 -m pytest tests/agent_config/test_envmerge.py -v`

Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

空字符串视为缺失。禁止调用 `os.environ` 或读取 `.env`。

- [ ] **Step 4: Run the tests and make sure they pass**

Run: `PYTHONPATH=scripts python3 -m pytest tests/agent_config/test_envmerge.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/agent_config/envmerge.py scripts/agent_config/redact.py tests/agent_config/test_envmerge.py
git commit -m "$(cat <<'EOF'
feat: 实现跨宿主 env 引用 merge 且保留现场字面量

新建键只写引用，已有密钥取值不被清单覆盖。
EOF
)"
```

---

### Task 4: Cursor MCP check / apply / prune

**Files:**

- Create: `scripts/agent_config/adapters/__init__.py`
- Create: `scripts/agent_config/adapters/cursor.py`
- Create: `scripts/agent_config/sync.py`（先只调 Cursor MCP；其它宿主 no-op 直到后续任务）
- Create: `tests/agent_config/test_cursor_mcp.py`

**Interfaces:**

- Consumes: `McpEntry`、`merge_env_map`、`paths.home()`
- Produces: `cursor.mcp_path() -> Path`（`home()/.cursor/mcp.json`）；`check_mcp(entries) -> CheckResult`；`apply_mcp(entries, prune: bool) -> None`。`CheckResult` 含 `gaps: list[str]`、`drift: list[str]`、`file_error: bool`。Cursor 服务器对象含 `command`/`args` 或 `url`、`env`、`headers`（由 `headers_env` 生成引用）、`agentConfigId`。允许创建最小 `{"mcpServers": {}}`。

- [ ] **Step 1: Write the failing test**

```python
import json
from agent_config.schema import parse_mcp
from agent_config.adapters import cursor

def test_apply_creates_marked_server_with_env_ref(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    entries = parse_mcp({"mcp": [{"id": "ctx", "hosts": ["cursor"], "transport": "stdio",
                                  "command": "npx", "args": ["-y", "pkg"], "env": ["K"]}]})
    cursor.apply_mcp(entries, prune=False)
    data = json.loads((tmp_path / ".cursor" / "mcp.json").read_text())
    srv = data["mcpServers"]["ctx"]
    assert srv["agentConfigId"] == "ctx"
    assert srv["env"]["K"] == "${env:K}"

def test_prune_skips_unmarked_extra(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    p = tmp_path / ".cursor" / "mcp.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"mcpServers": {
        "ctx": {"command": "npx", "args": [], "agentConfigId": "ctx"},
        "hand": {"command": "npx", "args": []},
    }}))
    cursor.apply_mcp([], prune=True)
    data = json.loads(p.read_text())
    assert "hand" in data["mcpServers"]
    assert "ctx" not in data["mcpServers"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=scripts python3 -m pytest tests/agent_config/test_cursor_mcp.py -v`

Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

upsert 按服务器名 = `id`。`hosts` 不含 `cursor` 的条目：不写入；prune 时若现场有 `agentConfigId==id` 则删除。check：清单需要但缺失或非密钥字段不一致 → gap；现场有标记且（清单无 id 或 cursor 不在 hosts）→ drift。非法 JSON → `file_error=True`，不写盘。

- [ ] **Step 4: Run the tests and make sure they pass**

Run: `PYTHONPATH=scripts python3 -m pytest tests/agent_config/test_cursor_mcp.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/agent_config/adapters scripts/agent_config/sync.py tests/agent_config/test_cursor_mcp.py
git commit -m "$(cat <<'EOF'
feat: 同步 Cursor 用户级 MCP 并支持按标记 prune

清单条目 merge 进 ~/.cursor/mcp.json，手加无标记服务器保留。
EOF
)"
```

---

### Task 5: starFactory 与 Codex MCP

**Files:**

- Create: `scripts/agent_config/adapters/starfactory.py`
- Create: `scripts/agent_config/adapters/codex.py`
- Create: `tests/agent_config/test_starfactory_mcp.py`
- Create: `tests/agent_config/test_codex_mcp.py`

**Interfaces:**

- Consumes: `McpEntry`、`merge_env_map`
- Produces: `starfactory.mcp_path() -> home()/.starFactory.json`，只 merge 顶层 `mcpServers`，**禁止创建**该文件（缺失或坏 JSON → `file_error`）；`codex.mcp_path() -> home()/.codex/config.toml`，只改 `mcp_servers` 表（Codex 键名按常见 `[mcp_servers.<id>]`），写 `agent_config_id`，env 引用 `${NAME}`，**禁止创建**缺失的 `config.toml`。同一 apply 里若还要改 hooks，Task 6 保证按文件串行。读 TOML 用 `tomllib`；写回用「解析为 dict → 只替换 `mcp_servers` → dump 整文件」仅当测试夹具无必须保留的无关注释；实现 `dump_toml(doc) -> str` 覆盖 string/list/table。不扫描 `mcp.yaml`。

- [ ] **Step 1: Write the failing test**

```python
from agent_config.schema import parse_mcp
from agent_config.adapters import starfactory, codex

def test_starfactory_missing_file_is_error(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    entries = parse_mcp({"mcp": [{"id": "ctx", "hosts": ["starFactory"], "transport": "stdio",
                                  "command": "npx", "args": []}]})
    r = starfactory.check_mcp(entries)
    assert r.file_error is True

def test_codex_keeps_unrelated_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    cfg = tmp_path / ".codex" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text('model = "gpt"\n')
    entries = parse_mcp({"mcp": [{"id": "ctx", "hosts": ["codex"], "transport": "stdio",
                                  "command": "npx", "args": ["-y", "pkg"]}]})
    codex.apply_mcp(entries, prune=False)
    text = cfg.read_text()
    assert "model" in text
    assert "ctx" in text
    assert "agent_config_id" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=scripts python3 -m pytest tests/agent_config/test_starfactory_mcp.py tests/agent_config/test_codex_mcp.py -v`

Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

starFactory apply：文件不存在则不创建，调用方记退出码 2。存在则 json load，保留其它顶层键。Codex：`tomllib.loads` 后设置 `doc.setdefault("mcp_servers", {})[id] = {...}` 再 dump。`hosts` 过滤同 Task 4。

- [ ] **Step 4: Run the tests and make sure they pass**

Run: `PYTHONPATH=scripts python3 -m pytest tests/agent_config/test_starfactory_mcp.py tests/agent_config/test_codex_mcp.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/agent_config/adapters/starfactory.py scripts/agent_config/adapters/codex.py tests/agent_config/test_starfactory_mcp.py tests/agent_config/test_codex_mcp.py
git commit -m "$(cat <<'EOF'
feat: 同步 Codex 与 starFactory 用户级 MCP

只 merge 各自 MCP 段，缺失主配置文件时失败且不创建。
EOF
)"
```

---

### Task 6: Hooks 与 Codex 唯一落点

**Files:**

- Modify: `scripts/agent_config/adapters/cursor.py` `codex.py` `starfactory.py`
- Create: `tests/agent_config/test_hooks.py`

**Interfaces:**

- Consumes: `HookEntry`
- Produces: `check_hooks` / `apply_hooks` 每宿主各一份。Cursor：`home()/.cursor/hooks.json`，结构 `{"hooks": [ {**adapter_fields, "agentConfigId": id} ]}`（yaml `adapters.cursor` 原样并入）；可建骨架。starFactory：`home()/.starFactory/settings.json` 的 `hooks` 键，值为列表，元素为 `{**adapters.starFactory, "agentConfigId": id}`；**禁止创建** settings.json。Codex `resolve_hooks_target() -> tuple[Path, str]` 其中 kind 为 `hooks_json` 或 `config_toml`：① `hooks.json` 存在则只它；② 否则 `config.toml` 含 `hooks` 键则只 toml；③ 否则 check 记缺口，apply 创建 `hooks.json`。toml 已有 hooks 时不得创建 hooks.json。upsert 先按标记，再按 `command`+`event`（adapter 里的 `command` 与 `event` 字段，缺省则只用 command）。prune 只删带标记项。MCP+Hooks 同改 `config.toml` 时：`sync.apply_all` 读一次、改两段、写一次。

- [ ] **Step 1: Write the failing test**

```python
import json
from agent_config.schema import parse_hooks
from agent_config.adapters import cursor, codex

def test_hook_skips_cursor_when_not_in_hosts(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "hooks.json").write_text(json.dumps({"hooks": []}))
    entries = parse_hooks({"hooks": [{"id": "git-ai-checkpoint", "hosts": ["codex"],
                                      "intent": "git-ai", "adapters": {"codex": {"command": "git-ai"}}}]})
    cursor.apply_hooks(entries, prune=False)
    data = json.loads((tmp_path / ".cursor" / "hooks.json").read_text())
    assert data["hooks"] == []

def test_codex_uses_toml_hooks_not_new_json(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_CONFIG_HOME", str(tmp_path))
    d = tmp_path / ".codex"
    d.mkdir()
    (d / "config.toml").write_text("[hooks]\nplaceholder = true\n")
    entries = parse_hooks({"hooks": [{"id": "h", "hosts": ["codex"], "intent": "i",
                                      "adapters": {"codex": {"command": "git-ai"}}}]})
    codex.apply_hooks(entries, prune=False)
    assert not (d / "hooks.json").exists()
    assert "git-ai" in (d / "config.toml").read_text()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=scripts python3 -m pytest tests/agent_config/test_hooks.py -v`

Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

Codex toml 的 hooks 用 `hooks.managed = [{...}]` 列表存放本工具条目，并保留已有其它 `hooks` 键。若官方 schema 是另一形状，仍把 `adapters.codex` 整块放入列表项并加 `agent_config_id`。双文件并存只读写 `hooks.json`。

- [ ] **Step 4: Run the tests and make sure they pass**

Run: `PYTHONPATH=scripts python3 -m pytest tests/agent_config/test_hooks.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/agent_config/adapters tests/agent_config/test_hooks.py
git commit -m "$(cat <<'EOF'
feat: 按宿主 merge Hooks 并解析 Codex 唯一落点

避免 hooks.json 与 config.toml 双写，且未声明的宿主不被写入。
EOF
)"
```

---

### Task 7: CLI、退出码、备份、`--only`

**Files:**

- Modify: `scripts/agent_config/cli.py` `sync.py`
- Create: `tests/agent_config/test_cli.py`
- Create: `inventory/README.md`

**Interfaces:**

- Consumes: 全部 check/apply
- Produces: `main(argv: list[str] | None) -> int`。子命令仅 `sync`；flags：`--check`（默认）、`--apply`、`--prune`（必须配 `--apply`，否则退出 2）、`--only {mcp,hooks}`。`--apply` 对每个将改文件 `shutil.copy2` 到 `tempfile.mkdtemp(prefix="agent-config-")`。坏的 starFactory.json 时 Cursor 仍 apply。schema 失败退出 2。stdout 禁止打印 `sk-` 与超长 token。

- [ ] **Step 1: Write the failing test**

```python
import json
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=scripts python3 -m pytest tests/agent_config/test_cli.py -v`

Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

`argparse`。`sync.py` 汇总三家 `CheckResult`：任一 `file_error` → 2；否则有 gap → 1；drift 打印警告仍 0。apply 后先写再 check 一遍算退出码。`inventory/README.md` 用中文说明两份 yaml 是源、CLI 用法、不做面板、密钥只写变量名。

- [ ] **Step 4: Run the tests and make sure they pass**

Run: `PYTHONPATH=scripts python3 -m pytest tests/agent_config -v`

Expected: 全绿。再手工：`python3 scripts/agent-config sync --check`（真实 HOME 只读 check，不 `--apply`）。

- [ ] **Step 5: Commit**

```bash
git add scripts/agent_config/cli.py scripts/agent_config/sync.py tests/agent_config/test_cli.py inventory/README.md
git commit -m "$(cat <<'EOF'
feat: 完成 agent-config sync CLI 的退出码与 --only

默认 check，apply 前备份，未选中域的坏文件不影响退出。
EOF
)"
```

---

## Spec coverage

| Spec                                        | Task                         |
| ------------------------------------------- | ---------------------------- |
| inventory + CLI 布局                        | 1, 7（包名 `agent_config/`） |
| schema / 无密钥值                           | 2                            |
| env 三步 merge                              | 3, 4                         |
| Cursor/Codex/starFactory MCP 路径与禁止创建 | 4, 5                         |
| 托管标记与 prune / hosts 移除               | 4, 5, 6                      |
| Hooks 与 Codex 落点 / 双写                  | 6                            |
| 同文件串行写 toml                           | 6–7                          |
| 退出码、`--only`、备份、脱敏                | 7                            |
| 验收 1–5                                    | 4–7 测试                     |
| Skills / 面板 / 项目级 / import             | 不实现（非目标）             |

## Placeholder scan

无 TBD。Codex hooks 在 toml 中落在 `hooks` 表下的列表，若本机官方 schema 不同，实现时只改 `adapters.codex` 字段透传，不改 CLI。
