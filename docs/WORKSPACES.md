# ワークスペース運用ガイド

## 構造

```
claude-code-worktrees/
├── _shared/              ← 全員で共有（スキル、ルール）
│   ├── skills/
│   └── rules/
├── workspaces/
│   ├── sasoli0502/       ← さそりさん用
│   │   ├── claude-workspace/  ← Claude Code起動場所
│   │   └── projects/          ← 個人プロジェクト（.gitignore）
│   └── eguchinatsu/      ← 夏さん用
│       ├── claude-workspace/
│       └── projects/
├── claude-workspace/     ← テンプレート（参考用）
└── docs/
```

## 使い方

### 1. リポジトリをclone

```bash
git clone https://github.com/NOGUCHILin/claude-code-worktrees.git
cd claude-code-worktrees/workspaces/<your-username>/claude-workspace
claude
```

### 2. 最新を取得

```bash
git pull
```

### 3. 共有スキルを使う

スキルは `_shared/skills/` にあり、各ワークスペースからシンボリックリンクで参照されます。

### 4. 新しいスキルを共有

```bash
# _shared/skills/ に直接作成
mkdir _shared/skills/my-new-skill
vim _shared/skills/my-new-skill/SKILL.md

# コミット＆プッシュ
git add _shared/skills/my-new-skill
git commit -m "feat: add my-new-skill"
git push
```

### 5. 個人設定（共有しない）

`*.local.md` や `*.local.json` は `.gitignore` されています。

```bash
# 例: 自分だけのルール
echo "私用ルール" > _shared/rules/my-rule.local.md
```

## プロジェクト管理

各ワークスペースの `projects/` は `.gitignore` されています。
個人のプロジェクトはここに追加してください。

```bash
cd workspaces/<your-username>/projects
# プロジェクトを追加...
```

## 注意

- `git pull` を頻繁に実行して最新を取得
- 同じファイルを同時編集すると競合する可能性あり
- 競合時は `git pull --rebase` で解決
