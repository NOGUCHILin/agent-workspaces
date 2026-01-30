# タスク管理システム アーキテクチャ提案書

**バージョン**: 1.0
**作成日**: 2025-10-15
**ステータス**: 提案（未実装）
**対象**: Claude Code運用環境での日次業務タスク管理

---

## 📋 目次

1. [エグゼクティブサマリー](#エグゼクティブサマリー)
2. [現状分析](#現状分析)
3. [設計原則](#設計原則)
4. [推奨アーキテクチャ](#推奨アーキテクチャ)
5. [データバリデーション戦略](#データバリデーション戦略)
6. [考慮事項と制約](#考慮事項と制約)
7. [段階的実装計画](#段階的実装計画)
8. [代替案の検討](#代替案の検討)
9. [未解決の質問](#未解決の質問)

---

## エグゼクティブサマリー

### 🎯 目的
出勤スタッフに対する日次業務タスク（査定・検品・出品・修理）の割り振りと進捗管理を、Claude Codeとの対話を通じて効率的に行う。

### 🔑 核心的な問題
現在の構成（Markdown表 + 空ディレクトリ）は、以下の点で不十分：
- **Claude Codeが処理しにくい** - 表のパースと編集にコストがかかる
- **バリデーションが不在** - データ破損リスクが高い
- **ワークフローが未定義** - 「何をすべきか」が不明確
- **拡張性の欠如** - 新機能追加が困難

### ✅ 推奨ソリューション
**構造化データ（YAML）+ Pydanticバリデーション + 軽量Pythonスクリプト**

- **2025年のベストプラクティス準拠** - Pydantic v2、Schema駆動バリデーション
- **Claude Code最適化** - 対話的な編集・クエリが容易
- **段階的実装** - 最小限から始めて必要に応じて拡張
- **低オーバーヘッド** - 複雑なツール不要、ファイルベース

---

## 現状分析

### 📂 現在のディレクトリ構造
```
work/task-management/
├── README.md                    # 概要のみ
├── staff-capabilities.md        # Markdown表形式
├── tasks/                       # 空
├── templates/                   # 空
└── archive/                     # 空
```

### ❌ 問題点の詳細

#### 1. データ形式の問題
```markdown
<!-- staff-capabilities.md -->
| スタッフ | 査定 | 検品 | 出品 | 修理 |
|---------|------|------|------|------|
| 細谷さん | ○ | ○ | ○ | - |
```

**Claude Code視点での課題**:
- ✗ パースコストが高い（正規表現/テーブル解析必要）
- ✗ 編集時の表整形が面倒
- ✗ バリデーション不可能（○と◯の混在、タイポ検出不可）
- ✗ クエリ困難（「修理できる人は？」→全行スキャン）
- ✗ 拡張困難（スキルレベル、経験年数などの追加が大変）

#### 2. アーキテクチャの問題
- **状態管理の欠如** - タスクが「誰に」「いつ」「どの状態」か追跡不可
- **ワークフロー未定義** - 朝・昼・夕方に何をするか不明
- **責任分離の欠如** - データ・ロジック・表示が混在
- **テスト不可能** - スクリプトが存在しないため検証不可

#### 3. 運用上の問題
- **Claude Codeとの対話が非効率** - 毎回「どうやって編集しますか？」の往復
- **人的ミスのリスク** - 手動編集時のタイポ・整形崩れ
- **履歴分析不可** - 過去データからの学習ができない

---

## 設計原則

### 🧭 基本方針

#### 1. **Claude Code First**
> すべての設計判断は「Claude Codeとの対話で使いやすいか」を最優先

- 構造化データ（YAML/JSON）を採用
- 明確なスキーマ定義
- 操作ガイド（CLAUDE.md）の充実

#### 2. **Fail Fast with Clear Errors**
> 間違いは早期に、明確なメッセージで検出

- Pydanticによる厳格なバリデーション
- スキーマ違反は即座にエラー
- ユーザーフレンドリーなエラーメッセージ

#### 3. **Progressive Enhancement**
> 最小限から始めて段階的に機能追加

- Phase 1: マスタデータ + 日次タスクリスト
- Phase 2: 自動割り振りロジック
- Phase 3: 分析・最適化機能

#### 4. **Separation of Concerns**
> データ・ロジック・表示を明確に分離

```
config/   → マスタデータ（週次更新程度）
tasks/    → トランザクションデータ（日次）
scripts/  → ビジネスロジック
templates/ → 生成ルール
```

#### 5. **Keep It Lightweight**
> 複雑なツールやフレームワークは避ける

- 標準ライブラリ + Pydantic + PyYAML のみ
- データベース不要（ファイルベース）
- 外部サービス依存なし

### 🎯 2025年のベストプラクティス（調査結果より）

#### YAML バリデーション
- **Schema駆動アプローチ**: 30%のミス削減効果（調査データ）
- **インデント統一**: 2スペース（タブ禁止）
- **文字列クォート**: 特殊文字・予約語は必ず引用符
- **コメント戦略**: チケット番号・設計文書への参照を記載

#### Pydantic活用
- **Pydantic v2使用**: 最新の型安全性と性能
- **BaseModel継承**: YAML ↔ オブジェクトの双方向変換
- **Enumによる制約**: 不正な値の事前防止
- **カスタムバリデータ**: ビジネスルールの実装

---

## 推奨アーキテクチャ

### 📁 ディレクトリ構造（最終形）

```
work/task-management/
├── CLAUDE.md                      # Claude Code用操作ガイド ★重要
├── README.md                      # 人間用プロジェクト概要
│
├── config/                        # マスタデータ（構造化）
│   ├── staff.yaml                # スタッフ情報・スキル定義
│   ├── task-types.yaml           # タスク種別定義
│   ├── schedule.yaml             # シフト・出勤予定
│   └── validation_rules.yaml    # カスタムバリデーションルール
│
├── tasks/                         # 日次タスクデータ
│   ├── active/
│   │   └── 2025-10-15.yaml      # 今日のタスク
│   └── archive/
│       └── 2025-10/
│           ├── 2025-10-01.yaml
│           └── 2025-10-14.yaml
│
├── scripts/                       # 自動化・ユーティリティ
│   ├── models.py                 # Pydanticモデル定義
│   ├── validate.py               # バリデーション実行
│   ├── assign_tasks.py           # タスク割り振りロジック
│   ├── show_status.py            # 進捗表示
│   ├── daily_report.py           # 日報生成
│   └── utils.py                  # 共通ユーティリティ
│
├── templates/                     # 生成用テンプレート
│   ├── daily-tasks.yaml.j2       # 日次タスク生成
│   └── weekly-report.md.j2       # 週次レポート
│
├── tests/                         # テストコード
│   ├── test_models.py            # モデルのバリデーションテスト
│   ├── test_assign.py            # 割り振りロジックのテスト
│   └── fixtures/                 # テスト用サンプルデータ
│
└── .pre-commit-config.yaml       # YAML自動検証（Git hookとして）
```

### 📄 各ファイルの詳細設計

#### 1. `config/staff.yaml` - スタッフマスタ

```yaml
# スタッフマスタデータ
# 最終更新: 2025-10-15
# 編集時注意: このファイルは scripts/validate.py で検証されます

staff:
  細谷:
    full_name: "細谷さん"
    employee_id: "EMP001"
    skills:
      査定:
        level: 3              # 1=初級, 2=中級, 3=上級
        speed_factor: 1.2     # 1.0が標準、1.2は20%速い
        certification: true   # 資格保持
      検品:
        level: 3
        speed_factor: 1.0
        certification: false
      出品:
        level: 2
        speed_factor: 0.9
        certification: false
    constraints:
      max_tasks_per_day: 20
      preferred_task_types: [査定, 検品]  # 優先的にアサインしたい業務
      unavailable_dates: []                # 休暇予定
    notes: "査定のエキスパート。複雑な案件優先。"

  雜賀:
    full_name: "雜賀さん"
    employee_id: "EMP005"
    skills:
      査定:
        level: 3
        speed_factor: 1.0
        certification: true
      修理:
        level: 3
        speed_factor: 1.3
        certification: true
    constraints:
      max_tasks_per_day: 15    # 修理は時間がかかるため少なめ
      preferred_task_types: [修理]
      unavailable_dates: ["2025-10-20"]
    notes: "修理専門。高難度修理を優先アサイン。"

# グローバル設定
settings:
  working_hours:
    start: "09:00"
    lunch_start: "12:00"
    lunch_end: "13:00"
    end: "18:00"
  default_task_duration:  # 分単位
    査定: 15
    検品: 20
    出品: 10
    修理: 60
```

**設計ポイント**:
- `level`と`speed_factor`の分離 - スキルと速度は別概念
- `constraints`で個別制約を明示
- `notes`で定性的情報を記録（Claude Code用の補足情報）

#### 2. `config/task-types.yaml` - タスク種別定義

```yaml
# タスク種別マスタ
# このファイルで新しい業務タイプを定義可能

task_types:
  査定:
    display_name: "査定"
    description: "端末の状態確認と価格査定"
    required_skills: [査定]
    default_duration_minutes: 15
    priority_base: 2           # 1=低, 2=中, 3=高
    can_parallel: false        # 同時実行可否
    required_tools: [検査ツール, 価格表]

  検品:
    display_name: "検品"
    description: "端末の動作確認と品質チェック"
    required_skills: [検品]
    default_duration_minutes: 20
    priority_base: 2
    can_parallel: true         # 複数台同時検品可能
    required_tools: [検査ツール]

  出品:
    display_name: "出品"
    description: "端末情報の登録と出品作業"
    required_skills: [出品]
    default_duration_minutes: 10
    priority_base: 1
    can_parallel: true
    required_tools: [PC, カメラ]

  修理:
    display_name: "修理"
    description: "端末の修理作業"
    required_skills: [修理]
    default_duration_minutes: 60
    priority_base: 3           # 修理は高優先度
    can_parallel: false
    required_tools: [修理キット, 交換部品]

# 業務間の依存関係
dependencies:
  - from: 査定
    to: 検品
    description: "査定完了後に検品が必要"
  - from: 検品
    to: 出品
    description: "検品完了後に出品可能"
```

**設計ポイント**:
- 拡張性 - 新業務追加が容易
- 依存関係の明示 - ワークフロー制御に利用
- メタデータの充実 - 自動割り振りアルゴリズムで活用

#### 3. `config/schedule.yaml` - シフト管理

```yaml
# 出勤スケジュール
# 毎週月曜に翌週分を更新

schedules:
  "2025-10-15":
    weekday: "水曜日"
    staff: [細谷, 江口, シャシャ, 佐々木, 雜賀]
    special_notes: "通常営業"

  "2025-10-16":
    weekday: "木曜日"
    staff: [細谷, シャシャ, 雜賀]
    special_notes: "江口さん休暇、佐々木さん午後のみ出勤"
    part_time:
      佐々木:
        available_from: "13:00"
        available_to: "18:00"

  "2025-10-17":
    weekday: "金曜日"
    staff: [細谷, 江口, シャシャ, 佐々木, 雜賀]
    special_notes: "繁忙期対応・全員出勤"
    overtime_approved: true

# デフォルトシフトパターン（週次テンプレート）
default_patterns:
  平日:
    staff: [細谷, 江口, シャシャ, 佐々木, 雜賀]
    working_hours: "09:00-18:00"
```

#### 4. `tasks/active/2025-10-15.yaml` - 日次タスク

```yaml
# 日次タスクリスト
# 生成日時: 2025-10-15 08:30:00
# 生成方法: scripts/assign_tasks.py による自動生成

metadata:
  date: "2025-10-15"
  weekday: "水曜日"
  generated_at: "2025-10-15T08:30:00+09:00"
  generated_by: "assign_tasks.py v1.0"
  total_staff: 5
  total_tasks: 12

tasks:
  - id: "T20251015-001"
    type: 査定
    description: "iPhone 14 Pro 256GB シルバー"
    device_id: "DEV-2024-1234"      # 管理番号
    assigned_to: 細谷
    status: completed                # pending | in_progress | completed | cancelled
    priority: high                   # low | medium | high
    estimated_minutes: 15
    actual_minutes: 12
    started_at: "2025-10-15T09:15:00+09:00"
    completed_at: "2025-10-15T09:27:00+09:00"
    notes: "バッテリー最大容量85%"

  - id: "T20251015-002"
    type: 修理
    description: "Galaxy S23 画面修理"
    device_id: "DEV-2024-1235"
    assigned_to: 雜賀
    status: in_progress
    priority: high
    estimated_minutes: 60
    actual_minutes: null
    started_at: "2025-10-15T10:30:00+09:00"
    completed_at: null
    blocked_by: null                 # 他タスクIDを指定（依存関係）
    notes: "交換部品到着済み"

  - id: "T20251015-003"
    type: 検品
    description: "在庫端末10台まとめて検品"
    device_id: "BULK-001"
    assigned_to: null                # 未アサイン
    status: pending
    priority: medium
    estimated_minutes: 120           # 10台×12分
    actual_minutes: null
    started_at: null
    completed_at: null
    can_split: true                  # 複数人で分割可能
    notes: "午後に着手予定"

# 統計情報（自動計算）
statistics:
  by_status:
    pending: 3
    in_progress: 2
    completed: 7
    cancelled: 0
  by_staff:
    細谷: {assigned: 4, completed: 3, in_progress: 1}
    江口: {assigned: 2, completed: 2, in_progress: 0}
    シャシャ: {assigned: 2, completed: 1, in_progress: 1}
    佐々木: {assigned: 3, completed: 1, in_progress: 1}
    雜賀: {assigned: 1, completed: 0, in_progress: 1}
  total_estimated_minutes: 480
  total_actual_minutes: 324
```

**設計ポイント**:
- **一意なタスクID** - `T{date}-{sequential}` 形式
- **nullable フィールド** - 未アサイン・未完了を明示的に表現
- **metadata と statistics** - 自動生成情報を分離
- **依存関係** - `blocked_by` で他タスクとの依存を表現

#### 5. `scripts/models.py` - Pydanticモデル定義

```python
"""
タスク管理システムのデータモデル定義

Pydantic v2を使用した厳密な型定義とバリデーション
"""

from datetime import date, datetime, time
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator, model_validator
import yaml


# ========== Enums ==========

class SkillLevel(int, Enum):
    """スキルレベル"""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3


class TaskStatus(str, Enum):
    """タスク状態"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """タスク優先度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskType(str, Enum):
    """タスク種別"""
    SATEI = "査定"
    KENPIN = "検品"
    SHUPPIN = "出品"
    SHURI = "修理"


# ========== Config Models ==========

class SkillDetail(BaseModel):
    """スキル詳細"""
    level: SkillLevel = Field(..., description="スキルレベル")
    speed_factor: float = Field(1.0, ge=0.1, le=3.0, description="速度係数")
    certification: bool = Field(False, description="資格保持")


class StaffConstraints(BaseModel):
    """スタッフ制約"""
    max_tasks_per_day: int = Field(20, ge=1, le=50, description="1日最大タスク数")
    preferred_task_types: List[TaskType] = Field(default_factory=list)
    unavailable_dates: List[date] = Field(default_factory=list)


class Staff(BaseModel):
    """スタッフ情報"""
    full_name: str = Field(..., min_length=1, description="フルネーム")
    employee_id: str = Field(..., pattern=r"^EMP\d{3}$", description="社員番号")
    skills: Dict[TaskType, SkillDetail] = Field(..., description="保有スキル")
    constraints: StaffConstraints = Field(default_factory=StaffConstraints)
    notes: str = Field("", description="備考")

    @field_validator('skills')
    @classmethod
    def validate_skills(cls, v: Dict[TaskType, SkillDetail]) -> Dict[TaskType, SkillDetail]:
        """最低1つのスキルが必要"""
        if not v:
            raise ValueError("スタッフは最低1つのスキルを持つ必要があります")
        return v


class StaffConfig(BaseModel):
    """スタッフマスタ設定"""
    staff: Dict[str, Staff] = Field(..., description="スタッフマップ")
    settings: Dict = Field(default_factory=dict, description="グローバル設定")

    @classmethod
    def from_yaml(cls, filepath: str) -> 'StaffConfig':
        """YAMLファイルから読み込み"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, filepath: str) -> None:
        """YAMLファイルへ書き込み"""
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(self.model_dump(), f, allow_unicode=True, sort_keys=False)


# ========== Task Models ==========

class Task(BaseModel):
    """タスク"""
    id: str = Field(..., pattern=r"^T\d{8}-\d{3}$", description="タスクID")
    type: TaskType = Field(..., description="タスク種別")
    description: str = Field(..., min_length=1, max_length=200, description="タスク内容")
    device_id: Optional[str] = Field(None, description="端末管理番号")
    assigned_to: Optional[str] = Field(None, description="担当者")
    status: TaskStatus = Field(TaskStatus.PENDING, description="状態")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="優先度")
    estimated_minutes: int = Field(..., ge=1, le=480, description="見積時間（分）")
    actual_minutes: Optional[int] = Field(None, ge=0, description="実績時間（分）")
    started_at: Optional[datetime] = Field(None, description="開始日時")
    completed_at: Optional[datetime] = Field(None, description="完了日時")
    blocked_by: Optional[str] = Field(None, description="依存タスクID")
    can_split: bool = Field(False, description="分割可能")
    notes: str = Field("", max_length=500, description="備考")

    @model_validator(mode='after')
    def validate_timestamps(self):
        """タイムスタンプの整合性チェック"""
        if self.status == TaskStatus.IN_PROGRESS and not self.started_at:
            raise ValueError("進行中タスクにはstarted_atが必要です")
        if self.status == TaskStatus.COMPLETED:
            if not self.started_at or not self.completed_at:
                raise ValueError("完了タスクにはstarted_atとcompleted_atが必要です")
            if self.started_at >= self.completed_at:
                raise ValueError("開始時刻は完了時刻より前である必要があります")
            if not self.actual_minutes:
                raise ValueError("完了タスクにはactual_minutesが必要です")
        return self


class TaskStatistics(BaseModel):
    """タスク統計"""
    by_status: Dict[TaskStatus, int]
    by_staff: Dict[str, Dict[str, int]]
    total_estimated_minutes: int
    total_actual_minutes: int


class DailyTaskList(BaseModel):
    """日次タスクリスト"""
    metadata: Dict = Field(..., description="メタデータ")
    tasks: List[Task] = Field(..., description="タスクリスト")
    statistics: Optional[TaskStatistics] = Field(None, description="統計情報")

    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v: Dict) -> Dict:
        """必須メタデータの検証"""
        required = ['date', 'generated_at']
        for key in required:
            if key not in v:
                raise ValueError(f"metadataに{key}が必要です")
        return v

    @classmethod
    def from_yaml(cls, filepath: str) -> 'DailyTaskList':
        """YAMLファイルから読み込み"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, filepath: str) -> None:
        """YAMLファイルへ書き込み"""
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(self.model_dump(mode='json'), f, allow_unicode=True, sort_keys=False)


# ========== Validation Utilities ==========

def validate_file(filepath: str, model_class: type[BaseModel]) -> tuple[bool, Optional[str]]:
    """
    YAMLファイルをバリデーション

    Returns:
        (成功フラグ, エラーメッセージ)
    """
    try:
        model_class.from_yaml(filepath)
        return True, None
    except Exception as e:
        return False, str(e)
```

**設計ポイント**:
- **Pydantic v2準拠** - 最新のベストプラクティス
- **厳密な制約** - `pattern`, `ge`, `le`, `min_length` などで不正データを防止
- **カスタムバリデータ** - ビジネスルール（開始時刻 < 完了時刻 など）を実装
- **YAML双方向変換** - `from_yaml()` / `to_yaml()` メソッド
- **型安全性** - Enumで許可値を制限

---

## データバリデーション戦略

### 🛡️ 多層防御アプローチ

#### Layer 1: Pydanticモデル（実行時バリデーション）
```python
# 例: タスクID形式の検証
id: str = Field(..., pattern=r"^T\d{8}-\d{3}$")

# 不正な値を入れると...
task = Task(id="invalid-id", ...)
# → ValidationError: String should match pattern '^T\d{8}-\d{3}$'
```

#### Layer 2: pre-commit hook（コミット前自動検証）
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: validate-yaml-syntax
        name: YAML Syntax Check
        entry: yamllint
        language: python
        types: [yaml]

      - id: validate-task-schema
        name: Task Schema Validation
        entry: uv run python scripts/validate.py
        language: system
        files: 'config/.*\.yaml|tasks/.*\.yaml'
```

**効果**: Gitコミット時に自動検証、不正データの混入を防止

#### Layer 3: IDE統合（編集中リアルタイム検証）

**VSCode設定例** (`work/task-management/.vscode/settings.json`):
```json
{
  "yaml.schemas": {
    "./schemas/staff.json": "config/staff.yaml",
    "./schemas/tasks.json": "tasks/**/*.yaml"
  },
  "yaml.validate": true,
  "yaml.format.enable": true
}
```

**効果**: ファイル編集中に赤線で警告、Claude Code実行前に問題発見

#### Layer 4: CI/CD（継続的バリデーション）

将来的にGitHub Actionsなどで自動テスト実行（現時点では不要）

### 📋 バリデーションルールの詳細

#### 必須制約
```yaml
# config/validation_rules.yaml

constraints:
  staff:
    - field: employee_id
      rule: "pattern"
      value: "^EMP\\d{3}$"
      message: "社員番号はEMP001形式である必要があります"

    - field: skills
      rule: "min_items"
      value: 1
      message: "最低1つのスキルが必要です"

    - field: max_tasks_per_day
      rule: "range"
      min: 1
      max: 50
      message: "1日のタスク数は1〜50の範囲で設定してください"

  tasks:
    - field: id
      rule: "pattern"
      value: "^T\\d{8}-\\d{3}$"
      message: "タスクIDはT20251015-001形式である必要があります"

    - field: estimated_minutes
      rule: "range"
      min: 1
      max: 480
      message: "見積時間は1〜480分（8時間）の範囲で設定してください"

    - field: description
      rule: "length"
      min: 1
      max: 200
      message: "タスク説明は1〜200文字で記載してください"

  business_rules:
    - name: "completed_task_requires_actual_time"
      condition: "status == 'completed'"
      requires: ["started_at", "completed_at", "actual_minutes"]
      message: "完了タスクには開始/完了時刻と実績時間が必須です"

    - name: "in_progress_requires_assignment"
      condition: "status == 'in_progress'"
      requires: ["assigned_to", "started_at"]
      message: "進行中タスクには担当者と開始時刻が必須です"

    - name: "time_consistency"
      rule: "started_at < completed_at"
      message: "開始時刻は完了時刻より前である必要があります"
```

### 🔍 バリデーション実行方法

#### 手動検証
```bash
# 全ファイルを検証
uv run python scripts/validate.py --all

# 特定ファイルのみ検証
uv run python scripts/validate.py config/staff.yaml

# 詳細モード（警告も表示）
uv run python scripts/validate.py --verbose

# 出力例
✓ config/staff.yaml: OK
✓ config/task-types.yaml: OK
✗ tasks/active/2025-10-15.yaml: FAILED
  - Task T20251015-002: 完了タスクにactual_minutesが設定されていません
  - Task T20251015-005: 担当者 '田中' はstaff.yamlに存在しません
```

#### Claude Codeでの使用
```
User: "今日のタスクファイルをチェックして"

Claude Code:
1. scripts/validate.py を実行
2. エラーがあれば具体的に指摘
3. 修正案を提示
4. ユーザー承認後に自動修正
```

---

## 考慮事項と制約

### ⚠️ 技術的考慮事項

#### 1. **ファイルサイズと性能**

**問題**: YAMLファイルが大きくなるとパース速度低下

**対策**:
- 日次ファイルは1日分のみ（翌日には自動アーカイブ）
- アーカイブは月単位でディレクトリ分割
- 統計・分析時はPandasで効率的処理

**閾値**: 1ファイル < 1MB、タスク数 < 1000件/日

#### 2. **同時編集の競合**

**問題**: Claude Codeと人間が同時に編集すると競合

**対策**:
- **原則**: Claude Code経由でのみ編集
- 緊急時の手動編集後は `validate.py` 実行を強制
- Git管理で変更履歴を追跡

**運用ルール**:
```
1. タスク更新は Claude Code に依頼
2. 手動編集は config/ のみ（マスタデータ）
3. tasks/ は基本的に自動生成のみ
```

#### 3. **データ移行コスト**

**問題**: 既存の `staff-capabilities.md` からの移行

**対策**:
- 移行スクリプトを用意 (`scripts/migrate_from_markdown.py`)
- 一度だけの手動作業（5分程度）
- 移行後は旧ファイルを削除

#### 4. **YAMLの落とし穴**

**問題**: YAMLの予約語（yes, no, on, off, true, false）が意図しない型に変換

**対策**:
```yaml
# ❌ 悪い例
notes: yes  # → boolean True に変換される

# ✅ 良い例
notes: "yes"  # → 文字列 "yes" として保持
```

**バリデーションで防止**: Pydanticの型チェックで早期発見

#### 5. **日本語の扱い**

**問題**: YAMLのUnicode処理、文字化け

**対策**:
- ファイルは全て **UTF-8 with BOM なし**
- Pydanticモデルで `allow_unicode=True`
- Gitの改行コード統一（LF）

### 🤔 運用上の考慮事項

#### 1. **学習コスト**

**問題**: YAML/Pydanticに不慣れなユーザー

**対策**:
- **Claude Codeが主役** - ユーザーはYAML直接編集不要
- 自然言語で指示 → Claude CodeがYAML編集
- マスタデータ編集時のみテンプレートをコピペ

**例**:
```
User: "細谷さんの1日最大タスク数を25に変更して"
Claude: config/staff.yaml を編集します...
```

#### 2. **障害時の復旧**

**問題**: ファイル破損、誤削除

**対策**:
- **Git管理** - `git revert` で即座に復旧
- アーカイブは削除しない（履歴保存）
- 毎朝の自動バックアップ（`scripts/backup.sh`）

#### 3. **段階的導入**

**問題**: 一度に全機能実装は負担大

**対策**: 3段階の段階的実装（後述）

#### 4. **既存ツールとの共存**

**問題**: 他のタスク管理ツール（Trello, Notionなど）との重複

**検討事項**:
- 現在他のツールを使用しているか？
- このシステムは「業務タスク割り振り」に特化
- 個人Todo管理は別ツール推奨

**質問**: 既に使用中のタスク管理ツールはありますか？

### 🔐 セキュリティ・プライバシー

#### データ保護
- スタッフ個人情報（社員番号など）の取り扱い
- Gitリポジトリがプライベートか確認
- 必要に応じて `.gitignore` で機密データ除外

#### 推奨設定
```gitignore
# .gitignore
config/staff.yaml      # スタッフ情報は非公開
tasks/active/*.yaml    # 進行中タスクも非公開
!tasks/archive/**      # アーカイブは統計用にコミット可（要判断）
```

**質問**: このリポジトリはプライベートですか？スタッフ情報をGit管理しても問題ないですか？

---

## 段階的実装計画

### 📅 Phase 1: 基盤構築（推定: 2-3時間）

**目標**: バリデーション付きマスタデータ + 手動タスク管理

#### 成果物
```
work/task-management/
├── CLAUDE.md                 # 操作ガイド
├── config/
│   ├── staff.yaml           # スタッフマスタ（移行完了）
│   └── task-types.yaml      # タスク種別定義
├── tasks/active/
│   └── 2025-10-15.yaml      # 手動作成のサンプル
├── scripts/
│   ├── models.py            # Pydanticモデル
│   └── validate.py          # バリデーションツール
└── pyproject.toml           # uv依存管理
```

#### タスク
1. ✅ Pydanticモデル実装 (`scripts/models.py`)
2. ✅ バリデーションスクリプト (`scripts/validate.py`)
3. ✅ Markdown → YAML 移行スクリプト実行
4. ✅ サンプルタスクファイル作成
5. ✅ CLAUDE.md 作成（基本操作ガイド）

#### Claude Codeでできること
- スタッフ情報の追加・更新
- タスクの追加・状態更新
- バリデーション実行
- 進捗確認

**この段階での価値**: データ破損リスク大幅減少、Claude Codeでの編集が容易に

---

### 📅 Phase 2: 自動化（推定: 3-4時間）

**目標**: タスク自動割り振り + 進捗可視化

#### 追加成果物
```
scripts/
├── assign_tasks.py          # 自動割り振りロジック
├── show_status.py           # 進捗表示CLI
└── utils.py                 # 共通ユーティリティ
```

#### タスク
1. ✅ スキルベース割り振りアルゴリズム実装
2. ✅ 進捗表示ツール（CLI）
3. ✅ 統計情報自動計算
4. ✅ テンプレート機能（Jinja2）

#### Claude Codeでできること（追加）
- 「今日のタスクを自動割り振りして」
- 「現在の進捗を表示して」
- 「細谷さんの負荷状況は？」
- 「修理タスクの平均所要時間は？」

**この段階での価値**: 毎朝の割り振り作業が自動化、負荷分散の最適化

---

### 📅 Phase 3: 分析・最適化（推定: 4-5時間）

**目標**: 履歴データからの学習と最適化

#### 追加成果物
```
scripts/
├── analyze.py               # 履歴分析
├── optimize.py              # 割り振り最適化
└── daily_report.py          # 日報自動生成
```

#### タスク
1. ✅ アーカイブデータ分析（Pandas）
2. ✅ スタッフ別平均所要時間の算出
3. ✅ ボトルネック検出
4. ✅ 割り振りアルゴリズムの機械学習的改善
5. ✅ レポート自動生成（Markdown/PDF）

#### Claude Codeでできること（追加）
- 「先月の細谷さんの査定平均時間は？」
- 「修理がボトルネックになっている日を教えて」
- 「今週の日報を生成して」
- 「最適な人員配置を提案して」

**この段階での価値**: データドリブンな業務改善、長期的な効率化

---

### 🎯 各段階の優先順位

| 段階 | 投資時間 | ROI | 推奨 |
|------|---------|-----|------|
| Phase 1 | 2-3h | ★★★★★ | **今すぐ** |
| Phase 2 | 3-4h | ★★★★☆ | 1週間後 |
| Phase 3 | 4-5h | ★★★☆☆ | 1ヶ月後 |

**推奨**: まずPhase 1を完成させ、2週間運用してから次段階を判断

---

## 代替案の検討

### 🔄 Option A: 現在の構成を維持（Markdown表）

**メリット**:
- 学習コスト ゼロ
- 人間の可読性 高い

**デメリット**:
- Claude Codeとの相性 最悪
- バリデーション 不可能
- 自動化 不可能
- 拡張性 低い

**評価**: ❌ 非推奨 - Claude Code運用には不適

---

### 🔄 Option B: Notion/Trello等の既存ツール

**メリット**:
- UI が洗練
- モバイル対応
- コラボレーション機能

**デメリット**:
- Claude Codeとの統合 困難
- API制限・コスト
- カスタマイズ性 低い
- データのローカル管理 不可

**評価**: △ 特定用途には有効、ただしClaude Code運用には不向き

---

### 🔄 Option C: スプレッドシート（Google Sheets/Excel）

**メリット**:
- 馴染み深いUI
- 関数・集計が容易

**デメリット**:
- Claude Codeとの統合 面倒（API経由）
- バージョン管理 困難
- バリデーション 弱い
- オフライン作業 不可（Google Sheets）

**評価**: △ 簡易的な用途には可、本格的な自動化には不向き

---

### 🔄 Option D: データベース（SQLite/PostgreSQL）

**メリット**:
- リレーショナルデータの表現 容易
- クエリ性能 優秀
- 大量データに対応

**デメリット**:
- セットアップコスト 高い
- Claude Codeとの統合 複雑
- Git管理 困難（バイナリファイル）
- オーバーエンジニアリング（現状の規模では）

**評価**: △ 将来的な選択肢、現時点では過剰

---

### 🔄 Option E: 提案アーキテクチャ（YAML + Pydantic）

**メリット**:
- Claude Codeとの相性 ★★★★★
- バリデーション 厳密
- Git管理 容易（テキストファイル）
- 段階的拡張 可能
- 軽量・シンプル

**デメリット**:
- 初期学習コスト 若干あり（ユーザー側はほぼ不要）
- YAMLの癖（予約語など）に注意

**評価**: ✅ **最推奨** - Claude Code運用に最適化

---

### 📊 比較表

| 観点 | Markdown表 | Notion | スプレッドシート | DB | **YAML+Pydantic** |
|------|-----------|--------|---------------|----|--------------------|
| Claude Code統合 | ★☆☆☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★★★☆☆ | **★★★★★** |
| バリデーション | ☆☆☆☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★★★★★ | **★★★★★** |
| Git管理 | ★★★★★ | ★☆☆☆☆ | ★☆☆☆☆ | ★☆☆☆☆ | **★★★★★** |
| 人間の可読性 | ★★★★★ | ★★★★☆ | ★★★★☆ | ★★☆☆☆ | **★★★★☆** |
| 拡張性 | ★☆☆☆☆ | ★★★☆☆ | ★★☆☆☆ | ★★★★★ | **★★★★☆** |
| 初期コスト | ★★★★★ | ★★★★☆ | ★★★★☆ | ★☆☆☆☆ | **★★★☆☆** |
| 自動化 | ★☆☆☆☆ | ★★☆☆☆ | ★★★☆☆ | ★★★★★ | **★★★★★** |

---

## 未解決の質問

### 🤔 決定が必要な事項

#### 1. データ管理ポリシー

**Q1**: スタッフ個人情報（社員番号、スキル情報）をGit管理しても問題ないですか？
- [ ] Yes - `config/staff.yaml` を通常通りコミット
- [ ] No - `.gitignore` で除外、ローカルのみ管理

**Q2**: タスクの履歴はどこまで保存しますか？
- [ ] 直近3ヶ月のみ（`archive/2025-08/` 以降のみ保持）
- [ ] 1年分保存
- [ ] 永続的に保存（容量が許す限り）

---

#### 2. 運用ルール

**Q3**: 毎朝のタスク割り振りのタイミングは？
- [ ] 前日夕方に翌日分を作成
- [ ] 当日朝9時に作成
- [ ] その他: _______________

**Q4**: 緊急タスクの追加ルールは？
- [ ] Claude Code経由でのみ追加
- [ ] 直接YAMLファイル編集も許可
- [ ] 別途緊急タスク専用ファイルを用意

---

#### 3. 技術的詳細

**Q5**: Python環境の依存管理は？
- [x] uv（既存環境に合わせる）
- [ ] poetry
- [ ] pip + requirements.txt

**Q6**: テストの実装範囲は？
- [ ] Phase 1から必須（pytest導入）
- [ ] Phase 2以降で追加
- [ ] 不要（バリデーションのみで十分）

---

#### 4. 将来的な拡張

**Q7**: 他の部門・チームでも使用する可能性は？
- [ ] ある → マルチテナント設計を考慮
- [ ] ない → 現チーム専用で最適化

**Q8**: モバイルアプリからの閲覧・更新は必要？
- [ ] 必要 → Web APIの検討
- [ ] 不要 → ファイルベースのみ

---

#### 5. 既存システムとの関係

**Q9**: 現在使用中のタスク管理ツールは？
- [ ] Notion
- [ ] Trello
- [ ] Asana
- [ ] なし
- [ ] その他: _______________

**Q10**: 既存ツールとこのシステムの棲み分けは？
- [ ] このシステムに完全移行
- [ ] 併用（使い分けルール: _______________ ）
- [ ] このシステムは試験的運用

---

### 📝 確認事項チェックリスト

#### 前提条件
- [ ] Gitリポジトリはプライベート設定か
- [ ] uvが正常に動作するか（`uv --version`）
- [ ] Python 3.10以上がインストール済みか
- [ ] スタッフ全員が現在の `staff-capabilities.md` に記載されているか

#### 運用体制
- [ ] データ更新の責任者は誰か
- [ ] Claude Codeの利用権限は誰にあるか
- [ ] 障害時のエスカレーション先は明確か

#### 移行計画
- [ ] 既存データのバックアップ方法は決まっているか
- [ ] 移行作業の実施日時は調整済みか
- [ ] ロールバックプランは用意されているか

---

## 次のステップ

### ✅ このドキュメントのレビュー後

1. **未解決の質問に回答** - 上記Q1〜Q10への回答
2. **実装方針の最終決定** - Phase 1から始めるか、代替案を選ぶか
3. **実装開始** - 承認後、Phase 1の構築開始

### 💬 レビュー時の観点

- [ ] **アーキテクチャ**: 提案構造は要件に合致しているか
- [ ] **バリデーション**: 制約は十分か、過剰でないか
- [ ] **運用性**: 日常的に使いやすいか
- [ ] **拡張性**: 将来的なニーズに対応できるか
- [ ] **コスト**: 学習・実装コストは妥当か

### 🔄 フィードバックのお願い

このドキュメントについて：
- 不明な点はありますか？
- 追加で検討すべき観点はありますか？
- 別の方向性を試したいですか？

**改善したい点や懸念事項があれば、対話しながらブラッシュアップしていきましょう。**

---

**改訂履歴**:
- v1.0 (2025-10-15): 初版作成
