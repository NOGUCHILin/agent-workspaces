#!/usr/bin/env python3
"""
YAMLファイルのバリデーションスクリプト

使用例:
  uv run python scripts/validate.py --all
  uv run python scripts/validate.py config/staff.yaml
  uv run python scripts/validate.py --verbose
"""

import sys
import argparse
from pathlib import Path
from typing import List, Tuple

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scripts"))

from models import StaffConfig, DailyTaskList, validate_file


def validate_config_files(verbose: bool = False) -> List[Tuple[str, bool, str]]:
    """config/配下のYAMLファイルを検証"""
    results = []
    config_dir = project_root / "config"

    if not config_dir.exists():
        return [("config/", False, "ディレクトリが存在しません")]

    # staff.yaml
    staff_yaml = config_dir / "staff.yaml"
    if staff_yaml.exists():
        success, error = validate_file(str(staff_yaml), StaffConfig)
        results.append((str(staff_yaml.relative_to(project_root)), success, error or "OK"))

    return results


def validate_task_files(verbose: bool = False) -> List[Tuple[str, bool, str]]:
    """tasks/配下のYAMLファイルを検証"""
    results = []
    tasks_dir = project_root / "tasks"

    if not tasks_dir.exists():
        return [("tasks/", False, "ディレクトリが存在しません")]

    # active/配下の全YAMLファイル
    active_dir = tasks_dir / "active"
    if active_dir.exists():
        for yaml_file in active_dir.glob("*.yaml"):
            success, error = validate_file(str(yaml_file), DailyTaskList)
            results.append((str(yaml_file.relative_to(project_root)), success, error or "OK"))

    return results


def validate_specific_file(filepath: str) -> Tuple[bool, str]:
    """特定のファイルを検証"""
    path = Path(filepath)

    if not path.exists():
        return False, f"ファイルが存在しません: {filepath}"

    # ファイルパスから適切なモデルクラスを判定
    if "staff.yaml" in str(path):
        model_class = StaffConfig
    elif "tasks/" in str(path):
        model_class = DailyTaskList
    else:
        return False, "未対応のファイル形式です"

    return validate_file(filepath, model_class)


def print_results(results: List[Tuple[str, bool, str]], verbose: bool = False):
    """検証結果を出力"""
    success_count = sum(1 for _, success, _ in results if success)
    total_count = len(results)

    print("\n" + "=" * 60)
    print("バリデーション結果")
    print("=" * 60 + "\n")

    for filepath, success, message in results:
        if success:
            print(f"✓ {filepath}: OK")
            if verbose and message != "OK":
                print(f"  詳細: {message}")
        else:
            print(f"✗ {filepath}: FAILED")
            print(f"  エラー: {message}")

    print("\n" + "-" * 60)
    print(f"結果: {success_count}/{total_count} ファイルが正常")
    print("-" * 60 + "\n")

    return success_count == total_count


def main():
    parser = argparse.ArgumentParser(
        description="タスク管理システムのYAMLファイルバリデーション"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="検証するファイルパス（指定しない場合は--allが必要）"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="全ファイルを検証"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="詳細情報を表示"
    )

    args = parser.parse_args()

    results = []

    if args.all:
        # 全ファイル検証
        results.extend(validate_config_files(args.verbose))
        results.extend(validate_task_files(args.verbose))
    elif args.files:
        # 指定されたファイルのみ検証
        for filepath in args.files:
            success, message = validate_specific_file(filepath)
            results.append((filepath, success, message))
    else:
        parser.print_help()
        return 1

    if not results:
        print("検証するファイルが見つかりませんでした")
        return 1

    all_success = print_results(results, args.verbose)

    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
