# Advanced Tool Use

出典: [Anthropic Engineering](https://www.anthropic.com/engineering/advanced-tool-use)

---

## 3つの新機能（2025年11月）

### 1. Tool Search Tool

**課題**: 全ツール定義読み込みで55K～134Kトークン消費

**解決策**: 動的にツール検索、必要なもののみ読み込み

**効果**: 85%トークン削減、精度向上（79.5%→88.1%）

```python
{"name": "get_team_members", "defer_loading": true}
```

### 2. Programmatic Tool Calling

**課題**: 中間結果がコンテキストに蓄積

**解決策**: ClaudeがPythonコードで複数ツールを並列実行

**効果**: 37%トークン削減、レイテンシー大幅短縮

### 3. Tool Use Examples

**課題**: JSONスキーマは使用パターンを表現不可

**解決策**: `input_examples`で具体例を提供

**効果**: 複雑なパラメータ処理の精度が72%→90%に向上

---

## ベストプラクティス

| 機能 | 利用時 | 非推奨 |
|------|--------|--------|
| Tool Search | 定義量>10Kトークン | <10ツール |
| Programmatic | 大規模データセット | 単純な検索 |
| Examples | 複雑なネスト構造 | 標準形式 |

---

## 実装例

```python
client.beta.messages.create(
  betas=["advanced-tool-use-2025-11-20"],
  model="claude-sonnet-4-5-20250929",
  tools=[
    {"type": "tool_search_tool_regex_20251119"},
    {"type": "code_execution_20250825"}
  ]
)
```

---

## 重要

> 「3つの機能を同時に使わない。最大のボトルネックから段階的に対処。」
