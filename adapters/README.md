# Agent 适配层说明

## 原则

1. **Codex / Cursor / starFactory 的适配文件，一律只放在 `adapters/<host>/`。** 本工作流仓库根目录不存放这些宿主的适配源。
2. **在要用某个 Agent 开发的仓库里，按该 Agent 的目录约定做路径对齐**（复制或链接均可）。

跨 Agent 能力对照见 `.agent-workflow/CAPABILITIES.md`。本目录不定义生命周期与门禁。

**业务仓接入步骤（交给 AI）** 写在仓库根 `README.md`「接入（交给 AI）」；此处只列路径对齐表。

## 路径对齐

| 宿主        | 本仓库源（唯一）                            | 开发仓库对齐到                      |
| ----------- | ------------------------------------------- | ----------------------------------- |
| Codex       | `adapters/codex/AGENTS.md`                  | 项目根 `AGENTS.md`                  |
| Cursor      | `adapters/cursor/rules/cursor-workflow.mdc` | `.cursor/rules/cursor-workflow.mdc` |
| starFactory | `adapters/starFactory/AGENTS.md`            | `.starFactory/AGENTS.md`            |

各宿主目录内的 `README.md`、以及 `adapters/cursor/rules/adapters-layout.mdc`，是本适配层仓库的说明/维护约定，不对齐到业务项目。

## Claude Code（仅设计参考，不接入）

**本工作流不使用 Claude Code。** 不提供开发仓库对齐入口。参考材料在 `docs/reference/claude/`。

可选：社区 Skill / MCP 增强见 `docs/community-capability-alignment.md`。
