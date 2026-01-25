# agent-browser ルール

## ブラウザ操作

「ブラウザ開いて」「ブラウザで確認」「画面見せて」等の指示があった場合:
- agent-browserを使用してブラウザを操作する
- **必ず`--session $(basename $(pwd))`でworktree名をセッション名として指定**

## 基本ワークフロー

**重要: 全コマンドに`--session $(basename $(pwd))`と`--headed`を付ける**

```bash
# ブラウザを開く
npx agent-browser --session $(basename $(pwd)) open <url> --headed

# 操作
npx agent-browser --session $(basename $(pwd)) snapshot -i
npx agent-browser --session $(basename $(pwd)) click @e1
npx agent-browser --session $(basename $(pwd)) fill @e2 "text"

# 閉じる
npx agent-browser --session $(basename $(pwd)) close
```

## セッション（worktreeごとに分離・自動永続化）

**`--session $(basename $(pwd))`を全コマンドに付けること**

- worktreeごとに別々のブラウザプロファイルを使用
- **Cookie・localStorage等は自動的に永続化される**
- プロファイル保存場所: `~/.playwright-profiles/{session-name}/`

```bash
# セッション確認
npx agent-browser session list
```

## Vercel固定URL（重要）

**デプロイごとのURLではなく固定エイリアスを使用**

```bash
vercel alias ls  # 固定エイリアス一覧
```

## URL推測禁止

| サービス | 確認方法 |
|---------|---------|
| Vercel | `vercel alias ls` |
| Railway | `railway status` |
| その他 | CLIまたはユーザーに確認 |

## 認証が必要な場合

1. ブラウザを開いてログイン状態を確認
2. 未ログインならユーザーにログインを依頼
3. **ログイン後、状態を保存**

## 認証状態の永続化（重要）

セッションだけでは不十分な場合、明示的に状態を保存:

```bash
# ログイン後に状態を保存
npx agent-browser --session $(basename $(pwd)) state save ./auth-state.json

# 次回起動時に状態を読み込み
npx agent-browser --session $(basename $(pwd)) state load ./auth-state.json
npx agent-browser --session $(basename $(pwd)) open <url> --headed
```

**保存場所**: worktreeルート直下の `auth-state.json`（.gitignore推奨）

## ワークフロー記録

操作を記録して再現可能にする:

```bash
# 記録開始
npx agent-browser --session $(basename $(pwd)) trace start ./workflow.zip

# 操作を実行...

# 記録終了
npx agent-browser --session $(basename $(pwd)) trace stop ./workflow.zip
```

記録されたトレースは Playwright Trace Viewer で確認可能
