#!/bin/bash
# Edit/Write前に1回だけプル（セッション内で重複防止）

PULL_FLAG="/tmp/claude-auto-pull-$$"

# すでにプル済みならスキップ
if [[ -f "$PULL_FLAG" ]]; then
  exit 0
fi

# プル実行
git pull --rebase origin HEAD 2>/dev/null || true

# フラグ作成
touch "$PULL_FLAG"
