---
name: agent-config-ui
source: Linear tokens via https://github.com/VoltAgent/awesome-design-md/tree/main/design-md/linear.app
direction: dense, quiet, scannable ops tool (frontend-design-direction)
---

# agent-config ui 视觉方向

日常配置工作台，不是营销页。深蓝画布上用三套域色区分卡片：MCP 紫、Hooks 橙、Skills 青绿；宿主再用蓝 / 青 / 粉 chip。

## 氛围

画布 `#0a0e18`，带极轻的紫/青绿/橙光晕，不铺满屏渐变。字 `#f4f6fb`。CTA 用亮紫 `#7c6cff`。域色：MCP `#8b7cff`、Hooks `#ff9f43`、Skills `#2ee6a6`。宿主：Cursor `#82a8ff`、Codex `#5eead4`、starFactory `#ff7ab6`。成功 `#3dd68c`，告警 `#ffc14d`，错误 `#ff6b7a`。

## 字体

系统 UI 栈：`ui-sans-serif, SF Pro Display, Inter, system-ui`。正文 **16px**，标题 18px。id 用等宽。区块留白：顶栏约 18–28px，卡片内边距 20px，网格间距 18px。

## 组件

- 顶栏贴顶；搜索、主操作、主题图标（浅色 / 深色 / 系统）在右侧。筛选条只留宿主与域。检查结果按宿主拆成 pill，hover 出明细。
- 分段控件：炭底 + 激活项用对应域/宿主色。
- 卡片：左侧 3px 域色条 + 顶部淡域色；状态 pill 带底色。路径单独一行省略；宿主 chip 换行完整显示。截断文案 hover 用浮层展示全文（不用原生 title）。
- 主按钮亮紫；次按钮表面色。
- 对话框同表面层级。

## 不做

营销英雄区、大卡片套小卡片、装饰性插画。光晕只作背景层次，不挡阅读。
