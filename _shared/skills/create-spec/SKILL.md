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
   - ユーザーにヒアリングして要件を明確化
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
