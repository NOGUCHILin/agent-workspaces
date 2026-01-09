# ワークスペース構造

## 全体構造

```
claude-code-workspaces/
├── CLAUDE.md                    # ワークスペースルール
├── .claude/
│   └── skills/                  # 共通Skill
│       ├── manage-workspace/    # ワークツリー管理
│       ├── create-spec/         # 仕様書作成
│       └── check-status/        # 進捗確認
├── docs/
│   ├── reference/               # 参考資料
│   └── workspace/               # ワークスペース説明（このファイル）
└── projects/
    └── {project-name}/
        └── worktrees/
            └── {branch-name}/
                ├── CLAUDE.md    # ブランチ固有ルール
                ├── .claude/     # ブランチ固有設定
                ├── docs/
                │   └── specs/   # 仕様書（Kiro形式）
                └── repo/        # git worktree（実際のコード）
```

## 階層と継承

```
~/.claude/CLAUDE.md              # グローバル（個人設定）
    ↓ 継承
workspace/CLAUDE.md              # ワークスペース共通
    ↓ 継承
worktree/CLAUDE.md               # ブランチ固有
```

## ディレクトリの役割

| ディレクトリ | 役割 |
|-------------|------|
| projects/ | プロジェクト群 |
| worktrees/ | ブランチごとの作業環境 |
| docs/specs/ | AWS Kiro形式の仕様書 |
| repo/ | 実際のgit worktree（.gitignore対象） |

## 仕様書（specs）構造

```
docs/specs/{spec-name}/
├── 01-requirements.md    # 要件定義
├── 02-design.md          # 設計
└── 03-tasks.md           # タスク
```

順序: requirements → design → tasks
