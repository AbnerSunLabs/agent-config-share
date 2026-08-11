# Claude Code 入口草稿（仅设计参考，不接入）

> **本工作流不使用 Claude Code。** 当前实际使用：Codex、Cursor、starFactory。  
> 本文件是历史/参考草稿，**不要**复制到业务项目根目录作为工作流入口。  
> 核心流程以 `.agent-workflow/WORKFLOW.md` 为准；当前宿主落地见 `.agent-workflow/CAPABILITIES.md`。

## 必读顺序

1. `.agent-workflow/WORKFLOW.md`
2. `.agent-workflow/PROJECT.md`
3. 当前任务 `.agent-workflow/tasks/<task-id>.md`
4. 项目声明的架构和测试文档
5. 需要对照「本宿主怎么落地」时再读 `.agent-workflow/CAPABILITIES.md`

Claude 插件、Command、Agent、Hook 和 LSP 都不能改变人工确认门禁、授权范围、最大修复轮次和 Definition of Done。

## 冲突优先级

与 Codex / Cursor 相同，以 `WORKFLOW.md` 为准：宿主安全审批 > 已批准授权包与门禁/DoD > 改变范围的口头指令须回审批 > `PROJECT.md` > 本适配文件。

## Claude Code 能力映射

对照设计参考文档中的能力拆分思路（历史材料，非当前宿主列）。插件只是填格子的可选说明，不是流程前置依赖：

- `explore` / `plan` / `design` / `implement`：`feature-dev`（设计后必须暂停等批准）或原生能力
- `review`：`code-review` 编排；维度可用 `pr-review-toolkit`，输出仍须落入 `REVIEW_TEMPLATE.md`
- `deliver`：`commit-commands` 仅在批准级别内；默认 L2 不允许 Push；也可用 Git CLI
- `learn`：`claude-md-management` 或人工维护；经验按核心晋升规则进入长期文档
- 代码语义：语言 LSP；不改变流程状态

插件未安装或本工作流不使用 Claude 时，当前宿主按 `CAPABILITIES.md` 降级列与 `WORKFLOW.md` 继续。

插件细则见同目录 `plugins.md`。

## Claude Code 执行约束

- 规划设计确认前只进行读取、搜索、分析和任务文件维护。
- 批准后自主执行实现、验证、Review、修复和复验。
- 普通测试失败和 Review Finding 在 AI 内部闭环处理，不反复打断用户。
- `ralph-loop` 如启用，最多 3 轮，且不得改变批准基线。
- `code-simplifier` 仅在行为测试通过后可选执行，执行后必须重新验证。
- `hookify` 只用于稳定、机械、已有真实失败证据的 Guardrail。
- Governed Path 才按项目配置启用深度安全或迁移专项审查。

## 无能力时的降级

- 无目标插件：使用原生读取、编辑、命令和 Agent 能力执行相同契约。
- 无独立 Agent：使用新会话 Review；仍不可用时按 Review 模板串行复审。
- 无 Git 仓库：L2 降级为 L1，并在最终交付中说明。
- Hook 故障：不得把 Hook 未拦截视为操作已获授权，仍以任务授权记录为准。
