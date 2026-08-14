# Codex / Cursor / starFactory 全局配置统一维护设计

日期：2026-08-13  
范围：用户主目录下的 **Hooks、Rules、MCP、Plugins**（以及与它们同层的 **Skills**，因为 `~/.agents` 实际只对 Skills 是跨宿主标准路径）  
决策规则：三家都能在初始化时加载 `~/.agents` 的配置 → 公共部分维护在 `~/.agents`；否则维护在各自目录。

> 路径说明：用户提到的 `~/.cidex` 按 Codex 官方约定对应 **`~/.codex`**。macOS 默认大小写不敏感，`~/.starFactory` 与 `~/.StarFactory` 是同一目录。

---

## 1. 结论（先看这张表）

| 配置类型             | 能否统一进 `~/.agents`                | 三家关系                                             | 应维护在哪里                                                                                                                                                                |
| -------------------- | ------------------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Skills**           | **能**（三家都扫 `~/.agents/skills`） | **并集发现**；同名时各家解析策略不同                 | 公共 Skill → `~/.agents/skills/<name>/SKILL.md`                                                                                                                             |
| **Rules / 常驻指令** | **不能**                              | **相互独立**（格式与入口都不同）                     | Codex：`~/.codex/AGENTS.md`；Cursor：User Rules + 项目 `.cursor/rules`；starFactory：`~/.starFactory` 侧 AGENTS / 项目 `AGENTS.md`                                          |
| **Hooks**            | **不能**                              | **相互独立**（事件名、配置格式、加载入口都不同）     | Codex：`~/.codex/config.toml` 或 `hooks.json`；Cursor：`~/.cursor/hooks.json`；starFactory：`~/.starFactory/settings.json` 的 `hooks`                                       |
| **MCP**              | **不能**                              | **相互独立**（配置文件格式不同；同进程内多层才合并） | Codex：`~/.codex/config.toml`；Cursor：`~/.cursor/mcp.json`；starFactory：**`~/.starFactory.json`** + 项目根 **`.mcp.json`**（`~/.starFactory/mcp.yaml` 不是 CLI 文档路径） |
| **Plugins**          | **不能**                              | **相互独立**（清单格式、市场、安装缓存都不同）       | `~/.codex/plugins`、`~/.cursor/plugins`、`~/.starFactory/plugins`                                                                                                           |

一句话：**`~/.agents` 不是「万能配置根目录」，它目前只是 Agent Skills 开放标准的用户级 Skills 仓。** 把 Hooks / Rules / MCP / Plugins 丢进 `~/.agents`，三家都不会当自己的主配置加载。

---

## 2. `~/.agents` 到底是什么

`~/.agents` 来自 [Agent Skills](https://agentskills.io) 约定，官方用户级路径是：

```text
~/.agents/skills/<skill-name>/SKILL.md
```

仓库级对应：

```text
<repo>/.agents/skills/<skill-name>/SKILL.md
```

本机现状（2026-08-13）：

- `~/.agents/` 只有 `skills/` 与 `.skill-lock.json`，**没有** hooks、rules、mcp、plugins。
- `~/.agents/skills` 约 72 个 Skill（`npx skills` / 社区安装的公共库）。
- `~/.cursor/skills` 另有一份（约 14 个，与 `~/.agents` 大量重名）。
- `~/.starFactory/skills` 另有一份（与 `~/.agents` 大量重名，疑似安装器双写）。
- `~/.codex/skills` 几乎为空（仅 `playwright`）；Codex 的用户级 Skill **官方主路径就是 `~/.agents/skills`**。

---

## 3. 三家加载模型：并集还是独立

先分两层，避免混谈：

1. **跨产品（Codex vs Cursor vs starFactory）**：除 Skills 外，**配置根目录相互独立**。改 `~/.cursor/mcp.json` 不会让 Codex 连上同一组 MCP。
2. **同一产品内部的多层路径**（用户目录 vs 项目目录 vs 插件）：多数是 **并集加载**，冲突时再按优先级取一条。

```text
                    ┌─────────────────────────────────────┐
                    │  ~/.agents/skills   （唯一跨宿主公共仓）│
                    └───────────┬───────────┬─────────────┘
                                │ 并集发现    │
              ┌─────────────────┼─────────────┼─────────────────┐
              ▼                 ▼             ▼                 │
        Codex 还会扫        Cursor 还会扫   starFactory 还会扫   │
        ~/.codex/*          ~/.cursor/*    ~/.starFactory/*     │
        项目 AGENTS.md      .cursor/rules  项目 AGENTS.md       │
        .agents/skills      .cursor/skills .factory 或等价路径  │
        config.toml MCP     mcp.json       ~/.starFactory.json / .mcp.json │
```

---

## 4. 分项：路径、优先级、并集语义

### 4.1 Skills（唯一建议统一到 `~/.agents`）

#### 发现路径

| 宿主            | 用户级                                                                           | 项目级                                                               | 兼容路径                                                                 |
| --------------- | -------------------------------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **Codex**       | **`~/.agents/skills`**（官方 USER）                                              | 从 cwd 一直扫到 git root 的 **`.agents/skills`**                     | 也可见 `~/.codex/skills`（非官方主路径，本机仅 playwright）              |
| **Cursor**      | `~/.agents/skills` **与** `~/.cursor/skills`                                     | `.agents/skills/` **与** `.cursor/skills/`（含子目录里的同名文件夹） | `.claude/skills`、`.codex/skills`、`~/.claude/skills`、`~/.codex/skills` |
| **starFactory** | 帮助中心：`~/.starFactory/skills`；用户确认另扫 `~/.agents/skills`（文档表未列） | `.starFactory/skills/`（启动目录向上到仓库根）；`--add-dir` 下同路径 | 插件 `<plugin>/skills/`                                                  |

三家都会在启动/会话初始化时扫描 `~/.agents/skills/**/SKILL.md`。因此 **跨宿主公共 Skill 只应在 `~/.agents/skills` 留一份**。

#### 同宿主内部：并集 + 同名处理

- **Cursor**：多目录 **并集发现**。文档未承诺「`~/.cursor/skills` 覆盖 `~/.agents/skills`」；同名 Skill 同时存在时容易出现重复条目或行为不确定。实践上 **不要双写**。
- **Codex**：多 scope **并集发现**。官方说明：同 `name` **不合并**，选择器里可能同时出现；TUI 讨论里的优先级倾向是 **Repo > User > System > Admin**。用户级请只放 `~/.agents/skills`，避免再在 `~/.codex/skills` 放同名副本。
- **starFactory**（帮助中心 Skills 页）：官方表格三层为个人 `~/.starFactory/skills`、项目 `.starFactory/skills`、插件 skills。官方同名优先级为 **个人 > 项目**，同名覆盖内置；插件用 `plugin-name:skill-name` 命名空间。用户确认 **另外会扫 `~/.agents/skills`**（该页正文未写此路径）。公共 Skill 仍只留 `~/.agents` 一份，避免与 `~/.starFactory/skills` 双写。

#### 放置策略

- 三家都能用的流程类 Skill（superpowers、lark、gsap、skill-creator 等）→ **只放 `~/.agents/skills`**。
- 仅 Cursor 内置/插件技能（`~/.cursor/skills-cursor`）→ **不要搬**，那是 Cursor 产品目录。
- 仅 Codex 的 sidecar（如 `agents/openai.yaml`）→ 仍可放在该 Skill 目录内，Cursor/starFactory 会忽略未知 frontmatter。
- 宿主专属 Skill（强依赖某一家工具名、slash 语法）→ 留在该宿主目录，或在 SKILL.md 写清「仅某宿主」。

---

### 4.2 Rules / 常驻指令（不能进 `~/.agents`）

| 宿主            | 用户级                                                                    | 项目级                                                                | 多层关系                                                       |
| --------------- | ------------------------------------------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------- |
| **Codex**       | `~/.codex/AGENTS.md`（若存在 `AGENTS.override.md` 则只读 override）       | 从 git root 走到 cwd，每层最多一个 `AGENTS.override.md` / `AGENTS.md` | **拼接并集**：根 → cwd，后出现的覆盖冲突项；总大小默认 32 KiB  |
| **Cursor**      | **User Rules**（产品设置，不是 `~/.agents` 文件）                         | `.cursor/rules/*.mdc`；根或子目录 `AGENTS.md`                         | **合并并集**，冲突时 **Team → Project → User**（先出现的优先） |
| **starFactory** | 个人 `AGENTS.md`（Factory 文档为 `~/.factory/AGENTS.md`；本机未见该文件） | 仓库 `AGENTS.md`（本工作流对齐到 `.starFactory/AGENTS.md`）           | 项目指令与个人指令分层，**不是**读 `~/.agents/AGENTS.md`       |

**不存在**「三家共同加载 `~/.agents/rules`」的机制。

跨宿主「同一套人话规则」的正确做法（本仓库 V1 已采用）：

- 契约正文放在项目 `.agent-workflow/` 与根 `AGENTS.md`。
- 各宿主用 **薄适配入口** 指向同一契约，而不是在 `~/.agents` 再维护一份全局 Rules。

用户级、与具体仓库无关的偏好：

- Codex → 只改 `~/.codex/AGENTS.md`
- Cursor → User Rules
- starFactory → 其个人 AGENTS / settings，不要幻想 Cursor 会读它

---

### 4.3 Hooks（不能进 `~/.agents`）

事件名、JSON/TOML schema、工作目录都不兼容，**不能共用一份 hooks 文件**。

| 宿主            | 用户级入口                                                   | 项目级                                                           | 多层关系                                                                                                                                                           |
| --------------- | ------------------------------------------------------------ | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Codex**       | `~/.codex/hooks.json` 或 `~/.codex/config.toml` 的 `[hooks]` | `<repo>/.codex/hooks.json` / `config.toml`                       | **并集执行**：多层 hooks **全部加载**，高层 **不替换** 低层；另加已信任的插件 hooks                                                                                |
| **Cursor**      | `~/.cursor/hooks.json`（脚本相对 `~/.cursor/`）              | `<repo>/.cursor/hooks.json`（脚本相对项目根）                    | **并集执行**；冲突响应按 Team / Project / User 合并。另有系统级 `/Library/Application Support/Cursor/hooks.json`                                                   |
| **starFactory** | `~/.starFactory/settings.json` 的 `hooks`                    | `.starFactory/settings.json`、`.starFactory/settings.local.json` | **合并而非替换**；同一事件可同时有全局与项目 Hook。事件：SessionStart / UserPromptSubmit / PreToolUse / PostToolUse / Stop / PreCompact / PostCompact / SessionEnd |

本机实例：

- Cursor：`~/.cursor/hooks.json` 里审批 hook **已全部注释**。
- Codex：`config.toml` 里 git-ai checkpoint（codex）。
- starFactory：`settings.json` 里 git-ai checkpoint（claude matcher）。

这三份 **必须分开放**：命令参数、事件名、stdin 协议都按宿主定制。即便脚本二进制相同（git-ai），配置文件也不能合成一个。

---

### 4.4 MCP（不能进 `~/.agents`）

没有 `~/.agents/mcp.json` 这种跨宿主标准。

| 宿主            | 用户级                                                                               | 项目级                                         | 同名时                                                                                                                         |
| --------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **Codex**       | `~/.codex/config.toml` 的 MCP 段                                                     | 项目 `.codex` 配置层                           | 按 Codex 配置层合并（高层覆盖字段，不是三家共享）                                                                              |
| **Cursor**      | `~/.cursor/mcp.json`                                                                 | `.cursor/mcp.json`                             | 全局 + 项目 **并集**；同名服务器以产品合并规则为准（项目通常覆盖/并存于 UI）                                                   |
| **starFactory** | user：`~/.starFactory.json` 的 `mcpServers`；local（默认）：同一文件的**项目条目下** | 项目根 **`.mcp.json`**（团队共享，首次需批准） | 三作用域独立登记；用 `star mcp add --scope user\|project`。本机另有 `~/.starFactory/mcp.yaml`，**不是**帮助中心记载的 CLI 路径 |

跨宿主「同一组 MCP」只能：

- **分别登记三份配置**（推荐，密钥与审批模型不同），或
- 用脚本从一份清单 **生成** 三份宿主文件（生成器可放在本仓库，**生成结果仍写入各自目录**）。

不要把密钥写进任何可提交文件；Cursor 用 `${env:NAME}`，starFactory 项目 `.mcp.json` 用 JSON（Token 走 `--header` / `--env` / OAuth，勿提交），Codex 用自己的 env 展开。

---

### 4.5 Plugins（不能进 `~/.agents`）

| 宿主            | 用户级缓存/安装                                                  | 清单                                                           |
| --------------- | ---------------------------------------------------------------- | -------------------------------------------------------------- |
| **Codex**       | `~/.codex/plugins`                                               | `.codex-plugin/plugin.json`                                    |
| **Cursor**      | `~/.cursor/plugins`（含 `cache/`、`local/`）                     | `.cursor-plugin/plugin.json` 或 Agent Plugins 的 `plugin.json` |
| **starFactory** | `~/.starFactory/plugins`（marketplaces、installed_plugins.json） | `.factory-plugin/plugin.json`；兼容 `.claude-plugin/`          |

插件是 **发行格式**，不是 `~/.agents` 目录约定。本机 starFactory 已启用 `superpowers@claude-plugins-official`，与 `~/.agents/skills` 里的 superpowers 技能可能 **重复提供同一套流程**——这是「插件源 vs Skills 仓」的重叠，不是 `~/.agents` 能消掉的。

统一原则：

- 要分发给某一家 → 用那一家的 plugin 格式装进对应 `~/.xxx/plugins`。
- 只要三家都能当 Skill 用 → **不要打成三家插件，只维护 `~/.agents/skills`**。

---

## 5. 推荐目录布局（落地标准）

```text
~/.agents/
  skills/                 # 唯一跨 Codex / Cursor / starFactory 的公共仓
    <skill>/SKILL.md
  .skill-lock.json        # 安装锁，随 skills 工具维护

~/.codex/                 # Codex 专属：Rules / Hooks / MCP / Plugins / 会话状态
  AGENTS.md
  config.toml             # 含 hooks、mcp
  plugins/
  skills/                 # 尽量空；不要与 ~/.agents/skills 同名双写

~/.cursor/                # Cursor 专属
  hooks.json
  mcp.json
  plugins/
  skills/                 # 尽量空或只放 Cursor 专属；公共的只放 ~/.agents
  skills-cursor/          # 产品内置，勿改

~/.starFactory.json       # CLI MCP：user 的 mcpServers + local 项目条目（含密钥，不进 git、不整文件软链）

~/.starFactory/           # starFactory 专属目录
  settings.json           # 全局 hooks（与项目 .starFactory/settings.json 合并）
  mcp.yaml                # 本机残留/IDE 示例，不是帮助中心记载的 CLI MCP 路径
  skills/                 # 官方个人 Skills；公共技能以 ~/.agents/skills 为准，避免双写
  plugins/
```

**禁止**：在 `~/.agents` 下自创 `hooks/`、`mcp.json`、`plugins/`、`rules/` 并期待三家读取。

**允许的符号链接（仅 Skills）**：

```text
# 若某安装器坚持写入 ~/.starFactory/skills，可改为：
~/.starFactory/skills → ~/.agents/skills

# Cursor 同理（仅当 UI 仍往 ~/.cursor/skills 装公共技能时）
~/.cursor/skills → ~/.agents/skills
```

不要把整个 `~/.cursor` 链到 `~/.agents`。

---

## 6. 方案对比（brainstorm 备选）

| 方案                      | 做法                                    | 优点                           | 缺点                                            | 结论             |
| ------------------------- | --------------------------------------- | ------------------------------ | ----------------------------------------------- | ---------------- |
| **A. 按能力分流（推荐）** | Skills → `~/.agents`；其余 → 各宿主目录 | 符合三家真实加载器；无幽灵配置 | MCP 要登记最多三次                              | **采用**         |
| B. 强行一切进 `~/.agents` | 自建 hooks/mcp/plugins 子目录           | 目录好看                       | **三家不读**，等于没配置                        | 否决             |
| C. 全部符号链接宿主目录   | `~/.cursor/skills` 等全部 ln 到 agents  | 安装器兼容                     | 链错会污染产品缓存；Hooks/MCP schema 仍不能共用 | 仅 Skills 可选用 |

---

## 7. 本机已观察到的重复与风险

1. **`~/.agents/skills` 与 `~/.starFactory/skills` 大量同名**：starFactory 侧副本会被标成 Overridden 或造成无效重复。清理方向：保留 `~/.agents`，starFactory 改为 symlink 或删除重复目录。
2. **`~/.agents/skills` 与 `~/.cursor/skills` 部分同名**：Cursor 并集发现，可能 slash 菜单重复。公共技能只留 `~/.agents`。
3. **git-ai hooks 在 Codex 与 starFactory 各写一份**：正确，不要合并。
4. **starFactory `enabledPlugins.superpowers` 与 `~/.agents` 里 superpowers skills**：能力重复，不是路径错误；若觉得吵，只开一侧。
5. **本工作流仓库** 的项目级入口仍按 `adapters/` 对齐（Codex `AGENTS.md`、Cursor `.cursor/rules`、starFactory `.starFactory/AGENTS.md`），与本次「用户主目录整理」正交：仓库契约不进 `~/.agents`。

---

## 8. 明确不做

- 不把三家 MCP 合成一份 `~/.agents/mcp.json`。
- 不发明跨宿主 hooks 格式。
- 不移动 `~/.cursor/skills-cursor`、各家 `plugins/cache`、会话数据库。
- 本次文档 **不执行** 删除或 `ln -s`；清理属于实现阶段，且删除 `~/.starFactory/skills` 下重复目录前需人工确认。

---

## 9. 验收标准

整理完成后应满足：

1. 在 Cursor / Codex / starFactory 新会话中，同一公共 Skill（例如 `brainstorming`）都能被发现，且磁盘上 **只有** `~/.agents/skills/brainstorming` 一份正文。
2. 修改 `~/.cursor/mcp.json` **不会** 改变 Codex MCP 列表；反之亦然。
3. `~/.agents` 下除 `skills/` 与锁文件外，没有被误当成「已生效」的 hooks/mcp/plugins。
4. 各宿主 hooks 仍按各自事件跑通（至少 git-ai 在 Codex 与 starFactory 各跑各的）。

---

## 10. 参考（官方加载行为）

- Cursor Skills：<https://cursor.com/docs/skills.md>（明确列出 `~/.agents/skills/`）
- Cursor Hooks：<https://cursor.com/docs/hooks.md>（仅 `.cursor/hooks.json` 与 `~/.cursor/hooks.json`）
- Cursor MCP：<https://cursor.com/docs/mcp.md>（仅 `.cursor/mcp.json` 与 `~/.cursor/mcp.json`）
- Cursor Rules：<https://cursor.com/docs/rules.md>（Team → Project → User）
- Codex Customization / Skills：用户级 Skills = `~/.agents/skills`；AGENTS = `~/.codex/AGENTS.md`
- Codex Hooks：<https://developers.openai.com/codex/hooks>（config 层并集，不读 `~/.agents`）
- starFactory 帮助中心（本机内网，Playwright 读取）：`/starfactory/docs/skills`、`/starfactory/docs/hooks`、`/starfactory/docs/mcp`（StarFactory 1.0.x）。**不要**把这三页全文拷进公开仓库。
- starFactory Skills 官方表：`~/.starFactory/skills`、`.starFactory/skills`、插件 skills；**未列出** `~/.agents/skills`。`~/.agents/skills` 仍按用户确认计入兼容扫描。
- starFactory Hooks：只写在各层 `settings.json`，三层**合并**。
- starFactory MCP：`~/.starFactory.json`（user / local）与项目根 `.mcp.json`；不要把 `~/.starFactory/mcp.yaml` 当成 CLI 权威路径。
