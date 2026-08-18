<div align="center">

<img src="./assets/logo.png" width="84" alt="usage-statusline">

# usage-statusline

### A status line for **Claude Code**

**What you've spent, how much context is left, how close you are to your limits, and whether hitting one stops you dead — on the line you're already looking at.**

[![for Claude Code](https://img.shields.io/badge/for-Claude%20Code-D97757?logo=anthropic&logoColor=white)](https://claude.com/claude-code)
[![statusLine API](https://img.shields.io/badge/uses-statusLine%20hook-D97757?logo=anthropic&logoColor=white)](https://docs.claude.com/en/docs/claude-code/statusline)
[![License: MIT](https://img.shields.io/badge/License-MIT-black)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Zero dependencies](https://img.shields.io/badge/dependencies-0-success)](#anything-else)
[![Single file](https://img.shields.io/badge/single%20file-~440%20lines-informational)](./scripts/statusline.py)

[中文](./README.md) · [Install](#install) · [Alternatives](#how-it-compares)

<img src="./assets/statusline.png" width="900" alt="Claude Code status line: subscription, limit running out, pay-as-you-go, themes">

`Claude Code` · `statusline` · `usage monitor` · `rate limit` · `context window` · `token usage` · `subscription` · `pay-as-you-go` · `CLI` · `zero dependencies`

<sub>A community project, not affiliated with or endorsed by Anthropic. Claude and Claude Code are trademarks of Anthropic.</sub>

</div>

## Install

```bash
git clone https://github.com/webkubor/usage-statusline ~/.claude/skills/usage-statusline
```

Then run `/usage-statusline` in Claude Code — it follows [SKILL.md](./SKILL.md) to install:
backs up your existing config, asks before overwriting anything, and verifies the render.
**Restart Claude Code and it's live.**

<sub>Not using the skill flow? Run <code>./install.sh</code>. Want <code>git pull</code> to be the whole upgrade (no copy)? <code>./install.sh --link</code>. Uninstall, segment contract, and mode differences are all in <a href="./SKILL.md">SKILL.md</a>.</sub>

## Why

Claude Code doesn't tell you how much longer you can keep going. By the time you hit a limit, your work is already interrupted.

And **the percentage alone will lead you to the wrong call** — which is why the four things below exist.

## Reading the line

```
my-project main ±3 ↑2  Opus 5·high                 ← directory + git state + model
~$4.48·ctx █░░░░░░░░░ 11%·5h █░░░░░░░░░ 4%(15:40)·7d ██░░░░░░░░ 21%(08-24)
```

| Part | Meaning |
|---|---|
| `main ±3 ↑2` | Branch, **3 files uncommitted**, **2 commits unpushed**; all markers vanish when clean and in sync |
| `Opus 5·high` | Current model + effort level (`·fast` when fast mode is on) — **the thing you switch temporarily and forget** |
| `~$4.48` | Session spend. **The tilde means equivalent, not billed** — see below |
| `ctx … 11%` | Context window used |
| `5h / 7d … (15:40)` | Limit usage and reset time |

Every bar cell is colored for **its own position on the track**, so the **right end is always the alarm color** — you see the danger zone before the fill gets there.

## Four things the percentage alone gets wrong

#### 1. That `~$4.48` may not be real money

The same figure means opposite things depending on your account:

| | Shown as | What it is | What actually constrains you |
|---|---|---|---|
| **Subscription** (Pro / Max / Team) | `~$4.48` | **Equivalent** spend at API list price — never charged | The limit gauges |
| **Pay-as-you-go** (API credits) | `$4.48` | Your **real bill** | Your balance |

On a subscription, watching the dollars tells you nothing — watch the gauges. On pay-as-you-go it's the reverse.

#### 2. `⚠hard stop`: hitting the limit isn't "costs more", it's "stop working"

When a subscription goes over, some accounts roll into pay-as-you-go and keep running; others **stop dead until the window resets** — depending on whether extra usage is enabled *and* still funded.

At ≥80% with **no pay-as-you-go fallback**, it says so:

```
5h █████████░ 87% ⚠hard stop(15:40)
```

Meaning: continuing isn't spending a bit more, it's **blocked until 15:40**. Knowing early lets you wrap up deliberately instead of getting cut off.

#### 3. `→full`: 40% on day one isn't 40% on day six

The 5-hour window extrapolates your current burn rate and **names the time it will run out** — if that lands before the reset. If you'll make it, it says nothing:

```
5h █████░░░░░ 46%(18:00) →full 14:46
```

Only the 5h window is projected. Extrapolating an hour of active work across three days assumes you never sleep, which would leave the warning permanently lit — **a predictor that always fires is noise, not information**.

#### 4. `⚠200k+`: you've crossed into the long-context price tier

Higher per-token rate — but it only costs real money on pay-as-you-go, so subscriptions aren't nagged about it.

## Themes

Three built in, **tuned to look right with no configuration**. Switching is one line and
**takes effect immediately — no restart**:

```bash
echo cool > ~/.claude/statusline/theme     # default | cool | mono
```

Inside Claude Code you can also just say `/usage-statusline cool`, or "make the status line grey".

| Theme | Ramp | Good for |
|---|---|---|
| `default` | Sage → amber → coral | Deliberately desaturated, sits quietly while you have headroom |
| `cool` | Teal → indigo → magenta | Dark themes where green reads as "terminal green" and loses its warning value |
| `mono` | Pure luminance | No hue at all — disappears into the terminal until it matters |

All three keep **calm on the left, alarming on the right**: a theme changes the palette, never what the color is telling you. 24-bit truecolor where available, 8 colors otherwise, characters under `NO_COLOR`.

## Add your own

Want something that **isn't usage** — job heartbeats, queue depth, deploy status? Drop an executable into `~/.claude/statusline/segments/`. It receives the same payload, and its first line is appended:

```
my-project main  ⏱ deploy ok·queue 3
~$4.48·ctx █░░░░░░░░░ 11%
```

A broken segment is skipped silently and **can never break your status line**. Full contract in [SKILL.md](./SKILL.md).

## How it compares

This space is crowded, and some alternatives do **considerably more**. Straight answer:
**want powerline segments, a graphical configurator, Git PR/CI status? use ccstatusline.
Want it to look right on install, in a source file you can read in one sitting? use this.**

| | **usage-statusline** | [ccstatusline](https://github.com/sirmalloc/ccstatusline) | [claude-powerline](https://github.com/Owloops/claude-powerline) | [CCometixLine](https://github.com/Haleclipse/CCometixLine) |
|---|---|---|---|---|
| Stars | — | 12.4k | 1.1k | 3.4k |
| Implementation | Single Python file | TypeScript / npm | TypeScript / npm | Rust binary |
| Runtime deps | **None** (`python3` ships with CC) | Node.js | Node.js | Prebuilt binary |
| Configuration | **None** | TUI configurator | JSON config | Config file |
| 5h / 7d limits | ✅ / ✅ | ✅ / ✅ | ✅ / — | — |
| Subscription vs PAYG | ✅ | Partial | — | — |
| **Hard-stop warning** | ✅ | not documented | not documented | not documented |
| **Burn-rate projection** | ✅ | not documented | not documented | not documented |
| Themes / gradients | ✅ good by default | ✅ via TUI | ✅ | ✅ |
| Powerline / PR / CI | ❌ | ✅ | ✅ | Partial |

> Based on each project's public README as of 2026-08. `—` means not mentioned there — **not proof it's missing**.
> Stars left blank here: a personal tool released as-is, not competing on scale.

## Anything else

No network calls, and **zero dependencies** beyond `python3` (ships with Claude Code) and optionally `git`. Any missing payload field is simply skipped — even malformed JSON can't break your status line.

It writes exactly one file: `~/.claude/statusline/history.jsonl`, a pure cache for the `→full` projection — one sample per 60s, 400 rows, **~17 KB ceiling**, delete it and you only lose the estimate. `USAGE_STATUSLINE_NO_HISTORY=1` makes it fully stateless.

## License

MIT — see [LICENSE](./LICENSE).
