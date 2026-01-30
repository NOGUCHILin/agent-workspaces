#!/usr/bin/env python3
"""
共通ユーティリティモジュール

スタッフタスク管理システム全体で使用する共通関数を提供:
- 名前解決（ニックネーム → YAMLキー変換）
- スキル情報の統一読み込み
- スタッフ情報の統一アクセス
- タスクタイプ情報の読み込み
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent

# ========== 名前解決マッピング（実際の呼び方 + 音声入力エラー対策） ==========
# ニックネーム・通称 → YAMLキー（苗字）の変換
NICKNAME_TO_KEY = {
    # 江口さん（なっちゃん・えぐちゃん）
    'なっちゃん': '江口',
    'えぐちゃん': '江口',
    '江口': '江口',
    # 音声入力エラー候補
    'なっちゃ': '江口',  # ん脱落
    'えぐちゃ': '江口',  # ん脱落
    'エグちゃん': '江口',  # カタカナ表記

    # 雜賀さん（はるし）
    'はるし': '雜賀',
    '雜賀': '雜賀',
    'ハルシ': '雜賀',
    # 音声入力エラー候補
    'はるしー': '雜賀',  # 伸ばし棒追加
    'さいか': '雜賀',  # 漢字読みの誤変換

    # 野口さん（さら）※ 野口が3人いるため名前で識別
    'さら': '野口',
    '沙羅': '野口',
    'サラ': '野口',
    # 音声入力エラー候補
    'さらー': '野口',  # 伸ばし棒追加

    # 佐々木さん
    '佐々木': '佐々木',
    'ささき': '佐々木',
    # 音声入力エラー候補
    '佐々木さん': '佐々木',  # 「さん」付き
    'さ3き': '佐々木',  # 「々」が「3」に誤認識
    '佐佐木': '佐々木',  # 「々」が「佐」に誤認識

    # 須加尾さん
    '須加尾': '須加尾',
    'すがお': '須加尾',
    # 音声入力エラー候補
    '須加尾さん': '須加尾',  # 「さん」付き
    '菅尾': '須加尾',  # 漢字の誤変換
    'すかお': '須加尾',  # が→か の誤認識

    # 高橋さん
    '高橋': '高橋',
    'たかはし': '高橋',
    # 音声入力エラー候補
    '高橋さん': '高橋',  # 「さん」付き
    'たかはしさん': '高橋',

    # 島田さん
    '島田': '島田',
    'しまだ': '島田',
    # 音声入力エラー候補
    '島田さん': '島田',  # 「さん」付き

    # 平山さん
    '平山': '平山',
    'ひらやま': '平山',
    # 音声入力エラー候補
    '平山さん': '平山',  # 「さん」付き

    # 細谷さん
    '細谷': '細谷',
    'ほそや': '細谷',
    # 音声入力エラー候補
    '細谷さん': '細谷',  # 「さん」付き
    '細3': '細谷',  # 「谷」が「3」に誤認識

    # NANTさん（シャシャさん）
    'シャシャ': 'NANT',
    'しゃしゃ': 'NANT',
    'NANT': 'NANT',

    # 原さん（くれは）
    'くれは': '原',
    '原': '原',
    'はら': '原',
    # 音声入力エラー候補
    'クレハ': '原',  # カタカナ表記
    'はらさん': '原',  # 「さん」付き
    '原さん': '原',

    # 本間さん
    '本間': '本間',
    'ほんま': '本間',
    # 音声入力エラー候補
    '本間さん': '本間',  # 「さん」付き
    'ほんまさん': '本間',

    # 創さん
    'そう': '創',
    '創': '創',
}

# YAMLキー → ニックネーム（逆引き）
KEY_TO_NICKNAME = {v: k for k, v in NICKNAME_TO_KEY.items()}


def resolve_staff_name(name: str) -> str:
    """スタッフ名を正規化（ニックネーム→YAMLキーに変換）

    Args:
        name: ニックネームまたはYAMLキー

    Returns:
        正規化されたYAMLキー（苗字）

    Examples:
        >>> resolve_staff_name('シャシャ')
        'NANT'
        >>> resolve_staff_name('NANT')
        'NANT'
        >>> resolve_staff_name('細谷')
        '細谷'
    """
    return NICKNAME_TO_KEY.get(name, name)


def resolve_staff_names(names: List[str]) -> List[str]:
    """スタッフ名リストを一括正規化

    Args:
        names: ニックネームまたはYAMLキーのリスト

    Returns:
        正規化されたYAMLキーのリスト
    """
    return [resolve_staff_name(name) for name in names]


# ========== スキル情報読み込み ==========

def load_staff_skills() -> Dict[str, Dict[str, Any]]:
    """スタッフのスキル情報を読み込み（staff-skills.yaml）

    Returns:
        スタッフ名をキーとするスキル情報の辞書

    Example:
        {
            '江口': {
                '査定': {'time_per_task': 8, 'tasks_per_day': 60},
                '検品': {'time_per_task': 7, 'tasks_per_day': 69},
                ...
            },
            ...
        }
    """
    skills_file = PROJECT_ROOT / "config" / "staff-skills.yaml"

    with open(skills_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    return data.get('staff_skills', {})


def load_staff_info() -> Dict[str, Dict[str, Any]]:
    """スタッフの基本情報を読み込み（staff.yaml）

    Returns:
        スタッフ名とsettingsをキーとする基本情報の辞書

    Example:
        {
            '江口': {
                'full_name': '江口 那都',
                'nickname': 'なっちゃん',
                'constraints': {'max_tasks_per_day': 20, ...},
                ...
            },
            'settings': {
                'working_hours': {...},
                'common_unavailable_times': [...],
                ...
            },
            ...
        }
    """
    staff_file = PROJECT_ROOT / "config" / "staff.yaml"

    with open(staff_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # staffとsettingsの両方を含める
    result = data.get('staff', {}).copy()
    if 'settings' in data:
        result['settings'] = data['settings']

    return result


def load_task_types() -> Dict[str, Dict[str, Any]]:
    """タスクタイプ情報を読み込み（task-types.yaml）

    Returns:
        タスクタイプ名をキーとするタスク情報の辞書

    Example:
        {
            '査定': {
                'display_name': '査定',
                'category': 'quantity_based',
                'default_duration_minutes': 15,
                'quantity_management': {...},
                ...
            },
            ...
        }
    """
    task_types_file = PROJECT_ROOT / "config" / "task-types.yaml"

    with open(task_types_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    return data.get('task_types', {})


def load_skills_master() -> Dict[str, Dict[str, Any]]:
    """スキルマスター情報を読み込み（skills.yaml）

    Returns:
        スキル名をキーとするスキル定義の辞書
    """
    skills_file = PROJECT_ROOT / "config" / "skills.yaml"

    with open(skills_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    return data.get('skills', {})


# ========== スタッフ能力計算 ==========

def get_staff_capacity(staff_name: str, task_type: str) -> Dict[str, Any]:
    """特定スタッフの特定タスクに対する能力情報を取得

    Args:
        staff_name: スタッフのYAMLキー（正規化済み推奨）
        task_type: タスクタイプ名（例: '査定', '検品'）

    Returns:
        能力情報の辞書
        {
            'can_do': bool,  # このタスクができるか
            'time_per_task': float,  # タスク1件あたりの時間（分）
            'tasks_per_day': int,  # 1日あたりの処理可能件数
            'skill_level': int,  # スキルレベル（あれば）
        }
    """
    staff_name = resolve_staff_name(staff_name)
    staff_skills = load_staff_skills()

    staff_skill_set = staff_skills.get(staff_name, {})
    skill_detail = staff_skill_set.get(task_type, {})

    # スキルがあるか判定
    can_do = task_type in staff_skill_set

    return {
        'can_do': can_do,
        'time_per_task': skill_detail.get('time_per_task', 0),
        'tasks_per_day': skill_detail.get('tasks_per_day', 0),
        'tasks_per_hour': skill_detail.get('tasks_per_hour', 0),
    }


def get_staff_available_time(staff_name: str, working_hours: Dict[str, Any]) -> int:
    """スタッフの実働可能時間を計算（分）

    Args:
        staff_name: スタッフのYAMLキー
        working_hours: 勤務時間情報
            {
                'start': '10:00',
                'end': '19:00',
                'break_minutes': 60,
                'constraints': [...]  # 制約時間（法人販売等）
            }

    Returns:
        実働可能時間（分）
    """
    from datetime import datetime, timedelta

    # 基本勤務時間の計算
    start_time = datetime.strptime(working_hours['start'], '%H:%M')
    end_time = datetime.strptime(working_hours['end'], '%H:%M')
    total_minutes = int((end_time - start_time).total_seconds() / 60)

    # 休憩時間を引く
    break_minutes = working_hours.get('break_minutes', 60)
    available_minutes = total_minutes - break_minutes

    # 制約時間を引く（法人販売、棚卸し等）
    constraints = working_hours.get('constraints', [])
    for constraint in constraints:
        constraint_minutes = constraint.get('duration_minutes', 0)
        available_minutes -= constraint_minutes

    return available_minutes


# ========== 名前表示ヘルパー ==========

def format_staff_name(staff_key: str, include_nickname: bool = True) -> str:
    """スタッフ名を人間が読みやすい形式にフォーマット

    Args:
        staff_key: YAMLキー（苗字）
        include_nickname: ニックネームを含めるか

    Returns:
        フォーマットされた名前

    Examples:
        >>> format_staff_name('江口', True)
        '江口（なっちゃん）'
        >>> format_staff_name('江口', False)
        '江口'
    """
    if include_nickname and staff_key in KEY_TO_NICKNAME:
        nickname = KEY_TO_NICKNAME[staff_key]
        return f"{staff_key}（{nickname}）"
    return staff_key


# ========== バリデーション ==========

def validate_staff_exists(staff_name: str) -> bool:
    """スタッフが存在するか確認

    Args:
        staff_name: スタッフ名（ニックネームまたはYAMLキー）

    Returns:
        存在する場合True
    """
    staff_key = resolve_staff_name(staff_name)
    staff_info = load_staff_info()
    return staff_key in staff_info


def validate_task_type_exists(task_type: str) -> bool:
    """タスクタイプが存在するか確認

    Args:
        task_type: タスクタイプ名

    Returns:
        存在する場合True
    """
    task_types = load_task_types()
    return task_type in task_types


def calculate_available_minutes(staff_key: str, date_str: Optional[str] = None) -> int:
    """スタッフの実働可能時間を計算（分単位）

    Args:
        staff_key: スタッフのYAMLキー
        date_str: 対象日（YYYY-MM-DD形式、省略時は今日）

    Returns:
        実働可能時間（分）
    """
    from datetime import datetime, timedelta

    staff_info = load_staff_info()

    # 勤務時間設定を取得
    settings = staff_info.get('settings', {})
    working_hours = settings.get('working_hours', {})

    # デフォルト値
    start_time = working_hours.get('start', '10:00')
    end_time = working_hours.get('end', '19:00')
    lunch_start = working_hours.get('lunch_start', '13:00')
    lunch_end = working_hours.get('lunch_end', '14:00')

    # 時刻を分に変換
    def time_to_minutes(time_str: str) -> int:
        h, m = map(int, time_str.split(':'))
        return h * 60 + m

    start_minutes = time_to_minutes(start_time)
    end_minutes = time_to_minutes(end_time)
    lunch_start_minutes = time_to_minutes(lunch_start)
    lunch_end_minutes = time_to_minutes(lunch_end)

    # 基本勤務時間
    total_minutes = end_minutes - start_minutes

    # 休憩時間を引く
    lunch_duration = lunch_end_minutes - lunch_start_minutes
    available_minutes = total_minutes - lunch_duration

    # スタッフ個別の制約時間を引く
    staff = staff_info.get(staff_key, {})
    constraints = staff.get('constraints', {})
    unavailable_times = constraints.get('unavailable_times', [])

    for time_block in unavailable_times:
        duration = time_block.get('duration_minutes', 0)
        available_minutes -= duration

    # 全スタッフ共通の制約時間を引く
    common_unavailable = settings.get('common_unavailable_times', [])
    for time_block in common_unavailable:
        if time_block.get('applies_to_all', False):
            duration = time_block.get('duration_minutes', 0)
            available_minutes -= duration

    return max(0, available_minutes)


def load_staff_constraints(date_str: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """スタッフの制約条件を読み込む

    Args:
        date_str: 対象日（YYYY-MM-DD形式、省略時は今日）

    Returns:
        スタッフごとの制約条件
        {
            'staff_constraints': {
                '佐々木': {'unavailable_minutes': 60, 'reason': '法人販売'},
                ...
            }
        }
    """
    staff_info = load_staff_info()
    constraints = {'staff_constraints': {}}

    for staff_key, staff_data in staff_info.items():
        if staff_key == 'settings':
            continue

        staff_constraints = staff_data.get('constraints', {})
        unavailable_times = staff_constraints.get('unavailable_times', [])

        if unavailable_times:
            total_unavailable = sum(t.get('duration_minutes', 0) for t in unavailable_times)
            reasons = ', '.join(t.get('name', '不明') for t in unavailable_times)

            constraints['staff_constraints'][staff_key] = {
                'unavailable_minutes': total_unavailable,
                'reason': reasons
            }

    return constraints


# ========== デバッグ用 ==========

if __name__ == "__main__":
    # テスト実行
    print("=== 名前解決テスト ===")
    print(f"シャシャ → {resolve_staff_name('シャシャ')}")
    print(f"NANT → {resolve_staff_name('NANT')}")
    print(f"細谷 → {resolve_staff_name('細谷')}")
    print()

    print("=== スキル情報読み込みテスト ===")
    staff_skills = load_staff_skills()
    print(f"スタッフ数: {len(staff_skills)}")
    print(f"江口さんのスキル: {list(staff_skills.get('江口', {}).keys())[:5]}...")
    print()

    print("=== タスクタイプ読み込みテスト ===")
    task_types = load_task_types()
    print(f"タスクタイプ数: {len(task_types)}")
    print(f"タスクタイプ例: {list(task_types.keys())[:5]}")
    print()

    print("=== スタッフ能力テスト ===")
    capacity = get_staff_capacity('江口', '査定')
    print(f"江口さんの査定能力: {capacity}")
