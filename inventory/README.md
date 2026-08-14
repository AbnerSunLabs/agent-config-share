# Agent 配置清单

本目录是 Codex、Cursor、starFactory 三家用户级 MCP 与 Hooks 的**唯一意图来源**（`mcp.yaml`、`hooks.yaml`）。

本期已按本机用户级并集填入公共条目。密钥只写环境变量名。

## 用法

安装（与 skillshare 相同形态）：

```bash
curl -fsSL https://raw.githubusercontent.com/AbnerSunLabs/agent-loom/main/install.sh | sh
```

在本仓库开发时可执行 `./install.sh`，shim 指向当前工作树。

```bash
agentloom ui                 # 本机面板（127.0.0.1）
agentloom sync               # 默认只检查
agentloom sync --apply       # 合并写入（写入前自动备份）
agentloom sync --apply --prune
agentloom sync --only mcp --host cursor
agentloom sync --apply --only hooks --host starFactory
agentloom sync --apply --host cursor --host codex
```

未安装时开发路径仍可用：`python3 scripts/agentloom sync`。

退出码：`0` 无缺口；`1` 有缺口；`2` 目标文件缺失/解析失败或清单 schema 错误。

## 说明

- 密钥与 Token **只写环境变量名**（如 `GITHUB_TOKEN`），禁止在 yaml 中写真实取值。
- `tech-debt` 仅 Cursor（本机 star-flow 路径）；`node_repl` 为 Codex.app 内置，不进公共清单。
- Cursor 现有 `Figma` 与清单 `figma` 不同名，apply 会新增托管名 `figma`，旧名无标记不会被 prune。
- 每条 MCP / Hook 必填 `description`（用途说明），只给清单与 `agentloom ui` 展示，不写入宿主配置。
- 写入宿主配置的托管标记：JSON 用 `agentLoomId`，TOML 用 `agent_loom_id`。不读写旧名。
- 覆盖路径的环境变量：`AGENT_LOOM_HOME`（用户主目录）、`AGENT_LOOM_ROOT`（仓库根，测试用）、`AGENT_LOOM_SHARE_ROOT`（远程安装目录，默认 `~/.local/share/agent-loom`）、`AGENT_LOOM_BIN_DIR`（shim 目录）。不读取 `AGENT_CONFIG_*`。
- `macos-approval-notify` 仅 starFactory 的 `Notification`（权限/系统提醒）。`macos-stop-notify` 走 `Stop`（本轮回复结束）。Cursor 对应条目仍是注释，清单不写 Cursor。
