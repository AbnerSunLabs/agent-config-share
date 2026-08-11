# Claude Code 工作流入口

> 将本文件复制到项目根目录 `CLAUDE.md`，并确保项目已包含 `.agent-workflow/`。本文件只做 Claude Code 能力映射，核心流程以 `.agent-workflow/WORKFLOW.md` 为准。

## 必读顺序

1. `.agent-workflow/WORKFLOW.md`
2. `.agent-workflow/PROJECT.md`
3. 当前任务 `.agent-workflow/tasks/<task-id>.md`
4. 项目声明的架构和测试文档

Claude 插件、Command、Agent、Hook 和 LSP 都不能改变人工确认门禁、授权范围、最大修复轮次和 Definition of Done。

## Claude Code 能力映射

- `feature-dev`：映射探索、规划、设计和实现。设计完成后必须暂停，人工批准后才能进入实现。
- `code-review`：作为独立 Review 编排能力。
- `pr-review-toolkit`：为 Review 提供测试、异常、类型、质量和简化维度，不单独重复编排。
- `commit-commands`：只在批准的交付级别内执行；默认 L2 不允许 Push。
- `claude-md-management`：维护项目长期上下文，但经验必须按核心晋升规则进入长期文档。
- 语言 LSP：提供符号、类型、引用和诊断，不改变流程状态。

插件未安装时，按 `.agent-workflow/WORKFLOW.md` 的通用能力和降级路径继续，不得将插件缺失视为流程阻断。

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

完整插件映射见 `docs/claude-plugin-mapping.md`。

