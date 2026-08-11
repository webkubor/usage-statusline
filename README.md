# claude-usage-statusline

A Claude Code status line that shows session cost, context-window usage, and
your 5-hour / 7-day rate-limit usage — right where you're already looking.

```
my-project main  $0.62·ctx 7%·5h 7%(4h)·7d 8%(5d)
```

- `my-project main` — current directory name + git branch (branch omitted outside a repo)
- `$0.62` — total cost of the current session
- `ctx 7%` — context window used
- `5h 7%(4h)` — 5-hour rate-limit window: 7% used, resets in ~4 hours
- `7d 8%(5d)` — 7-day rate-limit window: 8% used, resets in ~5 days

Colors: green/gray under 50%, yellow at 50–79%, red at 80%+. Respects `NO_COLOR`.

No network calls, no external state, no dependencies beyond `python3` (already
required by Claude Code itself) and, optionally, `git` for the branch name.

## Install

### Option A — as a Claude Code Skill (recommended)

```bash
git clone https://github.com/<you>/claude-usage-statusline ~/.claude/skills/usage-statusline
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
git clone https://github.com/<you>/claude-usage-statusline
cd claude-usage-statusline
./install.sh
```

Same behavior as Option A, minus the conversation: merges into
`~/.claude/settings.json` (backing up the original to
`settings.json.bak-usage-statusline` on first run), refuses to clobber a
different existing `statusLine.command`.

Restart Claude Code (or open a new session) — `statusLine` is read at startup.

## How it works

Claude Code pipes a JSON payload to whatever command is configured under
`statusLine` in `settings.json`, once per render. This script reads that
payload from stdin and prints one line to stdout. The fields it looks at:

- `cost.total_cost_usd`
- `context_window.used_percentage`
- `rate_limits.five_hour.{used_percentage,resets_at}`
- `rate_limits.seven_day.{used_percentage,resets_at}`
- `workspace.current_dir` / `cwd` (for the directory + git branch prefix)

Any missing field is just skipped — the script never errors out, even on
malformed input, so it can't break your status line.

## Combining with your own status line

Already have a `statusLine` script? Don't run the installer over it. Instead,
call `scripts/statusline.py` from inside your own script and append its
output, e.g.:

```bash
usage=$(python3 /path/to/usage.py <<< "$payload")
echo "${your_existing_segment}  ${usage}"
```

## Uninstall

Remove the `statusLine` key from `~/.claude/settings.json` (or restore
`settings.json.bak-usage-statusline` if present), then delete
`~/.claude/statusline/usage.py`.

## License

MIT — see [LICENSE](./LICENSE).
