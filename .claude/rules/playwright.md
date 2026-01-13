# Playwright MCP ルール

## ブラウザ操作

「ブラウザ開いて」「ブラウザで確認」「画面見せて」等の指示があった場合:
- Playwright MCPを使用してブラウザを操作する
- CLIで完了できない場合のフォールバックとしても使用

## Vercel固定URL（重要）

**セッション維持のため、デプロイごとのURLではなく固定エイリアスを使用すること。**

Vercelは毎デプロイで新しいURL（`project-abc123-org.vercel.app`）を生成するが、Cookieはドメイン単位で保存されるため、毎回異なるURLだとログイン状態が引き継がれない。

### URL取得方法

```bash
# 固定エイリアス一覧を取得（これを使う）
vercel alias ls

# デプロイ一覧（参考用）
vercel list --prod
```

### 固定URLの例

| プロジェクト | 固定URL |
|------------|---------|
| dashboard | `dashboard-noguchilins-projects.vercel.app` |
| dashboard | `dashboard-silk-alpha-67.vercel.app` |

❌ 禁止: `dashboard-iol8zdyzi-noguchilins-projects.vercel.app`（デプロイごとに変わる）
✅ 正解: `dashboard-noguchilins-projects.vercel.app`（固定エイリアス）

## URL推測禁止

**URLを推測・生成してはいけない。必ず以下の方法で確認すること:**

| サービス | 確認方法 |
|---------|---------|
| Vercel | `vercel alias ls` で固定URLを取得 |
| Railway | `railway status` でURLを確認 |
| その他 | CLIコマンドまたはユーザーに確認 |

## 認証が必要な場合

ログイン・認証が必要な画面では:
1. ユーザーに協力を依頼する
2. 「ログインをお願いします」と伝える
3. ログイン完了後に作業を継続
