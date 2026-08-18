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
BAR_WIDTH = 10
BAR_FULL = "▓"
BAR_EMPTY = "░"

raw = sys.stdin.read()
try:
    payload = json.loads(raw)
except Exception:
    sys.exit(0)

NO_COLOR = bool(os.environ.get("NO_COLOR"))
RESET = "" if NO_COLOR else "\033[0m"


def color(pct):
    if NO_COLOR or pct is None:
        return ""
    if pct >= 80:
        return "\033[31m"
    if pct >= 50:
        return "\033[33m"
    return "\033[32m"


def dim(text):
    return text if NO_COLOR else f"\033[90m{text}{RESET}"


def bar(pct):
    pct = min(max(pct, 0), 100)
    filled = int(round(pct / 100 * BAR_WIDTH))
    # Any non-zero usage keeps one cell lit, so "barely used" still reads as used
    # rather than as an empty bar.
    if pct > 0:
        filled = max(filled, 1)
    return BAR_FULL * filled + BAR_EMPTY * (BAR_WIDTH - filled)


def gauge(label, pct, suffix=""):
    return f"{color(pct)}{label} {bar(pct)} {pct:.0f}%{suffix}{RESET}"


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
    try:
        branch = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=1,
        ).stdout.strip()
    except Exception:
        branch = ""
    if branch:
        label += f" {dim(branch)}"
    head.append(label)

head.extend(extension_segments())

# --- line 2: cost and the three usage gauges --------------------------------
metrics = []

cost = (payload.get("cost") or {}).get("total_cost_usd")
if cost is not None:
    metrics.append(dim(f"${cost:.2f}"))

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
    if resets_at:
        delta_hours = (resets_at - now) / 3600
        dt = datetime.datetime.fromtimestamp(resets_at)
        # <20h shows a clock time (fits the 5h window, incl. overnight resets);
        # further out shows a date (fits the 7-day window, where the day is what matters).
        suffix = f"({dt.strftime('%H:%M')})" if delta_hours < 20 else f"({dt.strftime('%m-%d')})"
    return gauge(label, pct, suffix)


rate_limits = payload.get("rate_limits") or {}
for label, key in (("5h", "five_hour"), ("7d", "seven_day")):
    rendered = window(label, rate_limits.get(key))
    if rendered:
        metrics.append(rendered)

for line in ("  ".join(head), "·".join(metrics)):
    if line:
        print(line)
