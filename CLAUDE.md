# claude-code-workspaces

Claude Codeで複数プロジェクト・ブランチを管理するワークスペース

## 参考ドキュメント

- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Claude Code Docs](https://code.claude.com/docs/en/overview)
- [GitHub](https://github.com/anthropics/claude-code)

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
