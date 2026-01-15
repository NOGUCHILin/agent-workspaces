# claude-code-workspaces

複数プロジェクト・ブランチを管理するワークスペース

## ワークスペース設計原則

| 概念 | パス | 役割 |
|------|------|------|
| worktreeルート | `projects/{project}/worktrees/{branch}/` | Claude Code起動場所 |
| repo | `projects/{project}/worktrees/{branch}/repo/` | ソースコード（Git管理） |

**重要:**
- Claude Codeは常に **worktreeルート** で開く
- `repo/.claude/` は使用しない（`worktree/.claude/` を使用）

## 設定階層

| 層 | パス | 共有範囲 | 方法 |
|---|------|---------|------|
| ワークスペース共通 | `_shared/` | 全project | → project/.claude/へコピー |
| project共通 | `project/.claude/` | 全worktree | → worktree/.claude/へsymlink |
| worktree個別 | `worktree/.claude/` | 個別 | 直接配置 |

**ディレクトリ構成:**
```
my-claude-code-worktrees/
├── .claude/           ← このワークスペース専用(manage-workspace, check-status)
├── _shared/           ← 全project共通テンプレート(rules, skills)
└── projects/{project}/
    ├── .claude/       ← project共通(_shared/からコピー、カスタマイズ可)
    └── worktrees/{branch}/
        └── .claude/   ← symlink → project/.claude/
```

## 初回セットアップ

```bash
.claude/scripts/setup.sh
```

### 必要な設定

| 設定 | 方法 |
|------|------|
| `.mcp.json` | `.mcp.json.example`をコピーしてトークン設定 |
| Slack Token | https://api.slack.com/apps → OAuth & Permissions |
| Team ID | SlackのURL `app.slack.com/client/Txxxxxxxx/` |

詳細: [docs/SETUP.md](docs/SETUP.md)

## projects/内で作業時

- projects/は独自git管理（親の.gitignoreで除外済み）
- 親のCLAUDE.md設定を継承する

## 参照

- セットアップ: @docs/SETUP.md
- Claude Code参考: @docs/reference/
