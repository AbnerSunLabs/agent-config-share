# Codex 工作流入口

> **本仓库源路径：** `adapters/codex/AGENTS.md`。  
> **开发仓库对齐到：** 项目根 `AGENTS.md`。  
> 请确保项目已包含 `.agent-workflow/`。本文件只做 Codex 能力映射，核心流程以 `.agent-workflow/WORKFLOW.md` 为准；跨宿主实现对照见 `.agent-workflow/CAPABILITIES.md`。

## 必读顺序

1. `.agent-workflow/WORKFLOW.md`
2. `.agent-workflow/PROJECT.md`
3. 当前任务 `.agent-workflow/tasks/<task-id>.md`
4. 项目声明的架构和测试文档
5. 需要对照「本宿主怎么落地」时再读 `.agent-workflow/CAPABILITIES.md`

## 默认行为

收到非琐碎开发任务时，**默认**按 `WORKFLOW.md` 执行：探索 → 写/更新任务文件 → `awaiting_approval` → 停止改业务源码。用户只需描述任务；批准时说「批准，L2」（或指定级别）即可，无需粘贴长启动话术。

## 冲突优先级

以 `WORKFLOW.md` 为准。摘要：

1. 宿主安全审批与环境强制限制
2. 已批准的执行授权包、人工门禁与 Definition of Done
3. 用户即时口头指令若改变目标/范围/验收，必须回到 `drafting` 重新审批
4. `PROJECT.md` 与任务设计
5. 本适配文件

不得用本文件或口头「跳过流程」覆盖审批门禁与 DoD。

## Codex 能力映射

对照 `CAPABILITIES.md` 中的 Codex 列：

- `explore` / `plan` / `design`：规划协作能力 + 任务模板；先探索真实仓库，再形成执行授权包。
- 人工门禁：规划设计完成后停止变异操作，等待用户明确批准。
- `implement`：批准后在范围内直接推进，普通技术选择不阻塞用户。
- `verify`：运行 `PROJECT.md` 中的真实命令并记录证据。
- `review`：优先独立代码 Reviewer；不可用时新会话，再不可用则按 `REVIEW_TEMPLATE.md` 串行。
- `fix`：P0/P1 必须修复并复验；最多 3 轮。
- `deliver`：默认 L2，原子 Commit；未经 L3 授权禁止 Push 或创建 PR。
- `learn`：写入任务经验沉淀，稳定后晋升到 `AGENTS.md` 或项目规则。

## Codex 执行约束

- 工具调用前简要说明目的和预期结果，但不因普通步骤请求人工决策。
- 用户在执行期间追加要求时，判断其是范围内补充还是执行基线变化；基线变化必须回到审批。
- 修改文件使用宿主推荐的安全编辑方式。
- 保留用户已有变更，禁止擅自回滚无关内容。
- 完成前必须运行项目检查、完成独立 Review、修复阻断问题并复验。
- 没有验证证据时只报告「尚未验证」，不得报告完成。

## 无能力时的降级

- 无规划模式：按任务模板在对话和文件中完成规划设计。
- 无子 Agent：使用新会话 Reviewer；仍不可用时按 Review 模板串行复审。
- 无 Git 仓库：L2 降级为 L1，并在最终交付中说明。
- 无网络或外部权限：完成所有可执行的本地工作，将精确阻断写入任务文件。
- 不要寻找或模拟 Claude Code 插件（本工作流不使用 Claude Code）；缺失的能力一律走 `CAPABILITIES.md` 降级列。
