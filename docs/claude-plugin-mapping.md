# Claude Code 官方插件能力映射

## 1. 定位

Claude Code Plugin 可以组合 Skill、Command、Agent、Hook、MCP 和 LSP。它们在本工作流中属于宿主适配层：负责增强某项通用能力，但不拥有生命周期状态、人工审批、权限边界和完成标准。

核心流程永远可在没有任何插件时运行。

## 2. V1.1 推荐组合

| 通用能力 | Claude 插件 | 使用方式 | 缺失时降级 |
|---|---|---|---|
| 项目初始化 | `claude-code-setup` | 初次接入时扫描仓库并提出配置建议 | 人工填写 `PROJECT.md` |
| 探索、规划、设计、实现 | `feature-dev` | 复用完整开发流程，但在设计后插入人工门禁 | 按核心流程串行执行 |
| 独立 Review | `code-review` | 编排独立专业 Reviewer | 新会话或串行 Review |
| Review 维度 | `pr-review-toolkit` | 提供 testing、error-handling、type-design、quality、simplification 检查 | 使用 `REVIEW_TEMPLATE.md` |
| L2 交付 | `commit-commands` | 生成符合项目规范的原子 Commit | 使用标准 Git CLI |
| 长期上下文 | `claude-md-management` | 维护 `CLAUDE.md` 和会话经验 | 人工维护项目文档 |
| 代码语义 | 语言 LSP | 提供类型、符号、引用和诊断 | 文本搜索、编译器和测试 |

建议先使用上述组合跑通真实任务，不要同时引入 Hook、自动循环和状态引擎。

## 3. `feature-dev` 接入契约

`feature-dev` 的探索、设计、实现、Review 顺序与本工作流高度一致，但必须增加人工授权边界：

```text
理解代码库
→ 输出规划与设计
→ 写入任务文件
→ 状态 awaiting_approval
→ 人工确认
→ 状态 approved
→ 实现与验证
```

禁止让插件在规划设计完成后自动越过人工确认。批准后，插件可以连续执行实现阶段，不需要为普通技术细节再次提问。

## 4. Review 组合方式

`code-review` 与 `pr-review-toolkit` 的关系是“编排器 + 检查维度”，不是两个相互独立的重复 Review：

```text
code-review
├── correctness 与 acceptance
├── pr-review-toolkit/testing
├── pr-review-toolkit/error-handling
├── pr-review-toolkit/type-design
├── pr-review-toolkit/code-quality
└── 项目 Review Profile
```

所有 Reviewer 输出必须转换成统一 Finding：

- ID
- 文件和行号
- 优先级 P0-P3
- 置信度 high、medium、low
- 类别
- 影响
- 证据
- 修复建议

低置信度且没有复现或第二证据的问题不能单独作为 P0/P1 阻断结论。

## 5. L2 交付与 `commit-commands`

`commit-commands` 只执行任务授权的交付级别：

- L1：不得 Commit。
- L2：允许原子 Commit，禁止 Push。
- L3：允许 Push 功能分支并创建或更新 PR。
- L4：是否合并或部署仍受项目和宿主安全审批约束。

Commit 前必须完成 DoD，不允许用 Commit 成功代替测试和 Review 通过。

## 6. V2 可选增强

### 6.1 `security-guidance`

适合实现期间持续提醒注入、XSS、SSRF、硬编码凭证和权限问题。它是软护栏，不替代 Governed Path 的最终专项审查。

### 6.2 `claude-security`

仅在 `security` Profile 或 Governed Path 按需启用，用于深度安全审计、对抗验证和修复复验。普通低风险任务不默认运行。

### 6.3 `code-simplifier`

只在以下条件全部满足时启用：

- 行为实现已完成。
- 相关测试已经通过。
- 简化范围只包含近期修改。
- 简化后重新运行测试和 Review。

它不能作为所有任务的强制阶段，避免无收益改写扩大 diff。

### 6.4 `ralph-loop`

只映射 `reviewing → fixing → validating → reviewing` 循环：

- 最多 3 轮。
- 只处理当前任务验收、测试和 Review 问题。
- 不得增加新功能或改变公共契约。
- 每轮必须产生真实验证证据。
- 超限后进入 `blocked`，输出根因、尝试和选项。

### 6.5 `hookify`

只把符合以下条件的规则转换为 Hook：

- 判断输入明确。
- 行为可以机械判定。
- 误拦截成本可控。
- 已在多个真实任务中重复出现。
- Hook 故障时有降级方式。

优先候选：敏感凭证、危险删除、强制推送、未授权数据库迁移、未经授权的 L3/L4 操作。

不适合 Hook：主观风格、命名偏好、架构建议和依赖业务语义的判断。

## 7. 工作流建设工具

以下插件用于建设工作流，不是日常开发任务的必需运行时依赖：

| 插件 | 用途 | 推荐阶段 |
|---|---|---|
| `skill-creator` | 创建、优化和评估稳定 Skill | V2 |
| `plugin-dev` | 将 Skills、Agents、Hooks、MCP 打包 | V3 |
| `session-report` | 分析 Session 成本和使用模式 | V3 |
| `receipts` | 汇总交付产出和复盘信息 | V3 |
| `example-plugin` | 学习最小插件目录结构 | V3 |

## 8. 插件晋升门槛

一个能力进入个人流程默认配置前，必须满足：

- 解决已经发生的真实问题。
- 在至少多个代表性任务中收益稳定。
- 明确知道输入、输出和失败行为。
- 可以在插件不可用时降级。
- 不改变人工审批和权限边界。
- 不与现有能力重复产生噪声。

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

这个顺序先保证开发闭环，再增强质量和强制约束，最后才进行插件化分发。

