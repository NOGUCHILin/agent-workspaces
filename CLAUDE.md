# claude-code-worktrees

マルチユーザー対応のworktree開発環境

## 🚀 セッション開始時（必須）

**セッション開始時、必ず以下を実行してユーザーのワークスペースを確認:**

```bash
# ユーザー名を取得
USER_NAME=$(git config user.name | tr ' ' '-' | tr '[:upper:]' '[:lower:]')
echo "User: $USER_NAME"

# ワークスペース確認
ls -d workspaces/$USER_NAME 2>/dev/null && echo "✓ Workspace exists" || echo "✗ Workspace not found"
```

### 結果に応じたアクション

| 状態 | アクション |
|------|-----------|
| Workspace exists | 「ワークスペースに移動しますか？」→ `cd workspaces/$USER_NAME` |
| Workspace not found | 「ワークスペースを作成しましょう」→ `/setup-workspace` スキルを実行 |

---

## 使い方

### 1. 新規ユーザー（初回のみ）

```bash
/setup-workspace
```

対話的にワークスペースを作成します。

### 2. リポジトリ追加

ワークスペースに移動後:
```bash
../../scripts/add-repo.sh <repo-url> [branch]
```

### 3. worktreeで作業

```bash
cd repos/<repo-name>/worktrees/<branch>
```

---

## ディレクトリ構造

```
claude-code-worktrees/
├── .claude/                  # 共有設定・hooks
├── scripts/                  # セットアップスクリプト
├── workspaces/
│   ├── _template/           # テンプレート
│   └── {username}/          # 各ユーザーのワークスペース
│       ├── .claude/         # ユーザー固有設定
│       ├── CLAUDE.md
│       └── repos/           # 管理するリポジトリ群
│           └── {repo}/
│               ├── .bare/
│               └── worktrees/
```

---

## オーナー向け

リポジトリオーナー（NOGUCHILin）のみ:
- 他ユーザーの作業は自動コミット＆プッシュされる
- 自分の作業は手動コミット
