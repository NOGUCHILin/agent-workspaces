---
name: setup-mcp
description: MCP設定をユーザーと協力して行う。「セットアップして」「Slack連携して」「MCP設定して」と言われた時に使用。agent-browserでブラウザを案内。
---

# MCP設定ガイド（agent-browser使用）

## 概要

agent-browserを使ってブラウザを開き、ユーザーと協力してSlackトークンを取得・設定する。

## 実行手順

### Step 1: 現状確認

```bash
# .mcp.json の存在確認
cat .mcp.json 2>/dev/null || echo "未設定"
```

### Step 2: Slack App設定ページへ案内

1. **ブラウザを開く**
   ```bash
   npx agent-browser open https://api.slack.com/apps --headed
   ```

2. **ユーザーにログインを依頼**
   - 「Slackにログインしてください」と伝える
   - ログイン完了を待つ

3. **アプリ選択/作成を案内**
   - 既存アプリがあれば選択
   - なければ「Create New App」→「From scratch」

### Step 3: OAuth Token取得

1. **OAuth & Permissionsページへ移動**
   ```
   左メニューの「OAuth & Permissions」をクリック
   ```

2. **Scopesを確認**（必要に応じて追加）
   - User Token Scopes: `channels:history`, `channels:read`, `chat:write`, `users:read`

3. **トークンをコピー**
   - 「User OAuth Token」(xoxp-で始まる) または
   - 「Bot User OAuth Token」(xoxb-で始まる)

### Step 4: Team ID取得

1. **SlackアプリのURLを確認**
   ```
   https://app.slack.com/client/Txxxxxxxx/Cxxxxxxxx
                              ↑ここがTeam ID
   ```

2. **ユーザーに確認**
   - 「SlackのURLからTで始まるIDを教えてください」

### Step 5: 設定ファイル更新

```bash
# .mcp.json.example をベースに作成
cp .mcp.json.example .mcp.json

# トークンを設定（ユーザーから受け取った値で）
```

設定内容:
```json
{
  "mcpServers": {
    "slack": {
      "env": {
        "SLACK_BOT_TOKEN": "<ユーザーから取得したトークン>",
        "SLACK_TEAM_ID": "<ユーザーから取得したTeam ID>"
      }
    }
  }
}
```

### Step 6: 確認

```bash
# Claude Code再起動後に確認
claude mcp list
```

## 会話テンプレート

### 開始時
「MCP設定を行います。まずブラウザでSlack APIページを開きます。ログインをお願いします。」

### ログイン待ち
「ログインが完了したら教えてください。」

### トークン取得時
「OAuth & Permissionsページで、User OAuth Token（xoxp-で始まる）をコピーして貼り付けてください。」

### Team ID取得時
「SlackのURL（app.slack.com/client/Txxxxxxxx/...）からTで始まるIDを教えてください。」

### 完了時
「設定が完了しました。Claude Codeを再起動してください。」

## トラブルシューティング

| 問題 | 対処 |
|------|------|
| ログインできない | 別ブラウザで試す、Cookieクリア |
| トークンが見つからない | 「Install to Workspace」が必要 |
| 権限エラー | Scopesを追加して再インストール |
