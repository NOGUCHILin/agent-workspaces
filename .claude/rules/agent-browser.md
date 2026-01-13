# agent-browser ルール

## ブラウザ操作

「ブラウザ開いて」「ブラウザで確認」「画面見せて」等の指示があった場合:
- agent-browserを使用してブラウザを操作する
- `npx agent-browser` または `./node_modules/.bin/agent-browser` で実行

## 基本ワークフロー

**注意: 常に `--headed` を付けてブラウザを表示する**

```bash
npx agent-browser open <url> --headed  # ページを開く（表示モード）
npx agent-browser snapshot -i          # インタラクティブ要素を取得（@e1, @e2...）
npx agent-browser click @e1            # refで要素をクリック
npx agent-browser fill @e2 "text"      # refで入力
npx agent-browser close                # ブラウザを閉じる
```

## セッション（複数ブラウザ）

```bash
npx agent-browser --session agent1 open site-a.com --headed
npx agent-browser --session agent2 open site-b.com --headed
```

## 認証状態の保存・復元

```bash
npx agent-browser state save auth.json   # 認証状態を保存
npx agent-browser state load auth.json   # 認証状態を復元
```

## Vercel固定URL（重要）

**セッション維持のため、デプロイごとのURLではなく固定エイリアスを使用すること。**

```bash
# 固定エイリアス一覧を取得（これを使う）
vercel alias ls

# デプロイ一覧（参考用）
vercel list --prod
```

## URL推測禁止

**URLを推測・生成してはいけない。必ず以下の方法で確認すること:**

| サービス | 確認方法 |
|---------|---------|
| Vercel | `vercel alias ls` で固定URLを取得 |
| Railway | `railway status` でURLを確認 |
| その他 | CLIコマンドまたはユーザーに確認 |

## 認証が必要な場合

1. 保存済み状態があれば `state load` で復元
2. なければユーザーにログインを依頼
3. ログイン後 `state save` で保存
