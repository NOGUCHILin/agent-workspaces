# The "think" Tool

出典: [Anthropic Engineering](https://www.anthropic.com/engineering/claude-think-tool)

---

## 概要

複雑な問題解決能力向上のための「think」ツール。
ツール呼び出しシーケンス中に専用思考スペースを提供。

---

## Extended Thinkingとの違い

| Extended Thinking | Think Tool |
|------------------|------------|
| 応答生成**前**の考察 | ツール結果処理**後**の思考 |

---

## パフォーマンス

| ドメイン | 結果 |
|---------|------|
| 航空業界 | 0.370 → 0.570（54%改善） |
| 小売業界 | 0.783 → 0.812 |
| SWE-Bench | 平均1.6%向上 |

---

## 実装例

```json
{
  "name": "think",
  "description": "複雑な推論やメモリが必要な場合に使用",
  "input_schema": {
    "type": "object",
    "properties": {
      "thought": {
        "type": "string",
        "description": "思考内容"
      }
    },
    "required": ["thought"]
  }
}
```

---

## 使用時機

### 最適な場面
- ツール出力の慎重な分析
- ポリシー遵守が必要な環境
- 多段階の連続判断

### 避けるべき場面
- 単一または並列ツール呼び出し
- 制約が少ない単純なタスク

---

## ベストプラクティス

- ドメイン固有の例を含む明確な指示
- 複雑な実装ガイダンスはシステムプロンプトに配置
