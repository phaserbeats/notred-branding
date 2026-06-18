#!/usr/bin/env bash
# Daily-planner runner. Invoked by launchd every day at 06:00 IST.
#
# Strategy: claude --print does ONLY the file write (its strength). The shell
# wrapper handles all orchestration — verifying the file landed, committing,
# pushing, and posting to Discord. Headless claude struggles to drive bash
# reliably, so we split the responsibility cleanly.

set -euo pipefail

PROJECT_DIR="/Volumes/T7/Development with Claude/notred-branding"
LOG_DIR="$PROJECT_DIR/.claude/logs"
DATE=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/run-$DATE.log"
DAILY_FILE="daily/$DATE.md"

mkdir -p "$LOG_DIR"

# Make standard tool paths available when launchd invokes us with a minimal env.
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

{
  echo "=== run-daily-planner.sh starting at $(date) ==="
  cd "$PROJECT_DIR"

  if ! command -v claude >/dev/null 2>&1; then
    echo "FATAL: 'claude' CLI not found on PATH" >&2
    exit 1
  fi

  # Skip the generation step if today's file already exists (idempotent).
  if [[ -f "$DAILY_FILE" ]]; then
    echo "INFO: $DAILY_FILE already exists, skipping generation"
  else
    echo "--- invoking notred-daily-planner via claude --print ---"
    claude --print --permission-mode acceptEdits <<EOF
Use the notred-daily-planner subagent to write today's daily file at $DAILY_FILE.

Your only job in this run is to write that one file. Do NOT commit. Do NOT push.
Do NOT run any shell commands. Do NOT create helper scripts. The wrapper script
that invoked you will handle commit, push, and Discord push after you finish.

When the file is written, your work is done.
EOF
    echo "--- claude --print returned exit=$? ---"
  fi

  if [[ ! -f "$DAILY_FILE" ]]; then
    echo "FATAL: $DAILY_FILE was not created" >&2
    exit 2
  fi

  # Commit (only if there's something to commit).
  if [[ -n "$(git status --porcelain "$DAILY_FILE")" ]]; then
    echo "--- committing $DAILY_FILE ---"
    git add "$DAILY_FILE"
    git commit -m "chore(daily): plan for $DATE"
  else
    echo "INFO: nothing to commit for $DAILY_FILE"
  fi

  # Push (best-effort — log but don't fail the run on push errors).
  echo "--- pushing to origin ---"
  if git push 2>&1; then
    echo "push ok"
  else
    echo "WARN: git push failed; continuing"
  fi

  # Discord push (best-effort).
  echo "--- posting to Discord ---"
  if bash scripts/post-to-discord.sh "$DAILY_FILE"; then
    echo "discord ok"
  else
    echo "WARN: discord push failed; file is still written and committed"
  fi

  echo "=== run-daily-planner.sh finished at $(date) ==="
} >> "$LOG_FILE" 2>&1
