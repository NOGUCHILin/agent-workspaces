# agent-browser ルール

## 基本ワークフロー

```bash
npx agent-browser open <url> --headed  # ページを開く
npx agent-browser snapshot -i          # 要素取得（@e1, @e2...）
npx agent-browser click @e1            # クリック
npx agent-browser fill @e2 "text"      # 入力
npx agent-browser close                # 閉じる
```

## セッション管理

環境変数`AGENT_BROWSER_SESSION`で自動分離される。
手動指定する場合のみ`--session`オプションを使用。

## 認証状態

```bash
npx agent-browser state save auth.json   # 保存
npx agent-browser state load auth.json   # 復元
```

## 注意事項

- 常に`--headed`を付けてブラウザを表示
- URLは推測せず、CLIコマンドで確認する
- 認証が必要な場合はユーザーに協力を依頼
