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

### 2. agent-browser（ブラウザ自動化）

```bash
npm install  # package.jsonに含まれている
```

使用方法:
```bash
npx agent-browser open https://example.com
npx agent-browser snapshot -i
npx agent-browser click @e1
```

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
package.json        # agent-browser等の依存関係
.claude/
  scripts/
    setup.sh        # セットアップスクリプト
  skills/           # スキル定義
    agent-browser/  # ブラウザ自動化スキル
  rules/            # ルール定義
    agent-browser.md # ブラウザ操作ルール
  settings.json     # hooks設定
```

## トラブルシューティング

| 問題 | 対処 |
|------|------|
| Slack MCP接続失敗 | トークン確認、`claude mcp list`で状態確認 |
| agent-browser見つからない | `npm install` を実行 |
| 権限エラー | `chmod +x .claude/scripts/*.sh` |
