---
name: check-status
description: 全プロジェクトの進捗状況を確認する。「今どうなってる?」「状況教えて」「進捗確認」と言われた時に使用。セッション開始時にも使用推奨。
---

# 使用手順

1. `scripts/scan-status.sh` を実行
2. 結果をユーザーに報告
3. 次のアクションを提案

# コマンド

```bash
# 全体スキャン
.claude/skills/check-status/scripts/scan-status.sh

# 特定プロジェクトのみ
.claude/skills/check-status/scripts/scan-status.sh <project-name>
```

# 出力例

```
=== Workspace Status ===

[xlm-trader/master]
  specs/auth-flow:
    - 01-requirements: completed
    - 02-design: draft (作業中)
    - 03-tasks: draft
  specs/dashboard:
    - 未着手

[xlm-trader/feature-x]
  specs/refactor:
    - 01-requirements: completed
    - 02-design: completed
    - 03-tasks: draft (3/5 完了)

=== Summary ===
Active specs: 2
Completed specs: 0
```

# 報告後のアクション提案

- 作業中のspecがあれば「続きをやりますか?」
- 全完了なら「新しいタスクを始めますか?」
- 未着手があれば「どれから始めますか?」
