---
name: search
description: 情報を検索する。「調べて」「検索して」「最新情報」と言われた時に使用。目的に応じてContext7/Gemini CLI/Playwright MCPを自動選択。
---

# 検索フロー

1. ユーザーの検索目的を特定
2. 下記テーブルに従いツール選択
3. 実行・結果報告

# ツール選択

| 目的 | 1st選択 | フォールバック |
|------|---------|----------------|
| ライブラリAPI・使い方 | Context7 MCP | Gemini CLI |
| 速報・トレンド（数時間以内） | Playwright MCP → Grok | - |
| 技術比較・選定 | Gemini CLI | WebSearch |
| エラー解決 | Gemini CLI | WebSearch |
| ベストプラクティス・意見・体験談 | Gemini CLI (`site:reddit.com`) | Playwright MCP → Reddit |
| コード実例 | Context7 MCP | Gemini CLI → GitHub |

# 各ツールの使い方

## Context7 MCP

ライブラリ名でresolve → get-library-docs

## Gemini CLI

```bash
gemini "検索クエリ 情報源のURLも教えて"
gemini "site:reddit.com 検索クエリ 情報源のURLも教えて"  # Reddit検索
```

**重要**: `-p`フラグは非推奨。位置引数を使用すること。

## Playwright MCP → Grok

1. x.com/i/grok にアクセス
2. プロンプト: `{トピック}についてX上を検索して最新情報を教えて`
3. ログイン必要時はユーザーに依頼

## WebSearch

Gemini CLIレート制限時のフォールバック

# 注意事項

- Gemini CLIはX直接アクセス不可（`site:x.com`で公開投稿のみ）
- GrokはX内検索+ウェブ検索を自動実行
- ログイン必要時はユーザーに協力依頼
