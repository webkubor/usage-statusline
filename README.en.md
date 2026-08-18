<div align="center">

<img src="./assets/logo.png" width="84" alt="usage-statusline">

# usage-statusline

### A status line for **Claude Code**

**What you've spent, how much context is left, how close you are to your limits, and whether hitting one stops you dead — on the line you're already looking at.**

[![for Claude Code](https://img.shields.io/badge/for-Claude%20Code-D97757?logo=anthropic&logoColor=white)](https://claude.com/claude-code)
[![statusLine API](https://img.shields.io/badge/uses-statusLine%20hook-D97757?logo=anthropic&logoColor=white)](https://docs.claude.com/en/docs/claude-code/statusline)
[![License: MIT](https://img.shields.io/badge/License-MIT-black)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Zero dependencies](https://img.shields.io/badge/dependencies-0-success)](#how-it-works)
[![Single file](https://img.shields.io/badge/single%20file-~440%20lines-informational)](./scripts/statusline.py)

[中文](./README.md) · [Install](#install) · [Subscription vs pay-as-you-go](#subscription-vs-pay-as-you-go) · [Segments](#extension-segments) · [Alternatives](#how-it-compares)

<img src="./assets/statusline.png" width="900" alt="Claude Code status line: subscription, limit running out, pay-as-you-go, themes">

`Claude Code` · `statusline` · `usage monitor` · `rate limit` · `context window` · `token usage` · `subscription` · `pay-as-you-go` · `CLI` · `zero dependencies`

<sub>A community project, not affiliated with or endorsed by Anthropic. Claude and Claude Code are trademarks of Anthropic.</sub>

</div>

## Why

Claude Code doesn't tell you how much longer you can keep going. By the time you hit a limit, your work is already interrupted.

This status line keeps three things in front of you: **is the context filling up**, **how much of the 5-hour / 7-day limit is left**, and **what this session has cost**. It also distinguishes subscription accounts from pay-as-you-go ones — because the same dollar figure means very different things depending on which you are.

## Reading the line

```
my-project main ±3 ↑2  Opus 5·high                 ← directory + git state + model (+ your own segments)
~$4.48·ctx █░░░░░░░░░ 11%·5h █░░░░░░░░░ 4%(15:40)·7d ██░░░░░░░░ 21%(08-24)
```

| Part | Meaning |
|---|---|
| `my-project` | Current directory |
| `main` | git branch (hidden outside a repo) |
| `±3` | **3 files changed but not committed** (untracked files included) |
| `↑2` | **2 commits not pushed**; behind the remote shows as `↓N` |
| `Opus 5·high` | Current model + effort level; fast mode adds `·fast` |
| `~$4.48` | Session spend. **The `~` means "equivalent, not billed"** — see below |
| `ctx … 11%` | Context window used |
| `5h … 4%(15:40)` | 5-hour limit: 4% used, resets at 15:40 |
| `7d … 21%(08-24)` | 7-day limit: 21% used, resets on 08-24 |

git markers **appear only when there's something to say**: a clean tree in sync with its
remote leaves just the branch name. A quiet status line means a quiet repo — no need to
run `git status` to confirm.

Model and effort level stay visible because they get **switched mid-session and forgotten** —
spending an afternoon on a level you meant to set temporarily is a silent, expensive mistake.

> Deliberately no cloud/emoji icons here: emoji are double-width in terminals and their
> width varies by font, which makes the whole line jump around and knocks the bars out of
> alignment. `±↑↓` are single-width and stay put.

Branch, ahead/behind, and dirty count come from **one** `git status --porcelain=v2 --branch`
call, not three separate git invocations. A 638-file repo measured ~2ms slower than an empty
one; a 1s timeout backs it up, so a slow or missing git just means no git info and the rest
still renders.

Each gauge is a 10-cell bar: **bright = used, dark = remaining**. Any non-zero usage lights at least one cell, so 1% never looks like 0%.

Every cell is colored for **its own position on the track**, not for the current value — so the **right end is always the alarm color** and you can see where the danger zone is before you get there:

```
5h ██████████  ← calm on the left, alarming on the right; the fill warms up as it advances
```

> The bar is one solid glyph split by color rather than shade characters like `▓░` — those render as muddy dot patterns in many fonts and the boundary disappears.

## Themes

Three built-in themes, **tuned to look right out of the box — no configuration required**. Switch with an env var:

```bash
export USAGE_STATUSLINE_THEME=cool     # default | cool | mono
```

| Theme | Ramp | Good for |
|---|---|---|
| `default` | Sage → amber → coral | The default. Deliberately desaturated so a mostly-empty bar sits quietly instead of glowing at you |
| `cool` | Teal → indigo → magenta | Dark themes where green reads as "terminal green" and loses its warning value |
| `mono` | Pure luminance ramp | No hue at all — lets the status line disappear into the terminal until it matters |

All three keep the same meaning: **calm on the left, alarming on the right**. A theme changes the palette, never what the color is telling you.

24-bit truecolor when `COLORTERM=truecolor`; terminals without it degrade to 8 colors, and `NO_COLOR` falls back to `▓░` characters.

## Subscription vs pay-as-you-go

This is the easiest thing to misread: **the same `$4.48` means two different things.**

| | Shown as | What the number is | What actually constrains you |
|---|---|---|---|
| **Subscription** (Pro / Max / Team) | `~$4.48` | **Equivalent** spend at API list price — never charged | The 5h / 7d gauges |
| **Pay-as-you-go** (API credits) | `$4.48` | Your **actual bill** | Your balance |

So on a subscription, watching the dollar figure tells you nothing useful — watch the limit gauges. On pay-as-you-go it's the reverse.

### What `⚠hard stop` means

When a subscription exceeds its limit, some accounts roll over into pay-as-you-go billing and keep running; others **stop dead until the window resets**. Which one you get depends on whether extra usage is enabled *and* still has credit behind it.

When a window is **≥80%** with **no pay-as-you-go fallback**, the status line says so:

```
5h █████████░ 87% ⚠hard stop(15:40)
```

Meaning: continuing isn't "spend a bit more", it's **stop working until 15:40**. Knowing in advance lets you wrap up deliberately instead of getting cut off mid-task.

(Pay-as-you-go accounts never show this — there's no fallback to lose; going over simply keeps billing.)

### `→full` — "this pace won't make it to the reset"

A percentage alone doesn't tell you whether you'll make it through the current stretch. So the
5-hour gauge extrapolates your **current burn rate**, and if that would exhaust the window
*before* it resets, it says when:

```
5h █████░░░░░ 46%(18:00) →full 14:46
```

Read as: the 5h window doesn't reset until 18:00, but at this pace **you'll be out at 14:46**.

Burning slower than the reset shows nothing — there's nothing to say, so it says nothing.

**Only the 5-hour window is projected, never the 7-day one.** That's deliberate: extrapolating an
hour of active work across three days assumes you never stop to sleep, which makes almost any
sustained use trip the warning — a predictor that always fires is noise, not information. Inside a
5-hour window you're plausibly still working, so the slope actually means something.

Two more guards against confident nonsense: extrapolation needs at least **10 minutes** of samples
(two adjacent points right after a reset produce garbage), and when a window rolls over
(`resets_at` changes) old samples stop counting, so last window's slope is never dragged in.

The projection relies on a sample file — see [the one file it writes](#the-one-file-it-writes);
you can turn it off.

### What `⚠200k+` means

Past 200k input tokens, the **long-context price tier** applies and the per-token rate goes up.
That only costs real money on pay-as-you-go, so subscriptions aren't nagged about it:

```
ctx ██░░░░░░░░ 22% ⚠200k+
```

The marker states the fact (you've crossed 200k) rather than a multiplier — the multiplier
varies by model.

Detection reads `oauthAccount.billingType`, `hasExtraUsageEnabled`, and `cachedExtraUsageDisabledReason` from `~/.claude.json`. If none of it can be read, it degrades safely: no tilde, no warning.

## Install

### Option A — as a Claude Code Skill (recommended)

```bash
git clone https://github.com/webkubor/usage-statusline ~/.claude/skills/usage-statusline
```

Open Claude Code and run:

```
/usage-statusline
```

Claude reads `SKILL.md`, installs the script to `~/.claude/statusline/usage.py`, and wires it into `~/.claude/settings.json`. If you already have a custom `statusLine`, it won't be silently overwritten — Claude tells you what's there and asks first.

### Option B — plain shell install

```bash
git clone https://github.com/webkubor/usage-statusline
cd usage-statusline
./install.sh
```

Same behavior, minus the conversation: merges into `~/.claude/settings.json` (backing the original up to `settings.json.bak-usage-statusline` on first run) and refuses to clobber a different existing `statusLine.command`.

Restart Claude Code afterwards — `statusLine` is read at startup.

## Extension segments

Anything you want on the line that **isn't usage** — job heartbeats, queue depth, on-call state, deploy status — goes in a segment instead of a fork of this script. Drop an executable into `~/.claude/statusline/segments/`:

```bash
cat > ~/.claude/statusline/segments/10-queue.sh <<'EOF'
#!/bin/sh
cat > /dev/null                     # consume the payload on stdin, even if unused
echo "queue $(ls ~/jobs | wc -l | tr -d ' ')"
EOF
chmod +x ~/.claude/statusline/segments/10-queue.sh
```

It appends after the directory name, like the third row of the screenshot:

```
my-project main  ⏱ deploy ok·queue 3
$4.48·ctx █░░░░░░░░░ 11%
```

The contract:

- Segments run in filename order (prefix with `10-`, `20-`, … to sequence them)
- Each receives the **same JSON payload** on stdin that the main script gets
- Its **first stdout line** is appended to line 1; print nothing to stay hidden
- ANSI colors are fine; honor `NO_COLOR` yourself
- A segment that fails, times out (1s), or isn't executable is skipped silently. **A broken segment can never break your status line**

Segments live outside this repo, so upgrades never touch them and private status bits never reach a public checkout.

### Alternative: wrap this script

Prefer keeping your own script as the entry point? Call this one from it:

```bash
usage=$(python3 ~/.claude/statusline/usage.py <<< "$payload")
echo "${your_existing_segment}  ${usage}"
```

## How it works

Claude Code pipes a JSON payload to the `statusLine` command in `settings.json` once per render. This script reads it from stdin and prints up to two lines. Fields used:

- `cost.total_cost_usd`
- `context_window.used_percentage`
- `rate_limits.five_hour.{used_percentage,resets_at}`
- `rate_limits.seven_day.{used_percentage,resets_at}`
- `workspace.current_dir` / `cwd`

Missing fields are skipped. The script never errors out, even on malformed input, so it can't break your status line.

No network calls, and no dependencies beyond `python3` (already required by Claude Code) and optionally `git`.

### The one file it writes

`~/.claude/statusline/history.jsonl` — usage samples, used only for the [`→full` projection](#full--this-pace-wont-make-it-to-the-reset):

- **Pure cache**: delete it and you lose the `→full` estimate for a while, nothing else
- **Can't grow**: one sample per 60s at most, 400 lines retained, **capped at ~17 KB**
- **Corruption-safe**: unparseable lines are skipped; an unreadable file just means no projection
- **Opt out**: `export USAGE_STATUSLINE_NO_HISTORY=1` and the script is fully stateless again

Nothing else is ever written.

## How it compares

This space is crowded, and some alternatives do **far more** than this one. Straight answer:
**want powerline segments, a graphical configurator, Git PR/CI status? use ccstatusline.
Want something that looks right without configuring anything, in 440 lines you can read in one sitting? use this.**

| | **usage-statusline** | [ccstatusline](https://github.com/sirmalloc/ccstatusline) | [claude-powerline](https://github.com/Owloops/claude-powerline) | [CCometixLine](https://github.com/Haleclipse/CCometixLine) |
|---|---|---|---|---|
| Stars | — | 12.4k | 1.1k | 3.4k |
| Implementation | Single Python file, ~440 lines | TypeScript / npm | TypeScript / npm | Rust binary |
| Runtime deps | **None** (`python3` ships with Claude Code) | Node.js | Node.js | Prebuilt binary |
| Configuration | **None**, works on install | TUI configurator | JSON config | Config file |
| 5-hour limit | ✅ | ✅ | ✅ | — |
| 7-day limit | ✅ | ✅ | — | — |
| Subscription vs pay-as-you-go | ✅ via `~` prefix | Partial (shows extra-usage amount + currency) | — | — |
| **Hard-stop warning** | ✅ `⚠hard stop` | not documented | not documented | not documented |
| **Burn-rate projection** | ✅ `→full 14:46` (5h window only) | not documented | not documented | not documented |
| Custom extensions | Drop an executable in a directory | Widget system | Segment config | — |
| Themes / gradients | ✅ 3 themes, good by default | ✅ via TUI configuration | ✅ | ✅ |
| Powerline segments | ❌ | ✅ | ✅ | ✅ |
| Git dirty / unpushed | ✅ `±3 ↑2`, single call | ✅ | ✅ | ✅ |
| Git PR / CI status | ❌ (wire it up as a segment) | ✅ | ✅ | — |

> Based on each project's public README as of 2026-08. `—` means not mentioned there — **not proof it's missing**.
> Stars left blank here because this is a personal tool released as-is, not competing on scale.

**Don't pick this if** you want powerline segments, a graphical configurator, Git PR/CI status, or finer
usage breakdowns (weekly, per-model, extra-usage amounts with currency). ccstatusline has all of that;
this doesn't and isn't planning to.

**Do pick this if:**

- You'd rather not add a Node dependency for a status line
- You want it to **look right on install, without learning a configuration system first**
- You want to read the entire source in one sitting when something breaks
- You want to add your own bits without learning a widget/segment abstraction — just drop in an executable
- You want to know **whether hitting your limit stops you dead**, not just that you're at 100%

## Uninstall

Remove the `statusLine` key from `~/.claude/settings.json` (or restore `settings.json.bak-usage-statusline`), then delete `~/.claude/statusline/usage.py`. Segments in `~/.claude/statusline/segments/` are yours — delete them separately if you want them gone.

## License

MIT — see [LICENSE](./LICENSE).
