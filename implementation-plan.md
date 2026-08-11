# 个人 AI 研发工作流 V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付一套以“人工确认规划与设计，AI 自主完成实现、Review、修复、验证和 L2 交付”为核心的跨 Agent 个人研发工作流 V1。

**Architecture:** 使用 Agent 无关的 Markdown 流程契约作为唯一事实源，并通过 Codex、Claude Code、Cursor 的薄适配文件接入。Claude 官方插件只映射到能力接口，不进入核心流程依赖；状态引擎、Hooks 和 Plugin 打包作为后续迭代能力。

**Tech Stack:** Markdown、Git、Agent 规则文件；V1 不引入运行时依赖、数据库或自动化引擎。

## Global Constraints

- 规划与设计完成后必须等待一次人工确认，确认后 AI 自动推进到最终交付。
- 默认交付级别为 L2：本地实现、完整验证、原子 Git Commit；禁止自动 Push、创建 PR、合并或部署。
- 没有真实验证证据时，禁止把任务标记为完成。
- 核心流程不得依赖 Codex、Claude Code、Cursor 的专属命令或插件。
- 删除、关键配置、数据库迁移、凭证、外部发布等未授权高风险操作必须暂停并确认。
- V1 保持纯文档、无依赖、可复制，不实现 SQLite 状态机、Hooks 或多 Agent 调度器。

---

### Task 1: 最终设计与演进路线

**Files:**
- Create: `docs/personal-ai-development-workflow-v1-design.md`
- Create: `docs/evolution-roadmap.md`

**Interfaces:**
- Consumes: 已确认的人工决策边界、L2 默认交付、两份参考文档中的阶段与插件能力分类。
- Produces: 后续核心流程、模板和 Agent 适配器共同遵循的架构基线。

- [x] **Step 1: 编写最终设计文档**

  明确设计目标、职责边界、一次审批模型、三条路径、AI 自主闭环、停止条件、DoD、交付级别和跨 Agent 架构。

- [x] **Step 2: 编写演进路线**

  将建设顺序固化为 V1 文档契约、V1.1 Agent 适配、V2 Skills/Review/Hooks、V3 状态与可观测性，并列出每阶段进入条件和不做事项。

- [x] **Step 3: 验证设计覆盖**

  Run: `rg -n "人工确认|自主执行|Definition of Done|L2|Fast Path|Standard Path|Governed Path|Claude|Codex" docs/*.md`

  Expected: 每项核心约束至少在设计或路线文档中出现一次，且 Claude/Codex 只作为适配器出现。

### Task 2: 跨 Agent 核心流程契约

**Files:**
- Create: `.agent-workflow/WORKFLOW.md`
- Create: `.agent-workflow/PROJECT.template.md`

**Interfaces:**
- Consumes: Task 1 定义的状态、门禁、停止条件和 DoD。
- Produces: 所有 Agent 必须读取并执行的唯一核心流程，以及每个项目需要填写的真实命令和风险配置。

- [x] **Step 1: 编写核心流程**

  定义 `drafting → awaiting_approval → approved → implementing → validating → reviewing → fixing → ready_for_delivery → done/blocked` 状态和允许的转换。

- [x] **Step 2: 编写项目配置模板**

  包含项目概况、仓库边界、架构约束、工具链命令、Review Profile、交付级别和高风险操作。

- [x] **Step 3: 验证核心契约无宿主绑定**

  Run: `rg -n "\$dev-workflow|/plugin install|spawn_agent|update_plan" .agent-workflow`

  Expected: 无输出；核心契约不得要求任何特定宿主工具。

### Task 3: 任务与 Review 模板

**Files:**
- Create: `.agent-workflow/TASK_TEMPLATE.md`
- Create: `.agent-workflow/REVIEW_TEMPLATE.md`

**Interfaces:**
- Consumes: Task 2 的状态和 DoD。
- Produces: 单任务事实源和统一 Finding 格式，供实现者、Reviewer 与最终交付复用。

- [x] **Step 1: 编写任务模板**

  覆盖目标、非目标、验收条件、探索证据、规划设计、人工审批、授权边界、实现记录、验证证据、Review、修复复验、最终交付和经验沉淀。

- [x] **Step 2: 编写 Review 模板**

  覆盖 correctness、testing、error-handling、compatibility、security、maintainability，并定义 P0-P3 和 high/medium/low 置信度。

- [x] **Step 3: 验证完成门禁字段**

  Run: `rg -n "验收条件|人工确认|验证证据|P0|P1|复验|遗留风险|Git" .agent-workflow/*TEMPLATE.md`

  Expected: 所有交付门禁均能在任务或 Review 模板中记录。

### Task 4: Agent 薄适配入口

**Files:**
- Create: `adapters/AGENTS.md`
- Create: `adapters/CLAUDE.md`
- Create: `adapters/cursor-workflow.mdc`
- Create: `docs/claude-plugin-mapping.md`

**Interfaces:**
- Consumes: Task 2 的核心流程和项目配置，Task 3 的任务与 Review 模板。
- Produces: 不复制核心规则的宿主入口，以及 Claude 官方插件到通用能力的映射。

- [x] **Step 1: 编写三个薄适配入口**

  每个入口只规定读取顺序、宿主能力映射和降级行为，不复制完整流程正文。

- [x] **Step 2: 编写 Claude 插件能力映射**

  映射 `feature-dev`、`code-review`、`pr-review-toolkit`、`commit-commands`、`claude-md-management`、`security-guidance`、`claude-security`、`ralph-loop`、`hookify`、LSP，并明确引入阶段和边界。

- [x] **Step 3: 验证适配器引用核心契约**

  Run: `rg -l "\.agent-workflow/WORKFLOW.md" adapters/*`

  Expected: 返回三个适配文件。

### Task 5: 使用说明与一致性验证

**Files:**
- Create: `README.md`
- Verify: all files under the deliverable root

**Interfaces:**
- Consumes: Tasks 1-4 的所有产物。
- Produces: 可复制、可初始化、可执行的用户入口和最终质量报告。

- [x] **Step 1: 编写 README**

  提供五分钟接入步骤、任务启动方式、审批方式、AI 自主执行方式、L2 交付说明和后续升级入口。

- [x] **Step 2: 执行结构检查**

  Run: `find . -type f -maxdepth 3 | sort`

  Expected: 设计、路线、核心流程、项目模板、任务模板、Review 模板、三个适配入口和 README 全部存在。

- [x] **Step 3: 执行占位符扫描**

  Run: `rg -n "TBD|TODO|待补充|稍后填写" .`

  Expected: 模板中仅允许明确标识为“由项目维护者填写”的输入字段，不存在设计遗漏型占位符。

- [x] **Step 4: 执行自审**

  对照设计逐项核对范围、授权、状态流转、Review、验证、L2 交付、插件映射和演进路线；修复冲突后重新运行上述检查。
