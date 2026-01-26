---
name: reference-parent
description: 親プロジェクト（my-claude-code-worktrees）の構造・パターンを参照して、一貫性のある開発をサポート。「他のプロジェクトはどうなってる？」「一貫性をチェックして」と言われた時に使用。
---

# 親プロジェクト参照スキル

## 親プロジェクトのパス

```
/Users/noguchilin/my-claude-code-worktrees/
```

## 構造確認コマンド

### 全体構造
```bash
ls -la /Users/noguchilin/my-claude-code-worktrees/
```

### 他プロジェクト一覧
```bash
ls /Users/noguchilin/my-claude-code-worktrees/projects/
```

### 特定プロジェクトの構造確認
```bash
# worktree構造
ls -la /Users/noguchilin/my-claude-code-worktrees/projects/{project}/worktrees/{branch}/

# MCP設定
cat /Users/noguchilin/my-claude-code-worktrees/projects/{project}/worktrees/{branch}/.mcp.json

# Claude Code設定
cat /Users/noguchilin/my-claude-code-worktrees/projects/{project}/worktrees/{branch}/.claude/settings.json
```

### 共有リソース
```bash
# 共有ルール
ls /Users/noguchilin/my-claude-code-worktrees/_shared/rules/

# 共有スキル
ls /Users/noguchilin/my-claude-code-worktrees/_shared/skills/

# claude-workspaceの設定（参考）
ls /Users/noguchilin/my-claude-code-worktrees/claude-workspace/.claude/
```

## 一貫性チェック項目

### 1. worktree構造
各プロジェクトは以下の構造であるべき：
```
projects/{name}/
├── .bare/           # bareリポジトリ
├── .claude/         # プロジェクトレベル設定（任意）
└── worktrees/
    └── {branch}/
        ├── .claude/     # Claude Code設定
        ├── .mcp.json    # MCP設定
        ├── CLAUDE.md    # 説明
        └── repo/        # リポジトリ本体
```

### 2. MCP設定パターン
```json
{
  "mcpServers": {
    "context7": { ... },
    "playwright": {
      "args": ["@playwright/mcp@0.0.54", "--user-data-dir=/Users/{user}/.playwright-profiles/{project}-{branch}"]
    }
  }
}
```

### 3. hooks設定パターン
```json
{
  "hooks": {
    "PreToolUse": [{"matcher": "Edit|Write", "hooks": [{"type": "command", "command": ".claude/scripts/auto-pull.sh"}]}],
    "PostToolUse": [{"matcher": "Edit|Write", "hooks": [{"type": "command", "command": ".claude/scripts/auto-commit.sh"}]}]
  }
}
```

## 比較コマンド

### MCP設定を比較
```bash
for p in /Users/noguchilin/my-claude-code-worktrees/projects/*/worktrees/*/; do
  echo "--- $p ---"
  cat "$p.mcp.json" 2>/dev/null | head -15
done
```

### settings.jsonを比較
```bash
for p in /Users/noguchilin/my-claude-code-worktrees/projects/*/worktrees/*/; do
  echo "--- $p ---"
  cat "$p.claude/settings.json" 2>/dev/null
done
```

## このプロジェクトの特殊性

claude-code-worktreesは他のプロジェクトと異なり、内部にマルチユーザーワークスペース構造を持つ：

```
repo/workspaces/{username}/
├── .claude/         # ユーザー固有設定
├── .mcp.json
├── CLAUDE.md
└── repos/           # ユーザーが管理するリポジトリ群
```
