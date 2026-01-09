---
name: create-worktree
description: 既存プロジェクトに新しいブランチ用ワークツリーを作成する。「ワークツリー作って」「新しいブランチで作業したい」「feature-xブランチを追加して」と言われた時に使用。
---

# 使用手順

1. プロジェクト名を確認（projects/配下に存在するか）
2. ブランチ名をヒアリング
3. `scripts/setup.sh` を実行
4. 作成結果を報告

# 実行コマンド

```bash
.claude/skills/create-worktree/scripts/setup.sh <project-name> <branch-name>
```

# 作成される構造

```
projects/{project-name}/worktrees/{branch-name}/
├── CLAUDE.md      # ブランチ固有の設定
├── .claude/       # ブランチ固有のrules/skills
├── docs/          # ブランチ固有のドキュメント
└── repo/          # git worktree（実際のコード）
```

# 注意事項

- ブランチ名とワークツリー名は同一にする
- repo/内で `git worktree add` を実行する
- 既存のworktreeがある場合はエラーを返す
