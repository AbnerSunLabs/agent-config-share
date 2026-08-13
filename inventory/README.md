# Agent 配置清单

本目录是 Codex、Cursor、starFactory 三家用户级 MCP 与 Hooks 的**唯一意图来源**（`mcp.yaml`、`hooks.yaml`）。

## 用法

在仓库根目录执行：

```bash
python3 scripts/agent-config sync              # 默认只检查
python3 scripts/agent-config sync --apply      # 合并写入（写入前自动备份）
python3 scripts/agent-config sync --apply --prune
python3 scripts/agent-config sync --only mcp
python3 scripts/agent-config sync --only hooks
```

退出码：`0` 无缺口；`1` 有缺口；`2` 目标文件缺失/解析失败或清单 schema 错误。

## 说明

- 密钥与 Token **只写环境变量名**（如 `CONTEXT7_API_KEY`），禁止在 yaml 中写真实取值。
- 本工具不提供 Web 配置面板；仅通过 CLI 对账与合并。
- `--only` 时不会读取未选中域的宿主配置文件，避免无关损坏影响结果。
