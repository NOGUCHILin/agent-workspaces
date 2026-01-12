# description: レポート生成。「レポート」「週次報告」「成績確認」で発動

## 週次レポート

```bash
cd /Users/noguchilin/claude-code-workspaces/projects/xlm-trader/worktrees/master/repo
python weekly_report.py
```

## 出力内容

- 先週のパフォーマンス
- 取引履歴
- 改善提案

## Slack通知

SLACK_WEBHOOK_URL環境変数が設定されていれば自動通知
