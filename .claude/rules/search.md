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

## Grok検索プロンプト

速報・トレンド検索時は以下の形式で質問:

```
{トピック}の最新ニュースを教えて
```

より詳細な検索が必要な場合:
```
{トピック}について、X上の最新の反応とウェブの情報を合わせて教えて
```

## 注意

- Gemini CLIはX直接アクセス不可（`site:x.com`で公開投稿のみ検索可）
- GrokはX内検索+ウェブ検索を自動実行する
