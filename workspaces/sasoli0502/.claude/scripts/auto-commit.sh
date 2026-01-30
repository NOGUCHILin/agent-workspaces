#!/bin/bash
# 変更があれば自動コミット＆プッシュ

if [[ -n $(git status --porcelain) ]]; then
  git add -A
  git commit -m "auto: $(date '+%Y-%m-%d %H:%M')"
  git push origin HEAD 2>/dev/null || true
fi
