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
| verify-schedule | スプレッドシートとKOTの固定休確認 |
| input-schedule | KOTに従業員シフトを入力 |
| fix-holiday-pattern | KOTで公休にパターンが入っている場合の修正 |
| open-daily-shipping | 発送業務ワークスペース準備（Notion/BM/kintone） |
| update-progress | kintoneレコード番号一括検索・進捗変更 |
| kintone-login | kintoneログイン（自動使用） |
| open-backmarket | バックマーケット販売者管理ページを開く |
| open-shipping-schedule | Notion発送予定を今日の日付で開く |
| notion-tag-copy | Notionテーブルでタグを下のセルにコピペ |

## プロジェクト管理

```bash
# 新規プロジェクト追加
../../_shared/skills/manage-workspace/scripts/setup.sh <project-name> <branch> <repo-url>
```

## 共有スキルへの貢献

新しいスキルを作成したら `../../_shared/skills/` に追加してpush。

## ブラウザ設定

- 画面配置: 縦並び（画面2が上、画面1が下）
- 作業画面: 画面2（上のモニター）
- ブラウザ表示: 画面1（下のモニター）で最大化

### 「ブラウザを開いて」と言われたら

`about:blank` を開くだけでOK。リサイズ・最大化・スクリーンショットは不要。
