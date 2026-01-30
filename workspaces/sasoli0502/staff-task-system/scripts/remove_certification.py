#!/usr/bin/env python3
"""
staff-skills.yamlからcertificationを削除するマイグレーションスクリプト
"""

import yaml
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).resolve().parent.parent

def backup_file(filepath: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = filepath.with_suffix(f".yaml.backup.{timestamp}")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return backup_path

def main():
    config_dir = project_root / 'config'
    staff_skills_path = config_dir / 'staff-skills.yaml'
    
    print("=" * 60)
    print("certification削除マイグレーション")
    print("=" * 60)
    print()
    
    with open(staff_skills_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    staff_skills = data.get('staff_skills', {})
    removed_count = 0
    
    for staff_name, skills in staff_skills.items():
        for skill_name, skill_info in skills.items():
            if not skill_info or 'certification' not in skill_info:
                continue
            del skill_info['certification']
            removed_count += 1
    
    print(f"✅ {removed_count}件のcertificationを削除しました")
    print()
    
    backup_path = backup_file(staff_skills_path)
    print(f"💾 バックアップ: {backup_path}")
    
    with open(staff_skills_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    
    print(f"✅ 保存完了: {staff_skills_path}")
    print()

if __name__ == "__main__":
    main()
