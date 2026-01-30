# スタッフタスク管理システム - Claude Code操作ガイド

<context>
## 📅 日付コンテキスト

**今日の日付を常に認識してください。**

- 「今日」「本日」 → システムの現在日時を使用
- タスクファイル: `tasks/active/YYYY-MM-DD.yaml`
- 日付未指定 → 今日の日付を自動使用
- スクリプトは `datetime.now()` で今日を取得

## 👥 スタッフ通称・愛称マッピング

**スタッフは通称・愛称で呼ばれます。YAMLキー（苗字）への変換が必須です。**

| 通称 | 正式名 | YAMLキー |
|------|--------|---------|
| なっちゃん | 江口 那都 | 江口 |
| はるし | 雜賀 晴士 | 雜賀 |
| さら | 野口 器 | 野口 |
| ゆうと | 佐々木 悠斗 | 佐々木 |
| れん | 須加尾 蓮 | 須加尾 |
| りょう | 高橋 諒 | 高橋 |
| ひろふみ | 島田 博文 | 島田 |
| ゆうだい | 平山 優大 | 平山 |
| たかひろ | 細谷 尚央 | 細谷 |
| シャシャ | NANT YOON THIRI ZAW OO | NANT |
| くれは | 原 紅映 | 原 |
| ひさたか | 本間 久隆 | 本間 |

**重要**: スクリプト実行時は必ず**YAMLキー**（苗字）を使用

## ⏰ 勤務時間・休憩時間

**標準勤務時間（ほぼ固定）**
- 勤務時間：10:00 - 19:00（9時間）
- 休憩時間：13:00 - 14:00（1時間）
- 実働時間：8時間

**例外**
- シャシャさん：休憩時間を取らずに6時間連続勤務することがあります
</context>

<instructions>
## ⚠️ 最重要指示

**ユーザーの質問に対して、必ずBashツールでコマンドを実行してください。**
**説明だけで終わることは許されません。まずコマンドを実行し、その結果を基に会話を続けてください。**

## 🚨 必須ルール

### YAML直接操作の禁止
**理由**: データ整合性とバリデーション保証のため

- ❌ `Read(config/*.yaml)` / `Edit(config/*.yaml)` - 直接操作禁止
- ❌ `Read(tasks/**/*.yaml)` / `Edit(tasks/**/*.yaml)` - 直接操作禁止
- ✅ **必ず scripts/ 配下のツールを使用**

### Python実行ルール
- **常に `uv run python` を使用**
- 例: `uv run python scripts/show_status.py`

### システム設計哲学
- **非対話式スクリプト**: 全スクリプトがコマンドライン引数で動作
- **理由**: Claude Codeとの対話 = "ユーザー→Claude→スクリプト実行"（ユーザー→スクリプト（input()）ではない）

## ⚡ 自動実行ルール - キーワード→コマンドマッピング

ユーザーがこれらのキーワードを使った場合、**即座に対応コマンドを実行**してください。

### 1. スタッフ・スキル検索
**キーワード**: 「〜できる人」「〜のスキル」「修理」「査定」「検品」「出品」、スタッフ名

```bash
# スキル検索
uv run python scripts/show_staff.py --skill 修理

# 特定スタッフ
uv run python scripts/show_staff.py --name 細谷

# 全スタッフ
uv run python scripts/show_staff.py
```

### 2. タスク確認
**キーワード**: 「今日のタスク」「進捗」「状況」

```bash
uv run python scripts/show_status.py
```

### 3. タスク追加
**キーワード**: 「タスクを追加」「〜のタスクを〜さんに」

```bash
uv run python scripts/add_task.py --type 査定 --desc "iPhone 14" --staff 細谷
```

### 4. タスク更新
**キーワード**: 「進行中にして」「完了にして」

```bash
# 進行中
uv run python scripts/update_task.py T20251015-001 --status in_progress

# 完了（実績時間付き）
uv run python scripts/update_task.py T20251015-001 --status completed --actual 12
```

### 5. 朝の集計入力
**キーワード**: 「朝の集計」「10時の集計」

```bash
uv run python scripts/input_morning_summary.py --satei 50 --kaifuu 30
```

**自動計算**: 修理（査定の50%）、検品（査定の50%）、出品（査定の80%）、アクティベート（開封と同数）

### 6. 午後の集計入力
**キーワード**: 「13時の集計」「14時の集計」「発送準備」「梱包キット」

```bash
# 13時（発送関連）
uv run python scripts/input_afternoon_summary.py --time 13:00 --hassou-junbi 30

# 14時（梱包キット）
uv run python scripts/input_afternoon_summary.py --time 14:00 --konpou-kit 25
```

### 7. 時間帯別タスク追加
**キーワード**: 「10時のタスク追加」「13時のタスク追加」「16時のタスク追加」

```bash
uv run python scripts/add_scheduled_tasks.py --time 10:00
uv run python scripts/add_scheduled_tasks.py --time 13:00
uv run python scripts/add_scheduled_tasks.py --time 16:00
```

### 8. チェックポイント
**キーワード**: 「14時のチェックポイント」「17時のチェックポイント」

```bash
uv run python scripts/checkpoint.py --time 14:00
uv run python scripts/checkpoint.py --time 17:00
```

### 9. 役割分担決定（完全自動 v2.0）
**キーワード**: 「役割分担」「タスク割り振り」

**🎉 v2.0の新機能**:
- task-types.yamlの全タスクに自動対応（査定・検品・出品・修理・開封等）
- スキルマッチングによる最適割り当て
- ニックネーム自動解決（シャシャ→NANT等）
- 処理能力比率に基づく負荷分散

```bash
# 提案のみ
uv run python scripts/suggest_assignments.py --staff "細谷,江口,シャシャ,佐々木,雜賀"

# 提案＋自動作成（推奨）
uv run python scripts/suggest_assignments.py --staff "細谷,江口,シャシャ,雜賀" --auto-create

# ニックネームでもOK
uv run python scripts/suggest_assignments.py --staff "たかひろ,なっちゃん,シャシャ,ゆうと,はるし" --auto-create
```

**対応タスク**: 査定、検品、出品、修理、開封、アクティベート、梱包キット作成、発送準備、送り状作成、成約仕分

### 10. 欠勤対応
**キーワード**: 「欠勤」「休み」「〜さんが来れない」

```bash
# 提案のみ
uv run python scripts/handle_absence.py 雜賀 --reason "体調不良"

# 提案＋自動再割り当て
uv run python scripts/handle_absence.py 雜賀 --reason "体調不良" --auto-reassign
```

### 11. 日報生成
**キーワード**: 「日報」「今日のレポート」「まとめ」

```bash
uv run python scripts/generate_daily_report.py
```

### 12. データメンテナンス
**キーワード**: 「古いデータを整理」「アーカイブ」「メンテナンス」

```bash
# 定期メンテナンス（月1回推奨）
uv run python scripts/maintenance.py

# 確認モード
uv run python scripts/maintenance.py --dry-run
```

### 13. ダッシュボード（リアルタイム監視）
**キーワード**: 「ダッシュボード」「進捗モニター」「リアルタイム表示」

```bash
# ダッシュボードサーバー起動
uv run python scripts/start_dashboard.py

# カスタムポート指定
uv run python scripts/start_dashboard.py --port 9000
```

**機能**:
- リアルタイム進捗表示（5秒ごと自動更新）
- スタッフ別完了率を視覚化
- 自動警告検出（滞留タスク、未割当など）
- テレビモニター表示に最適化

**アクセス**: ブラウザで `http://127.0.0.1:8000/monitor` を開く

---

## 📚 詳細リファレンス

- **コマンド一覧・使用例**: [README.md](README.md)
- **1日の業務フロー**: [claudedocs/workflow.md](claudedocs/workflow.md)
- **トラブルシューティング**: [claudedocs/troubleshooting.md](claudedocs/troubleshooting.md)
- **テストガイド**: [claudedocs/testing-guide.md](claudedocs/testing-guide.md)
- **スタッフ追加手順**: [claudedocs/staff-addition.md](claudedocs/staff-addition.md)
- **タスク種別定義**: [config/task-types.yaml](config/task-types.yaml)
- **インシデント管理**: [docs/incidents/INDEX.md](docs/incidents/INDEX.md)
- **各コマンドの詳細**: `uv run python scripts/xxx.py --help`

---

## 🔧 インシデント管理（問題・改善案の追跡）

### インシデントの確認
**キーワード**: 「未解決のインシデント」「問題一覧」「インシデントを見て」

インシデントは`docs/incidents/`で管理:
- **open/**: 未着手・進行中のインシデント
- **resolved/**: 解決済みのインシデント
- **INDEX.md**: 全インシデントの一覧

### 新規インシデントの作成

1. `docs/incidents/template.md`をコピー
2. `docs/incidents/open/XXX-title.md`として保存
3. `docs/incidents/INDEX.md`を更新

または Claude Code に依頼:
```
"新しいインシデントを作成して。タイトルは〜"
```

### インシデント解決時

1. ファイルを`open/`から`resolved/`に移動
2. `INDEX.md`を更新（Resolved セクションに追加）

または Claude Code に依頼:
```
"XXXのインシデントを解決済みにして"
```

</instructions>

最終更新: 2025-10-30（公式ベストプラクティスに基づき圧縮）
