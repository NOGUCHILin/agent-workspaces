# スタッフタスク管理システム

出勤スタッフに対する日次業務タスク（査定・検品・出品・修理）の割り振りと進捗管理システム

## 概要

このプロジェクトは、Claude Codeとの対話を通じて効率的にタスク管理を行うために設計されています。
YAML形式の構造化データと Pydantic によるバリデーションにより、データ破損を防ぎながら柔軟な運用を実現します。

## 特徴

- **Claude Code最適化** - 対話的な編集・クエリが容易
- **厳格なバリデーション** - Pydantic v2によるデータ品質保証
- **段階的実装** - 最小限から始めて必要に応じて拡張
- **軽量設計** - ファイルベース、データベース不要

## プロジェクト構造

```
work/staff-task-system/
├── CLAUDE.md              # Claude Code操作ガイド ★重要
├── README.md              # このファイル
│
├── config/                # マスタデータ
│   ├── staff.yaml        # スタッフ情報・スキル定義
│   ├── task-types.yaml   # タスク種別定義
│   └── schedule.yaml     # シフト・出勤予定
│
├── tasks/                 # 日次タスクデータ
│   ├── active/           # 今日のタスク
│   └── archive/          # 過去のタスク（月別）
│
├── scripts/               # 自動化ツール
│   ├── models.py         # Pydanticモデル定義
│   └── validate.py       # バリデーションツール
│
└── templates/             # 生成用テンプレート（今後追加）
```

## セットアップ

### 1. 依存関係インストール

```bash
cd work/staff-task-system
uv sync
```

### 2. バリデーション確認

```bash
cd work/staff-task-system
uv run python scripts/validate.py --all
```

期待される出力:
```
✓ config/staff.yaml: OK
✓ config/task-types.yaml: OK
✓ config/schedule.yaml: OK

結果: 3/3 ファイルが正常
```

## 使い方

### Claude Codeでの基本操作

**スタッフ情報の確認:**
```
"スタッフ一覧を見せて"
"細谷さんのスキル情報を教えて"
```

**スタッフ情報の更新:**
```
"細谷さんの1日最大タスク数を25に変更"
"雜賀さんに10/20の休暇を追加"
```

**タスク作成:**
```
"今日のタスクを作成して。iPhone 14の査定を細谷さんに"
```

**タスク状態更新:**
```
"T20251015-001を進行中にして"
"T20251015-002を完了にして、実績時間は12分"
```

詳しい操作方法は [CLAUDE.md](CLAUDE.md) および [1日の業務フロー](claudedocs/workflow.md) を参照してください。

## コマンドクイックリファレンス

### タスク操作

```bash
# タスク一覧
uv run python scripts/show_status.py

# タスク追加
uv run python scripts/add_task.py --type 査定 --desc "iPhone 14" --staff 細谷

# タスク更新
uv run python scripts/update_task.py T20251015-001 --status in_progress
uv run python scripts/update_task.py T20251015-001 --status completed --actual 12
```

### スタッフ情報

```bash
# 全スタッフ
uv run python scripts/show_staff.py

# 特定スタッフ
uv run python scripts/show_staff.py --name 細谷

# スキル検索
uv run python scripts/show_staff.py --skill 修理

# スキルマトリックス表示
uv run python scripts/show_skill_matrix.py
```

### 朝の集計（10:00）

```bash
# 集計入力（非対話式）
uv run python scripts/input_morning_summary.py --satei 50 --kaifuu 30

# 10時のタスク追加
uv run python scripts/add_scheduled_tasks.py --time 10:00

# 役割分担の提案
uv run python scripts/suggest_assignments.py --staff "細谷,江口,シャシャ,佐々木,雜賀"

# 役割分担＋タスク自動作成
uv run python scripts/suggest_assignments.py --staff "細谷,江口,シャシャ,雜賀" --auto-create

# 集計確認
uv run python scripts/show_morning_summary.py
```

### 午後の集計

```bash
# 13時の集計（発送関連）
uv run python scripts/input_afternoon_summary.py --time 13:00 --hassou-junbi 30
uv run python scripts/add_scheduled_tasks.py --time 13:00

# 14時の集計（梱包キット）
uv run python scripts/input_afternoon_summary.py --time 14:00 --konpou-kit 25

# 16時のタスク追加（梱包キット）
uv run python scripts/add_scheduled_tasks.py --time 16:00
```

### チェックポイント

```bash
# 14時チェックポイント（午前の進捗確認）
uv run python scripts/checkpoint.py --time 14:00

# 17時チェックポイント（終業確認）
uv run python scripts/checkpoint.py --time 17:00
```

### 突発対応

```bash
# 欠勤対応（提案のみ）
uv run python scripts/handle_absence.py 雜賀 --reason "体調不良"

# 欠勤対応（自動再割り当て）
uv run python scripts/handle_absence.py 雜賀 --reason "体調不良" --auto-reassign

# フィードバック記録
uv run python scripts/add_feedback.py 雜賀 "修理ペースが遅い。午後は簡単な案件から"
```

### レポート・分析

```bash
# 日報生成
uv run python scripts/generate_daily_report.py

# 週次分析
uv run python scripts/analyze_history.py --period week

# 月次分析
uv run python scripts/analyze_history.py --period month
```

### データメンテナンス

```bash
# 定期メンテナンス（月1回推奨）
uv run python scripts/maintenance.py

# アーカイブのみ実行
uv run python scripts/archive_old_tasks.py --days 30

# 確認モード
uv run python scripts/maintenance.py --dry-run
```

### バリデーション

```bash
# 全ファイル検証
uv run python scripts/validate.py --all

# 特定ファイル検証
uv run python scripts/validate.py config/staff.yaml
```

## データ形式

### スタッフ情報（config/staff.yaml）

```yaml
staff:
  細谷:
    full_name: "細谷さん"
    employee_id: "EMP001"
    skills:
      査定:
        level: 3              # 1-3の3段階
        speed_factor: 1.2     # 1.0が標準
        certification: true
    constraints:
      max_tasks_per_day: 20
      preferred_task_types: [査定, 検品]
```

### タスク情報（tasks/active/YYYY-MM-DD.yaml）

```yaml
metadata:
  date: "2025-10-15"
  generated_at: "2025-10-15T08:30:00+09:00"

tasks:
  - id: "T20251015-001"
    type: 査定
    description: "iPhone 14 Pro 256GB"
    assigned_to: 細谷
    status: pending           # pending | in_progress | completed
    priority: high            # low | medium | high
    estimated_minutes: 15
```

## 実装状況

### Phase 1: 基盤構築 ✅ 完了
- [x] ディレクトリ構造
- [x] マスタデータ（YAML形式）
- [x] Pydanticモデル
- [x] バリデーションツール
- [x] タスク表示ツール（show_status.py）
- [x] スタッフ情報表示（show_staff.py）
- [x] タスク追加ツール（add_task.py）
- [x] タスク更新ツール（update_task.py）
- [x] CLAUDE.md（操作ガイド）
- [x] README.md

### Phase 2: 朝の集計・進捗管理 ✅ 完了
- [x] 朝の集計入力（input_morning_summary.py）
- [x] 朝の集計表示（show_morning_summary.py）
- [x] チェックポイント進捗確認（checkpoint.py）
- [x] 一括タスク作成（bulk_create_tasks.py）
- [x] 役割分担AI提案（suggest_assignments.py）
- [x] フィードバック記録（add_feedback.py）

### Phase 3-A: 突発対応 ✅ 完了
- [x] 欠勤対応・タスク再割り当て（handle_absence.py）
- [x] スキルマトリックス表示（show_skill_matrix.py）

### Phase 3-B: 分析機能 ✅ 完了
- [x] 日報自動生成（generate_daily_report.py）
- [x] 作業履歴分析（analyze_history.py）

### Phase 4: 外部連携 ✅ 完了
- [x] Kintone連携（fetch_from_kintone.py）
- [x] Slack通知連携（notify_slack.py）

### Phase 5: データメンテナンス ✅ 完了
- [x] 日付コンテキスト自動注入（CLAUDE.md）
- [x] 自動アーカイブスクリプト（archive_old_tasks.py）
- [x] 定期メンテナンススクリプト（maintenance.py）
- [x] ディスク使用量レポート機能

**🎉 全フェーズ実装完了！**

## スタッフ情報

現在登録されているスタッフ:

| スタッフ | 査定 | 検品 | 出品 | 修理 | 備考 |
|---------|------|------|------|------|------|
| 細谷さん | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | - | 査定エキスパート |
| 江口さん | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | - | 検品が得意 |
| シャシャさん | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | - | 出品スペシャリスト |
| 佐々木さん | ⭐⭐ | ⭐⭐ | ⭐⭐ | - | オールラウンダー |
| 雜賀さん | ⭐⭐⭐ | - | - | ⭐⭐⭐ | 修理専門 |

## トラブルシューティング

### バリデーションエラー

```bash
# 詳細エラー確認
cd work/staff-task-system
uv run python scripts/validate.py config/staff.yaml --verbose
```

よくあるエラー:
- インデント不正 → 2スペース統一を確認
- 必須フィールド欠如 → エラーメッセージで指摘されたフィールドを追加
- パターン不一致 → 社員番号（EMP001形式）、タスクID（T20251015-001形式）を確認

### Pydanticインポートエラー

```bash
cd work/staff-task-system
uv sync
```

## 関連ドキュメント

- [CLAUDE.md](CLAUDE.md) - Claude Code操作ガイド（必読）
- [1日の業務フロー](claudedocs/workflow.md) - 標準的な業務フロー
- [トラブルシューティング](claudedocs/troubleshooting.md) - 問題解決ガイド
- [テストガイド](claudedocs/testing-guide.md) - テスト実行方法
- [スタッフ追加手順](claudedocs/staff-addition.md) - 新規スタッフ登録方法
- [インシデント管理](docs/incidents/INDEX.md) - 問題・改善案の進捗管理

## ライセンス

社内利用のみ

---

最終更新: 2025-10-15
作成者: Claude Code
