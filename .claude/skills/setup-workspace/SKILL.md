# setup-workspace スキル

新規ユーザーのワークスペースを対話的にセットアップする。

## トリガー

- `/setup-workspace`
- 「ワークスペースを作成」「セットアップして」

## 実行手順

### 1. ユーザー名の確認

```bash
USER_NAME=$(git config user.name | tr ' ' '-' | tr '[:upper:]' '[:lower:]')
USER_EMAIL=$(git config user.email)
echo "Name: $USER_NAME"
echo "Email: $USER_EMAIL"
```

ユーザーに確認: 「このユーザー名でワークスペースを作成しますか？」
- 別の名前を使いたい場合は入力してもらう

### 2. ワークスペース作成

```bash
./scripts/setup-workspace.sh <username>
```

### 3. 初期リポジトリの追加（オプション）

ユーザーに質問: 「管理したいリポジトリのURLはありますか？」

ある場合:
```bash
cd workspaces/<username>
../../scripts/add-repo.sh <repo-url>
```

### 4. 完了メッセージ

```
ワークスペースを作成しました！

次のステップ:
1. ワークスペースに移動: cd workspaces/<username>
2. リポジトリを追加: ../../scripts/add-repo.sh <repo-url>
3. worktreeで作業開始: cd repos/<repo>/worktrees/<branch>
```

## 注意事項

- ユーザー名は小文字、スペースはハイフンに変換
- 既存のワークスペースがある場合はエラー
- リポジトリURLはGitHubのHTTPSまたはSSH形式
