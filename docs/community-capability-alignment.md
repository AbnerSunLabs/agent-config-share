# 社区 Skill / MCP 能力对齐

> **定位：** 用可移植的社区 Skill（`SKILL.md`）与 MCP，为 **Codex / Cursor / starFactory** 增强与 Claude 官方插件**同职责**的能力。  
> **权威契约：** `.agent-workflow/WORKFLOW.md`、`.agent-workflow/CAPABILITIES.md`。  
> **Claude 对照（仅参考）：** `docs/reference/claude/plugins.md`。  
> 社区方案只增强执行，不得越过人工审批、改变 L1–L4 或降低 Definition of Done。

## 1. 为什么需要本表

Claude Code 插件不能安装到其他宿主。跨 Agent 可复用的是：

1. 本仓库的**能力名**（`explore` / `plan` / …）与流程契约；
2. 开放格式的 **Agent Skills**（见 [skills.sh](https://skills.sh/)、[agentskills](https://agentskills.io)）；
3. 跨宿主的 **MCP**（工具与外部系统）。

对齐单位永远是**能力**，不是 Claude 插件名。不要把插件名写进任务文件或当前宿主适配入口。

## 2. 使用规则

1. V1 **不要求**安装任何社区 Skill 或 MCP；缺失时走 `CAPABILITIES.md` 降级列。
2. 安装前确认：输入/输出清晰、失败可降级、不绕过 `awaiting_approval`。
3. Skill 路径因宿主而异（如 `.agents/skills/`、`.cursor/skills/`、`~/.codex/skills/`）；可用 `npx skills add <owner/repo@skill>` 安装。
4. 含 Hook / `allowed-tools` 等宿主专属字段的 Skill，换端时需删减或改写。
5. 发现与晋升仍遵循 `docs/evolution-roadmap.md`：先有真实痛点，再固化为默认配置。

## 3. 能力对齐总表

| 能力 / 场景            | Claude 插件（设计参考）       | 社区 Skill（优先）                                                                                                                              | MCP / 宿主原生                                        | 保真度     | 备注                                   |
| ---------------------- | ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ---------- | -------------------------------------- |
| `explore`–`implement`  | `feature-dev`                 | `obra/superpowers@brainstorming` + `writing-plans` + `executing-plans` + `subagent-driven-development`；备选 `notedit/happy-skills@feature-dev` | —                                                     | 高         | 规划写完须停在 `awaiting_approval`     |
| `review`（编排）       | `code-review`                 | `mattpocock/skills@code-review`；`obra/superpowers@requesting-code-review` + `receiving-code-review`                                            | —                                                     | 高         | 优先独立子代理或新会话                 |
| Review 维度            | `pr-review-toolkit`           | `wshobson/agents@code-review-excellence`；或自建多 Skill                                                                                        | —                                                     | 中         | 权威维度仍以 `REVIEW_TEMPLATE.md` 为准 |
| `deliver`（L2 Commit） | `commit-commands`             | `github/awesome-copilot@conventional-commit` / `git-commit`                                                                                     | Git CLI                                               | 中高       | 遵守批准的交付级别                     |
| `deliver`（L3 PR）     | `commit-commands`（越权部分） | —                                                                                                                                               | **GitHub MCP**                                        | 中高       | 仅 L3+ 授权后使用                      |
| `learn`                | `claude-md-management`        | 宿主 Rules / `AGENTS.md` / `.starFactory` 说明                                                                                                  | —                                                     | 中         | 无统一跨端「上下文管理器」             |
| 项目初始化             | `claude-code-setup`           | （可选）bootstrap 类 Skill                                                                                                                      | —                                                     | 低         | 默认人工填写 `PROJECT.md`              |
| 代码语义               | 语言 LSP                      | —                                                                                                                                               | **宿主 LSP** + 编译器/测试；文档可用 **Context7 MCP** | 高（LSP）  | LSP 不是 Skill                         |
| 安全软护栏             | `security-guidance`           | `addyosmani/agent-skills@security-and-hardening`；`getsentry/skills@security-review`                                                            | —                                                     | 中         | 不替代 Governed 专项审查               |
| 深度安全审计           | `claude-security`             | 同上 + 领域 Skill（auth 等）                                                                                                                    | 可选安全类 MCP                                        | 中         | 仅 Governed / security Profile         |
| 测后简化               | `code-simplifier`             | `brianlovin/agent-config@simplify`；`simonwong/writing-skills@code-simplifier`                                                                  | —                                                     | 中高       | 测过 → 只改近期 diff → 复验            |
| `fix` 循环             | `ralph-loop`                  | `andrelandgraf/fullstackrecipes@ralph-loop`；`giuseppe-trisciuoglio/developer-kit@ralph-loop`                                                   | —                                                     | 中         | **最多 3 轮**；不得改审批基线          |
| Guardrail              | `hookify`                     | 仅规则文案类 Skill                                                                                                                              | **宿主 Hook** / 权限系统                              | 低（跨端） | 强制执行须各宿主自配                   |
| 造 Skill（建设期）     | `skill-creator`               | `anthropics/skills@skill-creator`                                                                                                               | —                                                     | 高         | 非日常任务依赖                         |
| 查库文档               | （探索辅助）                  | `upstash/context7@find-docs` 等                                                                                                                 | **Context7 MCP**                                      | 高         | 补文档，不改流程状态                   |
| 浏览器验收             | （验证辅助）                  | —                                                                                                                                               | **Playwright MCP**                                    | 高         | 按 `PROJECT.md` 需要启用               |

安装量与包名以 [skills.sh](https://skills.sh/) 实时检索为准；上表为对齐起点，可被更新的社区包替代，但能力名与契约不变。

## 4. 可选增强起步包（对照 Claude 参考闭环）

以下安装**均非** V1 / V1.1 退出条件；未安装仍按 `CAPABILITIES.md` 降级列执行。  
仅在有真实痛点时，按与 Claude 参考文档同构的顺序择一验证：

```text
feature-dev 平替（superpowers 规划/执行套件）
→ code-review 平替
→ conventional-commit
→ 宿主 LSP +（可选）Context7
→ security / simplify / ralph-loop（有真实痛点再加）
→ 宿主 Hook（仅机械、已验证规则）
```

示例安装命令（全部可选；按痛点择一验证即可）：

```bash
# 对齐 explore–implement（feature-dev）
npx skills add obra/superpowers@brainstorming
npx skills add obra/superpowers@writing-plans
npx skills add obra/superpowers@executing-plans
npx skills add obra/superpowers@subagent-driven-development

# 对齐 review
npx skills add mattpocock/skills@code-review
npx skills add obra/superpowers@requesting-code-review
npx skills add obra/superpowers@receiving-code-review

# 对齐 deliver（L2）
npx skills add github/awesome-copilot@conventional-commit

# 可选：simplify / ralph / security（V2 痛点驱动）
npx skills add brianlovin/agent-config@simplify
npx skills add andrelandgraf/fullstackrecipes@ralph-loop
npx skills add addyosmani/agent-skills@security-and-hardening
```

MCP（按需）：

| 缺口          | 建议           |
| ------------- | -------------- |
| 库文档        | Context7       |
| L3 PR / Issue | GitHub MCP     |
| UI / E2E 证据 | Playwright MCP |

## 5. 与流程契约的接法

```text
.agent-workflow/WORKFLOW.md      ← 阶段、门禁、DoD、最多 3 轮修复
.agent-workflow/CAPABILITIES.md  ← 能力名与各宿主落地/降级
docs/community-capability-alignment.md  ← 本文件：可选社区增强
adapters/                        ← 宿主适配源；开发仓库按宿主约定对齐路径
```

强制约束示例：

- `writing-plans` / `feature-dev` 类 Skill 输出后 → 任务状态 `awaiting_approval`，未批准不改业务源码。
- `ralph-loop` 类 Skill → 映射 `fix`，超 3 轮 → `blocked`，并写清根因与选项。
- `code-simplifier` → 不得作为 DoD 强制阶段。
- 任何 Hook / MCP → 故障时不得视为「已获授权」。

## 6. 已知缺口（社区暂无 1:1）

| Claude 参考能力               | 现状                                                        |
| ----------------------------- | ----------------------------------------------------------- |
| `pr-review-toolkit` 五维一体  | 以 `REVIEW_TEMPLATE.md` 自建最稳；社区多为单点 Review Skill |
| `hookify` 跨端强制            | 只能各宿主分别配置 Hook                                     |
| `claude-md-management`        | 用各宿主长期文档 + 本仓库经验晋升规则                       |
| `session-report` / `receipts` | 留待 V3；暂无成熟通用平替                                   |
| `claude-code-setup`           | 默认人工维护 `PROJECT.md`                                   |

## 7. 晋升门槛

社区包进入个人或项目默认配置前，须满足与 Claude 插件相同的门槛（见 `docs/reference/claude/plugins.md` §8）：

- 解决已发生的真实问题，多任务收益稳定；
- 输入、输出、失败行为明确，可降级；
- 不改变人工审批与权限边界；
- 不与现有能力重复制造噪声。
