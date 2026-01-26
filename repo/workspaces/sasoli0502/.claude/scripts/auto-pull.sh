#!/bin/bash
# Edit/Write前に1回だけプル（セッション内で重複防止）

PULL_FLAG="/tmp/claude-auto-pull-$$"

if [[ -f "$PULL_FLAG" ]]; then
  exit 0
fi

git pull --rebase origin HEAD 2>/dev/null || true
touch "$PULL_FLAG"
