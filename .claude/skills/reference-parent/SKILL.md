---
name: reference-parent
description: 親プロジェクト（my-claude-code-worktrees）の構造・パターンを参照して、claude-code-worktreesの開発・改善をサポート。「他のプロジェクトはどうなってる？」「一貫性をチェックして」と言われた時に使用。
---

# claude-code-worktrees改善のための親プロジェクト参照

## 目的

親プロジェクト（my-claude-code-worktrees）の設計パターン・ベストプラクティスを学び、claude-code-worktreesの開発・改善に活かす。

## 親プロジェクトのパス

```
/Users/noguchilin/my-claude-code-worktrees/
```

## 改善のための参照ポイント

### 1. 共有リソースの仕組み（_shared/）

親プロジェクトは`_shared/`でルール・スキルを共有している。

```bash
# 共有ルールを確認
cat /Users/noguchilin/my-claude-code-worktrees/_shared/rules/claude-code-config.md

# 共有スキルを確認
ls /Users/noguchilin/my-claude-code-worktrees/_shared/skills/
```

**claude-code-worktreesへの応用:**
- `repo/workspaces/_shared/`を作成して各ユーザー間でルール・スキルを共有できるようにする

### 2. MCP設定のパターン

```bash
# 他プロジェクトのMCP設定を参考にする
cat /Users/noguchilin/my-claude-code-worktrees/projects/xlm-trader/worktrees/master/.mcp.json
```

**ベストプラクティス:**
- Playwrightプロファイルは`{project}-{branch}`形式で競合を防ぐ
- context7は全プロジェクトで共通

### 3. hooks設定のパターン

```bash
# 他プロジェクトのhooks設定を参考にする
cat /Users/noguchilin/my-claude-code-worktrees/projects/xlm-trader/worktrees/master/.claude/settings.json
```

**ベストプラクティス:**
- PreToolUse: 編集前にpull
- PostToolUse: 編集後にcommit & push（オーナー以外）

### 4. worktree構造のパターン

```bash
# 正しい構造の例
ls -la /Users/noguchilin/my-claude-code-worktrees/projects/xlm-trader/worktrees/master/
```

**標準構造:**
```
worktrees/{branch}/
├── .claude/     # Claude Code設定
├── .mcp.json    # MCP設定
├── CLAUDE.md    # 説明
└── repo/        # リポジトリ本体
```

## 改善チェックリスト

claude-code-worktreesを改善する際に確認すべき項目：

### 構造
- [ ] worktree直下はClaude Code設定用、repo/にリポジトリ本体
- [ ] 各ユーザーワークスペースに.claude/settings.jsonがある
- [ ] MCP設定でPlaywrightプロファイルが競合しない

### 共有
- [ ] _shared/でユーザー間共有リソースを管理
- [ ] テンプレートが最新の構造を反映している

### 自動化
- [ ] 自動pull/commit/pushが正しく動作する
- [ ] setup-workspace.shがテンプレートを正しくコピーする

## 比較コマンド

### 親プロジェクトとclaude-code-worktreesの構造比較
```bash
echo "=== 親 ===" && ls /Users/noguchilin/my-claude-code-worktrees/
echo "=== claude-code-worktrees ===" && ls repo/
```

### 他プロジェクトのスキル一覧（参考にできるもの）
```bash
for p in /Users/noguchilin/my-claude-code-worktrees/projects/*/worktrees/*/; do
  skills=$(ls "$p.claude/skills/" 2>/dev/null | tr '\n' ', ')
  [[ -n "$skills" ]] && echo "$(basename $(dirname $(dirname $p))): $skills"
done
```
