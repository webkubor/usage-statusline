# claude-usage-statusline

A Claude Code status line that shows session cost, context-window usage, and
your 5-hour / 7-day rate-limit usage — right where you're already looking.

```
my-project main
$0.62·ctx ▓░░░░░░░░░ 7%·5h ▓░░░░░░░░░ 7%(20:10)·7d ▓░░░░░░░░░ 8%(08-17)
```

- `my-project main` — current directory name + git branch (branch omitted outside a repo)
- `$0.62` — total cost of the current session
- `ctx … 7%` — context window used
- `5h … 7%(20:10)` — 5-hour rate-limit window: 7% used, resets at 20:10
- `7d … 8%(08-17)` — 7-day rate-limit window: 8% used, resets on 08-17

Each gauge is a 10-cell bar so you can read "how full" without parsing digits.
Any non-zero usage lights at least one cell, so 1% never looks like 0%.

Colors: green under 50%, yellow at 50–79%, red at 80%+. Respects `NO_COLOR`.

No network calls, no external state, no dependencies beyond `python3` (already
required by Claude Code itself) and, optionally, `git` for the branch name.

## Install

### Option A — as a Claude Code Skill (recommended)

```bash
git clone https://github.com/webkubor/usage-statusline ~/.claude/skills/usage-statusline
```

Open Claude Code and run:

```
/usage-statusline
```

Claude reads `SKILL.md`, copies the script to `~/.claude/statusline/usage.py`,
and wires it into `~/.claude/settings.json`. If you already have a custom
`statusLine` configured, it won't be silently overwritten — Claude will tell
you what's already there and ask first.

### Option B — plain shell install

```bash
git clone https://github.com/webkubor/usage-statusline
cd usage-statusline
./install.sh
```

Same behavior as Option A, minus the conversation: merges into
`~/.claude/settings.json` (backing up the original to
`settings.json.bak-usage-statusline` on first run), refuses to clobber a
different existing `statusLine.command`.

Restart Claude Code (or open a new session) — `statusLine` is read at startup.

## Extension segments

Anything you want on the status line that isn't usage — a background job's
heartbeat, queue depth, on-call state, deploy status — goes in a **segment**
instead of a fork of this script.

Drop an executable into `~/.claude/statusline/segments/`:

```bash
cat > ~/.claude/statusline/segments/10-queue.sh <<'EOF'
#!/bin/sh
cat > /dev/null           # consume the payload on stdin, even if unused
echo "queue $(ls ~/jobs | wc -l | tr -d ' ')"
EOF
chmod +x ~/.claude/statusline/segments/10-queue.sh
```

```
my-project main  queue 3
$0.62·ctx ▓░░░░░░░░░ 7%·…
```

The contract:

- Segments run in filename order (prefix with `10-`, `20-`, … to sequence them).
- Each receives the **same JSON payload** on stdin that this script gets.
- Its **first stdout line** is appended to line 1. Print nothing to stay hidden.
- ANSI colors are fine; honor `NO_COLOR` if you set it.
- A segment that fails, hangs (1s timeout), or isn't executable is skipped
  silently. A broken segment can never break your status line.

Segments live outside this repo, so upgrading or reinstalling never touches
them — and your private/local status bits never end up in a public checkout.

### Alternative: wrap this script

If you'd rather keep your own script as the entry point, call this one from it:

```bash
usage=$(python3 ~/.claude/statusline/usage.py <<< "$payload")
echo "${your_existing_segment}  ${usage}"
```

## How it works

Claude Code pipes a JSON payload to whatever command is configured under
`statusLine` in `settings.json`, once per render. This script reads that
payload from stdin and prints up to two lines to stdout. The fields it reads:

- `cost.total_cost_usd`
- `context_window.used_percentage`
- `rate_limits.five_hour.{used_percentage,resets_at}`
- `rate_limits.seven_day.{used_percentage,resets_at}`
- `workspace.current_dir` / `cwd` (for the directory + git branch prefix)

Any missing field is just skipped — the script never errors out, even on
malformed input, so it can't break your status line.

## Uninstall

Remove the `statusLine` key from `~/.claude/settings.json` (or restore
`settings.json.bak-usage-statusline` if present), then delete
`~/.claude/statusline/usage.py`. Segments in `~/.claude/statusline/segments/`
are yours — delete them separately if you want them gone.

## License

MIT — see [LICENSE](./LICENSE).
