# 个人 AI 研发工作流 V1

这是一套跨 Agent 的个人开发流程：人工负责规划与设计确认，确认后 AI 自主完成实现、验证、独立 Review、修复、复验和默认 L2 交付。

V1 是纯 Markdown 契约，不要求安装运行时、数据库或插件。

**当前使用的 AI Agent：Codex、Cursor、starFactory。**  
**不使用 Claude Code。** Claude Code 及其插件体系仅作为工作流设计参考（能力分层、降级思路），见 `docs/reference/claude/`；不提供业务项目接入，也不要求安装任何 Claude 专属依赖。

**统一的是能力，不是插件。** 各宿主如何落地同一职责，见 `.agent-workflow/CAPABILITIES.md`。Codex / Cursor / starFactory 的适配文件一律在 `adapters/`；在要用某个 Agent 开发的仓库里，按该 Agent 目录约定做路径对齐。

## 核心模型

```text
人工：需求、规划设计确认、授权
                  ↓
AI：实现 → 验证 → Review → 修复 → 复验 → L2 交付
                  ↓
人工：接收成果、证据和遗留风险
```

AI 只有在范围变化、未授权高风险操作、外部权限缺失、严重安全风险或 3 轮修复仍失败时才暂停请求决策。

## 目录说明

```text
agent-config-share/
├── README.md
├── implementation-plan.md          # 本仓库建设记录，接入业务项目时可忽略
├── .agent-workflow/
│   ├── WORKFLOW.md                 # 流程唯一事实源
│   ├── CAPABILITIES.md             # 跨 Agent 能力矩阵（当前宿主）
│   ├── PROJECT.template.md
│   ├── TASK_TEMPLATE.md
│   └── REVIEW_TEMPLATE.md
├── adapters/                       # 宿主适配源（唯一存放处）
│   ├── README.md                   # 原则 + 路径对齐表
│   ├── codex/
│   │   ├── README.md
│   │   └── AGENTS.md               # 对齐到开发仓库 AGENTS.md
│   ├── cursor/
│   │   ├── README.md
│   │   └── rules/
│   │       ├── cursor-workflow.mdc # 对齐到 .cursor/rules/
│   │       └── adapters-layout.mdc # 本仓维护约定（不对齐业务项目）
│   └── starFactory/
│       ├── README.md
│       └── AGENTS.md               # 对齐到 .starFactory/AGENTS.md
└── docs/
    ├── personal-ai-development-workflow-v1-design.md
    ├── evolution-roadmap.md
    ├── community-capability-alignment.md  # 社区 Skill/MCP 与能力对齐
    ├── claude-plugin-mapping.md    # 重定向到 docs/reference/claude/
    └── reference/claude/           # Claude Code 设计参考（不接入）
        ├── README.md
        ├── CLAUDE.md
        └── plugins.md
```

## 接入（交给 AI）

本仓库托管到 GitHub 后，在**业务项目**里对当前 Agent 说一句即可（把 URL 换成实际地址，宿主三选一）：

```text
按 https://github.com/<org>/<repo> 把个人 AI 研发工作流接入本仓库（宿主：Cursor）
# 上行为占位：须替换为真实 GitHub URL；宿主改成 Codex / Cursor / starFactory
```

宿主可写：`Codex` / `Cursor` / `starFactory`。

AI 必须按下列步骤自动完成前置工作（人工只审结果，不手搓复制）：

1. **获取源**：从上述 GitHub 仓库取得材料（推荐：浅克隆或 sparse checkout 后只取 `.agent-workflow/` 与对应 `adapters/<host>/` 入口文件）。不要拷贝本工作流仓的 `docs/`、`implementation-plan.md`，也不要把 Claude 参考材料当成接入依赖。
2. **同步核心契约**：将远端 `.agent-workflow/` 放到本项目根。若本地已有该目录：更新契约与模板文件，**保留**已填写的 `PROJECT.md` 与 `tasks/`（缺模板字段再补，勿覆盖用户任务内容）。
3. **对齐当前宿主入口**（源在远端 `adapters/`；已有文件则合并「必读顺序 / 默认行为 / 冲突优先级」，勿整文件覆盖）：
   - Codex → `adapters/codex/AGENTS.md` → 项目根 `AGENTS.md`
   - Cursor → `adapters/cursor/rules/cursor-workflow.mdc` → `.cursor/rules/cursor-workflow.mdc`
   - starFactory → `adapters/starFactory/AGENTS.md` → `.starFactory/AGENTS.md`
4. **项目画像**：若不存在 `.agent-workflow/PROJECT.md`，从 `PROJECT.template.md` 创建；探索真实仓库后填写命令、结构与约束，不确定处标「未验证」。已有 `PROJECT.md` 则只补缺、不擅自改已验证项。
5. **任务目录**：确保存在 `.agent-workflow/tasks/`。
6. **汇报**：列出已对齐路径、`PROJECT.md` 中待确认项；到此停住，等待用户确认画像或直接下任务。

路径对齐细则见 `adapters/README.md`。

## 配置面板

用户级 MCP / Hooks / Skills 可用本机面板浏览，并点按钮做检查与写入：

```bash
curl -fsSL https://raw.githubusercontent.com/AbnerSunLabs/agent-config-share/main/install.sh | sh
agent-config ui
```

清单与 CLI 说明见 `inventory/README.md`。

## 日常使用

入口文件对齐后，**不必再粘贴长启动话术**。非琐碎开发任务默认走 `.agent-workflow/WORKFLOW.md`：

1. 你直接说任务（例如「做 XXX」）。
2. AI 探索 → 写/更新 `.agent-workflow/tasks/<task-id>.md` → 进入 `awaiting_approval` → **停止改业务源码**。
3. 你确认授权包后回复：`批准，L2`（或指定 L1–L4）。
4. AI 自主实现、验证、Review、修复、复验与按级别交付；仅命中 `WORKFLOW.md` 人工介入条件时再暂停。

琐碎改动（单行笔误、纯格式等）可不建任务文件；有疑问时按更高风险路径处理。

## 默认 L2 的含义

默认 L2 禁止 Push、创建 PR、合并和部署；这些操作必须在规划设计阶段明确升级授权。

L2 允许 AI：

- 修改本地代码。
- 运行测试、Lint、类型检查和构建。
- 完成独立 Review 和修复复验。
- 创建一个或多个有明确逻辑边界的原子 Commit。

L2 不允许 AI：

- Push 到远端。
- 创建或更新 PR。
- 合并分支。
- 部署或执行其他外部发布。

这些操作需要在规划设计阶段明确升级到 L3 或 L4。

## 三条路径

| 路径     | 适用场景                             | 特点                                        |
| -------- | ------------------------------------ | ------------------------------------------- |
| Fast     | 局部、低风险、可快速回滚             | 简化规划设计，但仍需人工确认、验证和 Review |
| Standard | 普通功能、Bug、行为变化、重构        | 默认完整流程                                |
| Governed | 安全、数据、迁移、基础设施、公共契约 | 增加专项 Review、回滚和逐项授权             |

## 跨 Agent 能力如何统一

不要按插件名对齐，按能力对齐。权威对照表：

`.agent-workflow/CAPABILITIES.md`

| 能力（示例）      | 各宿主共同点                 | 差异放哪里（当前宿主）                             |
| ----------------- | ---------------------------- | -------------------------------------------------- |
| `plan` / `design` | 写出执行授权包并停在审批门禁 | Codex Plan、Cursor Plan 模式、starFactory 任务模板 |
| `review`          | 独立只读 + 统一 Finding      | 子代理 / 新会话 / `REVIEW_TEMPLATE` 串行           |
| `deliver`         | 遵守 L1–L4                   | Git CLI                                            |

V1 不要求安装任何插件。能力缺口一律走矩阵「降级」列，且不能绕过人工确认或降低 DoD。

可选增强：用社区 Skill / MCP 对齐 Claude 参考插件的同职责能力（例如 `feature-dev` → superpowers 规划套件，`code-review` → 社区 Review Skill）。完整对照与安装命令见 `docs/community-capability-alignment.md`。

版本边界：

- **V1**：契约 + 能力矩阵 + 当前宿主（Codex / Cursor / starFactory）薄入口
- **V1.1**：在真实任务中验证上述宿主列的增强工具；Claude 参考材料不进入接入路径；社区 Skill/MCP 按痛点可选

## 完成标准

Agent 不能仅凭「代码已写完」宣布完成。最终必须交付：

- 实现结果。
- 修改清单。
- 验收条件逐项结果。
- 真实验证命令和结果。
- Review Finding、修复和复验。
- 未执行检查和遗留风险。
- Git Commit 与交付状态。

没有验证证据时，状态只能是「实现完成但尚未验证」，不能是 `done`。

## 跨 Agent 接力

在 Codex、Cursor、starFactory 之间切换时，让新 Agent 读取：

1. `.agent-workflow/WORKFLOW.md`
2. `.agent-workflow/PROJECT.md`
3. 当前任务文件
4. 当前 Git 状态和 diff

可选：`.agent-workflow/CAPABILITIES.md`（了解新宿主用什么工具继续）。

新 Agent 应从任务文件记录的状态继续，不重复已有可靠证据，也不把历史推测当作已验证事实。不要引入 Claude 专属插件或入口来「补齐」能力。

## 迭代方式

建议先用 V1 完成 10 至 20 个真实任务，记录漏步骤、无效字段、Review 误报、验证阻断和不必要的人工打断。只有稳定重复的问题才升级成 Skill 或 Hook。

完整演进路线见 `docs/evolution-roadmap.md`。

## 当前边界

V1 没有：

- 状态数据库和崩溃恢复。
- 多 Agent 自动调度。
- 自动 Hook 和危险操作拦截器。
- Review 聚合器。
- 自动 Push、PR、合并或部署。
- 跨宿主统一的插件运行时。
- Claude Code 作为运行时宿主（仅设计参考）。

这些是后续能力，不影响 V1 通过任务文件与能力矩阵完成跨 Agent 接力和证据交付。
