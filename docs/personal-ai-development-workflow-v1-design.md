# 个人 AI 研发工作流 V1 设计

> 版本：V1.0  
> 日期：2026-08-11  
> 状态：已确认设计基线

## 1. 摘要

这套工作流面向个人开发者，采用“人工决策、AI 自主执行、证据驱动交付”的协作模式。人工参与需求、规划和设计确认；确认后，AI 在授权范围内自主完成代码实现、验证、独立 Review、问题修复、重新验证和 L2 交付。

V1 使用 Agent 无关的 Markdown 契约作为唯一事实源，通过薄适配文件接入 **Codex、Cursor、starFactory**。  
**不使用 Claude Code**；其官方插件体系仅作为设计参考（能力分层：Skill / Agent / Hook / LSP / Plugin），材料见 `docs/reference/claude/`。宿主专属 Skill、Agent、Hook、Plugin 只负责实现能力，不定义核心流程。

## 2. 设计来源与取舍

设计吸收两类参考：

- 个人研发工作流设计中的 Fast、Standard、Governed 路径，分层 Review、风险分级、修复回退和证据交付。
- Claude Code 官方插件体系中的能力分层（**仅作设计参考，非运行时依赖**）：Skill 表达知识与流程，Agent 提供独立角色，Hook 强制 Guardrail，LSP 提供代码语义，Plugin 负责打包分发。

V1 不直接实现参考设计中的 SQLite 状态引擎、崩溃恢复、多 Agent 文件所有权、Review 聚合器和全生命周期 Hooks。这些能力只有在真实任务暴露出稳定瓶颈后才进入后续版本。

## 3. 核心原则

1. **人工决定 What 和 Why**：目标、范围、验收标准、风险容忍度和交付权限由人工确认。
2. **AI 决定 How**：实现细节、普通技术选择、测试组织和修复方式由 AI 在授权范围内自主决定。
3. **一次审批，后续放权**：规划和设计形成一个执行授权包；人工确认后，AI 不因普通实现问题反复等待。
4. **证据先于结论**：没有真实测试、Lint、类型检查、构建或等效证据，不得宣称完成。
5. **Review 必须闭环**：发现阻断问题后必须修复并重新验证，不能只生成报告。
6. **核心流程与宿主解耦**：任何宿主不可用时，流程仍可通过通用文件和命令串行执行。
7. **先跑通，再强制化**：先观察真实失败模式，再将稳定、高价值规则升级成 Skill 或 Hook。

## 4. 人机职责边界

| 角色        | 负责                                               | 不负责                                       |
| ----------- | -------------------------------------------------- | -------------------------------------------- |
| 人工        | 目标、范围、设计确认、授权等级、重大风险和发布决策 | 普通代码细节、常规测试失败、一般 Review 修复 |
| AI 实现者   | 探索、实现、测试、修复、文档和原子 Commit          | 未授权扩展范围、不可逆外部操作               |
| AI Reviewer | 独立检查正确性、回归、测试、安全和可维护性         | 直接修改代码或自行降低验收标准               |
| AI Verifier | 运行并记录真实验证，核对验收条件                   | 用推测或代码阅读代替可执行证据               |

## 5. 生命周期

```text
需求输入
  → drafting              探索、规划、设计
  → awaiting_approval     等待人工确认执行授权包
  → approved              授权基线冻结
  → implementing          AI 自主实现
  → validating            运行相关验证
  → reviewing             独立 Review
  → fixing                修复 P0/P1 和已决定处理的 P2
  → validating            修复后复验
  → ready_for_delivery    完整验证与交付检查
  → done                  L2 交付完成

异常终态：blocked
```

允许的主要回退：

- `validating → implementing`：验证发现实现缺陷。
- `reviewing → fixing → validating → reviewing`：Review 发现阻断问题。
- `ready_for_delivery → fixing`：最终检查发现缺陷。
- 任意执行状态 → `blocked`：出现必须人工决策的停止条件。

## 6. 执行授权包

人工确认前，AI 必须提交：

- 目标和面向用户的最终行为。
- 明确的非目标和范围边界。
- 可逐项验证的验收条件。
- 现状探索证据和受影响区域。
- 技术方案、接口或数据变化。
- 测试与验证方案。
- 风险、兼容性和回滚方式。
- 允许 AI 自主决定的事项。
- 需要再次确认的高风险操作。
- 本次交付级别，默认 L2。

人工确认后，上述内容成为执行基线。AI 可以调整内部实现，但不得静默改变目标、接口契约、数据语义、风险级别和验收标准。

## 7. 三条工作流路径

### 7.1 Fast Path

适用于文档、低风险样式、局部非行为修改和已有明确修复方案的小问题。

```text
探索 → 简化规划与设计 → 人工确认 → 实现 → 验证 → Review → L2 交付
```

不得仅用代码行数决定 Fast Path。涉及公共接口、数据、权限、依赖、关键配置或复杂回归时，必须升级。

### 7.2 Standard Path

适用于普通功能、非琐碎 Bug、局部重构和行为变化。

```text
完整探索 → 规划与设计 → 人工确认 → 实现 → 验证 → 独立 Review → 修复复验 → L2 交付
```

### 7.3 Governed Path

适用于认证授权、敏感数据、数据库迁移、基础设施、关键依赖和生产行为。

在 Standard Path 基础上增加：

- 明确回滚方案。
- 安全或迁移专项 Review。
- 高风险操作逐项授权。
- 更完整的集成、端到端或迁移验证。
- 默认不允许自动合并或部署。

## 8. AI 自主执行闭环

人工批准后，AI 连续执行：

1. 按现有架构进行最小影响实现。
2. 优先运行 touched-scope 检查，快速发现局部问题。
3. 运行项目声明的 Lint、类型检查、测试和构建命令。
4. 使用独立 Reviewer Agent；不可用时使用新上下文；仍不可用时按统一清单串行 Review。
5. 修复 P0/P1，记录 P2 的处理决定，忽略无证据的低置信度误报。
6. 修复后重新运行相关验证和 Review。
7. 最多自动循环 3 次；超过上限进入 `blocked` 并提交根因与尝试记录。
8. 执行完整交付检查并按授权级别交付。

AI 可以报告进度，但不得把普通实现选择变成阻塞式提问。

## 9. 必须暂停的条件

仅在以下情况请求人工介入：

- 需要突破已确认的目标、范围或验收条件。
- 设计基线存在根本矛盾，继续执行会产生错误结果。
- 需要执行未授权的删除、强制覆盖、数据库迁移、关键配置或外部发布。
- 缺少凭证、环境、数据或外部系统权限。
- 发现严重安全、隐私、数据丢失或生产事故风险。
- 同一阻断问题已完成 3 轮有证据的修复仍未解决。
- 真实项目状态与审批时的关键假设不一致。

## 10. Review 契约

Review 必须主动寻找缺陷，而不是总结改动。基础维度包括：

- Correctness：逻辑、状态流转、边界和并发。
- Acceptance：是否完整满足验收条件。
- Testing：关键路径、回归和失败场景是否有证据。
- Error handling：异常、超时、重试、降级和资源释放。
- Compatibility：API、配置、数据和迁移兼容性。
- Security：输入、权限、注入、凭证和敏感数据。
- Maintainability：复杂度、重复、耦合和命名。

优先级：

- P0：安全漏洞、数据丢失、生产事故风险，阻止交付。
- P1：逻辑错误、验收失败、破坏性回归，阻止交付。
- P2：重要质量或维护问题，需要修复或明确接受理由。
- P3：非阻断优化建议。

每条 Finding 必须包含位置、影响、证据、优先级、置信度和建议。无文件位置或可复现路径时，应明确标记为架构级问题或低置信度推断。

## 11. Definition of Done

任务只有同时满足以下条件才能进入 `done`：

- 验收条件逐项通过。
- 实际修改未超出授权范围。
- 真实验证命令和结果已记录。
- 未执行的验证及原因已记录。
- P0/P1 已清零。
- 修复后已完成相关复验。
- P2 已修复或明确记录接受理由。
- 遗留风险和后续事项已披露。
- Git 状态和交付级别符合授权。
- 最终修改清单、验证证据和 Review 结果完整。

没有运行验证时，只能报告“实现完成但尚未验证”，不得报告任务完成。

## 12. 交付级别

| 级别 | 授权范围                           |
| ---- | ---------------------------------- |
| L1   | 修改本地代码并验证                 |
| L2   | L1 + 创建原子 Git Commit，默认级别 |
| L3   | L2 + 推送功能分支并创建或更新 PR   |
| L4   | L3 + 合并或部署                    |

L3、L4 必须在执行授权包中明确授予。即使获得 L2 授权，AI 也不得自动 Push。

## 13. 跨 Agent 架构

核心契约定义能力，不绑定实现。完整矩阵见 `.agent-workflow/CAPABILITIES.md`。

| 通用能力  | 责任                                                          |
| --------- | ------------------------------------------------------------- |
| explore   | 只读探索和定位真实项目状态                                    |
| plan      | 输出目标、范围、验收条件和实施计划                            |
| design    | 输出架构、接口、数据、失败模式和测试策略                      |
| implement | 在授权范围内完成修改                                          |
| verify    | 执行并记录真实验证                                            |
| review    | 独立、只读、缺陷优先的审查                                    |
| fix       | 修复阻断问题并触发复验（逻辑角色，可与 implement 同一执行者） |
| deliver   | 按授权等级提交交付物                                          |
| learn     | 将复盘结果记录并按门槛提升为长期规则                          |

Codex、Cursor、starFactory 只负责把自身的 Mode、Skill、Agent、Command、Hook 和工具映射到上述能力。宿主适配源一律在 `adapters/<host>/`；在要用某个 Agent 开发的仓库里按该 Agent 目录约定对齐路径。Claude Code 不在当前使用列表中。

## 14. 跨宿主能力统一与 Claude 参考边界

跨 Agent 对齐的单位是**能力**（explore / plan / design / implement / verify / review / fix / deliver / learn），不是插件名。权威对照表：

`.agent-workflow/CAPABILITIES.md`

**当前使用宿主：** Codex、Cursor、starFactory。  
**Claude Code：** 不使用；`docs/reference/claude/` 仅保留设计参考，不可成为核心流程前置依赖，也不可要求当前宿主安装或模拟。参考摘要（理解能力拆分即可，不必落地）：

- `feature-dev` → explore、plan、design、implement（须插入人工门禁）
- `code-review` + `pr-review-toolkit` → review
- `commit-commands` → deliver（受 L1–L4 约束）
- `claude-md-management` → learn
- `security-guidance` / `claude-security` → Governed 或 security Profile 增强
- `ralph-loop` → 受限 fix 循环（最多 3 轮）
- `hookify` → 已验证的稳定 Guardrail
- LSP → 代码语义，不改变流程状态

当前宿主若用社区 Skill / MCP 对齐上述同等能力，见 `docs/community-capability-alignment.md`。

## 15. V1 产物

```text
.agent-workflow/
├── WORKFLOW.md
├── CAPABILITIES.md
├── PROJECT.template.md
├── TASK_TEMPLATE.md
└── REVIEW_TEMPLATE.md

adapters/                       # 宿主适配源（唯一存放处）
├── README.md                   # 原则 + 路径对齐表
├── codex/
│   ├── README.md
│   └── AGENTS.md               # 对齐到开发仓库 AGENTS.md
├── cursor/
│   ├── README.md
│   └── rules/
│       ├── cursor-workflow.mdc # 对齐到 .cursor/rules/
│       └── adapters-layout.mdc # 本仓维护约定（不对齐业务项目）
└── starFactory/
    ├── README.md
    └── AGENTS.md               # 对齐到 .starFactory/AGENTS.md

docs/
├── personal-ai-development-workflow-v1-design.md
├── evolution-roadmap.md
├── community-capability-alignment.md  # 社区 Skill/MCP 与能力对齐
├── claude-plugin-mapping.md    # 重定向至 docs/reference/claude/
└── reference/claude/           # 设计参考，不接入
    ├── README.md
    ├── CLAUDE.md
    └── plugins.md
```

V1 不提供运行时程序。任务状态由任务 Markdown 记录，项目命令由 `PROJECT.md` 声明，流程门禁由 Agent 执行并由最终证据验证。

## 16. 经验固化规则

纠正和异常先记录在当前任务的“经验沉淀”区域，再按以下条件提升：

- 明确的安全或破坏性操作红线：立即提升为全局规则。
- 同类行为问题重复出现：提升为规则或 Review 检查项。
- 已验证的完整操作方法：提升为 Skill。
- 跨项目稳定成立的工作流原则：提升为全局流程契约。
- 一次性业务偏好：保留在项目或任务级，不污染全局规则。

## 17. 成功标准

V1 的成功不以自动化程度衡量，而以以下结果衡量：

- 不同 Agent 能按同一任务文件接力。
- 规划设计确认后，AI 能完成实现到 L2 交付闭环。
- Agent 不再无证据宣称完成。
- Review 问题能进入修复和复验，而不是停留在报告。
- 高风险操作不会因为“自动执行”而默认扩大权限。
- 真实失败记录能够指导下一轮流程迭代。
