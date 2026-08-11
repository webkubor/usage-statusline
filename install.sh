#!/usr/bin/env bash
# Manual installer for people who aren't going through the Claude Code
# Skill flow — just clone the repo and run this once.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
target="$HOME/.claude/statusline/usage.py"
settings="$HOME/.claude/settings.json"

mkdir -p "$(dirname "$target")"
cp "$repo_dir/scripts/statusline.py" "$target"
chmod +x "$target"
echo "Installed script -> $target"

python3 - "$settings" "$target" <<'PY'
import json
import os
import sys

settings_path, command = sys.argv[1], sys.argv[2]

data = {}
if os.path.exists(settings_path):
    with open(settings_path) as f:
        raw = f.read().strip()
    data = json.loads(raw) if raw else {}
    existing = (data.get("statusLine") or {}).get("command")
    if existing and existing != command:
        print(f"settings.json already has a different statusLine command:\n  {existing}")
        print("Not overwriting it. Edit settings.json yourself if you want to switch, e.g.:")
        print(json.dumps({"statusLine": {"type": "command", "command": command, "padding": 0}}, indent=2))
        sys.exit(0)
    backup = settings_path + ".bak-usage-statusline"
    if not os.path.exists(backup):
        with open(backup, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Backed up existing settings.json -> {backup}")

data["statusLine"] = {"type": "command", "command": command, "padding": 0}

with open(settings_path, "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"Wrote statusLine config -> {settings_path}")
PY

echo
echo "Test render:"
echo '{"cwd":"'"$PWD"'","cost":{"total_cost_usd":0.1},"context_window":{"used_percentage":5},"rate_limits":{"five_hour":{"used_percentage":5,"resets_at":9999999999},"seven_day":{"used_percentage":5,"resets_at":9999999999}}}' \
  | "$target"
echo
echo "Done. Restart Claude Code (or open a new session) to see it in the status line."
