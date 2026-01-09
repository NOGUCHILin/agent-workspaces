# claude-code-workspaces

Claude Codeで複数プロジェクト・ブランチを管理するワークスペース

## 参考ドキュメント

| 外部リンク | ローカル |
|-----------|---------|
| [Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices) | [docs/workflows.md](docs/workflows.md) |
| [Claude Code Docs](https://code.claude.com/docs/en/overview) | [docs/claude-code-overview.md](docs/claude-code-overview.md) |
| [GitHub](https://github.com/anthropics/claude-code) | [docs/github-readme.md](docs/github-readme.md) |

## ディレクトリ構造

```
projects/
  {project-name}/
    worktrees/
      {branch-name}/
        CLAUDE.md      # ブランチ固有設定
        .claude/       # Claude設定
        docs/          # ドキュメント
        repo/          # git worktree（.gitignore対象）
```
