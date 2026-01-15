# Git操作ルール

## 重要: 作業ディレクトリ

このワークスペースでは、コードは`repo/`ディレクトリ内にあります。

**git操作は必ず`repo/`内で実行してください。**

```bash
# 正しい
cd repo && git status
cd repo && git fetch origin && git rebase origin/main

# 間違い（実行しないこと）
git status
git fetch origin
```

## 理由

- worktree/直下は設定ファイル用（CLAUDE.md, .claude/, docs/）
- repo/がgit worktreeの実体
- worktree/でgit操作すると不整合が発生する

## ブランチ更新手順

```bash
cd repo
git fetch origin
git rebase origin/main  # または git merge origin/main
```

## コミット手順

```bash
cd repo
git add .
git commit -m "メッセージ"
git push origin HEAD
```
