# Claude Code 插件实现说明（附录）

> **定位：** Claude Code **不是**本工作流当前使用的 AI Agent。本文件仅作设计参考：说明若用 Claude 插件，如何对应到通用能力。  
> **当前使用：** Codex、Cursor、starFactory。  
> **不是**跨 Agent 核心契约。当前宿主不要安装或模拟这些插件。  
> 插件名以 Anthropic 当前市场名为准；缺失或更名时对参考阅读无影响，执行仍按 `CAPABILITIES.md` 当前宿主列与降级列。

## 1. 与能力矩阵的关系

| 能力                                        | Claude 插件（可选）                    | 缺失时                        |
| ------------------------------------------- | -------------------------------------- | ----------------------------- |
| `explore` / `plan` / `design` / `implement` | `feature-dev`                          | 按 `WORKFLOW.md` 串行         |
| `review`                                    | `code-review` + `pr-review-toolkit`    | 新会话或 `REVIEW_TEMPLATE.md` |
| `deliver`                                   | `commit-commands`                      | Git CLI                       |
| `learn`                                     | `claude-md-management`                 | 人工维护项目文档              |
| （语义辅助，非流程能力）                    | 语言 LSP                               | 文本搜索、编译器、测试        |
| `fix`（V2 可选增强）                        | `ralph-loop`                           | 手动修复循环，仍限 3 轮       |
| 安全增强（Governed / security Profile）     | `security-guidance`、`claude-security` | `REVIEW_TEMPLATE` 安全清单    |
| Guardrail（V2）                             | `hookify`                              | 宿主权限 + 人工审批           |

核心流程永远可在没有任何插件时运行。

## 2. 参考：Claude 侧推荐组合（历史对照，非当前宿主接入）

若仅阅读 Claude 生态，下列组合曾用于跑通开发闭环；**当前宿主不要安装这些插件**，应改看 `docs/community-capability-alignment.md`。

| 通用能力              | Claude 插件            | 使用方式                                                      |
| --------------------- | ---------------------- | ------------------------------------------------------------- |
| 项目初始化            | `claude-code-setup`    | 初次接入时扫描仓库并提出配置建议；也可人工填写 `PROJECT.md`   |
| `explore`–`implement` | `feature-dev`          | 复用完整开发流程，但在设计后插入人工门禁                      |
| `review`              | `code-review`          | 编排独立专业 Reviewer                                         |
| Review 维度           | `pr-review-toolkit`    | testing、error-handling、type-design、quality、simplification |
| `deliver`（L2）       | `commit-commands`      | 原子 Commit；禁止越权 Push                                    |
| `learn`               | `claude-md-management` | 维护 `CLAUDE.md` 与会话经验                                   |
| 代码语义              | 语言 LSP               | 类型、符号、引用和诊断                                        |

## 3. `feature-dev` 接入契约

必须增加人工授权边界：

```text
理解代码库
→ 输出规划与设计
→ 写入任务文件
→ 状态 awaiting_approval
→ 人工确认
→ 状态 approved
→ 实现与验证
```

禁止插件在规划设计完成后自动越过人工确认。批准后可连续实现，无需为普通技术细节再提问。

## 4. Review 组合方式

`code-review` 与 `pr-review-toolkit` 是「编排器 + 检查维度」，不是两套重复 Review：

```text
code-review
├── correctness 与 acceptance
├── pr-review-toolkit/testing
├── pr-review-toolkit/error-handling
├── pr-review-toolkit/type-design
├── pr-review-toolkit/code-quality
└── 项目 Review Profile
```

所有输出必须转换成统一 Finding（见 `CAPABILITIES.md` §5 与 `REVIEW_TEMPLATE.md`）。  
低置信度且没有复现或第二证据的问题不能单独作为 P0/P1 阻断结论。

## 5. L2 交付与 `commit-commands`

- L1：不得 Commit。
- L2：允许原子 Commit，禁止 Push。
- L3：允许 Push 功能分支并创建或更新 PR。
- L4：合并或部署仍受项目与宿主安全审批约束。

Commit 前必须完成 DoD，不允许用 Commit 成功代替测试和 Review 通过。

## 6. V2 可选增强

### 6.1 `security-guidance`

实现期软护栏（注入、XSS、SSRF、硬编码凭证等），不替代 Governed Path 最终专项审查。

### 6.2 `claude-security`

仅在 `security` Profile 或 Governed Path 按需启用。普通低风险任务不默认运行。

### 6.3 `code-simplifier`

仅当行为已完成、相关测试已通过、只简化近期修改、且简化后重新验证时可选启用。不作为强制完成门禁。

### 6.4 `ralph-loop`

只映射 `reviewing → fixing → validating → reviewing`：

- 最多 3 轮；不得改批准基线或加新功能。
- 每轮必须有真实验证证据；超限进入 `blocked`。

### 6.5 `hookify`

只转换输入明确、可机械判定、误拦成本可控、已在多任务重复出现的规则。  
优先：敏感凭证、危险删除、强制推送、未授权迁移、未授权 L3/L4。  
不适合：主观风格、命名偏好、依赖业务语义的判断。

## 7. 工作流建设工具（非日常依赖）

| 插件             | 用途                         | 推荐阶段 |
| ---------------- | ---------------------------- | -------- |
| `skill-creator`  | 创建与评估 Skill             | V2       |
| `plugin-dev`     | 打包 Skills/Agents/Hooks/MCP | V3       |
| `session-report` | Session 成本与使用模式       | V3       |
| `receipts`       | 交付与复盘汇总               | V3       |
| `example-plugin` | 学习最小插件结构             | V3       |

## 8. 插件晋升门槛

进入个人默认配置前必须满足：

- 解决已发生的真实问题，且在多个代表性任务中收益稳定。
- 明确输入、输出和失败行为；不可用时可降级。
- 不改变人工审批与权限边界；不与现有能力重复制造噪声。

## 9. 推荐接入顺序

```text
feature-dev
→ code-review + pr-review-toolkit
→ commit-commands
→ claude-md-management
→ 按语言启用 LSP
→ security-guidance / claude-security
→ ralph-loop
→ hookify
→ skill-creator / plugin-dev
```

先保证开发闭环，再增强质量与强制约束，最后才插件化分发。

## 10. 当前宿主的社区平替

本文件描述的是 Claude 侧参考实现。  
**Codex / Cursor / starFactory** 若要用社区 Skill / MCP 对齐同一能力，见：

[`docs/community-capability-alignment.md`](../../community-capability-alignment.md)

不要在当前宿主上安装或模拟本节插件；按能力矩阵与社区对齐表选用可移植方案。
