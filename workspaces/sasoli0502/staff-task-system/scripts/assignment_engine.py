#!/usr/bin/env python3
"""
タスク自動割り振りエンジン（コアロジック）

完全自動でタスクを最適割り当てするアルゴリズムを実装:
1. タスクタイプ駆動: task-types.yamlの定義に基づき自動処理
2. スキルマッチング: スタッフの能力と作業負荷を考慮
3. 制約条件対応: 実働時間、専門作業時間を反映
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import yaml
import sys

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from utils import (
    resolve_staff_name,
    resolve_staff_names,
    load_staff_skills,
    load_staff_info,
    load_task_types,
    get_staff_capacity,
    format_staff_name,
    calculate_available_minutes,
)


@dataclass
class TaskAssignment:
    """タスク割り当て結果"""
    staff: str  # YAMLキー（苗字）
    task_type: str  # タスクタイプ名
    count: int  # 件数
    reason: str  # 割り当て理由
    estimated_total_minutes: int  # 予想合計時間（分）
    priority: str  # 優先度 (high/medium/low)


@dataclass
class StaffWorkload:
    """スタッフの作業負荷情報"""
    staff: str  # YAMLキー
    available_minutes: int  # 利用可能時間（分）
    assigned_minutes: int  # 割り当て済み時間（分）
    assignments: List[TaskAssignment]  # 割り当て済みタスク

    @property
    def remaining_minutes(self) -> int:
        """残り時間（分）"""
        return self.available_minutes - self.assigned_minutes

    @property
    def utilization_rate(self) -> float:
        """稼働率（0.0-1.0）"""
        if self.available_minutes == 0:
            return 0.0
        return self.assigned_minutes / self.available_minutes


class AssignmentEngine:
    """タスク自動割り振りエンジン"""

    def __init__(
        self,
        present_staff: List[str],
        morning_summary: Dict[str, int],
        date_str: str,
        constraints: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            present_staff: 出勤スタッフリスト（ニックネーム可）
            morning_summary: 朝の集計データ
            date_str: 対象日（YYYY-MM-DD）
            constraints: 制約条件（オプション）
        """
        # スタッフ名を正規化
        self.present_staff = resolve_staff_names(present_staff)
        self.morning_summary = morning_summary
        self.date_str = date_str
        self.constraints = constraints or {}

        # マスタデータ読み込み
        self.staff_skills = load_staff_skills()
        self.staff_info = load_staff_info()
        self.task_types = load_task_types()

        # 作業負荷トラッカー初期化
        self.workloads = self._initialize_workloads()

    def _initialize_workloads(self) -> Dict[str, StaffWorkload]:
        """各スタッフの作業負荷トラッカーを初期化"""
        workloads = {}

        for staff in self.present_staff:
            # staff.yamlの勤務時間定義と制約時間を読み込んで計算
            available_minutes = calculate_available_minutes(staff, self.date_str)

            workloads[staff] = StaffWorkload(
                staff=staff,
                available_minutes=available_minutes,
                assigned_minutes=0,
                assignments=[]
            )

        return workloads

    def assign_all_tasks(self) -> List[TaskAssignment]:
        """全タスクを自動割り当て

        Returns:
            割り当て結果のリスト
        """
        all_assignments = []

        # フェーズ1: quantity_basedタスク（数量管理タスク）
        quantity_assignments = self._assign_quantity_based_tasks()
        all_assignments.extend(quantity_assignments)

        # フェーズ2: assignment_basedタスク（担当制タスク）
        # ※ これは手動割り当てが基本なので、推奨のみ表示
        # （自動割り当てはしない）

        return all_assignments

    def _assign_quantity_based_tasks(self) -> List[TaskAssignment]:
        """数量管理タスク（quantity_based）を割り当て"""
        assignments = []

        # 優先度順にタスクタイプを取得
        quantity_tasks = self._get_quantity_tasks_by_priority()

        for task_info in quantity_tasks:
            task_type = task_info['name']
            task_count = task_info['count']
            priority = task_info['priority']

            if task_count == 0:
                continue

            # このタスクを割り当て
            task_assignments = self._assign_single_task_type(
                task_type, task_count, priority
            )
            assignments.extend(task_assignments)

        return assignments

    def _get_quantity_tasks_by_priority(self) -> List[Dict[str, Any]]:
        """数量管理タスクを優先度順に取得"""
        tasks = []

        for task_name, task_config in self.task_types.items():
            if task_config.get('category') != 'quantity_based':
                continue

            # 数量を計算
            count = self._calculate_task_quantity(task_name, task_config)

            if count > 0:
                tasks.append({
                    'name': task_name,
                    'count': count,
                    'priority': task_config.get('priority_base', 2),
                    'duration': task_config.get('default_duration_minutes', 15)
                })

        # 優先度順にソート（高い順）
        tasks.sort(key=lambda x: x['priority'], reverse=True)

        return tasks

    def _calculate_task_quantity(self, task_name: str, task_config: Dict[str, Any]) -> int:
        """タスクの数量を計算

        task-types.yamlのquantity_managementセクションに従って計算
        """
        quantity_mgmt = task_config.get('quantity_management', {})
        source = quantity_mgmt.get('source')

        if not source:
            return 0

        if source == 'morning_input':
            # 朝の集計から直接取得
            field = quantity_mgmt.get('base_quantity_field')
            return self.morning_summary.get(field, 0)

        elif source == 'calculated':
            # 計算式で算出
            formula = quantity_mgmt.get('formula', '')
            base_field = quantity_mgmt.get('base_quantity_field')

            if not formula or not base_field:
                return 0

            base_value = self.morning_summary.get(base_field, 0)

            # 簡易計算式評価（例: "satei_waiting * 0.5"）
            try:
                # セキュリティ上、evalは使わず手動パース
                if '*' in formula:
                    parts = formula.split('*')
                    multiplier = float(parts[1].strip())
                    return int(base_value * multiplier)
                else:
                    # 単純な参照
                    return base_value
            except:
                return 0

        elif source == 'afternoon_input':
            # 午後の集計から取得（今回は対象外）
            return 0

        return 0

    def _assign_single_task_type(
        self,
        task_type: str,
        total_count: int,
        priority: int
    ) -> List[TaskAssignment]:
        """単一タスクタイプを複数スタッフに割り当て

        Args:
            task_type: タスクタイプ名
            total_count: 総件数
            priority: 優先度

        Returns:
            割り当て結果のリスト
        """
        # このタスクができるスタッフを抽出
        capable_staff = self._get_capable_staff(task_type)

        if not capable_staff:
            # 誰もできない場合はスキップ
            return []

        # 処理能力でソート（高い順）
        capable_staff.sort(key=lambda x: x['capacity']['tasks_per_day'], reverse=True)

        # 専門タスクの場合は専門スタッフに全件割り当て
        if self._is_specialized_task(task_type):
            return self._assign_to_specialist(task_type, total_count, capable_staff[0], priority)

        # 通常タスク: 複数スタッフに負荷分散
        return self._distribute_to_multiple_staff(task_type, total_count, capable_staff, priority)

    def _get_capable_staff(self, task_type: str) -> List[Dict[str, Any]]:
        """指定タスクができるスタッフを取得"""
        capable = []

        for staff in self.present_staff:
            capacity = get_staff_capacity(staff, task_type)

            # スキルがあるが能力情報がない場合、デフォルト値を使用
            if capacity['can_do']:
                if capacity['tasks_per_day'] == 0:
                    # task-types.yamlからデフォルト時間を取得
                    task_config = self.task_types.get(task_type, {})
                    default_duration = task_config.get('default_duration_minutes', 10)

                    # デフォルト: 1タスクあたりdefault_duration分
                    # 8時間勤務で計算
                    capacity['time_per_task'] = default_duration
                    capacity['tasks_per_day'] = int(480 / default_duration)
                    capacity['tasks_per_hour'] = 60 / default_duration

                capable.append({
                    'staff': staff,
                    'capacity': capacity,
                    'workload': self.workloads[staff]
                })

        return capable

    def _is_specialized_task(self, task_type: str) -> bool:
        """専門タスクかどうか判定

        専門タスク: 修理など、特定の専門スタッフに集中させるべきタスク
        """
        specialized_tasks = ['修理', 'パーツ注文']
        return task_type in specialized_tasks

    def _assign_to_specialist(
        self,
        task_type: str,
        count: int,
        specialist: Dict[str, Any],
        priority: int
    ) -> List[TaskAssignment]:
        """専門スタッフに全件割り当て"""
        staff = specialist['staff']
        capacity = specialist['capacity']
        time_per_task = capacity['time_per_task']
        total_minutes = int(count * time_per_task)

        # 作業負荷を更新
        assignment = TaskAssignment(
            staff=staff,
            task_type=task_type,
            count=count,
            reason=f"{task_type}専門（{capacity['tasks_per_day']}件/日）",
            estimated_total_minutes=total_minutes,
            priority='high' if priority >= 3 else 'medium'
        )

        self.workloads[staff].assigned_minutes += total_minutes
        self.workloads[staff].assignments.append(assignment)

        return [assignment]

    def _distribute_to_multiple_staff(
        self,
        task_type: str,
        total_count: int,
        capable_staff: List[Dict[str, Any]],
        priority: int
    ) -> List[TaskAssignment]:
        """複数スタッフに負荷分散して割り当て

        処理能力比率に応じて分配
        """
        assignments = []

        # 総処理能力を計算
        total_capacity = sum(s['capacity']['tasks_per_day'] for s in capable_staff)

        remaining_count = total_count

        for i, staff_info in enumerate(capable_staff):
            if remaining_count == 0:
                break

            staff = staff_info['staff']
            capacity = staff_info['capacity']

            # 最後のスタッフは残り全て
            if i == len(capable_staff) - 1:
                count = remaining_count
            else:
                # 処理能力比率で割り当て
                ratio = capacity['tasks_per_day'] / total_capacity
                count = int(total_count * ratio)
                count = min(count, remaining_count)

            if count == 0:
                continue

            time_per_task = capacity['time_per_task']
            total_minutes = int(count * time_per_task)

            assignment = TaskAssignment(
                staff=staff,
                task_type=task_type,
                count=count,
                reason=f"{task_type}（{capacity['tasks_per_day']}件/日）",
                estimated_total_minutes=total_minutes,
                priority='medium' if priority >= 2 else 'low'
            )

            self.workloads[staff].assigned_minutes += total_minutes
            self.workloads[staff].assignments.append(assignment)
            assignments.append(assignment)

            remaining_count -= count

        return assignments

    def get_assignment_summary(self) -> str:
        """割り当て結果のサマリーを生成"""
        lines = []
        lines.append("=" * 60)
        lines.append("📋 タスク割り当て結果")
        lines.append("=" * 60)
        lines.append("")

        for staff, workload in sorted(self.workloads.items()):
            if not workload.assignments:
                continue

            lines.append(f"👤 {format_staff_name(staff)}")
            lines.append(f"   実働時間: {workload.available_minutes}分")
            lines.append(f"   割り当て: {workload.assigned_minutes}分 ({workload.utilization_rate:.0%})")
            lines.append(f"   残り時間: {workload.remaining_minutes}分")
            lines.append("")

            for assignment in workload.assignments:
                lines.append(f"   • {assignment.task_type}: {assignment.count}件")
                lines.append(f"     予想時間: {assignment.estimated_total_minutes}分")
                lines.append(f"     理由: {assignment.reason}")
                lines.append("")

            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)


# ========== テスト用 ==========

if __name__ == "__main__":
    # テスト実行
    present_staff = ['細谷', '江口', 'シャシャ', '佐々木', '雜賀', '須加尾']

    morning_summary = {
        'satei_waiting': 50,
        'kaifuu_count': 30,
        'shuri_needed': 15,
        'shuppin_ready': 24,
        'hensin_pending': 0,
    }

    engine = AssignmentEngine(
        present_staff=present_staff,
        morning_summary=morning_summary,
        date_str='2025-10-31'
    )

    assignments = engine.assign_all_tasks()

    print(engine.get_assignment_summary())

    print("\n📊 割り当て詳細:")
    for assignment in assignments:
        print(f"  {assignment.staff}: {assignment.task_type} x{assignment.count}件")
