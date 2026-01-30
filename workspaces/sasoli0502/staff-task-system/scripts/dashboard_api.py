#!/usr/bin/env python3
"""
ダッシュボード用APIバックエンド

既存のスクリプトロジックを統合し、JSON形式でデータを提供
"""

import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict
import yaml

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from models import DailyTaskList, TaskStatus


class DashboardAPI:
    """ダッシュボード用データ取得API"""

    def __init__(self, date_str: str = None, use_mock: bool = False):
        """
        Args:
            date_str: 対象日（YYYY-MM-DD形式、省略時は今日）
            use_mock: モックデータを使用する場合True
        """
        self.date_str = date_str or date.today().strftime("%Y-%m-%d")
        self.task_file = project_root / "tasks" / "active" / f"{self.date_str}.yaml"
        self.task_list = None
        self.use_mock = use_mock

        if self.task_file.exists() and not use_mock:
            try:
                self.task_list = DailyTaskList.from_yaml(str(self.task_file))
            except Exception as e:
                print(f"警告: タスクファイルの読み込みに失敗しました: {e}", file=sys.stderr)

        # データがない場合、モックデータを使用
        if self.task_list is None:
            self.use_mock = True

    def _generate_mock_data(self) -> Dict[str, Any]:
        """モックデータを生成
        
        Returns:
            全ダッシュボードデータのモック
        """
        now = datetime.now()
        
        # モックサマリー
        mock_summary = {
            "date": self.date_str,
            "total_tasks": 85,
            "completed": 48,
            "in_progress": 12,
            "pending": 25,
            "completion_rate": 56.5,
            "total_estimated_minutes": 680,
            "total_actual_minutes": 432,
            "efficiency_rate": 63.5
        }
        
        # モックスタッフ進捗
        mock_staff_progress = [
            {
                "staff": "細谷",
                "total_tasks": 18,
                "completed": 12,
                "in_progress": 2,
                "pending": 4,
                "completion_rate": 66.7,
                "actual_minutes": 96,
                "status_icon": "✅"
            },
            {
                "staff": "江口",
                "total_tasks": 16,
                "completed": 10,
                "in_progress": 3,
                "pending": 3,
                "completion_rate": 62.5,
                "actual_minutes": 90,
                "status_icon": "✅"
            },
            {
                "staff": "NANT",
                "total_tasks": 14,
                "completed": 9,
                "in_progress": 2,
                "pending": 3,
                "completion_rate": 64.3,
                "actual_minutes": 72,
                "status_icon": "✅"
            },
            {
                "staff": "佐々木",
                "total_tasks": 12,
                "completed": 6,
                "in_progress": 2,
                "pending": 4,
                "completion_rate": 50.0,
                "actual_minutes": 54,
                "status_icon": "🟡"
            },
            {
                "staff": "雜賀",
                "total_tasks": 15,
                "completed": 8,
                "in_progress": 2,
                "pending": 5,
                "completion_rate": 53.3,
                "actual_minutes": 72,
                "status_icon": "🟡"
            },
            {
                "staff": "須加尾",
                "total_tasks": 10,
                "completed": 3,
                "in_progress": 1,
                "pending": 6,
                "completion_rate": 30.0,
                "actual_minutes": 48,
                "status_icon": "🔴"
            }
        ]
        
        # モック警告
        mock_alerts = [
            {
                "level": "warning",
                "message": "須加尾: 進行中タスクが滞留（1件）"
            },
            {
                "level": "warning",
                "message": "進行中タスクが多い（12件）"
            }
        ]
        
        # モックマネージャーデータ
        checkpoints = ["14:00", "17:00"]
        next_checkpoint = None
        for cp in checkpoints:
            cp_hour, cp_min = map(int, cp.split(":"))
            cp_time = now.replace(hour=cp_hour, minute=cp_min, second=0)
            if now < cp_time:
                remaining = int((cp_time - now).total_seconds() / 60)
                next_checkpoint = {
                    "time": cp,
                    "remaining_minutes": remaining
                }
                break
        
        mock_manager_data = {
            "current_time": now.strftime("%H:%M"),
            "next_checkpoint": next_checkpoint,
            "morning_vs_actual": [
                {
                    "task_type": "査定",
                    "predicted": 50,
                    "completed": 42,
                    "completion_rate": 84.0,
                    "status": "ahead"
                },
                {
                    "task_type": "修理",
                    "predicted": 25,
                    "completed": 12,
                    "completion_rate": 48.0,
                    "status": "on_track"
                },
                {
                    "task_type": "検品",
                    "predicted": 25,
                    "completed": 8,
                    "completion_rate": 32.0,
                    "status": "delayed"
                },
                {
                    "task_type": "出品",
                    "predicted": 40,
                    "completed": 28,
                    "completion_rate": 70.0,
                    "status": "on_track"
                },
                {
                    "task_type": "開封",
                    "predicted": 30,
                    "completed": 26,
                    "completion_rate": 86.7,
                    "status": "ahead"
                }
            ],
            "bottlenecks": [
                {
                    "task_type": "検品",
                    "avg_actual_minutes": 18.5,
                    "avg_estimated_minutes": 10.0,
                    "ratio": 1.8,
                    "message": "検品: 平均処理時間が予定の1.8倍"
                },
                {
                    "staff": "須加尾",
                    "in_progress_count": 1,
                    "message": "須加尾: 1件のタスクが長時間進行中"
                }
            ],
            "estimated_finish_time": "18:25"
        }
        
        return {
            "summary": mock_summary,
            "staff_progress": mock_staff_progress,
            "alerts": mock_alerts,
            "manager_data": mock_manager_data
        }

    def get_summary(self) -> Dict[str, Any]:
        """全体サマリーを取得

        Returns:
            {
                "date": "2025-11-01",
                "total_tasks": 120,
                "completed": 45,
                "in_progress": 15,
                "pending": 60,
                "completion_rate": 37.5,
                "total_estimated_minutes": 840,
                "total_actual_minutes": 360,
                "efficiency_rate": 42.9
            }
        """
        if self.use_mock:
            return self._generate_mock_data()["summary"]
        
        if not self.task_list:
            return {
                "date": self.date_str,
                "error": "タスクデータが見つかりません",
                "total_tasks": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "completion_rate": 0,
                "total_estimated_minutes": 0,
                "total_actual_minutes": 0,
                "efficiency_rate": 0
            }

        tasks = self.task_list.tasks
        completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        in_progress = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        pending = [t for t in tasks if t.status == TaskStatus.PENDING]

        total_actual_minutes = sum(t.actual_minutes or 0 for t in completed)
        total_estimated_minutes = sum(t.estimated_minutes for t in tasks)

        completion_rate = (len(completed) / len(tasks) * 100) if tasks else 0
        efficiency_rate = (total_actual_minutes / total_estimated_minutes * 100) if total_estimated_minutes > 0 else 0

        return {
            "date": self.date_str,
            "total_tasks": len(tasks),
            "completed": len(completed),
            "in_progress": len(in_progress),
            "pending": len(pending),
            "completion_rate": round(completion_rate, 1),
            "total_estimated_minutes": total_estimated_minutes,
            "total_actual_minutes": total_actual_minutes,
            "efficiency_rate": round(efficiency_rate, 1)
        }

    def get_staff_progress(self) -> List[Dict[str, Any]]:
        """スタッフ別進捗を取得

        Returns:
            [
                {
                    "staff": "細谷",
                    "total_tasks": 20,
                    "completed": 12,
                    "in_progress": 2,
                    "pending": 6,
                    "completion_rate": 60.0,
                    "actual_minutes": 240,
                    "status_icon": "✅"  # 60%以上: ✅, 40-60%: 🟡, 40%未満: 🔴
                },
                ...
            ]
        """
        if self.use_mock:
            return self._generate_mock_data()["staff_progress"]
        
        if not self.task_list:
            return []

        staff_stats = defaultdict(lambda: {
            'total_tasks': 0,
            'completed': 0,
            'in_progress': 0,
            'pending': 0,
            'actual_minutes': 0
        })

        for task in self.task_list.tasks:
            staff = task.assigned_to or "未割当"
            stats = staff_stats[staff]

            stats['total_tasks'] += 1

            if task.status == TaskStatus.COMPLETED:
                stats['completed'] += 1
                stats['actual_minutes'] += task.actual_minutes or 0
            elif task.status == TaskStatus.IN_PROGRESS:
                stats['in_progress'] += 1
            elif task.status == TaskStatus.PENDING:
                stats['pending'] += 1

        result = []
        for staff, stats in staff_stats.items():
            completion_rate = (stats['completed'] / stats['total_tasks'] * 100) if stats['total_tasks'] > 0 else 0

            # ステータスアイコン決定
            if completion_rate >= 60:
                status_icon = "✅"
            elif completion_rate >= 40:
                status_icon = "🟡"
            else:
                status_icon = "🔴"

            result.append({
                "staff": staff,
                "total_tasks": stats['total_tasks'],
                "completed": stats['completed'],
                "in_progress": stats['in_progress'],
                "pending": stats['pending'],
                "completion_rate": round(completion_rate, 1),
                "actual_minutes": stats['actual_minutes'],
                "status_icon": status_icon
            })

        # 完了率降順でソート（未割当は最後）
        result.sort(key=lambda x: (x['staff'] == '未割当', -x['completion_rate']))

        return result

    def get_alerts(self) -> List[Dict[str, str]]:
        """警告・注意事項を取得

        Returns:
            [
                {"level": "warning", "message": "佐々木: 進行中タスクが滞留（3件）"},
                {"level": "error", "message": "未割当タスク: 15件"},
                ...
            ]
        """
        if self.use_mock:
            return self._generate_mock_data()["alerts"]
        
        if not self.task_list:
            return []

        alerts = []
        summary = self.get_summary()

        # 完了率が低い
        if summary['completion_rate'] < 30:
            alerts.append({
                "level": "error",
                "message": f"完了率が低い（{summary['completion_rate']}%）"
            })
        elif summary['completion_rate'] < 50:
            alerts.append({
                "level": "warning",
                "message": f"完了率が低い（{summary['completion_rate']}%）"
            })

        # 進行中タスクが多い
        if summary['in_progress'] > 10:
            alerts.append({
                "level": "warning",
                "message": f"進行中タスクが多い（{summary['in_progress']}件）"
            })

        # スタッフ別の進行中タスク滞留
        staff_progress = self.get_staff_progress()
        for staff_data in staff_progress:
            if staff_data['staff'] != '未割当' and staff_data['in_progress'] >= 3:
                alerts.append({
                    "level": "warning",
                    "message": f"{staff_data['staff']}: 進行中タスクが滞留（{staff_data['in_progress']}件）"
                })

        # 未割当タスク
        unassigned_count = next((s['total_tasks'] for s in staff_progress if s['staff'] == '未割当'), 0)
        if unassigned_count > 0:
            alerts.append({
                "level": "error",
                "message": f"未割当タスク: {unassigned_count}件"
            })

        return alerts

    def get_manager_data(self) -> Dict[str, Any]:
        """マネージャーモード用の詳細データを取得

        Returns:
            {
                "current_time": "14:35",
                "next_checkpoint": {"time": "17:00", "remaining_minutes": 145},
                "morning_vs_actual": [...],
                "bottlenecks": [...],
                "estimated_finish_time": "18:45"
            }
        """
        if self.use_mock:
            return self._generate_mock_data()["manager_data"]
        
        if not self.task_list:
            return {
                "current_time": datetime.now().strftime("%H:%M"),
                "next_checkpoint": None,
                "morning_vs_actual": [],
                "bottlenecks": [],
                "estimated_finish_time": None
            }

        now = datetime.now()
        current_time = now.strftime("%H:%M")

        # 次のチェックポイント計算（14:00, 17:00）
        checkpoints = ["14:00", "17:00"]
        next_checkpoint = None
        for cp in checkpoints:
            cp_hour, cp_min = map(int, cp.split(":"))
            cp_time = now.replace(hour=cp_hour, minute=cp_min, second=0)
            if now < cp_time:
                remaining = int((cp_time - now).total_seconds() / 60)
                next_checkpoint = {
                    "time": cp,
                    "remaining_minutes": remaining
                }
                break

        # 朝の予測 vs 実績
        morning_vs_actual = []
        if self.task_list.morning_summary:
            ms = self.task_list.morning_summary
            tasks = self.task_list.tasks

            # タスク種別ごとの実績集計
            type_stats = defaultdict(lambda: {"completed": 0, "total": 0})
            for task in tasks:
                task_type = task.type.value
                type_stats[task_type]["total"] += 1
                if task.status == TaskStatus.COMPLETED:
                    type_stats[task_type]["completed"] += 1

            # 朝の予測との比較
            comparisons = [
                ("査定", ms.satei_waiting),
                ("修理", ms.shuri_needed),
                ("検品", ms.kenpin_needed),
                ("出品", ms.shuppin_ready),
                ("開封", ms.kaifuu_count),
                ("アクティベート", ms.activate_count),
            ]

            for task_name, predicted in comparisons:
                if predicted > 0:
                    stats = type_stats.get(task_name, {"completed": 0, "total": 0})
                    completion_rate = (stats["completed"] / predicted * 100) if predicted > 0 else 0

                    status = "on_track"
                    if completion_rate < 40:
                        status = "delayed"
                    elif completion_rate >= 80:
                        status = "ahead"

                    morning_vs_actual.append({
                        "task_type": task_name,
                        "predicted": predicted,
                        "completed": stats["completed"],
                        "completion_rate": round(completion_rate, 1),
                        "status": status
                    })

        # ボトルネック検出（処理時間が予定より長いタスク）
        bottlenecks = []
        if self.task_list:
            tasks = self.task_list.tasks
            completed = [t for t in tasks if t.status == TaskStatus.COMPLETED and t.actual_minutes]

            # タスク種別ごとの平均処理時間
            type_times = defaultdict(lambda: {"total_actual": 0, "total_estimated": 0, "count": 0})
            for task in completed:
                task_type = task.type.value
                type_times[task_type]["total_actual"] += task.actual_minutes
                type_times[task_type]["total_estimated"] += task.estimated_minutes
                type_times[task_type]["count"] += 1

            for task_type, times in type_times.items():
                if times["count"] > 0:
                    avg_actual = times["total_actual"] / times["count"]
                    avg_estimated = times["total_estimated"] / times["count"]
                    ratio = avg_actual / avg_estimated if avg_estimated > 0 else 1.0

                    if ratio >= 1.5:  # 1.5倍以上遅い
                        bottlenecks.append({
                            "task_type": task_type,
                            "avg_actual_minutes": round(avg_actual, 1),
                            "avg_estimated_minutes": round(avg_estimated, 1),
                            "ratio": round(ratio, 1),
                            "message": f"{task_type}: 平均処理時間が予定の{ratio:.1f}倍"
                        })

            # スタッフ別の滞留タスク検出
            in_progress_tasks = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
            staff_in_progress = defaultdict(list)
            for task in in_progress_tasks:
                if task.assigned_to and task.started_at:
                    duration = (now - task.started_at).total_seconds() / 60
                    if duration > 60:  # 1時間以上進行中
                        staff_in_progress[task.assigned_to].append({
                            "task_id": task.id,
                            "task_type": task.type.value,
                            "duration_minutes": int(duration)
                        })

            for staff, tasks_list in staff_in_progress.items():
                if len(tasks_list) >= 3:
                    bottlenecks.append({
                        "staff": staff,
                        "in_progress_count": len(tasks_list),
                        "message": f"{staff}: {len(tasks_list)}件のタスクが長時間進行中"
                    })

        # 予想終了時刻（簡易計算）
        estimated_finish_time = None
        summary = self.get_summary()
        if summary["pending"] > 0 and summary["completed"] > 0:
            # 完了タスクの平均処理時間を使って残りタスクの所要時間を予測
            avg_time_per_task = summary["total_actual_minutes"] / summary["completed"]
            remaining_minutes = int(avg_time_per_task * summary["pending"])
            finish_time = now + timedelta(minutes=remaining_minutes)
            estimated_finish_time = finish_time.strftime("%H:%M")

        return {
            "current_time": current_time,
            "next_checkpoint": next_checkpoint,
            "morning_vs_actual": morning_vs_actual,
            "bottlenecks": bottlenecks,
            "estimated_finish_time": estimated_finish_time
        }

    def get_dashboard_data(self) -> Dict[str, Any]:
        """ダッシュボード用の全データを一括取得

        Returns:
            {
                "summary": {...},
                "staff_progress": [...],
                "alerts": [...],
                "manager_data": {...},
                "last_updated": "2025-11-01T10:35:00"
            }
        """
        return {
            "summary": self.get_summary(),
            "staff_progress": self.get_staff_progress(),
            "alerts": self.get_alerts(),
            "manager_data": self.get_manager_data(),
            "last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }


def main():
    """テスト用エントリーポイント"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="ダッシュボード用データ取得API")
    parser.add_argument('--date', help='対象日 (YYYY-MM-DD形式、省略時は今日)')
    parser.add_argument('--endpoint',
                       choices=['summary', 'staff', 'alerts', 'all'],
                       default='all',
                       help='取得するデータ種別')

    args = parser.parse_args()

    api = DashboardAPI(args.date)

    if args.endpoint == 'summary':
        data = api.get_summary()
    elif args.endpoint == 'staff':
        data = api.get_staff_progress()
    elif args.endpoint == 'alerts':
        data = api.get_alerts()
    else:  # all
        data = api.get_dashboard_data()

    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
