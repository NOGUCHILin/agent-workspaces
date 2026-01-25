# eguchinatsu workspace

## 利用可能なスキル

共有スキルは `../../_shared/skills/` にあります。

| スキル | 用途 |
|--------|------|
| manage-workspace | プロジェクト・ワークツリー作成 |
| check-status | 状態確認 |
| search | 情報検索 |
| create-shipping-label | B2 Cloud送り状作成 |
| yamato-login | ヤマト運輸ログイン |
| notify-shipment | 発送通知 |

## プロジェクト管理

```bash
# 新規プロジェクト追加
../../_shared/skills/manage-workspace/scripts/setup.sh <project-name> <branch> <repo-url>
```

## 共有スキルへの貢献

新しいスキルを作成したら `../../_shared/skills/` に追加してpush。
