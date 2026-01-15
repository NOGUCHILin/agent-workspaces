# claude-code-workspaces

複数プロジェクト・ブランチを管理するワークスペース

---

## 🚀 セッション開始時

**ユーザーが「こんにちは」「何ができる?」等と言ったら、まず状態を確認して報告:**

```bash
# 状態確認
.claude/skills/check-status/scripts/scan-status.sh
```

### 報告例

```
【ワークスペース: claude-code-workspaces】
複数のプロジェクト・ブランチを並行管理するワークスペースです。

📊 現在の状態:
- プロジェクト: 2個 (applebuyers_application, xlm-trader)
- アクティブworktree: 12個
- セットアップ: 完了

🔧 できること:
1. 新規プロジェクト/worktree作成
2. 各worktreeの作業状況確認
3. テンプレートリポジトリへの同期

💡 次のアクション:
- 特定のworktreeで作業を開始しますか?
- 新しいプロジェクトを追加しますか?
```

### 未セットアップの場合

```
このワークスペースはまだセットアップが完了していません。

📋 セットアップ手順:
1. cp .mcp.json.example .mcp.json
2. .mcp.jsonを編集してSlackトークン等を設定
3. プロジェクト追加:
   .claude/skills/manage-workspace/scripts/setup.sh <project> <branch> <repo-url>

セットアップを進めますか?
```

---

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
