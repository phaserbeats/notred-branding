#!/usr/bin/env bash
# Wrapper that fires the notred-daily-planner via Claude Code headless mode.
# Invoked by launchd (~/Library/LaunchAgents/com.notred.daily-planner.plist) every day at 06:00 IST.

set -euo pipefail

PROJECT_DIR="/Volumes/T7/Development with Claude/notred-branding"
LOG_DIR="$PROJECT_DIR/.claude/logs"
DATE=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/run-$DATE.log"

mkdir -p "$LOG_DIR"

# Ensure the standard tool paths are available when launchd invokes us with a
# minimal environment.
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

{
  echo "=== run-daily-planner.sh starting at $(date) ==="
  cd "$PROJECT_DIR"

  if ! command -v claude >/dev/null 2>&1; then
    echo "error: 'claude' CLI not found on PATH" >&2
    exit 1
  fi

  claude --print --permission-mode acceptEdits \
    "Invoke the notred-daily-planner subagent. Tell it: 'Write today's daily file at daily/$DATE.md. After writing, commit it, push to origin, and run scripts/post-to-discord.sh against the new file. If anything fails, report what failed.'"

  echo "=== run-daily-planner.sh finished at $(date) ==="
} >> "$LOG_FILE" 2>&1
