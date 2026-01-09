---
name: manage-workspace
description: プロジェクトとワークツリーを作成・管理する。「新しいプロジェクト作って」「ワークツリー追加して」「ブランチで作業したい」と言われた時に使用。構造検証も自動実行。
---

# 使用手順

## ワークツリー追加時

1. プロジェクト名をヒアリング
2. ブランチ名をヒアリング
3. `scripts/setup.sh <project> <branch>` を実行
4. 結果を報告

## 構造検証のみ実行時

1. `scripts/validate.sh [project]` を実行
2. 結果を報告

# コマンド

```bash
# プロジェクト+ワークツリー作成（プロジェクトがなければ自動作成）
.claude/skills/manage-workspace/scripts/setup.sh <project-name> <branch-name>

# 構造検証（全体または特定プロジェクト）
.claude/skills/manage-workspace/scripts/validate.sh [project-name]
```

# 作成される構造

```
projects/{project-name}/
└── worktrees/
    └── {branch-name}/
        ├── CLAUDE.md      # ブランチ固有の設定
        ├── .mcp.json      # Playwright MCP設定（自動生成）
        ├── .claude/       # ブランチ固有のrules/skills
        ├── docs/specs/    # 仕様書（Kiro形式）
        └── repo/          # git worktree（実際のコード）
```

# 検証項目

- projects/配下の構造が正しいか
- 必須ディレクトリ（.claude, docs, repo）の存在
- CLAUDE.mdの存在
- ワークツリー名とブランチ名の一致
