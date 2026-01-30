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
| backmarket-create-label | BM注文のB2送り状作成（PDFなし） |
| backmarket-ship | BM発送完了連絡（追跡番号入力） |

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


<task-reminder>
## タスクリマインダールール

### 自動表示ルール
- **作業開始時は、必ず最初の応答で江口那都個人のタスクを表示する**
- 「タスク確認して」と明示的に言われなくても、作業関連の会話では常にタスクを表示
- このルールは絶対に忘れない

### タスク確認時の動作
- **デフォルト**: 江口那都個人のタスク（`<pending-tasks>`セクション）を表示

### 表示フォーマット
- 応答の最後に未完了タスクを表示する
- フォーマット:
  ```
  📋 未完了タスク:
  - タスク名1
  - タスク名2
  - タスク名3
  ```
- タスクがない場合は表示しない
- **完了タスクが発生したら、必ず`<pending-tasks>`セクションから削除する**

### タスクの追加・更新
- 「タスク追加: ○○」と言われたら `<pending-tasks>` に追加
- 「○○ クローズ」と言われたら該当タスクを完了に変更
- タスクの変更は必ずCLAUDE.mdファイルに反映する
</task-reminder>

<pending-tasks>
## 未完了タスク

### 江口那都
- Back Market発送完了CSVインポート機能を作成する（B2クラウド＋BM注文データ突き合わせ）
</pending-tasks>
