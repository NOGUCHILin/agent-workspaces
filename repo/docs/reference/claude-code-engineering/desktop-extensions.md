# Desktop Extensions

出典: [Anthropic Engineering](https://www.anthropic.com/engineering/desktop-extensions)

---

## 概要

Desktop Extensionsは、MCPサーバーを**ワンクリックインストール**するパッケージング形式。
非技術者ユーザーにもMCPサーバーへのアクセスを提供。

---

## 解決する問題

- Node.js/Python等のインストール必須
- JSONファイルの手動編集
- 依存関係の競合管理
- サーバー発見の困難性
- 手動更新プロセス

---

## .mcpbファイル構造（ZIPアーカイブ）

```
extension.mcpb
├── manifest.json       # メタデータ・設定
├── server/             # MCPサーバー実装
├── dependencies/       # 依存パッケージ
└── icon.png            # オプション
```

---

## 開発ステップ

```bash
# 1. マニフェスト生成
npx @anthropic-ai/mcpb init

# 2. ユーザー入力定義（APIキー、権限等）

# 3. パッケージ化
npx @anthropic-ai/mcpb pack

# 4. テスト
# Claude Desktopにドラッグ＆ドロップ
```

---

## ユーザー設定

- OSキーチェーンに自動保存
- テンプレート変数で展開: `${user_config.api_key}`

---

## オープンソース

MCPB仕様・ツールチェーン・参照実装をオープンソース化。
他のAIデスクトップアプリにも互換性提供。
