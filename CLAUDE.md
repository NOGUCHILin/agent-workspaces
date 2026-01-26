# agent-workspaces

統一されたマルチユーザーworktree開発環境

## 構造

```
agent-workspaces/
├── workspaces/
│   ├── _template/           # 新規ユーザー用テンプレート
│   └── {username}/          # 各ユーザーのワークスペース
│       ├── .claude/         # Claude Code設定
│       ├── .mcp.json        # MCP設定
│       ├── CLAUDE.md
│       └── repos/           # 管理するリポジトリ群
├── _shared/                 # 共有リソース
│   ├── rules/
│   └── skills/
└── scripts/                 # セットアップスクリプト
```

## 使い方

### 新規ユーザー作成

```bash
./scripts/setup-workspace.sh <username>
```

### リポジトリ追加

```bash
cd workspaces/<username>
../../scripts/add-repo.sh <repo-url> [branch]
```

### worktreeで作業

```bash
cd repos/<repo-name>/worktrees/<branch>
```
