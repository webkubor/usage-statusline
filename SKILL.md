---
name: usage-statusline
version: 1.0.0
description: "在 Claude Code 状态栏常驻显示本次会话花费、上下文占用率、以及 5 小时/7 天限额用量百分比和重置倒计时。触发词：装/配置 usage statusline、状态栏加用量提示、想在状态栏看还剩多少配额、usage indicator、rate limit statusline。调用一次即完成安装，之后每次开 Claude Code 自动显示，无需重复调用。"
metadata:
  requires:
    bins: ["python3"]
---

# usage-statusline

把这个 skill 安装到 `~/.claude/statusline/usage.py`，并把 `~/.claude/settings.json` 的
`statusLine` 字段指向它。安装是一次性的：装完之后每次打开 Claude Code 都会自动显示，
不需要每次手动调用这个 skill。

效果示例（真实数值会不同）：

```
my-project main  $0.62·ctx 7%·5h 7%(4h)·7d 8%(5d)
```

- `my-project main` — 当前目录名 + git 分支（无 git 仓库则只显示目录名）
- `$0.62` — 本次会话累计花费
- `ctx 7%` — 上下文窗口占用率
- `5h 7%(4h)` — 5 小时限额用量 7%，约 4 小时后重置
- `7d 8%(5d)` — 7 天限额用量 8%，约 5 天后重置

百分比达到 50% 变黄、80% 变红，低于 50% 是绿色/灰色。

## 安装步骤（Claude 执行）

**第 1 步 — 找到本 skill 自己的目录。**

用 Bash 在常见 skill 安装位置里找 `scripts/statusline.py`：

```bash
find ~/.claude/skills ~/.claude/plugins . -maxdepth 6 -type f -path "*usage-statusline/scripts/statusline.py" 2>/dev/null
```

把匹配到的路径去掉 `/scripts/statusline.py` 后缀，记作 `SKILL_DIR`。如果找不到（比如用户是
从别处手动拖进来的目录），直接问用户这个 skill 目录当前挂在哪。

**第 2 步 — 把脚本落地到一个稳定路径，不依赖 skill 目录以后还在不在。**

```bash
mkdir -p ~/.claude/statusline
cp "$SKILL_DIR/scripts/statusline.py" ~/.claude/statusline/usage.py
chmod +x ~/.claude/statusline/usage.py
```

**第 3 步 — 读 `~/.claude/settings.json`，合并写入 `statusLine` 字段。**

- 文件不存在：创建一个只含 `statusLine` 字段的新 JSON。
- 文件存在但没有 `statusLine` 字段：只新增这个字段，其他字段原样保留。
- 文件存在且已有 **不同** 的 `statusLine.command`：**不要静默覆盖** —— 先告诉用户当前配置的是
  什么命令，问用户是要换成这个脚本、还是想办法两者都保留（比如把旧脚本的输出接到这个脚本前面），
  等用户确认再改。
- 文件存在且 `statusLine.command` 已经指向 `~/.claude/statusline/usage.py`：说明已装过，跳过，
  提示用户"已经装好了"。

写入的字段内容（`command` 用绝对路径，不要用 `~`，避免不同 shell 展开行为不一致）：

```json
"statusLine": {
  "type": "command",
  "command": "/absolute/home/.claude/statusline/usage.py",
  "padding": 0
}
```

改之前先把原 `settings.json` 备份成 `settings.json.bak-usage-statusline`（如果文件本来就存在）。
用 `python3 -m json.tool` 验证改完的 JSON 合法。

**第 4 步 — 用当前会话真实的 transcript 里最近一条 payload（或构造一份最小样例）测试渲染。**

```bash
echo '{"cwd":"'"$PWD"'","cost":{"total_cost_usd":0.1},"context_window":{"used_percentage":5},"rate_limits":{"five_hour":{"used_percentage":5,"resets_at":9999999999},"seven_day":{"used_percentage":5,"resets_at":9999999999}}}' \
  | ~/.claude/statusline/usage.py
```

确认输出是一行、没有报错、包含 `$0.10`、`ctx 5%`、`5h 5%`、`7d 5%` 这些片段。

**第 5 步 — 告诉用户装完了**，下次打开 Claude Code（或新开一个窗口）状态栏就会自动出现这行，
不需要再运行这个 skill。如果状态栏没变化，提醒用户重启一下 Claude Code 会话（`statusLine` 是
启动时读取的配置）。

## 卸载

把 `~/.claude/settings.json` 里的 `statusLine` 字段删掉（或者如果之前有 `.bak-usage-statusline`
备份，直接恢复那份），再删 `~/.claude/statusline/usage.py`。

## 反唤起信号

- 用户已经有自己的 statusLine 脚本、只是想加用量这一段 —— 不要覆盖对方脚本，改为建议把
  `scripts/statusline.py` 的输出拼接进对方脚本里，或者作为独立一段追加。
- 用户问的是"用量还剩多少"这种一次性查询，不是要装状态栏 —— 直接查 `~/.claude/settings.json`
  里现在生效的用量信息或建议用官方 `/usage` 类命令，不必安装本 skill。
