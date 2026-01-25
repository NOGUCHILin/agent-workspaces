# Hooks

出典: [Hooks](https://code.claude.com/docs/en/hooks)

---

## 概要

Hooksはツール実行前後にカスタムコマンドを実行する機能。

---

## 設定ファイル場所

| スコープ | 場所 |
|---------|------|
| ユーザー | `~/.claude/settings.json` |
| プロジェクト | `.claude/settings.json` |

---

## イベント種類

| イベント | タイミング |
|---------|----------|
| `PreToolUse` | ツール実行前 |
| `PostToolUse` | ツール実行後 |
| `PermissionRequest` | 権限リクエスト時 |
| `UserPromptSubmit` | プロンプト送信時 |
| `Stop` | 停止時 |
| `SessionStart` | セッション開始時 |

---

## 基本設定例

### ファイル編集後にフォーマット

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit",
      "hooks": [{
        "type": "command",
        "command": "npx prettier --write \"$FILE_PATH\""
      }]
    }]
  }
}
```

### 環境変数

| 変数 | 説明 |
|------|------|
| `$FILE_PATH` | 対象ファイルパス |
| `$TOOL_NAME` | ツール名 |
| `$SESSION_ID` | セッションID |

---

## ユースケース

| ユースケース | 設定例 |
|-------------|--------|
| コード整形 | PostToolUse + prettier |
| Lint実行 | PostToolUse + eslint |
| テスト実行 | PostToolUse + jest |
| 通知 | Stop + slack webhook |
