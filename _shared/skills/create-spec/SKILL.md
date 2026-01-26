---
name: create-spec
description: 新しい仕様書セットを作成する。「新しいタスク始めたい」「仕様書作って」「要件定義から始めよう」と言われた時に使用。AWS Kiro風の仕様駆動開発をサポート。
---

# 使用手順

## 新規spec作成時

1. ワークツリーのパスを確認
2. spec名をヒアリング（例: auth-flow, dashboard-redesign）
3. `scripts/init-spec.sh <worktree-path> <spec-name>` を実行
4. 作成されたファイルを報告

## spec作成後のワークフロー

**順序を守って進める**:

1. **01-requirements.md** を埋める
   - **インタビューモード**: ユーザーが「インタビューして」と言った場合
     - AskUserQuestionを使って詳細なヒアリングを実施
     - 大規模機能では20-40問の質問を繰り返す
     - 回答を元に要件を自動生成
   - **通常モード**: ユーザーが要件を直接伝える場合
     - ヒアリングして要件を明確化
   - 完了したら次へ

2. **02-design.md** を埋める
   - 要件に基づいて設計を決定
   - 完了したら次へ

3. **03-tasks.md** を埋める
   - 実装タスクを分割
   - 完了したら実装開始

## 進捗確認時

各ファイルの「Status:」行を確認:
- `draft` → 作業中
- `completed` → 完了

# コマンド

```bash
# 新規spec作成
.claude/skills/create-spec/scripts/init-spec.sh <worktree-path> <spec-name>

# 例
.claude/skills/create-spec/scripts/init-spec.sh projects/xlm-trader/worktrees/master auth-flow
```

# 作成される構造

```
<worktree>/docs/specs/<spec-name>/
├── 01-requirements.md   # 要件定義
├── 02-design.md         # 設計
└── 03-tasks.md          # タスク
```

# インタビューモード詳細

**トリガー**: 「インタビューして」「質問して詳細詰めて」「仕様を引き出して」

## 質問カテゴリ

1. **目的・背景**: なぜこの機能が必要か、解決したい課題
2. **ユーザー**: 誰が使うか、どんなシナリオで
3. **機能要件**: 具体的に何ができるべきか
4. **非機能要件**: パフォーマンス、セキュリティ、スケーラビリティ
5. **制約**: 技術スタック、予算、納期
6. **エッジケース**: 例外処理、エラー時の挙動
7. **優先度**: MVP vs Nice-to-have

## 質問の進め方

- AskUserQuestionを使い、1回2-4問ずつ質問
- 回答に基づいて次の質問を動的に生成
- 曖昧な回答には深掘り質問
- 十分な情報が集まったら要件書を自動生成

## 参考

- [Anthropic Thariq氏の手法](https://x.com/_nogu66/status/2005645420744318984)
