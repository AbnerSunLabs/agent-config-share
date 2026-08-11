# starFactory 工作流入口

> **本仓库源路径：** `adapters/starFactory/AGENTS.md`。  
> **开发仓库对齐到：** `.starFactory/AGENTS.md`。  
> 请确保项目已包含 `.agent-workflow/`。本文件只做 starFactory 能力映射，核心流程以 `.agent-workflow/WORKFLOW.md` 为准；跨宿主实现对照见 `.agent-workflow/CAPABILITIES.md`。

## 必读顺序

1. `.agent-workflow/WORKFLOW.md`
2. `.agent-workflow/PROJECT.md`
3. 当前任务 `.agent-workflow/tasks/<task-id>.md`
4. 项目声明的架构和测试文档
5. 需要对照「本宿主怎么落地」时再读 `.agent-workflow/CAPABILITIES.md`

源文件只在 `adapters/starFactory/`；在用 starFactory 开发的仓库里对齐到 `.starFactory/`。不要把本工作流入口散落到其他宿主目录。

## 默认行为

收到非琐碎开发任务时，**默认**按 `WORKFLOW.md` 执行：探索 → 写/更新任务文件 → `awaiting_approval` → 停止改业务源码。用户只需描述任务；批准时说「批准，L2」（或指定级别）即可，无需粘贴长启动话术。

## 冲突优先级

以 `WORKFLOW.md` 为准。摘要：

1. 宿主安全审批与环境强制限制
2. 已批准的执行授权包、人工门禁与 Definition of Done
3. 用户即时口头指令若改变目标/范围/验收，必须回到 `drafting` 重新审批
4. `PROJECT.md` 与任务设计
5. 对齐后的 `.starFactory/` 内适配文件

不得用本文件或口头「跳过流程」覆盖审批门禁与 DoD。不要依赖 Claude Code（本工作流不使用）或其他非当前宿主的专属插件名完成本流程。

## starFactory 能力映射

对照 `CAPABILITIES.md` 中的 starFactory 列：

- `explore` / `plan` / `design`：先只读探索真实仓库，再按任务模板写出执行授权包；规划完成后进入 `awaiting_approval`。
- 人工门禁：未批准前只维护 `.agent-workflow/tasks/*` 与必要的 `PROJECT.md`，不修改业务源码。
- `implement`：批准后在授权范围内最小影响实现；保留用户已有变更。
- `verify`：运行 `PROJECT.md` 真实命令并记录退出码与关键证据。
- `review`：优先独立 Reviewer 或新会话；否则按 `REVIEW_TEMPLATE.md` 串行复审；缺陷优先。
- `fix`：P0/P1 必须修复并复验；最多 3 轮，超限 `blocked`。
- `deliver`：默认 L2，原子 Commit；未经 L3 授权禁止 Push 或创建 PR。
- `learn`：写入任务经验沉淀；稳定后晋升到 `.starFactory/` 内的长期说明（不得改写 `WORKFLOW.md` 门禁）。

## 执行约束

- 工具调用前简要说明目的和预期结果，但不因普通步骤请求人工决策。
- 用户在执行期间追加要求时，判断是范围内补充还是执行基线变化；基线变化必须回到审批。
- 进入 `blocked` 时提交：精确阻断、已尝试、关键证据、2–3 个互斥选项及推荐。
- 完成前必须运行项目检查、完成独立 Review、修复阻断问题并复验。
- 没有验证证据时只报告「尚未验证」，不得报告完成。

## 无能力时的降级

- 无规划模式：按 `TASK_TEMPLATE.md` 在对话和文件中完成规划设计。
- 无独立 Reviewer：新会话 Review；仍不可用时按 Review 模板串行复审。
- 无 Git 仓库：L2 降级为 L1，并在最终交付中说明。
- 无网络或外部权限：完成所有可执行的本地工作，将精确阻断写入任务文件。
- 缺失能力一律走 `CAPABILITIES.md` 降级列。
