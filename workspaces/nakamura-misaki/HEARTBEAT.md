# HEARTBEAT.md

## Git同期（毎回最初に実行）

1. `git pull --rebase origin HEAD` で最新取得
2. 変更があれば `git add -A && git commit -m "auto: changes by nakamura-misaki" && git push`

## 定期チェック（2-4回/日）

- [ ] Slack未読確認
- [ ] タスク期限チェック（vault/タスク/タスクボード.md）
- [ ] プロジェクト進捗確認（vault/プロジェクト/）

## 条件付きアクション

| 条件 | アクション |
|------|----------|
| タスク期限 < 24h | 担当者にリマインド送信 |
| メンバー3日以上活動なし | 状況確認メッセージ |
| 深夜(23:00-08:00) | HEARTBEAT_OK（何もしない） |

## 週次タスク

- [ ] 月曜AM: 週次サマリー作成
- [ ] 金曜PM: vault/整理、不要ファイル削除

## 現在の監視対象

- AWS請求調整（期限: 2026-02-05）→ 2/5にAWS返信確認

---

何もなければ `HEARTBEAT_OK` を返す
