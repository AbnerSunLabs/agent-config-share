# Cursor 适配

**源只在本目录。** 用 Cursor 开发某个仓库时，按 Cursor 目录约定做路径对齐。

| 本仓库源                                    | 开发仓库对齐到                      |
| ------------------------------------------- | ----------------------------------- |
| `adapters/cursor/rules/cursor-workflow.mdc` | `.cursor/rules/cursor-workflow.mdc` |

须同时具备 `.agent-workflow/`。

- `rules/cursor-workflow.mdc`：工作流入口（对齐到开发仓库）
- `rules/adapters-layout.mdc`：本适配层仓库维护约定（不对齐到业务项目）
- `README.md`：本说明（不对齐）

边界：生命周期与门禁见 `.agent-workflow/WORKFLOW.md`；能力对照见 `CAPABILITIES.md`。
