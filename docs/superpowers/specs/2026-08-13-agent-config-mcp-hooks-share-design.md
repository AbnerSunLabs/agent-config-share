# MCP / Hooks 跨宿主清单同步设计

日期：2026-08-13  
地位：承接 [2026-08-13-agent-config-unification-design.md](./2026-08-13-agent-config-unification-design.md) 第 4.3 / 4.4 节的落地方案（文档中「从一份清单生成三份宿主文件」）。  
范围：**仅用户级 MCP 与 Hooks**。Skills 维持现有 `~/.agents/skills` + 软链，本工具不同步、不调用 skillshare。

---

## 1. 目标

在本仓库维护两份无密钥意图清单。本机用 CLI 对 Codex / Cursor / starFactory 的**用户级**配置做对账与合并写入，使「该三家都有的 MCP / Hook」只在仓库里改一处。

成功标准：

1. 新增或修改一条公共 MCP / Hook，只改 `inventory/` 下对应 yaml，再 `sync --apply`，三家声明了 `hosts` 的入口都出现等价配置。
2. `sync --check` 能报出：清单有而宿主无（缺口，退出 1）；清单无而宿主有且带本工具标记（漂移警告，默认不因此失败；仅 `--prune` 才删）；禁止创建或损坏的宿主文件（跳过，退出 2）。
3. 运行后宿主文件中**非清单管理字段**（模型、插件、密钥取值、UI 项）保持不变。
4. 仓库内任何提交物都不含 Token / API Key 字面量。

---

## 2. 非目标（V1）

- 不同步 Skills，不调用或替换 skillshare。
- 不写项目级配置：`.cursor/mcp.json`、项目 `.mcp.json`、`.starFactory/settings.json`、`.codex/`。
- 不创建或加载 `~/.agents/mcp.json`、`~/.agents/hooks.json`。
- 不把 `~/.starFactory/mcp.yaml` 当作 CLI MCP 权威路径。
- 不整文件覆盖 `~/.codex/config.toml`、`~/.starFactory.json`、`~/.starFactory/settings.json`。
- 不提供「从宿主反向 import 生成清单」；V1 清单由人维护。
- 不把本工具接入业务项目的工作流安装步骤（`README.md` 接入流程保持只对齐 `adapters/` 规则入口）。
- 不提供 skillshare 式 Web 配置面板；`agent-config ui`（按钮调用本 CLI）另开 **V1.1** spec，不在本实现范围内。

---

## 3. 仓库布局

```text
inventory/
  mcp.yaml                 # MCP 意图全集（可提交）
  hooks.yaml               # Hook 意图全集（可提交）
scripts/
  requirements.txt         # 仅 PyYAML（实现 CLI 用）
  agent-config             # 入口（Python 3.9+）
  agent-config.d/          # 按宿主展开与 merge，不直接当脚本跑
```

CLI：

```text
python3 scripts/agent-config sync              # 默认 --check
python3 scripts/agent-config sync --check
python3 scripts/agent-config sync --apply      # 只增不删（upsert）
python3 scripts/agent-config sync --apply --prune
python3 scripts/agent-config sync --only mcp
python3 scripts/agent-config sync --only hooks
```

未带 `--apply` 时等同 `--check`：只打印 diff。退出码：

| 码 | 含义 |
| -- | ---- |
| 0 | 对所选域：无缺口；若未开 `--prune`，托管漂移只警告仍可 0（见 §5） |
| 1 | 有缺口（清单有、目标无或内容不满足 upsert 后的期望非密钥字段） |
| 2 | 目标文件缺失（禁止创建的那种）或解析失败 |

`--apply` 在写入完成后按**写后状态**再算一遍：缺口已补则不再因先前缺口而报 1。未开 `--prune` 时，多余的托管条目只打印警告、**不**把退出码打成 1。`--only mcp` / `--only hooks` **不读取、不校验、不因未选中域的文件损坏而失败**。

---

## 4. 清单 schema

两份 yaml 顶层都是列表键 `mcp:` / `hooks:`。未知字段忽略但 check 时警告。`id` 在该文件内唯一，且用作各宿主上的服务器名或 hook 稳定键。

### 4.1 `inventory/mcp.yaml`

| 字段 | 必填 | 说明 |
| ---- | ---- | ---- |
| `id` | 是 | 稳定名，写入 Cursor `mcpServers` 键、Codex `[mcp_servers.<id>]`、starFactory `mcpServers.<id>` |
| `hosts` | 是 | 非空子集：`cursor` / `codex` / `starFactory` |
| `transport` | 是 | `stdio` 或 `http` |
| `command` / `args` | stdio 时必填 | 可执行文件与参数列表 |
| `url` | http 时必填 | 远程 MCP URL |
| `env` | 否 | **只写环境变量名**的列表，如 `[CONTEXT7_API_KEY]`。禁止写值 |
| `headers_env` | 否 | http 时：HTTP 头名 → 环境变量名，如 `Authorization: FOO_TOKEN` |

**托管标记（MCP 与 Hooks 同一规则）：**

- JSON 对象：写入 `"agentConfigId": "<id>"`。
- TOML 表：写入 `agent_config_id = "<id>"`。
- 若某宿主加载器会因未知字段拒绝配置，该宿主适配器 **禁止写标记**，且对该宿主 **禁用 prune、不把「现场有同名但无标记」报成托管漂移**（upsert 仍按 `id` == 服务器名 / 约定 hook 槽位）。V1 默认假定 Cursor JSON、Codex TOML 未知键可保留；实现时用最小样例验证，若验证失败则按「禁标记」降级并在 `--check` 打一行警告。

`--prune` 只删除带本工具标记、且满足以下任一条件的条目：清单里已无该 `id`；或清单仍有该 `id` 但 **当前宿主不在其 `hosts` 中**。无标记条目永不 prune。

宿主展开规则（适配器内实现，清单不写三份 JSON）：

- **Cursor** `~/.cursor/mcp.json`：`mcpServers.<id>`，并写 `agentConfigId`。
- **Codex** `~/.codex/config.toml`：只改 MCP 相关表，并写 `agent_config_id`。
- **starFactory** `~/.starFactory.json`：只 merge 顶层（user scope）`mcpServers.<id>`，并写 `agentConfigId`。

`hosts` 未包含的宿主：check 不报缺口，默认 apply 不写入、不删除该宿主上同名服务器（即使名字碰巧相同）。该宿主上若已有带本工具标记的同 id 条目，仅 `--prune` 时删除。

**`env` / 密钥取值（三家同一 merge 顺序，满足「不把密钥取值改掉」）：**

对每个清单声明的变量名 `VAR`：

1. 现场该键已有**非空字面量**（不是 env 引用）→ **原样保留**，不改写成引用、不清空。
2. 现场缺失该键，或值为空 → 写入该宿主的 env **引用**（Cursor：`"${env:VAR}"` 或文档等价；Codex / starFactory：各自展开语法）。**禁止**从环境或 `.env` 读出真实值再写入。
3. 现场已是 env 引用 → 保留引用形式；若引用的变量名与清单不一致，check 报缺口，apply 改成清单中的变量名（仍不写字面量）。

http 的 `headers_env` 同样按 1–3 处理。新建服务器对象时走第 2 步。

### 4.2 `inventory/hooks.yaml`

| 字段 | 必填 | 说明 |
| ---- | ---- | ---- |
| `id` | 是 | 稳定键 |
| `hosts` | 是 | 非空子集 |
| `intent` | 是 | 人读说明（如 `git-ai checkpoint`） |
| `adapters` | 是 | 仅包含 `hosts` 里出现的宿主。每个宿主一块**该宿主可加载的字段**（事件名、matcher、command、cwd 等） |

V1 不发明跨宿主统一事件名。`adapters.cursor` / `adapters.codex` / `adapters.starFactory` 的键名按该宿主官方 schema 填写；缺某个已声明 host 的 adapter 块则 schema 校验失败。

匹配与 upsert：每个 adapter 块映射到宿主文件里**一条** hook。识别顺序：① `agentConfigId` / `agent_config_id`；② 无论是否可写标记，再用 yaml 写死的 `command` + 事件名匹配，避免在已有未标记同类 hook 旁再插一条。② 只用于 upsert，不用于 prune。禁止三家共用一份 hooks 文件或互相软链。

### 4.3 清单示例（形状以字段为准，值可替换）

`inventory/mcp.yaml`：

```yaml
mcp:
  - id: context7
    hosts: [cursor, codex, starFactory]
    transport: stdio
    command: npx
    args: ["-y", "@upstash/context7-mcp"]
    env: [CONTEXT7_API_KEY]
  - id: some-http-mcp
    hosts: [cursor]
    transport: http
    url: https://example.invalid/mcp
    headers_env:
      Authorization: SOME_MCP_TOKEN
```

`inventory/hooks.yaml`：`adapters` 内键名用各宿主官方字段；下面仅示意结构。

```yaml
hooks:
  - id: git-ai-checkpoint
    hosts: [codex, starFactory]
    intent: git-ai checkpoint
    adapters:
      codex:
        command: git-ai
        # 其余键按 Codex hooks schema 补全
      starFactory:
        event: SessionEnd
        matcher: claude
        # 其余键按 starFactory settings.hooks schema 补全
```

### 4.4 密钥

- 清单、脚本、文档示例只允许变量**名**。
- apply 不得把环境里的真实值展开进目标文件（除非该宿主格式除引用外无法表达——V1 若遇到则 skip 该条并警告，仍不写字面量）。
- 禁止读取 `.env` / `.env.*` 以填充清单或目标文件。

---

## 5. 写入目标与 merge 语义

| 域 | Cursor | Codex | starFactory |
| -- | ------ | ----- | ----------- |
| MCP | `~/.cursor/mcp.json` | `~/.codex/config.toml` 的 MCP 段 | `~/.starFactory.json` 的 user `mcpServers` |
| Hooks | `~/.cursor/hooks.json` | 见下 | `~/.starFactory/settings.json` 的 `hooks` |

**Codex Hooks 落点（避免双写，先解析再对账）：**

解析顺序（只选一个目标）：

1. 若 `~/.codex/hooks.json` 存在 → 目标为该文件。
2. 否则若 `config.toml` 已有 `[hooks]` / hooks 相关键 → 目标为 toml 的 hooks 段。
3. 否则 apply 时 **创建** `~/.codex/hooks.json`；check 将「清单需要 Codex hooks 且 1、2 都不成立」记为缺口。

因此：`hooks.json` 不存在但 toml 已有 hooks 时，**不是** hooks.json 缺口，也 **不得** 再创建 hooks.json。下表「可创建骨架」仅适用于解析结果选中、且允许创建的那一类文件。若 `hooks.json` 与 toml `[hooks]` 同时存在，本工具只读写前者，不迁移或合并后者。

MCP 与 Hooks 若解析到同一路径（仅 `config.toml`），必须按文件串行读-改-写，禁止两域并行写同一文件。

**文件不存在时（对「解析后的目标文件」而言）：**

| 文件 | 不存在时 |
| ---- | -------- |
| `~/.cursor/mcp.json`、`~/.cursor/hooks.json` | check 记缺口；apply 可写最小骨架 |
| `~/.codex/hooks.json` | **仅当解析结果选中它**（上面第 1 或第 3 步）：不存在则 check 记缺口、apply 可建骨架。解析选中 toml 时忽略本行 |
| `~/.codex/config.toml`、`~/.starFactory.json`、`~/.starFactory/settings.json` | 作为解析目标却不存在：skip + 退出码 2；**禁止**创建 |

**merge：**

- `--apply`：按 `id` upsert 清单条目（MCP 服务器名 = `id`；Hook 按 §4.2）；其它键原样保留。
- `--prune`：只删带本工具标记、且清单已无该 id **或** 当前宿主已不在该 id 的 `hosts` 中的条目。默认 apply **不** prune。

**备份：** `--apply` 对每个将改文件先复制到系统临时目录（不进 git、不写仓库）。失败不回滚已成功的其它文件，但退出码非 0，并列出已改 / 未改路径。

---

## 6. 数据流

```text
inventory/mcp.yaml + inventory/hooks.yaml
        │
        ├─ 校验 schema（id 唯一、hosts、transport、adapters 齐全）
        ├─ 按宿主适配器展开「期望片段」
        └─ 读取现场用户级文件（解析失败 → 该文件 skip + 退出 2）
                │
                ├─ check：打印缺口 / 多余托管条目 / 未改
                └─ apply：merge 期望片段 → 写回（prune 仅在显式打开时）
```

巡检日常：只看两份 yaml 是否缺能力，再跑 `--check`。UI 里手加的 MCP 不会出现在 check 缺口里；只有清单声明了才要求三家对齐。若手加条目后来写进清单，下一次 apply 再 upsert。

---

## 7. 实现约束

- 入口为 `scripts/agent-config`，标准库 + PyYAML。修改其它依赖或根目录 `package.json` 须另征询。
- 适配器按宿主拆分，禁止一个函数里写三家格式。
- 不扫描、不修改 `~/.starFactory/mcp.yaml`。
- 日志与 check 输出不得打印疑似密钥的值（长 token、`sk-` 前缀等）；只打印 id、路径、缺/多。

---

## 8. 验收

1. 清单增加一条 `hosts: [cursor, codex, starFactory]` 的 stdio MCP（含 `env` 变量名），`--apply` 后三家用户级入口都能查到同名服务器且带托管标记。新建的 `env` 键为引用而非字面量；若某宿主该键事先已有字面量，apply 后字面量仍在。
2. 清单增加一条仅 `hosts: [codex, starFactory]` 的 hook（可按本机已有 git-ai 意图填写 adapters），Cursor hooks 文件不被写入该条。
3. 在 Cursor `mcp.json` 手加一个清单没有、也无 `agentConfigId` 的服务器，默认 `--apply` 与 `--prune` 后该服务器都仍在。清单曾写入且带标记、后来从 yaml 删除的条目，仅 `--prune` 后消失。从某条的 `hosts` 中去掉某一宿主后，仅 `--prune` 才删除该宿主上带标记的对应条目。
4. 破坏 `~/.starFactory.json` 为非法 JSON，`--check`/`--apply` 跳过该文件并以退出码 2 结束，Cursor/Codex 文件若本来合法仍按规则处理（apply 已改的不强制回滚）。
5. `inventory/` 与 `scripts/` 的 git diff 中无真实密钥。

---

## 9. 与既有文档的关系

- 统一设计文档第 1、4.3、4.4、8 节仍然有效：Skills 不进本工具；Hooks/MCP 不能共用一份运行时文件。
- 本 spec 只补充「仓库清单 + 用户级 merge CLI」。
- 不修改业务项目接入步骤，不要求把 `inventory/` 拷进其它仓库。
