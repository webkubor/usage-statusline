---
name: usage-statusline
version: 1.1.0
description: "在 Claude Code 状态栏常驻显示：会话花费（区分订阅制等价金额与按量付费实际账单）、上下文占用、5 小时/7 天限额条与重置时刻、无按量兜底时的硬停预警、5h 窗口燃尽预测、git 未提交/未推送计数、当前模型与 effort 档位；含三套主题与本地扩展段机制。触发词：装/配置 usage statusline、状态栏加用量提示、想在状态栏看还剩多少配额、状态栏显示模型/git 状态、切换状态栏主题、usage indicator、rate limit statusline。调用一次即完成安装，之后每次开 Claude Code 自动显示，无需重复调用。"
metadata:
  requires:
    bins: ["python3"]
---

# usage-statusline

## 先分派：这次要干什么

| 用户说的 | 做什么 | 往下读哪 |
|---|---|---|
| `default` / `cool` / `mono`（或「切主题」「换成青色」「太花了换灰的」） | **只切主题**，别碰安装 | 「切换主题」一节，两行命令搞定 |
| 「装一下」「配置状态栏」/ 首次调用 / 无参数 | 走完整安装 | 「安装步骤」 |
| 「不显示了」「没生效」「怎么卸载」 | 排查或卸载 | 「安装步骤」第 5 步 / 「卸载」 |

切主题是最常被调用的，别把它当安装跑一遍——那会重写 `settings.json`，没必要。

## 切换主题

主题名存在 `~/.claude/statusline/theme` 里，脚本每次渲染都读，所以**写完立即生效，不用重启**：

```bash
echo cool > ~/.claude/statusline/theme     # default | cool | mono
```

写完直接告诉用户已切好、下一次状态栏刷新就能看到，**不要**让他重启。
读不到文件或名字不认识都会静默回退 `default`，所以写错不会弄坏什么。

想确认当前是哪个：`cat ~/.claude/statusline/theme`（无文件＝`default`）。

⚠️ 如果用户 `settings.json` 的 `env` 里有 `USAGE_STATUSLINE_THEME`，它会**盖住**这个文件，
导致「切了没反应」。遇到这种情况把 env 里那条删掉、改用文件（`COLORTERM` 要留着，
那是真彩支持，跟主题无关）。

## 安装

把这个 skill 安装到 `~/.claude/statusline/usage.py`，并把 `~/.claude/settings.json` 的
`statusLine` 字段指向它。安装是一次性的：装完之后每次打开 Claude Code 都会自动显示，
不需要每次手动调用这个 skill。

效果示例（真实数值会不同，输出两行）：

```
my-project main
~$0.62·ctx █░░░░░░░░░ 7%·5h █░░░░░░░░░ 7%(20:10)·7d █░░░░░░░░░ 8%(08-17)
```

- `my-project main` — 当前目录名 + git 分支（无 git 仓库则只显示目录名）
- `~$0.62` — 本次会话消耗；**波浪号表示订阅制的「等价金额、非实付」**，按量付费账户无波浪号
- `ctx … 7%` — 上下文窗口占用率
- `5h … 7%(20:10)` — 5 小时限额用量 7%，20:10 重置
- `7d … 8%(08-17)` — 7 天限额用量 8%，08-17 重置

每个指标是 10 格色条，**亮色=已用、暗色=剩余**；非零占用至少点亮一格。
每格按**自己在轨道上的位置**着色，所以右端天生是警戒色，填过去之前就看得见危险区。

三套内置主题（`default` / `cool` / `mono`），写 `~/.claude/statusline/theme` 切换（见上「切换主题」），
默认无需配置。真彩终端走 24 位渐变，否则降级 8 色，`NO_COLOR` 退回 `▓░` 字符。

限额窗口 ≥80% 且账户**没有按量兜底**时会标 `⚠hard stop` —— 意思是撞满不是多花钱，
而是直接停到窗口重置。判断读 `~/.claude.json` 的 `oauthAccount.billingType`、
`hasExtraUsageEnabled`、`cachedExtraUsageDisabledReason`；读不到则安全降级（不加波浪号、不报警）。

按当前燃烧速度外推，若会在窗口重置**之前**撞满，会标 `→full 14:46`（预计撞满时刻）；
烧得比重置慢就不显示。**只对 5h 窗口预测，7d 不预测**——把一小时的活跃速度外推到三天
等于假设不睡觉，会让预警几乎永远亮着。这个预测需要采样历史，是本脚本**唯一会写的文件**：
`~/.claude/statusline/history.jsonl`（每 60 秒最多一点、最多 400 行、17 KB 封顶、纯缓存可删）。
用户不想要任何状态文件时告诉他设 `USAGE_STATUSLINE_NO_HISTORY=1`。

第一行还会追加**本地扩展段**的输出（见下方「扩展段」），没装扩展段时就只有目录 + 分支。

## 三种安装模式（README 只写一键入口，细节在这里）

| 模式 | 怎么装 | statusLine 指向 | 升级 | 什么时候用 |
|---|---|---|---|---|
| **skill 流程**（默认） | 用户执行 `/usage-statusline`，Claude 照下面步骤做 | `~/.claude/statusline/usage.py`（副本） | 重跑一次 skill | 默认推荐，装完稳定不变 |
| **脚本** | `./install.sh` | 同上（副本） | 重跑 `./install.sh` | 不走 Claude、CI、或写进 dotfiles |
| **跟随主线** | `./install.sh --link` | clone 里的 `scripts/statusline.py` | `git pull` | 用户要「改完就生效 / 不留副本 / 跟着 GitHub 走」 |

副本模式的坑：改了仓库忘了重装，状态栏还在跑旧副本（会表现为「代码明明改了但状态栏没变」）。
`--link` 没这个问题，代价是跑的是当前 checkout **含未提交改动**。用户没明说时用副本模式。

**三种模式共用** `~/.claude/statusline/segments/` 和 `history.jsonl`（路径写在脚本里，
与脚本放哪无关），所以换模式不会丢用户的扩展段和采样历史。

## 安装步骤（Claude 执行）

**第 1 步 — 找到本 skill 自己的目录。**

用 Bash 在常见 skill 安装位置里找 `scripts/statusline.py`：

```bash
find ~/.claude/skills ~/.claude/plugins . -maxdepth 6 -type f -path "*usage-statusline/scripts/statusline.py" 2>/dev/null
```

把匹配到的路径去掉 `/scripts/statusline.py` 后缀，记作 `SKILL_DIR`。如果找不到（比如用户是
从别处手动拖进来的目录），直接问用户这个 skill 目录当前挂在哪。

**第 2 步 — 把脚本落地到一个稳定路径，不依赖 skill 目录以后还在不在。**

> 例外：如果用户明确说要**跟着 GitHub 主线走 / 不要副本 / 改完就生效**，就别拷贝——
> 直接把 `statusLine.command` 指向那个 git clone 里的 `scripts/statusline.py`
> （等同 `./install.sh --link`），升级就是 `git pull`。代价是跑的是当前 checkout、
> 含未提交改动，要跟用户说明。默认仍走下面的拷贝方式。

```bash
mkdir -p ~/.claude/statusline/segments
cp "$SKILL_DIR/scripts/statusline.py" ~/.claude/statusline/usage.py
chmod +x ~/.claude/statusline/usage.py
```

`segments/` 是扩展段目录，**只创建、绝不清空**——用户已有的扩展段是他自己的东西，
重装本 skill 不该动它们。

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

确认输出是两行、没有报错，第二行包含 `$0.10`、`ctx`、`5h`、`7d` 各自的条形和 `5%`。

**第 5 步 — 告诉用户装完了**，下次打开 Claude Code（或新开一个窗口）状态栏就会自动出现这行，
不需要再运行这个 skill。如果状态栏没变化，提醒用户重启一下 Claude Code 会话（`statusLine` 是
启动时读取的配置）。

## 扩展段（用户想在状态栏加别的东西时走这里）

用户要显示的**不是用量**（后台任务心跳、队列深度、值班状态、部署状态……）时，
不要改 `usage.py`，做成扩展段：往 `~/.claude/statusline/segments/` 放一个可执行文件。

契约：

- 按文件名排序执行（用 `10-`、`20-` 前缀排顺序）
- stdin 收到和主脚本**同一份 payload JSON**（用不上也要读掉，否则上游拿到 EPIPE）
- **stdout 第一行**会被追加到状态栏第一行；不输出 = 不显示
- 可以用 ANSI 颜色；自行尊重 `NO_COLOR`
- 段失败 / 超时（1 秒）/ 没有可执行位 → 静默跳过，坏段永远不会弄坏状态栏

段放在仓库外，所以升级、重装都不会碰它们，私有内容也不会进公开 checkout。

## 卸载

把 `~/.claude/settings.json` 里的 `statusLine` 字段删掉（或者如果之前有 `.bak-usage-statusline`
备份，直接恢复那份），再删 `~/.claude/statusline/usage.py` 和 `~/.claude/statusline/history.jsonl`。
`segments/` 里是用户自己的扩展段，**不要替他删**，要删也先问。

## 反唤起信号

- 用户已经有自己的 statusLine 脚本、只是想加用量这一段 —— 不要覆盖对方脚本。两条路：
  把对方脚本里非用量的部分改造成**扩展段**（见上）然后切到本脚本；或者保留对方脚本作入口，
  在里面调 `~/.claude/statusline/usage.py` 把输出拼进去。选哪条问用户。
- 用户问的是"用量还剩多少"这种一次性查询，不是要装状态栏 —— 直接查 `~/.claude/settings.json`
  里现在生效的用量信息或建议用官方 `/usage` 类命令，不必安装本 skill。
