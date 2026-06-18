#!/usr/bin/env bash
# Post the contents of a daily markdown file to Discord via webhook.
# Usage: scripts/post-to-discord.sh daily/YYYY-MM-DD.md

set -euo pipefail

DAILY_FILE="${1:-}"
if [[ -z "$DAILY_FILE" ]]; then
  echo "usage: $0 <path/to/daily/file.md>" >&2
  exit 2
fi

if [[ ! -f "$DAILY_FILE" ]]; then
  echo "error: file not found: $DAILY_FILE" >&2
  exit 2
fi

CONFIG=".claude/daily-planner.config.json"
if [[ ! -f "$CONFIG" ]]; then
  echo "error: missing config at $CONFIG (copy $CONFIG.example and fill in)" >&2
  exit 3
fi

WEBHOOK_URL=$(python3 -c "import json,sys; print(json.load(open('$CONFIG'))['discord_webhook_url'])")
if [[ -z "$WEBHOOK_URL" ]] || [[ "$WEBHOOK_URL" == "REPLACE_ME" ]]; then
  echo "error: discord_webhook_url not configured in $CONFIG" >&2
  exit 3
fi

# Discord caps message bodies at 2000 characters. Split into chunks on blank-line
# boundaries where possible so headings stay intact.
python3 - "$DAILY_FILE" "$WEBHOOK_URL" <<'PY'
import json, sys, urllib.request, urllib.error

path, webhook = sys.argv[1], sys.argv[2]
with open(path) as f:
    body = f.read()

MAX = 1900  # leave headroom for codefence wrap
chunks, buf = [], ""
for para in body.split("\n\n"):
    candidate = (buf + "\n\n" + para).strip() if buf else para
    if len(candidate) > MAX and buf:
        chunks.append(buf)
        buf = para
    else:
        buf = candidate
if buf:
    chunks.append(buf)

for i, chunk in enumerate(chunks):
    payload = json.dumps({"content": chunk}).encode()
    req = urllib.request.Request(
        webhook,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=10).read()
    except urllib.error.URLError as e:
        print(f"discord push failed on chunk {i+1}/{len(chunks)}: {e}", file=sys.stderr)
        sys.exit(4)

print(f"posted {len(chunks)} chunk(s) to discord")
PY
