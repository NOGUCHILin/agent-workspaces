---
name: check-status
description: 全プロジェクトの進捗状況を確認する。「今どうなってる?」「状況教えて」「進捗確認」と言われた時に使用。セッション開始時にも使用推奨。
---

# セッション開始時のチェック

新しいセッション開始時、以下を確認してユーザーに報告する：

## 1. セットアップ状態

```bash
# .mcp.jsonが存在し、トークンが設定されているか
if [ -f ".mcp.json" ]; then
  grep -q "xoxp-" .mcp.json && echo "Slack: OK" || echo "Slack: トークン未設定"
  grep -q "playwright" .mcp.json && echo "Playwright: OK" || echo "Playwright: 未設定"
else
  echo ".mcp.json: 未作成 → .mcp.json.exampleをコピーして設定"
fi
```

## 2. プロジェクト状況

```bash
.claude/skills/check-status/scripts/scan-status.sh
```

## 3. 報告テンプレート

```
【ワークスペース状態】
- セットアップ: 完了 / 要設定
- プロジェクト: X個
- アクティブworktree: Y個

【現在の作業状況】
- [project/branch] spec名: 状態

【次のアクション候補】
1. ...
2. ...
```

# 未セットアップ時のガイド

セットアップが完了していない場合、以下を案内：

```
このワークスペースを使うには以下のセットアップが必要です：

1. MCP設定
   cp .mcp.json.example .mcp.json
   # Slackトークン、Team IDを設定

2. 新規プロジェクト追加
   .claude/skills/manage-workspace/scripts/setup.sh <project> <branch> <repo-url>

詳細: docs/SETUP.md を参照
```

# 使用コマンド

```bash
# 全体スキャン
.claude/skills/check-status/scripts/scan-status.sh

# 特定プロジェクトのみ
.claude/skills/check-status/scripts/scan-status.sh <project-name>
```

# 報告後のアクション提案

| 状態 | 提案 |
|------|------|
| 作業中specあり | 「続きをやりますか?」 |
| 全spec完了 | 「新しいタスクを始めますか?」 |
| 未着手specあり | 「どれから始めますか?」 |
| プロジェクトなし | 「プロジェクトを追加しますか?」 |

# 関連スキル

- `manage-workspace`: プロジェクト/worktree作成
- `sync-template`: テンプレートリポジトリに同期
