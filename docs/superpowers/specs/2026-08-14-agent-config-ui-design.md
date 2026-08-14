# agent-config 本地 Web 面板设计

日期：2026-08-14  
地位：承接 [2026-08-13-agent-config-mcp-hooks-share-design.md](./2026-08-13-agent-config-mcp-hooks-share-design.md) 中列为 V1.1 的「skillshare 式面板」；同步语义仍以该文档与现有 `sync` 为准。  
范围：本机 `127.0.0.1` 网页，浏览 Skills / MCP / Hooks；MCP 与 Hooks 点按钮调用现有检查/写入；Skills 仅打开目录与复制路径。安装体验对齐 skillshare：`curl | sh` 之后 PATH 上直接执行 `agent-config ui`。

---

## 1. 目标

用 `agent-config ui` 在本机打开卡片式目录页，降低对 CLI 参数的记忆成本。

成功标准：

1. 按 §4 安装后，终端直接执行 **`agent-config ui`**（不写 `python3 scripts/...`）。进程只绑定 `127.0.0.1`，打印可打开的 URL；默认尝试用系统浏览器打开该 URL（可用 `--no-open` 关闭）。
2. 页面能列出 `inventory/` 中的 MCP / Hooks，以及扫描到的 Skills 目录。
3. **检查差异** 调用现有 `sync.check`（不重写对账逻辑），顶栏与卡片展示结构化状态（已对齐 / 缺失 / 不一致 / 目标文件异常），不展示原始 stdout。
4. **写入同步** 须页面二次确认，且请求体带 `confirm: true`；确认后走现有 `backup_files` + `sync.apply`，默认 `prune=False`。
5. Skills 卡可「打开目录」「复制路径」；打开目录只允许扫描白名单内的路径。
6. 页面与 API 不输出密钥、Token、环境变量取值。

---

## 2. 非目标（本期）

- 不装、不卸、不启用/禁用 Skill，不调用 skillshare / `npx skills`。
- 不在面板里编辑 `inventory/*.yaml`。
- 不提供 prune 开关（UI 与 API 都不接受 `prune: true`）。
- 不展示原始终端日志。
- 不引入 Node / Vite / React 或新的 Python 第三方依赖；HTTP 用标准库。
- 不监听 `0.0.0.0`，不做账号、TLS、远程访问。
- 不把面板接入业务项目的工作流安装步骤。
- 不新增 `--json` CLI 输出（终端与面板解耦留待后续）。
- 不把 `description` 写入各宿主 MCP/Hooks 配置文件（只存在于仓库清单与面板）。

---

## 3. 架构

```text
curl | sh  →  ~/.local/bin/agent-config  →  安装树内 venv + scripts/agent-config
        │
        ▼
agent-config ui [--port 8765] [--no-open]
        │
        ▼
  http.server / 标准库 HTTP（仅 127.0.0.1）
        │
   ┌────┴────────────┐
   │ 静态页（仓库内） │  GET /
   └────┬────────────┘
        │ JSON
        ▼
  ui 适配层（只编排，不对账）
        │
        ├── sync.load_inventory / check / apply / backup_files
        └── Skills 扫描（只读目录枚举）
```

原则：

- **同步逻辑不重写。** 缺口、漂移、备份、按宿主过滤全部复用 `scripts/agent_config/sync.py` 与 adapters。
- **Skills 不进 sync。** 只扫目录、打开、复制路径。
- **CLI 入口唯一扩展：** `cli.py` 增加子命令 `ui`；`sync` 行为不变。

建议文件（实现时可微调命名，职责不可合并进 `sync.py`）：

```text
install.sh                           # curl | sh 入口（POSIX sh）
scripts/requirements-run.txt         # 运行时仅 PyYAML（venv 不装 pytest）
scripts/agent_config/cli.py          # 增加 ui 子命令
scripts/agent_config/ui.py           # HTTP 服务、路由、绑定 127.0.0.1
scripts/agent_config/ui_catalog.py   # 组装卡片数据；Skills 扫描
scripts/agent_config/ui_static/      # 单页 HTML/CSS/JS
tests/agent_config/test_ui.py        # HTTP 处理函数与白名单
tests/agent_config/test_install.py   # shim 内容与安装目录约定（不真的 curl 外网）
```

---

## 4. 安装与 CLI

对外主入口（skillshare 同款形态）：

```bash
curl -fsSL https://raw.githubusercontent.com/AbnerSunLabs/agent-loom/main/install.sh | sh
agent-config ui
agent-config ui --port 8765
agent-config ui --no-open
agent-config sync --check
```

文档与 README 的命令示例一律写 `agent-config ...`。仓库内 `python3 scripts/agent-config` 仅保留给未安装、跑测试的开发路径，不作为用户说明的主入口。

### 4.1 `install.sh` 行为

前置：`git`、`python3`（3.9+，且 `python3 -m venv` 可用）、`curl`。缺任一则 stderr 说明并退出非 0。

远程 clone URL 固定为：`https://github.com/AbnerSunLabs/agent-loom.git`（与 raw `install.sh` 同一仓库、默认分支 `main`）。

本地 vs 远程判定：脚本通过 `$0` 能定位到仓库根（该目录同时有 `inventory/` 与 `scripts/`）→ **本地安装**。`curl | sh` 时脚本在 stdin / 临时文件、旁路没有这两目录 → **远程安装**。

| 模式     | 如何触发                                              | 代码与清单落在哪                                                                                    |
| -------- | ----------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| 远程安装 | `curl \| sh`（旁路无本仓库工作树）                    | clone/更新到 `$HOME/.local/share/agent-loom`（可用环境变量 `AGENT_LOOM_SHARE_ROOT` 覆盖） |
| 本地安装 | 在 git clone 里执行 `./install.sh` 或 `sh install.sh` | **不另 clone**；venv 与 shim 指向当前仓库（开发者改 `inventory/` 与 PATH 命令是同一份）             |

随后公共步骤：

1. 在安装根创建 `.venv`，`pip install -r scripts/requirements-run.txt`（只含 PyYAML；`pytest` 留在开发 `requirements.txt`，不进用户 venv）。
2. 写入可执行 shim 到 **`$HOME/.local/bin/agent-config`**。该目录不可写时再尝试 `/usr/local/bin`（需 sudo），与 skillshare 类似但优先用户目录以免默认 sudo。
3. `chmod +x`；若 `command -v agent-config` 失败，打印把 `$HOME/.local/bin` 加入 PATH 的提示。
4. 再跑一次 `install.sh` = 更新：git pull（远程模式）或沿用当前仓库（本地模式），再重建/更新 venv 与 shim。

Shim 必须 `exec` 安装根里的 **venv 解释器** + `scripts/agent-config`，这样 `paths.repo_root()` 仍能靠「同时存在 `inventory/` 与 `scripts/`」定位清单，无需新环境变量。可选：`AGENT_LOOM_ROOT` 若已存在则 `repo_root()` 优先用它（测试用）；安装脚本本身不依赖它。

不把仓库拷到 `/usr/local/share`。不下载 GitHub Release 二进制。

Windows 本期不做（与 skillshare 的 `install.ps1` 对等物列为后续）。

### 4.2 `ui` 参数

| 参数        | 默认   | 说明                                               |
| ----------- | ------ | -------------------------------------------------- |
| `--port`    | `8765` | 仅本机端口。占用则打印错误并退出码 2，不自动换端口 |
| `--no-open` | 关     | 不调用系统打开浏览器                               |

启动成功后 stdout 打印一行 URL：`http://127.0.0.1:<port>/`。进程前台运行，Ctrl+C 退出。

---

## 4.3 清单 `description` 字段

MCP 与 Hooks 公共源各增加 **`description`（必填、非空字符串）**：给人看的用途说明，中文即可。schema 校验缺省或空白则清单无效。

- **MCP** `inventory/mcp.yaml`：与 `id` 同级。
- **Hooks** `inventory/hooks.yaml`：与 `id` 同级。已有 `intent` 仍是适配器用的短标签（事件语义），**卡片用途文案用 `description`，不用 `intent` 顶替**。
- **不写入** Cursor/Codex/starFactory 的 mcp/hooks 文件；check/apply 忽略该字段。

Skills 不进 `inventory/`。用途取自该目录 `SKILL.md` YAML frontmatter 的 `description`（Agent Skills 惯例）。无 frontmatter 或无该键 → 卡片上用途为空，不因此判 catalog 失败。

实现本期须给现有 `inventory/mcp.yaml` / `hooks.yaml` 每条补上 `description`（可按当前用途手写，不编造密钥）。

面板 catalog JSON 每张 MCP/Hooks/Skills 卡都带 `"description": "..."`。搜索框匹配 id、路径、**description**。

---

## 5. HTTP API

全部 JSON；只服务本机静态页。无鉴权（依赖回环接口）。

| 方法   | 路径               | 作用                                            |
| ------ | ------------------ | ----------------------------------------------- |
| `GET`  | `/`                | 静态 HTML                                       |
| `GET`  | `/static/*`        | 仅 `ui_static/` 内文件                          |
| `GET`  | `/api/catalog`     | 卡片列表（未检查时 MCP/Hooks 状态为 `unknown`） |
| `POST` | `/api/check`       | 对所选宿主做检查，返回结构化状态                |
| `POST` | `/api/apply`       | 确认后备份并写入，再检查并返回状态              |
| `POST` | `/api/skills/open` | 用系统打开白名单内 Skills 目录                  |

`POST /api/check` 与 `POST /api/apply` 体：

```json
{
  "hosts": ["cursor", "codex"],
  "only": null,
  "confirm": true
}
```

- `hosts`：省略或 `[]` 表示三家；元素必须是 `cursor` / `codex` / `starFactory`。
- `only`：`null` / 省略 = MCP+Hooks；或 `"mcp"` / `"hooks"`。Skills 从不进入这两个接口。
- `confirm`：**仅 apply 必填且必须为 `true`**，否则 400。check 忽略该字段。
- apply **忽略任何 prune 字段**；服务端恒为 `prune=False`。
- apply **不得**套用 §5.1 的「每宿主两次」拆法。写入路径与 CLI 相同：一次 `collect_apply_paths` → `backup_files` → `sync.apply(...)`。`only` 省略时必须走 `apply_all`（Codex 的 MCP 与 Hooks 可能写同一份 `config.toml`）。写入后再按 §5.1 做分宿主、分域 check，用于刷新卡片。
- Skills 卡前端与测试用 **`path` 作唯一键**（同名多根会有多张卡）。

`POST /api/skills/open` 体：`{"path": "<绝对路径>"}`。路径必须与最近一次扫描结果中的某个 Skills 目录 `resolve()` 后相等，否则 400。复制路径只在浏览器 `clipboard` 完成，无 API。

### 5.1 检查结果如何落到卡片

现有 `CheckResult` 在一次 `sync.check` 里会把 MCP 与 Hooks 合并；`gaps`/`drift` 是 **id 或无标记下标**，`file_errors` 是 **目标文件路径**，不能按「id 是否在 file_errors 里」匹配卡片。

面板层对每个所选宿主调用 **两次** check，禁止 `only=None` 的合并结果直接上卡：

```text
sync.check(..., only="mcp",   hosts=[host])
sync.check(..., only="hooks", hosts=[host])
```

映射规则（实现与测试必须按此断言）：

| 来源                                                     | 落到哪里                                                                                                                 |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 该次 `file_error=True`                                   | **该宿主 + 该 `only` 域**下、清单里声明了此宿主的**全部** MCP 或 Hooks 卡 → `file_error`。不解析路径字符串，不标另一域。 |
| `gaps` 中等于某张卡 `id` 的项                            | 该宿主该域该卡 → `gap`                                                                                                   |
| `drift` 中等于某张卡 `id` 的项                           | 该宿主该域该卡 → `drift`                                                                                                 |
| `drift`/`gaps` 对不上任何清单 id（例如无标记 hook 下标） | **只进顶栏计数**，不为它们造卡片                                                                                         |
| 以上都未命中且无该域 `file_error`                        | 该宿主该卡 → `aligned`                                                                                                   |

同一宿主同一卡多个信号时优先级：`file_error` > `gap` > `drift` > `aligned`。

卡片上的汇总标签：只看**当前筛选宿主**集合，取这些宿主状态里优先级最高的一个。

Skills 卡状态恒为 `readonly`，不参与 check。

不修改 adapters 的 gap/drift 字符串格式来迁就 UI。

宿主筛选对 Skills：按扫描根归属，**不是**始终全量。

| 根                      | 可见宿主             |
| ----------------------- | -------------------- |
| `~/.agents/skills`      | 三家都可见（公共仓） |
| `~/.cursor/skills`      | 仅 Cursor            |
| `~/.codex/skills`       | 仅 Codex             |
| `~/.starFactory/skills` | 仅 starFactory       |

筛选为 Cursor 时：展示公共仓 + `~/.cursor/skills`。MCP/Hooks 卡按条目 `hosts` 与筛选求交。

### 5.2 响应 JSON 形状

`GET /api/catalog`：

```json
{
  "error": null,
  "skills": [
    {
      "id": "playwright",
      "path": "/Users/me/.agents/skills/playwright",
      "description": "浏览器自动化与页面断言",
      "roots": [".agents"],
      "hosts": ["cursor", "codex", "starFactory"],
      "status": "readonly"
    }
  ],
  "mcp": [
    {
      "id": "figma",
      "transport": "http",
      "description": "读取与修改 Figma 设计稿",
      "hosts": ["cursor"],
      "env_names": ["FIGMA_TOKEN"],
      "per_host": {},
      "status": "unknown"
    }
  ],
  "hooks": [
    {
      "id": "notify",
      "intent": "Notification",
      "description": "需要授权时弹出 macOS 通知",
      "hosts": ["starFactory"],
      "per_host": {},
      "status": "unknown"
    }
  ]
}
```

`POST /api/check` 与成功的 `POST /api/apply` 在 catalog 字段基础上增加：

```json
{
  "error": null,
  "summary": {
    "cursor": {
      "mcp_gaps": 2,
      "hooks_gaps": 0,
      "drift": 1,
      "file_error": false
    }
  },
  "mcp": [
    {
      "id": "github",
      "transport": "stdio",
      "description": "GitHub 仓库与 PR 操作",
      "hosts": ["cursor", "codex"],
      "env_names": [],
      "per_host": { "cursor": "gap", "codex": "aligned" },
      "status": "gap"
    }
  ],
  "hooks": [],
  "skills": []
}
```

清单无效时：`{"error": "schema", "message": "清单无效"}`（4xx），不回 yaml 全文。apply 缺 `confirm`：`{"error": "confirm_required"}`（400）。

---

## 6. Skills 扫描

使用 `paths.home()`（测试可设 `AGENT_LOOM_HOME`）。扫描这些根（存在才扫）：

- `<home>/.agents/skills`
- `<home>/.cursor/skills`
- `<home>/.codex/skills`
- `<home>/.starFactory/skills`（与 `.StarFactory` 在 macOS 上为同一目录）

规则：每个根下**一层**子目录若含 `SKILL.md`，则生成一张卡。同名出现在不同根 → **多张卡**（路径不同），不做合并。不递归更深层。打不开的根跳过，不导致整个 catalog 失败。

「打开目录」：macOS 对白名单路径调用 `open <dir>`；其它平台可用 `xdg-open` / 等价；失败则该请求 500，JSON 说明打开失败，不影响列表。

---

## 7. 页面布局

单页，无多级路由。筛选同时影响前端展示与随后 check/apply 提交的 `hosts` / `only`。Skills 按 §5.1 根目录归属过滤。

主界面：

```text
┌──────────────────────────────────────────────────────────────────────────┐
│  agent-config ui                                              127.0.0.1  │
├──────────────────────────────────────────────────────────────────────────┤
│  宿主: [全部] [Cursor] [Codex] [starFactory]                             │
│  域:   [全部] [Skills] [MCP] [Hooks]     搜索 [____________]             │
│                                                                          │
│  [ 检查差异 ]     [ 写入同步 ]                                           │
│                                                                          │
│  摘要: Cursor MCP 2 缺失 · Hooks 已对齐 · Skills 只读                    │
├──────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ MCP         │  │ MCP         │  │ Hooks       │  │ Skills      │     │
│  │ github      │  │ figma       │  │ notify      │  │ playwright  │     │
│  │ GitHub 仓库 │  │ 读改设计稿  │  │ 授权时通知  │  │ 浏览器自动化│     │
│  │ 与 PR       │  │             │  │             │  │             │     │
│  │ stdio       │  │ http        │  │ Notification│  │ ~/.agents/… │     │
│  │ Cursor Codex│  │ Cursor      │  │ starFactory │  │ Cursor 可见 │     │
│  │ ● 缺失      │  │ ● 已对齐    │  │ ● 不一致    │  │ ○ 只读      │     │
│  │             │  │             │  │             │  │ [打开目录]  │     │
│  │             │  │             │  │             │  │ [复制路径]  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │
└──────────────────────────────────────────────────────────────────────────┘
```

写入确认：

```text
┌─────────────────────────────────────────┐
│  确认写入同步                           │
│                                         │
│  将备份后合并写入所选宿主的 MCP / Hooks │
│  默认不删除清单外条目（不做 prune）     │
│                                         │
│  宿主: Cursor, Codex                    │
│                                         │
│           [ 取消 ]    [ 确认写入 ]      │
└─────────────────────────────────────────┘
```

卡片字段：

| 域     | 展示                                    | 按钮               |
| ------ | --------------------------------------- | ------------------ |
| MCP    | id、description、transport、hosts、状态 | 无单卡同步         |
| Hooks  | id、description、intent、hosts、状态    | 无单卡同步         |
| Skills | 目录名、description、来源路径、只读     | 打开目录、复制路径 |

检查/写入是**顶栏批量**操作，按当前宿主筛选提交；域筛选为 Skills-only 时，检查/写入按钮禁用（没有 MCP/Hooks 可同步）。

清单 schema 无效：顶栏错误条，不提供写入；检查接口返回 4xx 与错误类型（不把 yaml 全文回给浏览器）。

---

## 8. 安全

- 绑定 `127.0.0.1`，禁止 `0.0.0.0`。
- 静态文件根固定为 `ui_static/`，拒绝 `..`。
- `skills/open` 路径白名单：必须等于扫描结果中的目录。
- MCP 卡可显示 `env` **变量名**；禁止读取 `.env` 或回显取值（遵守仓库「禁止读密钥文件」约定）。
- apply 无 `confirm: true` → 400，不写盘。

---

## 9. 错误处理

| 情况                     | 行为                                                                                                                         |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| 安装缺 git/python3/curl  | `install.sh` 非 0，说明缺什么                                                                                                |
| `~/.local/bin` 不在 PATH | 安装仍成功，打印如何 export PATH                                                                                             |
| 端口占用                 | `ui` 退出码 2，提示换 `--port`                                                                                               |
| 清单 schema 无效         | catalog/check/apply 返回错误类型；页面错误条；禁止写入                                                                       |
| 目标文件缺失/解析失败    | 对应宿主 `file_error`；检查可用；写入前摘要再提示，用户仍确认则可调用现有 apply（现有 CLI 语义：不因 UI 额外拦截合法 apply） |
| apply 抛错               | 500；摘要失败；不伪造成功；备份仍由现有 `backup_files` 在写入前完成                                                          |
| 打开目录路径非白名单     | 400                                                                                                                          |
| 打开目录系统调用失败     | 500，仅该请求                                                                                                                |

---

## 10. 测试

- `ui --help` 出现在 parser 中；无子命令或未知子命令行为与现在一致（`sync` 仍 `required` 的互斥改为 `sync`/`ui` 二选一）。
- catalog：临时 `AGENT_LOOM_HOME` 下造 Skills 目录（含带 `description` 的 SKILL.md），断言出现；MCP/Hooks 来自测试 inventory，缺 `description` 的清单应 schema 失败。
- check/apply：复用现有 tmp 宿主文件夹模式；apply 缺 `confirm` 不写文件。
- `skills/open`：白名单外路径 400；可用 monkeypatch 避免真的 `open`。
- 绑定地址单元断言为 `127.0.0.1`。
- 不强制浏览器 E2E。
- 现有 `tests/agent_config/test_cli.py` 与 sync 单测保持通过。
- 安装：用临时目录断言「本地模式」shim 指向该目录的 venv 与 `scripts/agent-config`；不在单测里对 GitHub 做 `curl \| sh`。`install.sh` 须能被 `sh -n` 语法检查。

---

## 11. 文档

实现时更新：

- 仓库根 `README.md` 或 `inventory/README.md`：安装命令用 `curl | sh` + `agent-config ui` / `agent-config sync`；删除「本工具不提供 Web 配置面板」。
- MCP/Hooks 设计文档 §2 中「另开 V1.1 spec」可链到本文。

不把本面板写入业务项目 `README.md` 接入步骤。
