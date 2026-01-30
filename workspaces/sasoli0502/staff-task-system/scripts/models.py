"""
タスク管理システムのデータモデル定義

Pydantic v2を使用した厳密な型定義とバリデーション
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import yaml


# ========== Enums ==========

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


class TaskCategory(str, Enum):
    """タスクカテゴリ"""
    QUANTITY_BASED = "quantity_based"      # 数量管理タスク
    ASSIGNMENT_BASED = "assignment_based"  # 担当制タスク
    OPTIONAL = "optional"                  # オプショナルタスク


class TaskType(str, Enum):
    """タスク種別（拡張版）"""
    # 数量管理タスク
    SATEI = "査定"
    SHURI = "修理"
    KENPIN = "検品"
    SHUPPIN = "出品"
    KAIFUU = "開封"
    ACTIVATE = "アクティベート"
    KONPOU_KIT = "梱包キット作成"
    HASSOU_JUNBI = "発送準備"
    OKURIJOU = "送り状作成"
    SEIYAKU_SHIWAKE = "成約仕分"

    # 担当制タスク
    HENSIN = "返信"
    FURIKOMI_MESSE = "振込メッセ"
    SAISOKU = "催促"
    SATEI_KEKKA = "査定結果送信"
    HENSOU_KOUSHOU = "返送交渉"
    SHINCHOKU_HENKOU = "進捗変更"
    HASSOU_KANRYOU = "発送完了連絡"
    DENWA_TAIOU = "電話対応"
    KPI_NYUURYOKU = "KPI入力"
    JITSUZANDAKA = "実残高入力"
    ZASEKI_KETTEI = "座席決定"
    TASK_SETTEI = "タスク設定"
    BM_ZAIKO = "BM在庫確認"
    SHINPIN_KAKAKU = "新品価格変更"
    HINSHITSU_KANRI = "品質管理チェック"
    PARTS_CHUUMON = "パーツ注文"
    HOUJIN_HANBAI = "法人販売"
    TENPO_JUNBI = "店舗準備"
    TENPO_SATEI = "店舗査定"
    TENPO_SHURI_UKETSUKE = "店舗修理受付"
    TENPO_SHURI_OWATASHI = "店舗修理お渡し"

    # オプショナルタスク
    MUSUBI_SATSUEI = "ムスビー撮影"
    MUSUBI_SHUPPIN = "ムスビー出品"


# ========== Config Models ==========

class QuantityManagement(BaseModel):
    """数量管理設定"""
    source: str = Field(..., description="morning_input | afternoon_input | calculated | manual")
    available_at: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="タスク追加可能時刻")
    base_quantity_field: Optional[str] = Field(None, description="基準となる集計フィールド名")
    formula: Optional[str] = Field(None, description="計算式（calculatedの場合）")
    detection_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$", description="判明時刻")
    addition_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$", description="追加時刻")


class AssignmentPolicy(BaseModel):
    """割り当てポリシー"""
    type: str = Field(..., description="skill_based | manual")
    skill_required: Optional[str] = Field(None, description="必要スキル")
    auto_assign: bool = Field(False, description="自動割り当てフラグ")


class AssignmentRequest(BaseModel):
    """タスク割り当てリクエスト（バリデーション用）"""
    staff_list: List[str] = Field(..., min_length=1, description="出勤スタッフリスト")
    date_str: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="対象日（YYYY-MM-DD）")
    auto_create: bool = Field(False, description="自動作成フラグ")
    dry_run: bool = Field(False, description="dry-runモード（プレビューのみ）")

    @field_validator('staff_list')
    @classmethod
    def validate_staff_list(cls, v: List[str]) -> List[str]:
        """スタッフリストのバリデーション"""
        if len(v) == 0:
            raise ValueError("スタッフが指定されていません")
        if len(set(v)) != len(v):
            raise ValueError("スタッフリストに重複があります")
        return v


class TaskTypeConfig(BaseModel):
    """タスクタイプ設定（拡張版）"""
    display_name: str
    category: TaskCategory
    description: str
    required_skills: List[str] = Field(default_factory=list)
    default_duration_minutes: int
    priority_base: int
    can_parallel: bool = False
    required_tools: List[str] = Field(default_factory=list)

    # 新規フィールド
    quantity_management: Optional[QuantityManagement] = None
    assignment_policy: Optional[AssignmentPolicy] = None


class MorningSummary(BaseModel):
    """朝の集計データ"""
    input_at: datetime
    satei_waiting: int = Field(..., ge=0, description="査定待ち台数")
    kaifuu_count: int = Field(..., ge=0, description="開封台数")
    shuri_needed: int = Field(..., ge=0, description="修理必要台数（自動計算）")
    kenpin_needed: int = Field(..., ge=0, description="検品必要台数（自動計算）")
    shuppin_ready: int = Field(..., ge=0, description="出品可能台数（自動計算）")
    activate_count: int = Field(..., ge=0, description="アクティベート台数（自動計算）")


class AfternoonSummary(BaseModel):
    """午後の集計データ"""
    time_slot: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="時間帯")
    input_at: datetime
    hassou_junbi_count: Optional[int] = Field(None, ge=0, description="発送準備件数")
    hassou_konpou_count: Optional[int] = Field(None, ge=0, description="発送梱包作成件数")
    konpou_kit_count: Optional[int] = Field(None, ge=0, description="梱包キット作成件数")
    scheduled_addition_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$", description="追加予定時刻")


class SkillDetail(BaseModel):
    """スキル詳細（処理能力ベース）"""
    # 処理能力情報（必須）
    time_per_task: float = Field(..., ge=0.1, description="1タスクあたりの処理時間（分）")
    tasks_per_hour: float = Field(..., ge=0.1, description="1時間あたりの処理数")
    tasks_per_day: int = Field(..., ge=1, description="1日あたりの処理数（8時間想定）")


class StaffConstraints(BaseModel):
    """スタッフ制約"""
    max_tasks_per_day: int = Field(20, ge=1, le=50, description="1日最大タスク数")
    preferred_task_types: List[TaskType] = Field(default_factory=list)
    unavailable_dates: List[date] = Field(default_factory=list)


class Staff(BaseModel):
    """スタッフ情報（簡素版）

    スキル情報は config/staff-skills.yaml で管理
    """
    full_name: str = Field(..., min_length=1, description="フルネーム")
    nickname: Optional[str] = Field(None, description="通称・愛称")
    employee_id: str = Field(..., pattern=r"^EMP\d{3}$", description="社員番号")
    constraints: StaffConstraints = Field(default_factory=StaffConstraints)
    notes: str = Field("", description="備考")


class StaffConfig(BaseModel):
    """スタッフマスタ設定"""
    staff: Dict[str, Staff] = Field(..., description="スタッフマップ")
    settings: Dict[str, Any] = Field(default_factory=dict, description="グローバル設定")

    @classmethod
    def from_yaml(cls, filepath: str) -> 'StaffConfig':
        """YAMLファイルから読み込み"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, filepath: str) -> None:
        """YAMLファイルへ書き込み"""
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(
                self.model_dump(mode='json'),
                f,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False
            )


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
    by_status: Dict[str, int]
    by_staff: Dict[str, Dict[str, int]]
    total_estimated_minutes: int
    total_actual_minutes: int


class DailyTaskList(BaseModel):
    """日次タスクリスト（拡張版）"""
    metadata: Dict[str, Any] = Field(..., description="メタデータ")
    tasks: List[Task] = Field(..., description="タスクリスト")
    statistics: Optional[TaskStatistics] = Field(None, description="統計情報")

    # 新規フィールド
    morning_summary: Optional[MorningSummary] = Field(None, description="朝の集計データ")
    afternoon_summaries: List[AfternoonSummary] = Field(default_factory=list, description="午後の集計データ")

    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v: Dict[str, Any]) -> Dict[str, Any]:
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
            yaml.dump(
                self.model_dump(mode='json'),
                f,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False
            )


# ========== Validation Utilities ==========

def validate_file(filepath: str, model_class: type[BaseModel]) -> tuple[bool, Optional[str]]:
    """
    YAMLファイルをバリデーション

    Returns:
        (成功フラグ, エラーメッセージ)
    """
    try:
        if model_class == StaffConfig:
            model_class.from_yaml(filepath)
        elif model_class == DailyTaskList:
            model_class.from_yaml(filepath)
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            model_class(**data)
        return True, None
    except Exception as e:
        return False, str(e)


# ========== Data Loaders ==========

def load_skills(filepath: str = "config/skills.yaml") -> Dict[str, Any]:
    """スキルマスターを読み込み"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_staff_skills(filepath: str = "config/staff-skills.yaml") -> Dict[str, Dict[str, Any]]:
    """スタッフ×スキル関連テーブルを読み込み"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data.get('staff_skills', {})


def load_task_types(filepath: str = "config/task-types.yaml") -> Dict[str, TaskTypeConfig]:
    """タスク種別マスタを読み込み

    Returns:
        Dict[str, TaskTypeConfig]: タスク名 → TaskTypeConfig のマップ
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    task_types = {}
    for task_name, config in data.get('task_types', {}).items():
        task_types[task_name] = TaskTypeConfig(**config)

    return task_types


def load_staff_config(filepath: str = "config/staff.yaml") -> StaffConfig:
    """スタッフマスタを読み込み"""
    return StaffConfig.from_yaml(filepath)


def get_staff_with_skills(staff_name: str) -> Dict[str, Any]:
    """
    スタッフ情報とスキル情報を結合して取得

    Returns:
        {
            "full_name": "細谷 尚央",
            "employee_id": "EMP001",
            "constraints": {...},
            "notes": "...",
            "skills": {
                "査定": {"level": 3, "speed_factor": 1.2, "certification": True},
                "検品": {"level": 3, ...},
                ...
            }
        }
    """
    # スタッフ基本情報
    staff_config = load_staff_config()
    if staff_name not in staff_config.staff:
        raise ValueError(f"スタッフ '{staff_name}' が見つかりません")

    staff_info = staff_config.staff[staff_name].model_dump()

    # スキル情報を追加
    staff_skills = load_staff_skills()
    if staff_name in staff_skills:
        staff_info['skills'] = staff_skills[staff_name]
    else:
        staff_info['skills'] = {}

    return staff_info


def get_all_staff_with_skills() -> Dict[str, Dict[str, Any]]:
    """全スタッフの情報とスキルを取得"""
    staff_config = load_staff_config()
    staff_skills_data = load_staff_skills()

    result = {}
    for staff_name, staff in staff_config.staff.items():
        staff_info = staff.model_dump()
        staff_info['skills'] = staff_skills_data.get(staff_name, {})
        result[staff_name] = staff_info

    return result


if __name__ == "__main__":
    # テスト用コード
    print("Pydanticモデル定義を読み込みました")
    print(f"- TaskStatus: {[s.value for s in TaskStatus]}")
    print(f"- TaskType: {[t.value for t in TaskType]}")
    print(f"- TaskPriority: {[p.value for p in TaskPriority]}")
