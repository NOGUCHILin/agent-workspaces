# 仕様駆動開発ルール

## 原則

1. **仕様優先**: 実装前に必ず仕様を確認・作成
2. **調査記録**: 調べた内容は research/ に記録
3. **変更追跡**: 仕様変更時は上流ドキュメントも更新

## トリガーキーワード

以下を検出したら仕様確認を開始:
- 計画、プラン、plan
- 仕様、spec
- 設計、design
- 要件、requirement

## 行動ルール

1. **確認**: `docs/specs/` を確認
2. **存在すれば**: 内容を読んで現状把握
3. **なければ**: テンプレートから新規作成を提案

```bash
mkdir -p docs/specs/{feature-name}
cp docs/_templates/*.md docs/specs/{feature-name}/
```

## ディレクトリ構造

```
docs/specs/{feature}/
├── 01-requirements.md  # 何を作るか
├── 02-design.md        # どう作るか
├── 03-tasks.md         # 作業項目
└── research/           # 調査結果
```

## 禁止事項

- `~/.claude/plans/` は使用しない（Claude Code内部用）
- Claude Codeの `/plan` コマンドは使用しない
- テンプレートを無視して自由形式で書かない
