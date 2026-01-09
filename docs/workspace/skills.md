# 利用可能なSkill一覧

## manage-workspace

**用途**: ワークツリーの作成・検証

**トリガー例**:
- 「ワークツリー作って」
- 「新しいブランチで作業したい」
- 「構造チェックして」

**コマンド**:
```bash
# ワークツリー作成
.claude/skills/manage-workspace/scripts/setup.sh <project> <branch>

# 構造検証
.claude/skills/manage-workspace/scripts/validate.sh [project]
```

---

## create-spec

**用途**: 仕様書セットの作成（AWS Kiro形式）

**トリガー例**:
- 「新しいタスク始めたい」
- 「仕様書作って」
- 「要件定義から始めよう」

**コマンド**:
```bash
.claude/skills/create-spec/scripts/init-spec.sh <worktree-path> <spec-name>
```

**作成されるファイル**:
- 01-requirements.md
- 02-design.md
- 03-tasks.md

---

## check-status

**用途**: 全プロジェクトの進捗確認

**トリガー例**:
- 「今どうなってる?」
- 「状況教えて」
- 「進捗確認」

**コマンド**:
```bash
.claude/skills/check-status/scripts/scan-status.sh [project]
```

**推奨**: セッション開始時に実行
