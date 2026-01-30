"""
D・ジャンクランクのデータを除外するスクリプト
S/A/B/Cランクのみ残す
"""
import json
import re
from pathlib import Path
from typing import List, Dict


def is_junk_or_d_rank(product_name: str, description: str = "") -> bool:
    """
    商品がジャンク・Dランクかどうか判定

    Args:
        product_name: 商品名
        description: 商品説明（オプション）

    Returns:
        True: ジャンク・Dランク（除外対象）
        False: S/A/B/Cランク（保持）
    """
    text = f"{product_name} {description}".upper()

    # ジャンク判定パターン
    junk_patterns = [
        r'ジャンク',
        r'JUNK',
        r'Dランク',
        r'D\s*ランク',
        r'RANK\s*D',
        r'故障',
        r'動作不良',
        r'起動不可',
        r'ボタン不良',
        r'タッチ不良',
        r'画面割れ',
        r'液晶割れ',
        r'バッテリー膨張',
        r'水没',
        r'部品取り',
    ]

    for pattern in junk_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def clean_json_file(input_path: Path, output_path: Path = None) -> Dict:
    """
    JSONファイルからジャンク・Dランクを除外

    Args:
        input_path: 入力JSONファイルパス
        output_path: 出力JSONファイルパス（Noneの場合は上書き）

    Returns:
        統計情報（元の件数、削除件数、残り件数）
    """
    if output_path is None:
        output_path = input_path

    # データ読み込み
    with open(input_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    original_count = len(products)

    # ジャンク・Dランク除外
    cleaned_products = [
        p for p in products
        if not is_junk_or_d_rank(
            p.get('product_name', ''),
            p.get('description', '')
        )
    ]

    removed_count = original_count - len(cleaned_products)

    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_products, f, ensure_ascii=False, indent=2)

    return {
        'file': input_path.name,
        'original': original_count,
        'removed': removed_count,
        'remaining': len(cleaned_products),
    }


def clean_all_rakuten_data():
    """楽天市場の全データからジャンク・Dランクを除外"""
    data_dir = Path('data/raw/rakuten')

    if not data_dir.exists():
        print(f"❌ ディレクトリが存在しません: {data_dir}")
        return

    json_files = list(data_dir.glob('*.json'))

    if not json_files:
        print(f"❌ JSONファイルが見つかりません: {data_dir}")
        return

    print(f"📁 対象ファイル数: {len(json_files)}")
    print()

    total_original = 0
    total_removed = 0
    total_remaining = 0

    files_with_junk = []

    for json_file in sorted(json_files):
        stats = clean_json_file(json_file)

        total_original += stats['original']
        total_removed += stats['removed']
        total_remaining += stats['remaining']

        if stats['removed'] > 0:
            files_with_junk.append(stats)
            print(f"🗑️  {stats['file']}: {stats['removed']}件削除 ({stats['original']} → {stats['remaining']})")

    print()
    print("=" * 60)
    print(f"✅ クリーニング完了")
    print(f"   総商品数: {total_original:,}件")
    print(f"   削除件数: {total_removed:,}件 ({total_removed/total_original*100:.1f}%)")
    print(f"   残り件数: {total_remaining:,}件 ({total_remaining/total_original*100:.1f}%)")
    print(f"   ジャンク含有ファイル: {len(files_with_junk)}/{len(json_files)}ファイル")
    print("=" * 60)


if __name__ == "__main__":
    clean_all_rakuten_data()
