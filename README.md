# 个人 AI 研发工作流 V1

这是一套跨 Agent 的个人开发流程：人工负责规划与设计确认，确认后 AI 自主完成实现、验证、独立 Review、修复、复验和默认 L2 交付。

V1 是纯 Markdown 契约，不要求安装运行时、数据库或插件。Codex、Claude Code、Cursor 通过薄适配文件执行同一套流程。

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
personal-ai-development-workflow/
├── README.md
├── implementation-plan.md
├── .agent-workflow/
│   ├── WORKFLOW.md
│   ├── PROJECT.template.md
│   ├── TASK_TEMPLATE.md
│   └── REVIEW_TEMPLATE.md
├── adapters/
│   ├── AGENTS.md
│   ├── CLAUDE.md
│   └── cursor-workflow.mdc
└── docs/
    ├── personal-ai-development-workflow-v1-design.md
    ├── evolution-roadmap.md
    └── claude-plugin-mapping.md
```

## 五分钟接入

### 1. 复制核心契约

将整个 `.agent-workflow/` 目录复制到目标项目根目录。

把：

```text
.agent-workflow/PROJECT.template.md
```

复制为：

```text
.agent-workflow/PROJECT.md
```

根据项目真实代码、配置和命令填写，不确定的内容标记为“未验证”。

### 2. 复制对应 Agent 入口

- Codex：将 `adapters/AGENTS.md` 复制到项目根目录。
- Claude Code：将 `adapters/CLAUDE.md` 复制到项目根目录。
- Cursor：将 `adapters/cursor-workflow.mdc` 复制到项目的规则目录。

如果项目已经存在对应文件，不要覆盖；将“必读顺序”和“核心契约优先”部分合并进去。

### 3. 创建任务文件

创建目录：

```text
.agent-workflow/tasks/
```

复制 `TASK_TEMPLATE.md` 为：

```text
.agent-workflow/tasks/<task-id>.md
```

### 4. 启动规划设计

向 Agent 提交：

```text
请按照 .agent-workflow/WORKFLOW.md 执行这个任务。
先探索真实项目并完成规划和设计，将结果写入当前任务文件。
到 awaiting_approval 后暂停，等待我确认，不要提前修改业务源码。
```

### 5. 授权执行

确认任务文件中的目标、非目标、验收条件、方案、风险、验证计划和交付级别后，回复：

```text
批准当前执行授权包，交付级别 L2。后续实现、验证、Review、修复和复验由 AI 自主推进；只有命中 WORKFLOW.md 的人工介入条件时再暂停。
```

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

| 路径 | 适用场景 | 特点 |
|---|---|---|
| Fast | 局部、低风险、可快速回滚 | 简化规划设计，但仍需人工确认、验证和 Review |
| Standard | 普通功能、Bug、行为变化、重构 | 默认完整流程 |
| Governed | 安全、数据、迁移、基础设施、公共契约 | 增加专项 Review、回滚和逐项授权 |

## Claude Code 专属插件适配（可选）

本节列出的插件只能在 Claude Code 中直接安装和调用，不能直接用于 Codex、Cursor 或其他 Agent。

跨 Agent 复用的是 `.agent-workflow/WORKFLOW.md` 定义的能力契约、任务模板和 Review 模板。不同 Agent 使用各自的原生能力实现同一职责：

| 通用能力 | Claude Code 实现 | 其他 Agent 的实现方式 |
|---|---|---|
| 规划与实现 | `feature-dev` | 原生 Plan、执行模式或通用 Skill |
| 独立 Review | `code-review` | Reviewer Agent、新会话或 Review 模板 |
| Review 维度 | `pr-review-toolkit` | `.agent-workflow/REVIEW_TEMPLATE.md` |
| Git 交付 | `commit-commands` | 标准 Git CLI |
| 长期上下文 | `claude-md-management` | `AGENTS.md`、Rules 或项目文档 |
| 安全护栏 | `hookify` | 宿主 Hook、权限系统或人工审批 |
| 代码语义 | Claude LSP 插件 | 宿主 LSP、编译器和类型检查 |

V1 不要求安装任何插件。只有使用 Claude Code 并进入 V1.1 后，才建议按以下顺序验证：

```text
feature-dev
→ code-review + pr-review-toolkit
→ commit-commands
→ claude-md-management
→ 语言 LSP
```

后续再按真实痛点引入 `security-guidance`、`claude-security`、`ralph-loop` 和 `hookify`。详细规则见 `docs/claude-plugin-mapping.md`。

Claude 插件只能增强 Claude Code 的执行能力，不能成为核心流程依赖，也不能绕过人工确认门禁、改变默认权限或降低 Definition of Done。插件不可用时，必须按照跨 Agent 核心契约继续或降级执行。

## 完成标准

Agent 不能仅凭“代码已写完”宣布完成。最终必须交付：

- 实现结果。
- 修改清单。
- 验收条件逐项结果。
- 真实验证命令和结果。
- Review Finding、修复和复验。
- 未执行检查和遗留风险。
- Git Commit 与交付状态。

没有验证证据时，状态只能是“实现完成但尚未验证”，不能是 `done`。

## 跨 Agent 接力

切换 Agent 时，只需要让新 Agent 读取：

1. `.agent-workflow/WORKFLOW.md`
2. `.agent-workflow/PROJECT.md`
3. 当前任务文件
4. 当前 Git 状态和 diff

新 Agent 应从任务文件记录的状态继续，不重复已有可靠证据，也不把历史推测当作已验证事实。

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

这些是后续能力，不影响 V1 通过任务文件完成跨 Agent 接力和证据交付。
