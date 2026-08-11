# 跨 Agent 能力矩阵

> 本文件定义工作流的**通用能力**及各宿主的实现方式。  
> 生命周期、门禁与 Definition of Done 以 `WORKFLOW.md` 为准；本文件不新增阶段，只说明「同一职责在不同 Agent 上怎么落地」。

## 1. 当前使用的宿主

**当前实际使用：** Codex、Cursor、starFactory。

**Claude Code：** 不使用。其插件体系与能力分层仅作为本工作流的**设计参考**（见 `docs/reference/claude/`），不提供业务项目接入入口，也不出现在下方主矩阵的「须落地」列中。

## 2. 使用规则

1. **统一的是能力，不是插件名。** 不得要求 Codex / Cursor / starFactory 安装或模拟 Claude 专属插件。
2. **行 = 必须具备的能力**；**列 = 当前宿主如何落地**。格子为空或工具不可用时，按「降级」列执行，不算流程失败。
3. 宿主专属细节放在对应适配目录（见 §6），不得回写进 `WORKFLOW.md`。
4. 新增宿主时：只增加一列实现说明，不改能力名称与契约要求。
5. 参考材料（含 Claude）不得改写当前宿主的接入步骤或完成标准。

## 3. 能力矩阵（当前宿主）

| 能力        | 契约要求（摘要）                                                      | Codex                                 | Cursor                                  | starFactory                          | 降级（任意宿主）                             |
| ----------- | --------------------------------------------------------------------- | ------------------------------------- | --------------------------------------- | ------------------------------------ | -------------------------------------------- |
| `explore`   | 只读探索真实代码、配置、测试与 Git 状态；能从仓库发现的事实不询问用户 | 只读搜索与文件阅读                    | 只读搜索与文件阅读                      | `.starFactory/` 入口约束下的只读探索 | 手动打开相关文件并记录到任务「探索证据」     |
| `plan`      | 输出执行授权包，写入任务文件，进入 `awaiting_approval` 后停止变异     | 可用的规划协作能力 + 任务模板         | Plan 模式或对话规划 + 任务模板          | 按任务模板规划；结果写入任务文件     | 按 `TASK_TEMPLATE.md` 在对话与文件中完成规划 |
| `design`    | 方案、影响范围、错误/回滚、验证计划、路径与 Review Profile、交付级别  | 与 `plan` 一并写入任务文件            | 同左                                    | 同左                                 | 同 `plan` 降级                               |
| `implement` | 批准后在授权范围内最小影响实现；保留用户已有变更                      | 直接编辑                              | Agent 模式直接编辑                      | 批准后直接编辑                       | 原生编辑工具按任务逐步改                     |
| `verify`    | 运行 `PROJECT.md` 真实命令，记录退出码与关键证据；禁止伪造通过        | Shell / 终端                          | Shell / 终端                            | Shell / 终端                         | 人工运行命令，执行者只负责记录结果           |
| `review`    | 独立、只读、缺陷优先；Finding 用统一格式；优先独立 Reviewer           | 独立 code-reviewer 子代理；否则新会话 | Task / 子代理 code-reviewer；否则新会话 | 独立 Reviewer 或新会话；否则串行模板 | 同一执行者按 `REVIEW_TEMPLATE.md` 串行复审   |
| `fix`       | 修复 P0/P1 与已决定处理的 P2；最多 3 轮，超限 `blocked`               | 实现循环内修复                        | 同左                                    | 同左                                 | 人工指定修复项后由执行者改并复验             |
| `deliver`   | 按批准的 L1–L4 交付；默认 L2 仅本地原子 Commit                        | Git CLI                               | Git CLI                                 | Git CLI                              | L2 不可用时降为 L1，并在交付中说明           |
| `learn`     | 任务结束记录踩坑；按晋升规则写入长期文档                              | `AGENTS.md` / 项目规则                | Rules / 项目文档                        | 晋升到 `.starFactory/` 内说明        | 只写在任务「经验沉淀」，不自动晋升           |

## 4. 能力与流程阶段对应

| 阶段 / 状态                      | 主要能力                                 |
| -------------------------------- | ---------------------------------------- |
| `drafting`                       | `explore` → `plan` + `design`            |
| `awaiting_approval` / `approved` | 人工门禁（非能力工具；任何插件不得越过） |
| `implementing`                   | `implement`                              |
| `validating`                     | `verify`                                 |
| `reviewing`                      | `review`                                 |
| `fixing`                         | `fix` → 再 `verify` / `review`           |
| `ready_for_delivery` / `done`    | `deliver`                                |
| 任务收尾                         | `learn`                                  |

## 5. Review 输出契约（宿主无关）

无论使用子代理还是串行复审，Finding 必须可落入 `REVIEW_TEMPLATE.md`：

- ID、位置、优先级 P0–P3、置信度 high/medium/low
- 类别、影响、证据、修复建议
- 低置信度且无第二证据时，不得单独作为 P0/P1 阻断

## 6. 宿主附录位置（工作流仓库源 → 开发仓库对齐）

下表左侧路径仅存在于**本工作流仓库**。在要用某个 Agent 开发的仓库里按右列对齐后，以已落盘的入口文件为准。

| 宿主        | 状态       | 工作流仓库源文件                            | 开发仓库对齐到                      |
| ----------- | ---------- | ------------------------------------------- | ----------------------------------- |
| Codex       | 当前使用   | `adapters/codex/AGENTS.md`                  | 项目根 `AGENTS.md`                  |
| Cursor      | 当前使用   | `adapters/cursor/rules/cursor-workflow.mdc` | `.cursor/rules/cursor-workflow.mdc` |
| starFactory | 当前使用   | `adapters/starFactory/AGENTS.md`            | `.starFactory/AGENTS.md`            |
| Claude Code | 仅设计参考 | `docs/reference/claude/`                    | **不对齐、不接入**                  |

原则：适配源只在 `adapters/<host>/`；在要用某个 Agent 开发的仓库里按上表对齐路径。详见 `adapters/README.md`。

## 7. 可选：社区 Skill / MCP 增强

当前宿主可用可移植的社区 **Skill**（`SKILL.md`）与 **MCP** 增强 §3 中的同一能力，而不安装 Claude 插件。

- 对齐表与起步安装命令：`docs/community-capability-alignment.md`
- 检索与安装：`npx skills find <关键词>`、[skills.sh](https://skills.sh/)

约束：

- V1 不要求安装；缺失时仍走本节矩阵「降级」列。
- 社区方案不得越过 `awaiting_approval`、改变 L1–L4 或降低 DoD。
- 宿主适配文件可引用能力名；避免把易变的社区包名写死为流程前置依赖。

## 8. Claude Code 参考说明（非接入）

Claude Code 的插件分层（Skill / Agent / Hook / LSP / Plugin）曾用于启发本工作流的能力拆分与降级思路。  
参考文档：`docs/reference/claude/plugins.md`、`docs/reference/claude/CLAUDE.md`。  
与社区平替的对照见 `docs/community-capability-alignment.md`。

阅读参考材料时注意：

- 不要把 Claude 插件名写进任务或当前宿主适配文件。
- 不要为「对齐 Claude」而安装任何 Claude 专属依赖。
- 当前宿主一律按 §3 矩阵与「降级」列执行；需要增强时优先看 §7。
