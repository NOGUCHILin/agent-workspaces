#!/usr/bin/env python3
"""
スキルシートCSVからstaff-skills.yamlを生成

使い方:
  uv run python scripts/generate_staff_skills.py ~/Downloads/スキルシート.csv
  uv run python scripts/generate_staff_skills.py ~/Downloads/スキルシート.csv --dry-run
"""

import csv
import sys
import yaml
from pathlib import Path
from typing import Dict, Any

# コアスキル（詳細管理が必要）
CORE_SKILLS = {"査定", "検品", "出品", "修理"}


def load_existing_staff_skills() -> Dict[str, Dict[str, Any]]:
    """既存のstaff.yamlからコアスキル情報を読み込み"""
    staff_yaml = Path("config/staff.yaml")
    if not staff_yaml.exists():
        print("⚠️  config/staff.yaml が見つかりません")
        return {}

    with open(staff_yaml, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # スタッフ名 → コアスキル詳細のマッピングを作成
    existing_skills = {}
    for staff_name, staff_info in data.get('staff', {}).items():
        existing_skills[staff_name] = staff_info.get('skills', {})

    return existing_skills


def load_skill_sheet(csv_path: str) -> Dict[str, Dict[str, bool]]:
    """
    スキルシートCSVを読み込み

    Returns:
        {
            "江口 那都": {"返信": True, "振込メッセ": True, ...},
            ...
        }
    """
    skill_matrix = {}

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)

        # ヘッダー行（スキル名）
        header = next(reader)
        skill_names = [skill.strip() for skill in header[1:]]  # 1列目はスタッフ名なのでスキップ

        # データ行
        for row in reader:
            if not row or not row[0]:
                continue

            # スタッフ名を抽出（"江口 那都" のような形式）
            full_name = row[0].strip()

            # スキルのマッピング
            skills = {}
            for i, skill_name in enumerate(skill_names, start=1):
                if i < len(row):
                    # "○" がある場合はTrue
                    has_skill = row[i].strip() == "○"
                    if has_skill:
                        skills[skill_name] = True

            skill_matrix[full_name] = skills

    return skill_matrix


def generate_staff_skills_yaml(
    skill_matrix: Dict[str, Dict[str, bool]],
    existing_skills: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    staff-skills.yaml形式のデータを生成

    Args:
        skill_matrix: スキルシートから読み込んだマトリックス
        existing_skills: 既存のコアスキル情報
    """
    staff_skills = {}

    for full_name, skills in skill_matrix.items():
        # スタッフ名（短縮形）を取得
        # "江口 那都" → "江口"
        staff_key = full_name.split()[0] if " " in full_name else full_name

        staff_skills[staff_key] = {}

        for skill_name in skills.keys():
            if skill_name in CORE_SKILLS:
                # コアスキル → 既存のレベル・効率値を引き継ぐ
                if staff_key in existing_skills and skill_name in existing_skills[staff_key]:
                    # 既存データを使用
                    staff_skills[staff_key][skill_name] = existing_skills[staff_key][skill_name]
                else:
                    # デフォルト値を設定
                    staff_skills[staff_key][skill_name] = {
                        "level": 2,
                        "speed_factor": 1.0,
                        "certification": False
                    }
            else:
                # 拡張スキル → 空オブジェクト
                staff_skills[staff_key][skill_name] = {}

    return {"staff_skills": staff_skills}


def save_yaml(data: Dict[str, Any], output_path: str) -> None:
    """YAMLファイルに保存"""
    with open(output_path, 'w', encoding='utf-8') as f:
        # ヘッダーコメント
        f.write("# スタッフ×スキル関連テーブル\n")
        f.write("# スタッフとスキルの多対多関連を管理\n")
        f.write("# 最終更新: 2025-10-21\n")
        f.write("# 生成元: スキルシートCSV\n\n")

        # YAMLデータ
        yaml.dump(
            data,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            indent=2
        )


def main():
    if len(sys.argv) < 2:
        print("使い方: uv run python scripts/generate_staff_skills.py <csv_path> [--dry-run]")
        sys.exit(1)

    csv_path = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    if not Path(csv_path).exists():
        print(f"❌ ファイルが見つかりません: {csv_path}")
        sys.exit(1)

    print("📋 スキルシートCSVを読み込み中...")
    skill_matrix = load_skill_sheet(csv_path)
    print(f"✓ {len(skill_matrix)}名のスタッフを読み込みました")

    print("\n📖 既存のコアスキル情報を読み込み中...")
    existing_skills = load_existing_staff_skills()
    print(f"✓ {len(existing_skills)}名の既存データを読み込みました")

    print("\n🔨 staff-skills.yamlを生成中...")
    staff_skills_data = generate_staff_skills_yaml(skill_matrix, existing_skills)

    # 統計情報を表示
    total_skills = sum(len(skills) for skills in staff_skills_data["staff_skills"].values())
    core_count = sum(
        1 for skills in staff_skills_data["staff_skills"].values()
        for skill_name in skills.keys()
        if skill_name in CORE_SKILLS
    )
    extended_count = total_skills - core_count

    print(f"✓ 生成完了:")
    print(f"  - スタッフ数: {len(staff_skills_data['staff_skills'])}名")
    print(f"  - 総スキル数: {total_skills}件")
    print(f"  - コアスキル: {core_count}件")
    print(f"  - 拡張スキル: {extended_count}件")

    if dry_run:
        print("\n🔍 Dry-runモード: ファイルは作成しません")
        print("\n--- 生成されるYAMLプレビュー（最初の2名） ---")
        preview_data = {
            "staff_skills": dict(list(staff_skills_data["staff_skills"].items())[:2])
        }
        print(yaml.dump(preview_data, allow_unicode=True, sort_keys=False, default_flow_style=False))
    else:
        output_path = "config/staff-skills.yaml"
        save_yaml(staff_skills_data, output_path)
        print(f"\n✅ {output_path} を作成しました")


if __name__ == "__main__":
    main()
