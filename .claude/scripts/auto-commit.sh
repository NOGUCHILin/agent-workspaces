#!/bin/bash
# 他ユーザーのClaude Code作業を自動コミット＆プッシュ

USER_EMAIL=$(git config user.email)
OWNER_EMAIL="noguchilin1103@gmail.com"

# オーナー以外なら自動コミット＆プッシュ
if [[ "$USER_EMAIL" != "$OWNER_EMAIL" ]]; then
  # 変更がある場合のみ
  if [[ -n $(git status --porcelain) ]]; then
    git add -A
    git commit -m "auto: changes by ${USER_EMAIL:-unknown}"
    git push origin HEAD 2>/dev/null || true
  fi
fi
