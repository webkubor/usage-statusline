<div align="center">

<img src="./assets/logo.png" width="84" alt="usage-statusline">

# usage-statusline

### 给 **Claude Code** 的状态栏

**花了多少、上下文还剩多少、限额还够不够、撞满会不会直接停——都在你已经在看的那一行里。**

[![for Claude Code](https://img.shields.io/badge/for-Claude%20Code-D97757?logo=anthropic&logoColor=white)](https://claude.com/claude-code)
[![statusLine API](https://img.shields.io/badge/uses-statusLine%20hook-D97757?logo=anthropic&logoColor=white)](https://docs.claude.com/en/docs/claude-code/statusline)
[![License: MIT](https://img.shields.io/badge/License-MIT-black)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Zero dependencies](https://img.shields.io/badge/dependencies-0-success)](#还有什么)
[![Single file](https://img.shields.io/badge/single%20file-~440%20lines-informational)](./scripts/statusline.py)

[English](./README.en.md) · [安装](#安装) · [同类对比](#同类项目对比)

<img src="./assets/statusline.png" width="900" alt="Claude Code 状态栏效果：订阅制、额度告急、按量付费、主题">

`Claude Code` · `statusline` · `状态栏` · `用量监控` · `限额预警` · `rate limit` · `context window` · `token 用量` · `订阅制` · `按量付费` · `CLI` · `零依赖`

<sub>社区项目，非 Anthropic 官方出品。Claude 与 Claude Code 是 Anthropic 的商标。</sub>

</div>

## 安装

```bash
git clone https://github.com/webkubor/usage-statusline ~/.claude/skills/usage-statusline
```

然后在 Claude Code 里执行 `/usage-statusline` —— Claude 会照 [SKILL.md](./SKILL.md) 装好：
备份你原有配置、遇到冲突先问你、装完当场验证渲染。**重启 Claude Code 即生效。**

<sub>不走 skill 流程就跑 <code>./install.sh</code>。想让 <code>git pull</code> 直接上线（不留副本）用 <code>./install.sh --link</code>。卸载、扩展段契约、各装法差异都在 <a href="./SKILL.md">SKILL.md</a>。</sub>

## 它解决什么问题

Claude Code 不告诉你「还能跑多久」。等你撞上限额，工作已经断在半路了。

而且**光看百分比会做出错的判断**——这就是下面这几件事存在的原因。

## 读懂这一行

```
my-project main ±3 ↑2  Opus 5·high                 ← 目录 + git 状态 + 模型
~$4.48·ctx █░░░░░░░░░ 11%·5h █░░░░░░░░░ 4%(15:40)·7d ██░░░░░░░░ 21%(08-24)
```

| 片段 | 含义 |
|---|---|
| `main ±3 ↑2` | 分支、**3 个文件没提交**、**2 个 commit 没推**；干净且同步时这些标记全不显示 |
| `Opus 5·high` | 当前模型 + effort 档位（开了 fast mode 加 `·fast`）——**临时切换后最容易忘记切回来** |
| `~$4.48` | 本次会话消耗。**波浪号 = 等价金额、不是实付**，见下 |
| `ctx … 11%` | 上下文窗口占用 |
| `5h / 7d … (15:40)` | 限额用量与重置时刻 |

条形的每一格按**自己在轨道上的位置**着色，所以**右端天生是警戒色**——你在填到那里之前就看得见危险区。

## 光看百分比会看错的四件事

#### 1. `~$4.48` 的钱可能根本不存在

同一个金额，两种账户含义完全相反：

| | 显示 | 这个数是什么 | 真正约束你的 |
|---|---|---|---|
| **订阅制**（Pro / Max / Team） | `~$4.48` | 按 API 价目折算的**等价消耗**，不会扣款 | 限额条 |
| **按量付费**（API credits） | `$4.48` | **真实账单** | 你的余额 |

订阅用户盯 `$` 是白盯的，该盯限额条；按量用户反过来。

#### 2. `⚠hard stop`：撞满不是多花钱，是直接停工

订阅制超限后，有账户自动转按量继续跑，有账户**停到窗口重置为止**——取决于你有没有开超额用量、以及是否还有余额。

限额 ≥80% 且**没有按量兜底**时会标出来：

```
5h █████████░ 87% ⚠hard stop(15:40)
```

意思是再跑下去不是多花点钱，而是**卡到 15:40**。提前知道，你可以决定现在收尾还是换账户。

#### 3. `→full`：40% 在第一天和第六天不是一回事

5 小时窗口按当前燃烧速度外推，**会在重置前撞满就报出时刻**，撑得住就一个字不说：

```
5h █████░░░░░ 46%(18:00) →full 14:46
```

只对 5h 窗口做预测。把一小时的活跃速度外推到未来三天等于假设你不睡觉，会让预警几乎永远亮着——**一个总在响的预警器是噪音，不是信息**。

#### 4. `⚠200k+`：越过 20 万 token 进了长上下文价档

单价更高，但这只对真花钱的按量账户有意义，所以订阅账户不会被这个标记打扰。

## 主题

三套内置主题，**默认就调好，不用配置**：

```bash
export USAGE_STATUSLINE_THEME=cool     # default | cool | mono
```

| 主题 | 色带 | 适合 |
|---|---|---|
| `default` | 灰绿 → 琥珀 → 珊瑚红 | 刻意不饱和，额度还多时安静待着不晃眼 |
| `cool` | 青 → 靛 → 品红 | 暗色主题下绿色容易读成「终端绿」而失去警示意味 |
| `mono` | 纯亮度灰阶 | 完全不要色相，隐进终端里，需要时才浮现 |

三套都保持**左边平静、右边告警**：主题只换配色，不换「颜色在告诉你什么」。真彩终端走 24 位渐变，否则降级 8 色，`NO_COLOR` 退回字符区分。

## 加你自己的东西

想显示的**不是用量**（任务心跳、队列深度、部署状态……）？丢个可执行文件进 `~/.claude/statusline/segments/`，它收到同一份 payload，输出的第一行会接在状态栏后面：

```
my-project main  ⏱ deploy ok·queue 3
~$4.48·ctx █░░░░░░░░░ 11%
```

坏掉的段会被静默跳过，**永远不会弄坏你的状态栏**。完整契约见 [SKILL.md](./SKILL.md)。

## 同类项目对比

这个赛道已经很热闹，也有比本项目**功能全得多**的方案。直说：
**要 powerline 分段、图形化配置器、Git PR/CI 状态，去用 ccstatusline；
要装完不用调就好看、且源码能一口气读完，用这个。**

| | **usage-statusline** | [ccstatusline](https://github.com/sirmalloc/ccstatusline) | [claude-powerline](https://github.com/Owloops/claude-powerline) | [CCometixLine](https://github.com/Haleclipse/CCometixLine) |
|---|---|---|---|---|
| Star | — | 12.4k | 1.1k | 3.4k |
| 实现 | 单文件 Python | TypeScript / npm | TypeScript / npm | Rust 二进制 |
| 运行依赖 | **无**（`python3` 自带） | Node.js | Node.js | 预编译二进制 |
| 配置 | **零配置** | TUI 配置器 | JSON 配置 | 配置文件 |
| 5h / 7d 限额 | ✅ / ✅ | ✅ / ✅ | ✅ / — | — |
| 订阅 vs 按量识别 | ✅ | 部分 | — | — |
| **无兜底硬停预警** | ✅ | 未见 | 未见 | 未见 |
| **燃尽速率预测** | ✅ | 未见 | 未见 | 未见 |
| 主题 / 渐变 | ✅ 零配置好看 | ✅ 需在 TUI 里调 | ✅ | ✅ |
| Powerline / PR / CI | ❌ | ✅ | ✅ | 部分 |

> 依据各项目 2026-08 公开 README，`—` 表示其 README 未提及、**不代表一定没有**。
> 本项目 star 留空：个人自用工具开源出来的，不比体量。

## 还有什么

无网络请求，除 `python3`（Claude Code 自带）和可选的 `git` 外**零依赖**。任何 payload 字段缺失都只是跳过，哪怕输入是坏 JSON 也不会弄坏状态栏。

只写一个文件：`~/.claude/statusline/history.jsonl`，纯缓存，供 `→full` 预测用——每 60 秒最多一点、400 行、**17 KB 封顶**、删了只丢预测。`USAGE_STATUSLINE_NO_HISTORY=1` 可回到完全无状态。

## License

MIT —— 见 [LICENSE](./LICENSE)。
