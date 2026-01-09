# claude-code-workspaces

Claude Codeで複数プロジェクト・ブランチを管理するワークスペース

## 参考ドキュメント

### 外部リンク → ローカル

| 外部 | ローカル |
|------|---------|
| [Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices) | [docs/workflows.md](docs/workflows.md) |
| [Overview](https://code.claude.com/docs/en/overview) | [docs/claude-code-overview.md](docs/claude-code-overview.md) |
| [GitHub](https://github.com/anthropics/claude-code) | [docs/github-readme.md](docs/github-readme.md) |

### 機能別ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| [docs/quickstart.md](docs/quickstart.md) | クイックスタート |
| [docs/memory.md](docs/memory.md) | CLAUDE.md・メモリ管理 |
| [docs/settings.md](docs/settings.md) | 設定ファイル |
| [docs/cli-reference.md](docs/cli-reference.md) | CLIコマンド |
| [docs/mcp.md](docs/mcp.md) | MCP連携 |
| [docs/hooks.md](docs/hooks.md) | Hooks |

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
