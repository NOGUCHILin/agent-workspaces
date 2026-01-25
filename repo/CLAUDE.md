# claude-code-worktrees

複数プロジェクト・ブランチを管理するワークスペーステンプレート

## 使い方

自分のワークスペースでClaude Codeを起動:

```bash
cd workspaces/<your-username>
claude
```

## 構造

```
claude-code-worktrees/
├── _shared/           # 共有スキル・ルール
│   ├── skills/
│   └── rules/
├── workspaces/        # ユーザー別ワークスペース
│   ├── eguchinatsu/
│   └── sasoli0502/
├── projects/          # プロジェクト（git worktree）
└── docs/              # ドキュメント
```

## 新規ユーザー追加

`workspaces/`に自分のディレクトリを作成してください。

詳細は [docs/SETUP.md](docs/SETUP.md) を参照。
