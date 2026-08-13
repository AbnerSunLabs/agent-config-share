# Agent 配置清单

本目录是 Codex、Cursor、starFactory 三家用户级 MCP 与 Hooks 的**唯一意图来源**（`mcp.yaml`、`hooks.yaml`）。

本期已按本机用户级并集填入公共条目。密钥只写环境变量名。

## 用法

在仓库根目录执行：

```bash
python3 scripts/agent-config sync              # 默认只检查
python3 scripts/agent-config sync --apply      # 合并写入（写入前自动备份）
python3 scripts/agent-config sync --apply --prune
python3 scripts/agent-config sync --only mcp --host cursor
python3 scripts/agent-config sync --apply --only hooks --host starFactory
python3 scripts/agent-config sync --apply --host cursor --host codex
```

退出码：`0` 无缺口；`1` 有缺口；`2` 目标文件缺失/解析失败或清单 schema 错误。

## 说明

- 密钥与 Token **只写环境变量名**（如 `GITHUB_TOKEN`），禁止在 yaml 中写真实取值。
- `tech-debt` 仅 Cursor（本机 star-flow 路径）；`node_repl` 为 Codex.app 内置，不进公共清单。
- Cursor 现有 `Figma` 与清单 `figma` 不同名，apply 会新增托管名 `figma`，旧名无标记不会被 prune。
- 本工具不提供 Web 配置面板。
