# Contextual Retrieval

出典: [Anthropic Engineering](https://www.anthropic.com/engineering/contextual-retrieval)

---

## 問題

従来のRAGではチャンク化で文脈情報が失われる。

例: 「売上成長率は3%」→ どの企業のいつの時期か不明確

---

## 解決策

チャンク化前に、チャンク固有の説明的文脈を追加。

```
"This chunk is from an SEC filing on ACME corp's performance in Q2 2023"
```

---

## 実装

Claude 3 Haikuで自動文脈生成:
- 1文書あたり約50-100トークンの説明文追加
- プロンプトキャッシングで**$1.02/百万トークン**

---

## 成果

| 手法 | 検索失敗率削減 |
|------|---------------|
| Contextual Embeddings単独 | 35%削減（5.7%→3.7%） |
| Embeddings + BM25併用 | 49%削減（5.7%→2.9%） |
| + Reranking | **67%削減**（5.7%→1.9%） |

---

## 考慮事項

| 項目 | 推奨 |
|------|------|
| 知識ベース < 200Kトークン | プロンプト全体埋め込みの方が効率的 |
| 埋め込みモデル | Gemini・Voyageが特に効果的 |
| 取得チャンク数 | 20個が最適（5・10個より優良） |
