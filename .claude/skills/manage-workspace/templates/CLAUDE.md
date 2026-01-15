# {{PROJECT}} - {{BRANCH}}

## 🚀 セッション開始時

1. `docs/specs/` を確認して仕様状況を把握
2. 各仕様のステータス（draft/in_progress/completed）を確認
3. 作業中のタスクがあれば続行、なければ次のアクションを提案

```bash
# 仕様状況確認
ls -la docs/specs/
```

## このブランチの目的

（ブランチ作成時に記入してください）

## 仕様管理

### 新規仕様の作成

```bash
# 仕様ディレクトリ作成
mkdir -p docs/specs/{feature-name}
cp docs/_templates/01-requirements.md docs/specs/{feature-name}/
cp docs/_templates/02-design.md docs/specs/{feature-name}/
cp docs/_templates/03-tasks.md docs/specs/{feature-name}/
```

### ステータス更新

各仕様ファイルの先頭フロントマターを更新:
```yaml
---
status: in_progress  # draft → in_progress → completed
updated: 2026-01-16
---
```

## 仕様書の場所

| ファイル | 内容 |
|----------|------|
| `docs/specs/{feature}/01-requirements.md` | 要件定義 |
| `docs/specs/{feature}/02-design.md` | 設計 |
| `docs/specs/{feature}/03-tasks.md` | タスク |
| `docs/specs/{feature}/research/` | 調査結果 |

## 作業メモ

（作業中のメモをここに）
