# claude-code-workspaces

Claude Codeで複数プロジェクト・ブランチを管理するワークスペース

## 参考ドキュメント

### claude-code-docs/（code.claude.com）

| ドキュメント | 内容 |
|-------------|------|
| [claude-code-overview.md](docs/claude-code-docs/claude-code-overview.md) | 概要・インストール |
| [quickstart.md](docs/claude-code-docs/quickstart.md) | クイックスタート |
| [memory.md](docs/claude-code-docs/memory.md) | CLAUDE.md・メモリ管理 |
| [settings.md](docs/claude-code-docs/settings.md) | 設定ファイル |
| [cli-reference.md](docs/claude-code-docs/cli-reference.md) | CLIコマンド |
| [mcp.md](docs/claude-code-docs/mcp.md) | MCP連携 |
| [hooks.md](docs/claude-code-docs/hooks.md) | Hooks |

### claude-code-engineering/（anthropic.com/engineering）

| ドキュメント | 内容 |
|-------------|------|
| [workflows.md](docs/claude-code-engineering/workflows.md) | 推奨ワークフロー |
| [long-running-agents.md](docs/claude-code-engineering/long-running-agents.md) | 長時間エージェントのハーネス |
| [advanced-tool-use.md](docs/claude-code-engineering/advanced-tool-use.md) | 高度なツール使用 |
| [code-execution-mcp.md](docs/claude-code-engineering/code-execution-mcp.md) | MCPでのコード実行 |
| [claude-code-sandboxing.md](docs/claude-code-engineering/claude-code-sandboxing.md) | サンドボックス化 |
| [agent-skills.md](docs/claude-code-engineering/agent-skills.md) | Agent Skills |
| [claude-agent-sdk.md](docs/claude-code-engineering/claude-agent-sdk.md) | Agent SDK |
| [context-engineering.md](docs/claude-code-engineering/context-engineering.md) | コンテキストエンジニアリング |
| [postmortem.md](docs/claude-code-engineering/postmortem.md) | 障害事後分析 |
| [writing-tools-for-agents.md](docs/claude-code-engineering/writing-tools-for-agents.md) | エージェント向けツール設計 |
| [desktop-extensions.md](docs/claude-code-engineering/desktop-extensions.md) | Desktop Extensions |
| [multi-agent-research-system.md](docs/claude-code-engineering/multi-agent-research-system.md) | マルチエージェントシステム |
| [think-tool.md](docs/claude-code-engineering/think-tool.md) | Thinkツール |
| [swe-bench-sonnet.md](docs/claude-code-engineering/swe-bench-sonnet.md) | SWE-bench結果 |
| [building-effective-agents.md](docs/claude-code-engineering/building-effective-agents.md) | 効果的なエージェント構築 |
| [contextual-retrieval.md](docs/claude-code-engineering/contextual-retrieval.md) | Contextual Retrieval |

### github/（github.com/anthropics/claude-code）

| ドキュメント | 内容 |
|-------------|------|
| [github-readme.md](docs/github/github-readme.md) | リポジトリ概要 |

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
