#!/usr/bin/env python3
"""
iPhone 16シリーズの価格分析

- 現在の買取価格
- 現在の販売価格
- 手数料引き後の販売価格（販売価格 × 0.89）
- 粗利（手数料引き後 - 買取価格）
- 粗利率
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent

# 最新の価格ファイル
BUYBACK_FILE = BASE_DIR / "買取価格20251119.csv"
SALES_FILE = BASE_DIR / "販売価格_新品バッテリー版_20251121.csv"

# 手数料率（BM手数料11%）
COMMISSION_RATE = 0.11
COMMISSION_MULTIPLIER = 1 - COMMISSION_RATE  # 0.89

# iPhone 16シリーズ
IPHONE16_MODELS = ['iPhone 16', 'iPhone 16 Plus', 'iPhone 16 Pro', 'iPhone 16 Pro Max']

def main():
    print("=" * 80)
    print("📊 iPhone 16シリーズ 価格分析")
    print("=" * 80)
    print()

    # 買取価格を読み込み
    df_buyback = pd.read_csv(BUYBACK_FILE, encoding='utf-8-sig')
    df_buyback = df_buyback.rename(columns={
        '機体型番': '機種',
        '記憶容量': '容量',
        '等級': 'ランク',
        '高額買取価格': '買取価格'
    })
    print(f"📂 買取価格: {BUYBACK_FILE.name}")
    print(f"   全体: {len(df_buyback)} 行")

    # 販売価格を読み込み
    df_sales = pd.read_csv(SALES_FILE, encoding='utf-8-sig')
    df_sales = df_sales.rename(columns={
        'グレード': 'ランク',
        '新品バッテリー版_平均売価': '販売価格'
    })
    # ランクマッピング（プレミアム→新品・未開封）
    rank_mapping = {
        'プレミアム': '新品・未開封',
        'A': '新品同様',
        'B': '美品',
        'C': '使用感あり'
    }
    df_sales['ランク'] = df_sales['ランク'].map(rank_mapping)

    print(f"📂 販売価格: {SALES_FILE.name}")
    print(f"   全体: {len(df_sales)} 行")
    print()

    # iPhone 16シリーズのみ抽出
    df_buyback_16 = df_buyback[df_buyback['機種'].isin(IPHONE16_MODELS)].copy()
    df_sales_16 = df_sales[df_sales['機種'].isin(IPHONE16_MODELS)].copy()

    print(f"📱 iPhone 16シリーズ")
    print(f"   買取価格: {len(df_buyback_16)} 行")
    print(f"   販売価格: {len(df_sales_16)} 行")
    print()

    # データを結合（販売価格に買取価格を結合）
    df_merged = pd.merge(
        df_sales_16[['機種', '容量', 'ランク', '販売価格']],
        df_buyback_16[['機種', '容量', 'ランク', '買取価格']],
        on=['機種', '容量', 'ランク'],
        how='outer'
    )

    # 手数料引き後の販売価格を計算
    df_merged['販売価格_手数料引後'] = (df_merged['販売価格'] * COMMISSION_MULTIPLIER).round(0).astype('Int64')

    # 粗利を計算
    df_merged['粗利'] = df_merged['販売価格_手数料引後'] - df_merged['買取価格']

    # 粗利率を計算
    df_merged['粗利率'] = (df_merged['粗利'] / df_merged['買取価格'] * 100).round(2)

    # カラムを整理
    df_result = df_merged[[
        '機種', '容量', 'ランク',
        '買取価格', '販売価格', '販売価格_手数料引後',
        '粗利', '粗利率'
    ]].copy()

    df_result = df_result.rename(columns={
        '販売価格': '販売価格（BM）'
    })

    # 機種・容量・ランクでソート
    model_order = {'iPhone 16': 1, 'iPhone 16 Plus': 2, 'iPhone 16 Pro': 3, 'iPhone 16 Pro Max': 4}
    capacity_order = {'1TB': 1, '512GB': 2, '256GB': 3, '128GB': 4}
    rank_order = {'S': 1, 'A': 2, 'B': 3, 'C': 4}

    df_result['_model_order'] = df_result['機種'].map(model_order)
    df_result['_capacity_order'] = df_result['容量'].map(capacity_order)
    df_result['_rank_order'] = df_result['ランク'].map(rank_order)

    df_result = df_result.sort_values(['_model_order', '_capacity_order', '_rank_order'])
    df_result = df_result.drop(columns=['_model_order', '_capacity_order', '_rank_order'])

    # 結果を表示
    print("=" * 120)
    print("📊 iPhone 16シリーズ 価格一覧")
    print("=" * 120)
    print()

    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', 120)
    print(df_result.to_string(index=False))
    print()

    # 統計情報
    print("=" * 80)
    print("📈 統計情報")
    print("=" * 80)
    print()

    for model in IPHONE16_MODELS:
        df_model = df_result[df_result['機種'] == model]
        if len(df_model) > 0:
            avg_margin = df_model['粗利'].mean()
            avg_margin_rate = df_model['粗利率'].mean()
            print(f"{model}:")
            print(f"  平均粗利: ¥{avg_margin:,.0f}")
            print(f"  平均粗利率: {avg_margin_rate:.2f}%")
            print()

    # CSVに保存
    output_file = Path(__file__).parent.parent / "data" / "results" / "iphone16_pricing_analysis.csv"
    df_result.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"💾 結果を保存: {output_file}")


if __name__ == "__main__":
    main()
