# 検索ルール

## 目的別ツール選択

| 目的 | 1st選択 | フォールバック |
|------|---------|----------------|
| ライブラリAPI・使い方 | Context7 MCP | Gemini CLI |
| 速報・トレンド（数時間以内） | Playwright → Grok (x.com/i/grok) | - |
| 技術比較・選定 | Gemini CLI | WebSearch |
| エラー解決 | Gemini CLI | WebSearch |
| 意見・体験談 | Gemini (`site:reddit.com`) | Playwright → Reddit |
| コード実例 | Context7 | Gemini → GitHub |

## フォールバック順序

1. Gemini CLI（レート制限時）→ WebSearch/WebFetch
2. WebSearch不可 → Playwright MCP でブラウザ操作
3. ログイン必要 → ユーザーに協力依頼

## 注意

- Gemini CLIはX直接アクセス不可（`site:x.com`で公開投稿のみ検索可）
