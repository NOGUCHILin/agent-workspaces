#!/usr/bin/env python3
"""
3社比較データを正規化（縦持ち変換）

横持ちデータ（企業が列）を縦持ち（企業が行）に変換する
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

def normalize_comparison_data(input_file: str) -> pd.DataFrame:
    """
    横持ちデータを縦持ちに変換

    入力形式:
        機種名, 容量, ランク, じゃんぱら, イオシス, 弊社, ...

    出力形式:
        機種名, 容量, ランク, 企業名, 買取価格
    """
    print("=" * 80)
    print("3社比較データの正規化（縦持ち変換）")
    print("=" * 80)

    # データ読み込み
    print(f"\n📂 読み込み中: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    print(f"✅ {len(df):,}レコード読み込み完了")

    # 必要な列のみ抽出
    key_columns = ['機種名', '容量', 'ランク']
    price_columns = ['じゃんぱら', 'イオシス', '弊社']

    print(f"\n🔄 縦持ちに変換中...")

    # 各企業のデータを縦に積み上げる
    normalized_records = []

    for _, row in df.iterrows():
        for company in price_columns:
            price = row[company]

            # 価格がNULLでない場合のみ追加
            if pd.notna(price):
                normalized_records.append({
                    '機種名': row['機種名'],
                    '容量': row['容量'],
                    'ランク': row['ランク'],
                    '企業名': company,
                    '買取価格': int(price)
                })

    df_normalized = pd.DataFrame(normalized_records)

    print(f"  - 変換前: {len(df):,}レコード（横持ち）")
    print(f"  - 変換後: {len(df_normalized):,}レコード（縦持ち）")

    # ソート: 機種名 -> 容量 -> ランク -> 企業名
    print(f"\n📊 ソート中...")
    df_normalized = df_normalized.sort_values(
        ['機種名', '容量', 'ランク', '企業名']
    ).reset_index(drop=True)

    return df_normalized

def show_statistics(df: pd.DataFrame):
    """統計情報を表示"""
    print("\n" + "=" * 80)
    print("📊 正規化後のデータ統計")
    print("=" * 80)

    print(f"\n総レコード数: {len(df):,}件")
    print(f"\nユニーク機種数: {df['機種名'].nunique()}機種")
    print(f"ユニーク容量数: {df['容量'].nunique()}種類")
    print(f"ユニークランク数: {df['ランク'].nunique()}ランク")

    print(f"\n企業別レコード数:")
    for company, count in df['企業名'].value_counts().items():
        print(f"  - {company}: {count:,}件")

    print(f"\n価格統計:")
    print(f"  - 最小: ¥{df['買取価格'].min():,}")
    print(f"  - 最大: ¥{df['買取価格'].max():,}")
    print(f"  - 平均: ¥{df['買取価格'].mean():,.0f}")
    print(f"  - 中央値: ¥{df['買取価格'].median():,.0f}")

    print(f"\nデータサンプル（最初の10件）:")
    print(df.head(10).to_string(index=False))

def save_normalized_data(df: pd.DataFrame, output_dir: str = 'reports'):
    """正規化データを保存"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_path / 'three_way_comparison_normalized.csv'
    output_file_timestamped = output_path / f'three_way_comparison_normalized_{timestamp}.csv'

    # 保存
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    df.to_csv(output_file_timestamped, index=False, encoding='utf-8-sig')

    print(f"\n💾 保存完了:")
    print(f"  - {output_file}")
    print(f"  - {output_file_timestamped}")

    return output_file

def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("使用方法: uv run python scripts/normalize_comparison.py <CSVファイルパス>")
        print("例: uv run python scripts/normalize_comparison.py reports/three_way_comparison_20251117_162756.csv")
        sys.exit(1)

    input_file = sys.argv[1]

    if not Path(input_file).exists():
        print(f"❌ エラー: ファイルが見つかりません: {input_file}")
        sys.exit(1)

    # 正規化
    df_normalized = normalize_comparison_data(input_file)

    # 統計表示
    show_statistics(df_normalized)

    # 保存
    output_file = save_normalized_data(df_normalized)

    print("\n" + "=" * 80)
    print("✅ 正規化完了")
    print("=" * 80)
    print(f"\n次のステップ:")
    print(f"  1. データ確認:")
    print(f"     uv run python scripts/view_csv.py {output_file}")

if __name__ == '__main__':
    main()
