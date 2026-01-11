---
name: manage-workspace
description: プロジェクトとワークツリーを作成・管理する。「新しいプロジェクト作って」「ワークツリー追加して」「ブランチで作業したい」と言われた時に使用。構造検証も自動実行。
---

# 使用手順

## 新規プロジェクト作成時

1. プロジェクト名をヒアリング
2. リポジトリURLをヒアリング
3. ブランチ名をヒアリング（デフォルト: master/main）
4. `scripts/setup.sh <project> <branch> <repo-url>` を実行

## 既存プロジェクトにworktree追加時

1. プロジェクト名を確認
2. ブランチ名をヒアリング
3. `scripts/setup.sh <project> <branch>` を実行（URLは不要）

## 構造検証のみ実行時

1. `scripts/validate.sh [project]` を実行
2. 結果を報告

# コマンド

```bash
# 新規プロジェクト作成（最初のworktree = clone）
.claude/skills/manage-workspace/scripts/setup.sh myproject master https://github.com/user/repo.git

# 既存プロジェクトにworktree追加（2つ目以降）
.claude/skills/manage-workspace/scripts/setup.sh myproject feature-x

# 構造検証
.claude/skills/manage-workspace/scripts/validate.sh [project-name]
```

# git worktree の仕組み

```
projects/myproject/worktrees/
├── master/repo/      ← 最初にclone（.git本体がここ）
├── feature-x/repo/   ← worktree（軽量、高速切替）
└── bugfix-y/repo/    ← worktree（軽量、高速切替）
```

- 最初のworktree: `git clone` で作成（.git本体を持つ）
- 2つ目以降: `git worktree add` で作成（軽量）
- メリット: ディスク節約、ブランチ切替が高速

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
- git worktreeの状態
