#!/usr/bin/env python3
"""
役割分担決定支援スクリプト（完全自動版）

朝の集計データとスキルシートを参照して、最適な役割分担を提案・自動作成
task-types.yamlの全タスクタイプに対応した完全自動割り振りシステム
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
import yaml
import json

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from utils import resolve_staff_names, format_staff_name, load_staff_constraints
from assignment_engine import AssignmentEngine, TaskAssignment
from models import AssignmentRequest
from pydantic import ValidationError


def log_execution(date_str: str, present_staff: list, auto_create: bool, dry_run: bool, result: dict):
    """実行履歴をログに記録"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "assignment_history.jsonl"
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "date": date_str,
        "staff_list": present_staff,
        "auto_create": auto_create,
        "dry_run": dry_run,
        "result": result
    }
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


def load_morning_summary(date_str: str):
    """朝の集計データを読み込み"""
    task_file = project_root / "tasks" / "active" / f"{date_str}.yaml"

    if not task_file.exists():
        return None

    with open(task_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    return data.get('morning_summary')


def suggest_assignments(present_staff: list, date_str: str = None, auto_create: bool = False, dry_run: bool = False):
    """役割分担を提案（完全自動版）

    Args:
        present_staff: 出勤スタッフのリスト（ニックネーム可）
        date_str: 対象日（省略時は今日）
        auto_create: Trueの場合、確認なしでタスクを作成
    """

    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # バリデーション実行
    try:
        request = AssignmentRequest(
            staff_list=present_staff,
            date_str=date_str,
            auto_create=auto_create,
            dry_run=dry_run
        )
    except ValidationError as e:
        print("=" * 60)
        print("❌ バリデーションエラー")
        print("=" * 60)
        print()
        for error in e.errors():
            field = error['loc'][0] if error['loc'] else 'unknown'
            msg = error['msg']
            print(f"  • {field}: {msg}")
        print()
        sys.exit(1)

    # 1人のみの場合は警告
    if len(present_staff) == 1:
        print("=" * 60)
        print("⚠️  警告: スタッフが1人のみ指定されています")
        print("=" * 60)
        print()
        print(f"全てのタスクが {present_staff[0]} に集中する可能性があります。")
        print()
        
        if not dry_run and not auto_create:
            response = input("続行しますか？ (y/N): ")
            if response.lower() != 'y':
                print("キャンセルしました。")
                sys.exit(0)
        print()

    print("=" * 60)
    print("🤖 完全自動タスク割り振りシステム v2.0")
    print("=" * 60)
    print()

    print(f"📅 対象日: {date_str}")

    # スタッフ名を正規化して表示
    normalized_staff = resolve_staff_names(present_staff)
    staff_display = [format_staff_name(s, include_nickname=True) for s in normalized_staff]
    print(f"👥 出勤スタッフ: {', '.join(staff_display)}")
    print()

    # 朝の集計データを読み込み
    morning_summary = load_morning_summary(date_str)

    if not morning_summary:
        print("❌ エラー: 朝の集計データが入力されていません")
        print()
        print("💡 まず朝の集計を入力してください:")
        print("   uv run python scripts/input_morning_summary.py --satei 50 --kaifuu 30")
        print()
        sys.exit(1)

    print("📊 朝の集計データ:")
    print(f"  査定待ち: {morning_summary.get('satei_waiting', 0)}台")
    print(f"  開封待ち: {morning_summary.get('kaifuu_count', 0)}台")
    print(f"  修理必要: {morning_summary.get('shuri_needed', 0)}台")
    print(f"  出品可能: {morning_summary.get('shuppin_ready', 0)}台")
    print(f"  未返信: {morning_summary.get('hensin_pending', 0)}件")
    print()

    # 自動割り振りエンジンを実行
    print("🔄 自動割り振りを計算中...")
    print()

    # 制約条件を読み込む
    constraints = load_staff_constraints(date_str)

    engine = AssignmentEngine(
        present_staff=present_staff,
        morning_summary=morning_summary,
        date_str=date_str,
        constraints=constraints
    )

    assignments = engine.assign_all_tasks()

    # 結果表示
    print(engine.get_assignment_summary())

    # タスク数の集計
    total_tasks = sum(a.count for a in assignments)
    print(f"✅ 合計 {total_tasks}件のタスクを {len(normalized_staff)}名に割り当てました")
    print()

    # dry-runモードの場合
    if dry_run:
        print("=" * 60)
        print("🔍 dry-runモード: タスクは作成されません")
        print("=" * 60)
        print()
        print("上記の割り当て案を確認してください。")
        print("実際に作成する場合は --auto-create フラグを追加してください。")
        print()
        
        # 実行履歴をログに記録
        log_execution(
            date_str=date_str,
            present_staff=normalized_staff,
            auto_create=auto_create,
            dry_run=dry_run,
            result={
                "status": "preview",
                "total_tasks": total_tasks,
                "staff_count": len(normalized_staff),
                "assignments": [
                    {"staff": a.staff, "task_type": a.task_type, "count": a.count}
                    for a in assignments
                ]
            }
        )
        return

    # タスク自動作成
    if auto_create:
        print("=" * 60)
        print("🔄 タスクを自動作成します...")
        print()

        # タスク一括作成用のデータを生成
        task_assignments = []
        for assignment in assignments:
            task_assignments.append({
                'staff': assignment.staff,
                'type': assignment.task_type,
                'count': assignment.count,
                'desc': assignment.task_type,
                'priority': assignment.priority,
                'estimated_minutes': int(assignment.estimated_total_minutes / assignment.count) if assignment.count > 0 else 15
            })

        # bulk_create_tasks.pyをインポートして実行
        from bulk_create_tasks import bulk_create_tasks

        created_tasks = bulk_create_tasks(task_assignments, date_str)

        print()
        print("=" * 60)
        print(f"✅ {len(created_tasks)}件のタスクを作成しました")
        print("=" * 60)
        print()
        print("💡 確認コマンド:")
        print("   uv run python scripts/show_status.py")
        print()
        
        # 実行履歴をログに記録
        log_execution(
            date_str=date_str,
            present_staff=normalized_staff,
            auto_create=auto_create,
            dry_run=dry_run,
            result={
                "status": "created",
                "total_tasks": len(created_tasks),
                "staff_count": len(normalized_staff),
                "assignments": [
                    {"staff": a.staff, "task_type": a.task_type, "count": a.count}
                    for a in assignments
                ]
            }
        )
    else:
        print("=" * 60)
        print("💡 タスクを作成する場合は --auto-create フラグを追加してください")
        print()
        print("例:")
        print(f'  uv run python scripts/suggest_assignments.py --staff "{",".join(present_staff)}" --auto-create')
        print()
        
        # 実行履歴をログに記録
        log_execution(
            date_str=date_str,
            present_staff=normalized_staff,
            auto_create=auto_create,
            dry_run=dry_run,
            result={
                "status": "suggested",
                "total_tasks": total_tasks,
                "staff_count": len(normalized_staff),
                "assignments": [
                    {"staff": a.staff, "task_type": a.task_type, "count": a.count}
                    for a in assignments
                ]
            }
        )


def main():
    parser = argparse.ArgumentParser(
        description="完全自動タスク割り振りシステム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 役割分担を提案（タスクは作成しない）
  uv run python scripts/suggest_assignments.py --staff "細谷,江口,シャシャ,佐々木,雜賀"

  # プレビューのみ（dry-run）
  uv run python scripts/suggest_assignments.py --staff "細谷,江口,シャシャ,雜賀" --dry-run

  # 役割分担を提案し、タスクも自動作成（推奨）
  uv run python scripts/suggest_assignments.py --staff "細谷,江口,シャシャ,雜賀" --auto-create

  # 特定日の役割分担
  uv run python scripts/suggest_assignments.py --staff "細谷,江口" --date 2025-10-30

機能:
  - task-types.yamlの全タスクタイプに自動対応
  - スキルマッチングによる最適割り当て
  - 処理能力比率に基づく負荷分散
  - 専門タスク（修理等）の専門スタッフへの集中割り当て
  - ニックネーム自動解決（シャシャ→NANT等）

対応タスク:
  - 査定、検品、出品、修理
  - 開封、アクティベート
  - 梱包キット作成、発送準備、送り状作成
  - 成約仕分
  - その他 quantity_based カテゴリの全タスク
"""
    )
    parser.add_argument(
        '--staff',
        help='出勤スタッフ（カンマ区切り、ニックネーム可）例: "細谷,江口,シャシャ,佐々木,雜賀"'
    )
    parser.add_argument('--date', help='対象日 (YYYY-MM-DD形式、省略時は今日)')
    parser.add_argument('--auto-create', action='store_true', help='確認なしでタスクを自動作成')
    parser.add_argument('--dry-run', action='store_true', help='プレビューのみ（タスクは作成しない）')

    args = parser.parse_args()

    # --staff が指定されていない場合、出勤者入力を促す
    if not args.staff:
        print("=" * 60)
        print("⚠️  出勤スタッフが指定されていません")
        print("=" * 60)
        print()
        print("タスク割り振りを行うには、今日の出勤スタッフを指定してください。")
        print()

        # 利用可能なスタッフ一覧を表示
        from utils import load_staff_info, format_staff_name
        staff_info = load_staff_info()

        print("📋 登録されているスタッフ:")
        for staff_key in sorted(staff_info.keys()):
            print(f"  • {format_staff_name(staff_key, include_nickname=True)}")
        print()

        print("💡 使い方:")
        print("  uv run python scripts/suggest_assignments.py --staff \"スタッフ名1,スタッフ名2,...\"")
        print()
        print("例:")
        print("  # 苗字で指定")
        print("  uv run python scripts/suggest_assignments.py --staff \"細谷,江口,シャシャ,佐々木,雜賀\" --auto-create")
        print()
        print("  # ニックネームで指定")
        print("  uv run python scripts/suggest_assignments.py --staff \"たかひろ,なっちゃん,シャシャ,ゆうと,はるし\" --auto-create")
        print()
        sys.exit(1)

    # スタッフリストをパース
    present_staff = [s.strip() for s in args.staff.split(',')]

    suggest_assignments(present_staff, args.date, args.auto_create, args.dry_run)


if __name__ == "__main__":
    main()
