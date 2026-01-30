#!/usr/bin/env python3
"""
iPhone 16シリーズ 買取価格調整案の作成

現状の問題:
- 複数の構成で赤字（粗利マイナス）
- 平均粗利率が低い（Pro: 7.07%, Pro Max: 4.95%）

目標:
- 全構成で黒字化
- 目標粗利率: 15%（最低ライン）〜20%（推奨）
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

# 目標粗利率
TARGET_MARGIN_MIN = 15.0  # 最低ライン
TARGET_MARGIN_RECOMMENDED = 20.0  # 推奨

def calculate_recommended_buyback(sales_price_after_fee, target_margin_rate):
    """
    目標粗利率から推奨買取価格を逆算

    粗利率 = (販売価格_手数料引後 - 買取価格) / 買取価格 * 100

    買取価格 = 販売価格_手数料引後 / (1 + 粗利率/100)
    """
    return sales_price_after_fee / (1 + target_margin_rate / 100)

def main():
    print("=" * 100)
    print("📊 iPhone 16シリーズ 買取価格調整案")
    print("=" * 100)
    print()

    # 買取価格を読み込み
    df_buyback = pd.read_csv(BUYBACK_FILE, encoding='utf-8-sig')
    df_buyback = df_buyback.rename(columns={
        '機体型番': '機種',
        '記憶容量': '容量',
        '等級': 'ランク',
        '高額買取価格': '現在の買取価格'
    })
    print(f"📂 買取価格: {BUYBACK_FILE.name}")

    # 販売価格を読み込み
    df_sales = pd.read_csv(SALES_FILE, encoding='utf-8-sig')
    df_sales = df_sales.rename(columns={
        'グレード': 'ランク',
        '新品バッテリー版_平均売価': '販売価格'
    })
    # ランクマッピング
    rank_mapping = {
        'プレミアム': '新品・未開封',
        'A': '新品同様',
        'B': '美品',
        'C': '使用感あり'
    }
    df_sales['ランク'] = df_sales['ランク'].map(rank_mapping)

    print(f"📂 販売価格: {SALES_FILE.name}")
    print()

    # iPhone 16シリーズのみ抽出
    df_buyback_16 = df_buyback[df_buyback['機種'].isin(IPHONE16_MODELS)].copy()
    df_sales_16 = df_sales[df_sales['機種'].isin(IPHONE16_MODELS)].copy()

    # データを結合
    df_merged = pd.merge(
        df_sales_16[['機種', '容量', 'ランク', '販売価格']],
        df_buyback_16[['機種', '容量', 'ランク', '現在の買取価格']],
        on=['機種', '容量', 'ランク'],
        how='outer'
    )

    # 手数料引き後の販売価格
    df_merged['販売価格_手数料引後'] = (df_merged['販売価格'] * COMMISSION_MULTIPLIER).round(0).astype('Int64')

    # 現在の粗利・粗利率
    df_merged['現在の粗利'] = df_merged['販売価格_手数料引後'] - df_merged['現在の買取価格']
    df_merged['現在の粗利率'] = (df_merged['現在の粗利'] / df_merged['現在の買取価格'] * 100).round(2)

    # 推奨買取価格（粗利率15%）
    df_merged['推奨買取価格_15%'] = df_merged['販売価格_手数料引後'].apply(
        lambda x: calculate_recommended_buyback(x, TARGET_MARGIN_MIN)
    ).round(0).astype('Int64')

    # 推奨買取価格（粗利率20%）
    df_merged['推奨買取価格_20%'] = df_merged['販売価格_手数料引後'].apply(
        lambda x: calculate_recommended_buyback(x, TARGET_MARGIN_RECOMMENDED)
    ).round(0).astype('Int64')

    # 価格差（現在 - 推奨15%）
    df_merged['価格差_15%'] = df_merged['現在の買取価格'] - df_merged['推奨買取価格_15%']

    # 価格差（現在 - 推奨20%）
    df_merged['価格差_20%'] = df_merged['現在の買取価格'] - df_merged['推奨買取価格_20%']

    # カラムを整理
    df_result = df_merged[[
        '機種', '容量', 'ランク',
        '販売価格', '販売価格_手数料引後',
        '現在の買取価格', '現在の粗利', '現在の粗利率',
        '推奨買取価格_15%', '価格差_15%',
        '推奨買取価格_20%', '価格差_20%'
    ]].copy()

    # ソート
    model_order = {'iPhone 16': 1, 'iPhone 16 Plus': 2, 'iPhone 16 Pro': 3, 'iPhone 16 Pro Max': 4}
    capacity_order = {'1TB': 1, '512GB': 2, '256GB': 3, '128GB': 4}
    rank_order = {'S': 1, 'A': 2, 'B': 3, 'C': 4}

    df_result['_model_order'] = df_result['機種'].map(model_order)
    df_result['_capacity_order'] = df_result['容量'].map(capacity_order)
    df_result['_rank_order'] = df_result['ランク'].map(rank_order)

    df_result = df_result.sort_values(['_model_order', '_capacity_order', '_rank_order'])
    df_result = df_result.drop(columns=['_model_order', '_capacity_order', '_rank_order'])

    # 結果を表示
    print("=" * 140)
    print("📊 iPhone 16シリーズ 価格調整案")
    print("=" * 140)
    print()

    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', 140)
    pd.set_option('display.max_columns', None)
    print(df_result.to_string(index=False))
    print()

    # 問題のある構成を抽出（現在の粗利率が15%未満）
    df_problem = df_result[df_result['現在の粗利率'] < TARGET_MARGIN_MIN].copy()

    if len(df_problem) > 0:
        print("=" * 100)
        print("⚠️ 粗利率15%未満の構成（要調整）")
        print("=" * 100)
        print()
        print(df_problem[['機種', '容量', 'ランク', '現在の買取価格', '現在の粗利率', '推奨買取価格_15%', '価格差_15%']].to_string(index=False))
        print()

    # 赤字構成を抽出
    df_loss = df_result[df_result['現在の粗利'] < 0].copy()

    if len(df_loss) > 0:
        print("=" * 100)
        print("🚨 赤字構成（緊急調整必要）")
        print("=" * 100)
        print()
        print(df_loss[['機種', '容量', 'ランク', '現在の買取価格', '現在の粗利', '推奨買取価格_15%', '価格差_15%']].to_string(index=False))
        print()

    # 統計サマリー
    print("=" * 100)
    print("📈 調整サマリー")
    print("=" * 100)
    print()

    print(f"総構成数: {len(df_result)}")
    print(f"赤字構成: {len(df_loss)} 件")
    print(f"粗利率15%未満: {len(df_problem)} 件")
    print()

    for model in IPHONE16_MODELS:
        df_model = df_result[df_result['機種'] == model]
        if len(df_model) > 0:
            avg_current_margin = df_model['現在の粗利率'].mean()
            avg_price_diff_15 = df_model['価格差_15%'].mean()
            avg_price_diff_20 = df_model['価格差_20%'].mean()
            print(f"{model}:")
            print(f"  現在の平均粗利率: {avg_current_margin:.2f}%")
            print(f"  平均調整額（15%目標）: -¥{avg_price_diff_15:,.0f}")
            print(f"  平均調整額（20%目標）: -¥{avg_price_diff_20:,.0f}")
            print()

    # CSVに保存
    output_file = Path(__file__).parent.parent / "data" / "results" / "iphone16_price_recommendations.csv"
    df_result.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"💾 結果を保存: {output_file}")
    print()

    # 実装用のCSV（買取価格テーブル形式）を作成
    df_implementation = df_result[['機種', '容量', 'ランク', '推奨買取価格_15%', '推奨買取価格_20%']].copy()
    df_implementation = df_implementation.rename(columns={
        '推奨買取価格_15%': '高額買取価格_15%目標',
        '推奨買取価格_20%': '高額買取価格_20%目標'
    })

    impl_file = Path(__file__).parent.parent / "data" / "results" / "iphone16_recommended_buyback_prices.csv"
    df_implementation.to_csv(impl_file, index=False, encoding='utf-8-sig')
    print(f"💾 実装用ファイルを保存: {impl_file}")
    print()

    # 提案
    print("=" * 100)
    print("💡 提案")
    print("=" * 100)
    print()
    print("1. 緊急対応（赤字回避）:")
    print("   - 赤字構成は最低でも粗利率15%まで買取価格を下げる必要があります")
    print("   - iPhone 16 Pro Max 1TB 新品・未開封: ¥236,000 → ¥162,071（-¥73,929）")
    print("   - iPhone 16 Pro 1TB 新品・未開封: ¥213,000 → ¥159,026（-¥53,974）")
    print()
    print("2. 推奨対応（健全な利益確保）:")
    print("   - 粗利率20%を目指すことで、より安定した収益構造になります")
    print("   - iPhone 16 Pro Max 1TB 新品・未開封: ¥236,000 → ¥155,318（-¥80,682）")
    print("   - iPhone 16 Pro 1TB 新品・未開封: ¥213,000 → ¥152,564（-¥60,436）")
    print()
    print("3. 段階的調整案:")
    print("   - 第1段階: 赤字構成のみ15%目標に調整（即座に実施）")
    print("   - 第2段階: 全体を20%目標に調整（1-2週間後、コンバージョン率を見ながら）")
    print()


if __name__ == "__main__":
    main()
