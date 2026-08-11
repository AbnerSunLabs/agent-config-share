# Claude Code 设计参考（不接入）

> **本工作流不使用 Claude Code。**  
> 当前实际使用的 AI Agent：Codex、Cursor、starFactory。

本目录仅保留 Claude Code 相关材料，作为工作流设计时的**能力分层与降级思路参考**，例如 Skill / Agent / Hook / LSP / Plugin 如何对应到通用能力。

| 文件         | 用途                                                                 |
| ------------ | -------------------------------------------------------------------- |
| `plugins.md` | Claude 插件与通用能力的对照（参考）                                  |
| `CLAUDE.md`  | 若将来有人阅读 Claude 风格入口时的参考草稿（**不要复制到业务项目**） |

当前宿主要用社区 Skill / MCP 对齐同等能力时，请读仓库根下：

[`docs/community-capability-alignment.md`](../../community-capability-alignment.md)

请勿：

- 将本目录复制到业务项目作为工作流入口
- 要求 Codex / Cursor / starFactory 安装或模拟其中插件
- 把插件名写进 `.agent-workflow/WORKFLOW.md` 或当前宿主适配文件

跨 Agent 落地请只看：

- `.agent-workflow/WORKFLOW.md`
- `.agent-workflow/CAPABILITIES.md`
- `adapters/`（Codex / Cursor / starFactory；开发仓库按宿主目录约定对齐）
