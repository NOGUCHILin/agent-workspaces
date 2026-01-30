# ワークスペース共通ルール

## 自動コミット

オーナー（NOGUCHILin）以外のユーザーは、Edit/Write後に自動でコミット&プッシュされます。

## Playwright MCP

各ワークスペースのPlaywrightプロファイルは競合しないよう、ユーザー名で分離されています。

## リポジトリ追加

ワークスペース内でリポジトリを追加する場合：
```bash
../../../scripts/add-repo.sh <repo-url> [branch]
```

## worktreeで作業

```bash
cd repos/<repo-name>/worktrees/<branch>
```
