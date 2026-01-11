# セットアップガイド

## クイックスタート

```bash
# 1. セットアップスクリプト実行
.claude/scripts/setup.sh

# 2. .mcp.json を編集
# SLACK_BOT_TOKEN と SLACK_TEAM_ID を設定

# 3. Claude Code 再起動
```

## 必要な設定

### 1. MCP設定 (`.mcp.json`)

```bash
cp .mcp.json.example .mcp.json
```

| 変数 | 取得方法 |
|------|----------|
| `SLACK_BOT_TOKEN` | https://api.slack.com/apps → OAuth & Permissions → User/Bot Token |
| `SLACK_TEAM_ID` | SlackのURL `app.slack.com/client/Txxxxxxxx/...` の `T`から始まる部分 |

**注意**: User Token(`xoxp-`)を使う場合も`SLACK_BOT_TOKEN`変数に設定

### 2. Playwright MCP

```bash
npm install -g @anthropic-ai/mcp-server-playwright
```

パスは自動検出されます（Mac/Linux対応）

### 3. Gemini CLI（検索スキル用）

```bash
# インストール
npm install -g @anthropic-ai/gemini-cli

# 認証
gemini auth
```

## ファイル構成

```
.mcp.json           # MCP設定（.gitignore済み）
.mcp.json.example   # テンプレート
.claude/
  scripts/
    setup.sh        # セットアップスクリプト
    playwright-mcp.sh # Playwright wrapper
  skills/           # スキル定義
  rules/            # ルール定義
  settings.json     # hooks設定
```

## トラブルシューティング

| 問題 | 対処 |
|------|------|
| Slack MCP接続失敗 | トークン確認、`claude mcp list`で状態確認 |
| Playwright見つからない | `npm install -g @anthropic-ai/mcp-server-playwright` |
| 権限エラー | `chmod +x .claude/scripts/*.sh` |
