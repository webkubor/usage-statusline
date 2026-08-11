#!/usr/bin/env python3
"""Claude Code status line: session cost, context-window usage, and
5-hour / 7-day rate-limit usage. Reads the JSON payload Claude Code pipes
to statusLine commands on stdin. No network access, no external state.
"""
import json
import os
import subprocess
import sys
import time

try:
    payload = json.load(sys.stdin)
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


parts = []

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
    parts.append(label)

metrics = []

cost = (payload.get("cost") or {}).get("total_cost_usd")
if cost is not None:
    metrics.append(dim(f"${cost:.2f}"))

ctx_pct = (payload.get("context_window") or {}).get("used_percentage")
if ctx_pct is not None:
    metrics.append(f"{color(ctx_pct)}ctx {ctx_pct:.0f}%{RESET}")

now = time.time()


def window(label, w):
    if not w:
        return None
    pct = w.get("used_percentage")
    if pct is None:
        return None
    resets_at = w.get("resets_at")
    remain = ""
    if resets_at:
        delta = resets_at - now
        if delta > 0:
            hours = int(delta // 3600)
            if hours >= 24:
                remain = f"({hours // 24}d)"
            elif hours > 0:
                remain = f"({hours}h)"
            else:
                remain = f"({int(delta // 60)}m)"
    return f"{color(pct)}{label} {pct:.0f}%{remain}{RESET}"


rate_limits = payload.get("rate_limits") or {}
five_hour = window("5h", rate_limits.get("five_hour"))
if five_hour:
    metrics.append(five_hour)
seven_day = window("7d", rate_limits.get("seven_day"))
if seven_day:
    metrics.append(seven_day)

if metrics:
    parts.append("·".join(metrics))

print("  ".join(parts))
