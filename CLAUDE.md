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

### エンジニアリングブログ（docs/engineering/）

| ドキュメント | 内容 |
|-------------|------|
| [long-running-agents.md](docs/engineering/long-running-agents.md) | 長時間エージェントのハーネス |
| [advanced-tool-use.md](docs/engineering/advanced-tool-use.md) | 高度なツール使用 |
| [code-execution-mcp.md](docs/engineering/code-execution-mcp.md) | MCPでのコード実行 |
| [claude-code-sandboxing.md](docs/engineering/claude-code-sandboxing.md) | サンドボックス化 |
| [agent-skills.md](docs/engineering/agent-skills.md) | Agent Skills |
| [claude-agent-sdk.md](docs/engineering/claude-agent-sdk.md) | Agent SDK |
| [context-engineering.md](docs/engineering/context-engineering.md) | コンテキストエンジニアリング |
| [postmortem.md](docs/engineering/postmortem.md) | 障害事後分析 |
| [writing-tools-for-agents.md](docs/engineering/writing-tools-for-agents.md) | エージェント向けツール設計 |
| [desktop-extensions.md](docs/engineering/desktop-extensions.md) | Desktop Extensions |
| [multi-agent-research-system.md](docs/engineering/multi-agent-research-system.md) | マルチエージェントシステム |
| [think-tool.md](docs/engineering/think-tool.md) | Thinkツール |
| [swe-bench-sonnet.md](docs/engineering/swe-bench-sonnet.md) | SWE-bench結果 |
| [building-effective-agents.md](docs/engineering/building-effective-agents.md) | 効果的なエージェント構築 |
| [contextual-retrieval.md](docs/engineering/contextual-retrieval.md) | Contextual Retrieval |

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
