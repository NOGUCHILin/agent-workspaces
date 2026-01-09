# Effective Context Engineering for AI Agents

出典: [Anthropic Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

---

## 定義

**Context Engineering**: LLMの限られた注意予算にどのトークンを入れるかをキュレートする技術。

Prompt Engineering（指示の書き方）とは異なり、システム指示、ツール、外部データ、メッセージ履歴を含む全情報状態を管理。

---

## 主要課題: Context Rot

コンテキストウィンドウが大きくなるほど、情報を思い出す精度が低下。

原因:
- Transformerのn²計算関係
- 短いシーケンスに偏った学習データ

> 「LLMには各トークンで消耗する『注意予算』がある」

---

## 実装戦略

| 戦略 | 説明 |
|------|------|
| **System Prompts** | Goldilocks zone: 具体的かつ柔軟に |
| **Tools** | 最小限、重複なし。肥大化は判断を損なう |
| **Just-in-Time Retrieval** | 軽量識別子を維持、実行時に動的読み込み |

---

## 長期ホライズンテクニック

### Compaction
コンテキスト制限接近時に会話を要約、圧縮要約で再開。

### Structured Note-Taking
永続的外部メモリ（NOTES.md）で進捗追跡。

### Sub-Agent Architectures
特化エージェントが集中タスクを処理、凝縮要約をメインコーディネーターに返却。

---

## 指導原則

> 「望む結果の可能性を最大化する、最小のハイシグナルトークンセットを見つけよ」

コンテキストは豊富ではなく、貴重なものとして扱う。
