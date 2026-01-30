#!/usr/bin/env python3
"""
スタッフ通称を追加するスクリプト

CLAUDE.mdのスタッフスキルマトリックスから通称を抽出して staff.yaml に追加
"""

from pathlib import Path
import yaml

# パス設定
BASE_DIR = Path(__file__).parent.parent
STAFF_YAML = BASE_DIR / "config" / "staff.yaml"

# 通称マッピング（CLAUDE.mdより）
NICKNAMES = {
    "江口": "なっちゃん",
    "雜賀": "はるし",
    "野口": "さら",  # 野口器の通称
    "佐々木": "ゆうと",
    "須加尾": "れん",
    "高橋": "りょう",
    "島田": "ひろふみ",
    "平山": "ゆうだい",
    "細谷": "たかひろ",
    "NANT": "シャシャ",
    "原": "くれは",
    "本間": "ひさたか",
}


def add_nicknames():
    """staff.yamlに通称フィールドを追加"""

    # YAMLファイル読み込み
    with open(STAFF_YAML, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # 各スタッフに通称を追加
    updated_count = 0
    for staff_key in data['staff']:
        if staff_key in NICKNAMES:
            data['staff'][staff_key]['nickname'] = NICKNAMES[staff_key]
            updated_count += 1
            print(f"✅ {staff_key}: {data['staff'][staff_key]['full_name']} → 通称: {NICKNAMES[staff_key]}")
        else:
            # 通称がない場合はnullを設定
            data['staff'][staff_key]['nickname'] = None
            print(f"⚠️  {staff_key}: 通称なし")

    # YAMLファイルに書き戻し
    with open(STAFF_YAML, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print()
    print("=" * 70)
    print(f"✅ {updated_count}人の通称を追加しました")
    print("=" * 70)


if __name__ == "__main__":
    add_nicknames()
