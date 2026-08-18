#!/usr/bin/env python3
"""Claude Code status line: session cost, context-window usage, and
5-hour / 7-day rate-limit usage, drawn as compact bars.

Reads the JSON payload Claude Code pipes to statusLine commands on stdin.
No network access, no external state of its own.

Local extension segments let you append your own status bits (patrol heartbeat,
queue depth, on-call state, ...) to the first line without forking this script:
drop an executable into ~/.claude/statusline/segments/, it receives the same
payload on stdin and its first stdout line is appended. See README.
"""
import datetime
import json
import os
import subprocess
import sys
import time

SEGMENTS_DIR = os.path.expanduser("~/.claude/statusline/segments")
PROFILE = os.path.expanduser("~/.claude.json")
BAR_WIDTH = 10
SOLID = "█"      # colored halves (default)
BAR_FULL = "▓"   # NO_COLOR fallback
BAR_EMPTY = "░"
# A rate-limit window at or above this much, with no pay-as-you-go fallback left,
# means you are about to hit a hard stop rather than an overage charge.
WARN_AT = 80

raw = sys.stdin.read()
try:
    payload = json.loads(raw)
except Exception:
    sys.exit(0)

NO_COLOR = bool(os.environ.get("NO_COLOR"))
RESET = "" if NO_COLOR else "\033[0m"
TRUECOLOR = os.environ.get("COLORTERM", "") in ("truecolor", "24bit")

# Themes are ramps keyed by how used a gauge is: calm at the left, alarming at the
# right. Every theme keeps that meaning — a theme changes the palette, never what
# the color is telling you.
THEMES = {
    # Muted sage → amber → coral. Deliberately desaturated so a mostly-empty bar
    # sits quietly next to your prompt instead of glowing at you.
    "default": [(0, (0x74, 0xB3, 0x88)), (55, (0xD1, 0xB5, 0x66)), (80, (0xDE, 0x8A, 0x5F)), (100, (0xD6, 0x5D, 0x5D))],
    # Teal → indigo → magenta, for dark themes where green reads as "terminal green".
    "cool": [(0, (0x5A, 0xB8, 0xB0)), (55, (0x6D, 0x8F, 0xD8)), (80, (0xA1, 0x7A, 0xD8)), (100, (0xD1, 0x6B, 0xB0))],
    # No hue at all: pure luminance ramp. For people who want the status line to
    # disappear into the terminal until it matters.
    "mono": [(0, (0x6E, 0x6E, 0x78)), (55, (0x9A, 0x9A, 0xA4)), (80, (0xC6, 0xC6, 0xCE)), (100, (0xF0, 0xF0, 0xF4))],
}
THEME = THEMES.get(os.environ.get("USAGE_STATUSLINE_THEME", "default"), THEMES["default"])
# 8-color fallback keeps the same calm→alarm reading on terminals without truecolor.
BASIC = [(0, "\033[32m"), (55, "\033[33m"), (80, "\033[31m")]


def ramp(pct):
    """Interpolate the active theme at `pct`, as an ANSI foreground escape."""
    if NO_COLOR:
        return ""
    pct = min(max(pct, 0), 100)
    if not TRUECOLOR:
        chosen = BASIC[0][1]
        for at, code in BASIC:
            if pct >= at:
                chosen = code
        return chosen
    lo = THEME[0]
    hi = THEME[-1]
    for i in range(len(THEME) - 1):
        if THEME[i][0] <= pct <= THEME[i + 1][0]:
            lo, hi = THEME[i], THEME[i + 1]
            break
    span = hi[0] - lo[0] or 1
    t = (pct - lo[0]) / span
    r, g, b = (round(lo[1][i] + (hi[1][i] - lo[1][i]) * t) for i in range(3))
    return f"\033[38;2;{r};{g};{b}m"


def shade(pct, factor):
    """Same hue as `ramp(pct)`, dimmed — used for the un-filled half of a bar so
    the whole track still shows where the danger zone is."""
    if NO_COLOR:
        return ""
    if not TRUECOLOR:
        return "\033[90m"
    lo = THEME[0]
    hi = THEME[-1]
    for i in range(len(THEME) - 1):
        if THEME[i][0] <= pct <= THEME[i + 1][0]:
            lo, hi = THEME[i], THEME[i + 1]
            break
    span = hi[0] - lo[0] or 1
    t = (pct - lo[0]) / span
    r, g, b = (round((lo[1][i] + (hi[1][i] - lo[1][i]) * t) * factor) for i in range(3))
    return f"\033[38;2;{r};{g};{b}m"


def color(pct):
    return ramp(pct) if pct is not None else ""


def dim(text):
    return text if NO_COLOR else f"\033[90m{text}{RESET}"


def bar(pct):
    pct = min(max(pct, 0), 100)
    filled = int(round(pct / 100 * BAR_WIDTH))
    # Any non-zero usage keeps one cell lit, so "barely used" still reads as used
    # rather than as an empty bar.
    if pct > 0:
        filled = max(filled, 1)
    if NO_COLOR:
        # Shade characters are the only way to tell the halves apart without color,
        # but they render as muddy dot patterns in many fonts — so they are the
        # fallback, not the default.
        return BAR_FULL * filled + BAR_EMPTY * (BAR_WIDTH - filled)
    # Each cell is colored for its own position on the track, not for the current
    # value: the right end is always the alarm color, so the bar shows where the
    # danger zone is *before* you reach it. Filled cells are lit, the rest sit at
    # a fraction of the same hue.
    cells = []
    for i in range(BAR_WIDTH):
        at = (i + 1) / BAR_WIDTH * 100
        cells.append(f"{ramp(at) if i < filled else shade(at, 0.34)}{SOLID}")
    return "".join(cells)


def gauge(label, pct, suffix=""):
    return f"{color(pct)}{label} {bar(pct)}{color(pct)} {pct:.0f}%{suffix}{RESET}"


def billing():
    """How this account pays, read from ~/.claude.json.

    Returns {"subscription": bool, "fallback": bool} or None when unknown.

    It matters for reading the numbers on this line:
    - On a subscription, cost.total_cost_usd is API-list-price *equivalent* spend,
      not money that gets charged — the rate-limit windows are the real constraint.
    - "fallback" is whether exceeding those windows spills over into pay-as-you-go
      billing. Without it, a full window is a hard stop, not an overage.
    """
    try:
        with open(PROFILE) as handle:
            data = json.load(handle)
    except Exception:
        return None
    account = data.get("oauthAccount") or {}
    billing_type = account.get("billingType")
    if not billing_type:
        return None
    return {
        "subscription": "subscription" in billing_type,
        # Extra usage can be switched on yet unusable (e.g. out of credits), which
        # is exactly the case worth warning about — enabled is not the same as available.
        "fallback": bool(account.get("hasExtraUsageEnabled"))
        and not data.get("cachedExtraUsageDisabledReason"),
    }


def git_state(cwd):
    """Branch, unpushed/unpulled commit counts, and dirty-file count in one call.

    `status --porcelain=v2 --branch` yields all of it at once, which is both fewer
    processes than asking separately and the only way to get ahead/behind without
    a second round trip. Returns None outside a repo or if git is slow/missing —
    the status line renders fine without it.
    """
    try:
        proc = subprocess.run(
            ["git", "-C", cwd, "status", "--porcelain=v2", "--branch"],
            capture_output=True, text=True, timeout=1,
        )
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    branch, ahead, behind, dirty = "", 0, 0, 0
    for line in proc.stdout.splitlines():
        if line.startswith("# branch.head "):
            branch = line[14:].strip()
        elif line.startswith("# branch.ab "):
            parts = line[12:].split()
            for p in parts:
                if p.startswith("+"):
                    ahead = int(p[1:])
                elif p.startswith("-"):
                    behind = int(p[1:])
        elif line[:1] in ("1", "2", "u", "?"):
            # Tracked change, rename, unmerged path, or untracked file — all of
            # them are "work sitting here uncommitted", which is what you want counted.
            dirty += 1
    if not branch:
        return None
    return {"branch": branch, "ahead": ahead, "behind": behind, "dirty": dirty}


def git_label(state):
    """`main ±3 ↑2` — and just `main` when the tree is clean and in sync.

    Silence is the point: markers appear only when there is something you have
    not committed or not pushed, so a quiet status line means a quiet repo.
    """
    if not state:
        return ""
    out = dim(state["branch"])
    marks = []
    if state["dirty"]:
        marks.append(f"±{state['dirty']}")
    if state["ahead"]:
        marks.append(f"↑{state['ahead']}")
    if state["behind"]:
        marks.append(f"↓{state['behind']}")
    if marks:
        text = " ".join(marks)
        # Mid-ramp hue: worth noticing, not worth alarming about.
        out += " " + (text if NO_COLOR else f"{ramp(45)}{text}{RESET}")
    return out


def extension_segments():
    """Run every executable in SEGMENTS_DIR, in filename order, and collect the
    first line each one prints. A segment that fails, hangs, or prints nothing is
    skipped silently — the status line must never break because an extension did.
    """
    try:
        names = sorted(os.listdir(SEGMENTS_DIR))
    except OSError:
        return []
    collected = []
    for name in names:
        if name.startswith("."):
            continue
        path = os.path.join(SEGMENTS_DIR, name)
        if os.path.isdir(path) or not os.access(path, os.X_OK):
            continue
        try:
            proc = subprocess.run(
                [path], input=raw, capture_output=True, text=True, timeout=1,
            )
        except Exception:
            continue
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        if lines:
            collected.append(lines[0])
    return collected


# --- line 1: where you are, plus whatever local segments want to say ---------
head = []

cwd = (payload.get("workspace") or {}).get("current_dir") or payload.get("cwd") or ""
if cwd:
    base = os.path.basename(cwd)
    label = base if NO_COLOR else f"\033[36m{base}{RESET}"
    git = git_label(git_state(cwd))
    if git:
        label += f" {git}"
    head.append(label)

head.extend(extension_segments())

# --- line 2: cost and the three usage gauges --------------------------------
metrics = []
pay = billing()

cost = (payload.get("cost") or {}).get("total_cost_usd")
if cost is not None:
    # "~" marks spend that is equivalent-only: on a subscription this is what the
    # session would have cost at API list price, not what you are billed.
    prefix = "~" if pay and pay["subscription"] else ""
    metrics.append(dim(f"{prefix}${cost:.2f}"))

ctx_pct = (payload.get("context_window") or {}).get("used_percentage")
if ctx_pct is not None:
    metrics.append(gauge("ctx", ctx_pct))

now = time.time()


def window(label, w):
    if not w:
        return None
    pct = w.get("used_percentage")
    if pct is None:
        return None
    resets_at = w.get("resets_at")
    suffix = ""
    # Running this window out means work stops until it resets, so say so before
    # it happens rather than letting a full bar read as "just an overage".
    # Only meaningful on a subscription: pay-as-you-go has no window to fall back
    # *from* — exceeding usage there simply keeps billing.
    if pct >= WARN_AT and pay and pay["subscription"] and not pay["fallback"]:
        suffix += " ⚠hard stop"
    if resets_at:
        delta_hours = (resets_at - now) / 3600
        dt = datetime.datetime.fromtimestamp(resets_at)
        # <20h shows a clock time (fits the 5h window, incl. overnight resets);
        # further out shows a date (fits the 7-day window, where the day is what matters).
        suffix += f"({dt.strftime('%H:%M')})" if delta_hours < 20 else f"({dt.strftime('%m-%d')})"
    return gauge(label, pct, suffix)


rate_limits = payload.get("rate_limits") or {}
for label, key in (("5h", "five_hour"), ("7d", "seven_day")):
    rendered = window(label, rate_limits.get(key))
    if rendered:
        metrics.append(rendered)

for line in ("  ".join(head), "·".join(metrics)):
    if line:
        print(line)
