# Claude Agent SDK

出典: [Anthropic Engineering](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)

---

## 概要

Claude Code SDKを**Claude Agent SDK**に改名。コーディング以外の広範な適用性を反映。

> 「エージェントにコンピュータを与え、人間のように作業させる」

---

## エージェントループ

```
1. Gather context（コンテキスト収集）
     ↓
2. Take action（アクション実行）
     ↓
3. Verify work（作業検証）
     ↓
   （繰り返し）
```

---

## 主要機能

### Context Gathering

| 方式 | 説明 |
|------|------|
| Agentic search | bash（grep, tail）で情報を知的に読み込み |
| Semantic search | ベクターベース検索（高速） |
| Subagents | 並列処理、分離コンテキスト管理 |
| Compaction | コンテキスト制限接近時の自動要約 |

### Action Tools

| ツール | 用途 |
|--------|------|
| Custom tools | 主要アクション用の特化関数 |
| Bash/scripts | 汎用実行 |
| Code generation | 複雑操作の精密・再利用可能出力 |
| MCPs | 標準化統合（Slack, GitHub, Asana） |

### Work Verification

| 方式 | 説明 |
|------|------|
| Rule-based | コードlint、バリデーションチェック |
| Visual | スクリーンショット、レンダリング |
| LLM-as-judge | セカンダリモデル評価（堅牢性低） |

---

## ユースケース

- 金融エージェント（ポートフォリオ分析）
- パーソナルアシスタント（カレンダー、旅行管理）
- カスタマーサポート（複雑チケット処理）
- リサーチエージェント（大規模ドキュメント統合）

---

## ベストプラクティス

1. 失敗ケースを検証してエージェント評価
2. タスク誤解時は検索API構造を調整
3. 繰り返し失敗には正式バリデーションルール追加
4. 機能成長に合わせ代表的テストセット構築
