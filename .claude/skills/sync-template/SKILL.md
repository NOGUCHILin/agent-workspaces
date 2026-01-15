# sync-template スキル

テンプレートリポジトリ（claude-code-worktrees）に設定を同期する。

## 使用タイミング

- ワークスペース設定（.claude/, docs/, CLAUDE.md等）を変更した後
- 「テンプレートに反映」「テンプレートリポジトリに同期」と言われた時

## 実行方法

```bash
.claude/skills/sync-template/sync-to-template.sh "コミットメッセージ"
```

確認なしで実行：
```bash
.claude/skills/sync-template/sync-to-template.sh "コミットメッセージ" --force
```

## 同期対象

| 対象 | 説明 |
|------|------|
| `.claude/skills/manage-workspace` | worktree作成スキル |
| `.claude/skills/sync-template` | このスキル自体 |
| `.claude/rules` | 共通ルール |
| `docs/` | ドキュメント |
| `CLAUDE.md` | プロジェクト説明 |
| `.mcp.json.example` | MCP設定テンプレート |
| `.gitignore` | Git除外設定 |
| `package.json` | 依存関係 |

## 注意

- `projects/`は同期されない（個別プロジェクトデータのため）
- テンプレートリポジトリ: https://github.com/NOGUCHILin/claude-code-worktrees
