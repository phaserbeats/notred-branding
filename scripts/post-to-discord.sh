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

# Discord caps message bodies at 2000 characters. Use Python only to chunk the
# file and emit JSON payloads, then post each one with curl (which uses the
# macOS system cert store and avoids Python's SSL bundle issues).
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

python3 - "$DAILY_FILE" "$TMPDIR" <<'PY'
import json, sys, os

path, tmpdir = sys.argv[1], sys.argv[2]
with open(path) as f:
    body = f.read()

MAX = 1900
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
    with open(os.path.join(tmpdir, f"chunk-{i:03d}.json"), "w") as f:
        json.dump({"content": chunk}, f)

print(len(chunks))
PY

CHUNK_COUNT=$(ls "$TMPDIR" | wc -l | tr -d ' ')
i=0
for payload_file in "$TMPDIR"/chunk-*.json; do
  i=$((i + 1))
  if ! curl -sS -f \
        -X POST \
        -H "Content-Type: application/json" \
        --data-binary "@$payload_file" \
        --max-time 15 \
        "$WEBHOOK_URL" > /dev/null; then
    echo "discord push failed on chunk $i/$CHUNK_COUNT" >&2
    exit 4
  fi
done

echo "posted $CHUNK_COUNT chunk(s) to discord"
