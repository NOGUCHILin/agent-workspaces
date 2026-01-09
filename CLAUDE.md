# claude-code-workspaces

複数プロジェクト・ブランチを管理するワークスペース

## プロジェクト追加時

`projects/{project-name}/worktrees/` を作成せよ。

## ワークツリー追加時

以下の構造で作成せよ:
```
projects/{project-name}/worktrees/{branch-name}/
  ├── CLAUDE.md
  ├── .claude/
  ├── docs/
  └── repo/
```

- ワークツリー名はブランチ名と同一にせよ
- repo/内で `git worktree add . {branch-name}` を実行せよ

## repo/内で作業時

- repo/は独自git管理（親の.gitignoreで除外済み）
- 親のCLAUDE.md設定を継承する

## Claude Code使い方を調べる時

@docs/README.md を参照せよ。
