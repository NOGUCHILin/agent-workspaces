# {{PROJECT}} - {{BRANCH}}

## 🚀 セッション開始時

1. 仕様状況を確認
2. 作業中のタスクがあれば続行、なければ次のアクションを提案

```bash
# 仕様状況確認
.claude/scripts/scan-specs.sh
```

## このブランチの目的

（ブランチ作成時に記入してください）

## 仕様管理

### 仕様確認

```bash
.claude/scripts/scan-specs.sh
```

出力例:
```
Feature                        | Requirements | Design       | Tasks
------------------------------ | ------------ | ------------ | ------------
001-auth-integration           | in_progress  | draft        | draft
002-payment-feature            | completed    | in_progress  | draft
```

### 新規仕様の作成

```bash
.claude/scripts/create-spec.sh <feature-name>
```

→ `docs/specs/{NNN}-{feature-name}/` が作成される

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
| `docs/specs/{NNN}-{feature}/01-requirements.md` | 要件定義 |
| `docs/specs/{NNN}-{feature}/02-design.md` | 設計 |
| `docs/specs/{NNN}-{feature}/03-tasks.md` | タスク |
| `docs/specs/{NNN}-{feature}/research/` | 調査結果 |

## 作業メモ

（作業中のメモをここに）
