---
name: yamato-login
description: ヤマトビジネスメンバーズにログインする。「ヤマトにログイン」「クロネコログイン」「B2クラウドを開いて」と言われた時に使用。
---

# ヤマトビジネスメンバーズ ログインスキル

Playwright MCPを使用してヤマトビジネスメンバーズにログインする。

## 前提条件

- Playwright MCPが設定済みであること
- 認証情報ファイル（`.claude/credentials/yamato.json`）が存在すること

## 認証情報ファイル形式

`.claude/credentials/yamato.json`:
```json
{
  "customer_code": "035829605802",
  "password": "your_password",
  "user_id": ""
}
```

| フィールド | 説明 |
|-----------|------|
| customer_code | お客様コード（半角数字9桁〜12桁） |
| password | パスワード（半角英数字8桁〜12桁） |
| user_id | 個人ユーザーID（任意、半角英数字6桁〜20桁） |

## ログイン手順

### 1. ログインページに移動

```
URL: https://bmypage.kuronekoyamato.co.jp/bmypage/servlet/jp.co.kuronekoyamato.wur.hmp.servlet.user.HMPLGI0010JspServlet
```

### 2. 認証情報を入力

1. **お客様コード入力欄**（ref: textbox "000000000000"）に `customer_code` を入力
2. **パスワード入力欄**（ref: textbox "パスワード"）に `password` を入力
3. **個人ユーザーID入力欄**（任意、ref: textbox "00000000"）に `user_id` を入力（設定されている場合のみ）

### 3. ログインボタンをクリック

- **ログインボタン**（ref: link "ログイン"）をクリック

### 4. ログイン成功の確認

ログイン成功時、以下が表示される：
- ページタイトル: 「ヤマトビジネスメンバーズ」
- 会社名が表示される（例: 株式会社エコット）
- 発送情報グラフが表示される

## エラーハンドリング

| エラー | 対処 |
|--------|------|
| パスワード誤り | 「パスワードが正しくありません」→ 認証情報を確認 |
| お客様コード不明 | 「お客様コードのお問い合わせ」リンクを案内 |
| 利用時間外 | 利用可能時間 7:00〜25:00（B2クラウドは4:00〜） |
| 仮パスワード時間外 | 仮パスワードは22:00まで |

## 利用可能なサービス（ログイン後）

- 送り状発行システムB2クラウド
- Web請求書提供サービス
- 集荷依頼
- 荷物追跡
- YBM For Developers

## 使用例

```
ユーザー: ヤマトにログインして
Claude: [このスキルを実行]

ユーザー: B2クラウドで送り状を作りたい
Claude: [ログイン後、B2クラウドへ移動]
```

## 注意事項

- 認証情報は `.claude/credentials/` に保存し、gitignoreに追加すること
- セッションはPlaywrightプロファイルで永続化される（`~/.playwright-profiles/claude-workspace/`）
