#!/usr/bin/env python3
"""
iPhone 15シリーズ以降の傾向分析

対象機種:
- iPhone 15 / 15 Plus / 15 Pro / 15 Pro Max
- iPhone 16 / 16 Plus / 16 Pro / 16 Pro Max / 16e
- iPhone 17 / 17 Pro / 17 Pro Max
- iPhone Air
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "data" / "results"

# iPhone 15シリーズ以降の機種リスト
TARGET_MODELS = [
    'iPhone 17', 'iPhone 17 Pro', 'iPhone 17 Pro Max',
    'iPhone 16e', 'iPhone 16', 'iPhone 16 Plus', 'iPhone 16 Pro', 'iPhone 16 Pro Max',
    'iPhone Air',
    'iPhone 15', 'iPhone 15 Plus', 'iPhone 15 Pro', 'iPhone 15 Pro Max'
]

def main():
    print("=" * 80)
    print("📊 iPhone 15シリーズ以降 傾向分析（5日間）")
    print("=" * 80)
    print()

    # all_data.csvを読み込み
    all_data_file = RESULTS_DIR / "all_data.csv"
    if not all_data_file.exists():
        print("❌ all_data.csvが見つかりません")
        return

    df = pd.read_csv(all_data_file, encoding='utf-8-sig')
    df['日付'] = pd.to_datetime(df['日付'])

    # iPhone 15シリーズ以降のみ抽出
    df_15plus = df[df['機種'].isin(TARGET_MODELS)].copy()

    print(f"📅 分析期間: {df['日付'].min().date()} ～ {df['日付'].max().date()}")
    print(f"📊 全体データ: {len(df)} 行")
    print(f"📱 iPhone 15+データ: {len(df_15plus)} 行")
    print()

    # 1. 日別サマリー
    print("=" * 80)
    print("📈 1. 日別サマリー（iPhone 15シリーズ以降）")
    print("=" * 80)
    print()

    daily_summary = df_15plus.groupby('日付').agg({
        '仮査定数': 'sum',
        'キット・集荷数': 'sum'
    }).reset_index()

    daily_summary['コンバージョン率'] = (
        daily_summary['キット・集荷数'] / daily_summary['仮査定数'] * 100
    ).round(2)

    print(daily_summary.to_string(index=False))
    print()

    # 2. 機種別サマリー（全期間）
    print("=" * 80)
    print("📊 2. 機種別サマリー（全5日間合計）")
    print("=" * 80)
    print()

    model_summary = df_15plus.groupby('機種').agg({
        '仮査定数': 'sum',
        'キット・集荷数': 'sum'
    }).reset_index()

    model_summary['コンバージョン率'] = (
        model_summary['キット・集荷数'] / model_summary['仮査定数'] * 100
    ).round(2)

    model_summary = model_summary.sort_values('仮査定数', ascending=False)

    print(model_summary.to_string(index=False))
    print()

    # 3. 容量別サマリー（全期間）
    print("=" * 80)
    print("📦 3. 容量別サマリー（全5日間合計）")
    print("=" * 80)
    print()

    capacity_summary = df_15plus.groupby('容量').agg({
        '仮査定数': 'sum',
        'キット・集荷数': 'sum'
    }).reset_index()

    capacity_summary['コンバージョン率'] = (
        capacity_summary['キット・集荷数'] / capacity_summary['仮査定数'] * 100
    ).round(2)

    capacity_summary = capacity_summary.sort_values('仮査定数', ascending=False)

    print(capacity_summary.to_string(index=False))
    print()

    # 4. ランク別サマリー（全期間）
    print("=" * 80)
    print("🏆 4. ランク別サマリー（全5日間合計）")
    print("=" * 80)
    print()

    rank_summary = df_15plus.groupby('ランク').agg({
        '仮査定数': 'sum',
        'キット・集荷数': 'sum'
    }).reset_index()

    rank_summary['コンバージョン率'] = (
        rank_summary['キット・集荷数'] / rank_summary['仮査定数'] * 100
    ).round(2)

    rank_summary = rank_summary.sort_values('仮査定数', ascending=False)

    print(rank_summary.to_string(index=False))
    print()

    # 5. 機種×日付のピボット（仮査定数）
    print("=" * 80)
    print("📅 5. 機種別日次推移（仮査定数）")
    print("=" * 80)
    print()

    pivot_estimates = df_15plus.pivot_table(
        index='機種',
        columns='日付',
        values='仮査定数',
        aggfunc='sum',
        fill_value=0
    )

    pivot_estimates['合計'] = pivot_estimates.sum(axis=1)
    pivot_estimates = pivot_estimates.sort_values('合計', ascending=False)

    # 日付カラムを文字列に変換（見やすくするため）
    pivot_estimates.columns = [col.strftime('%m/%d') if isinstance(col, pd.Timestamp) else col for col in pivot_estimates.columns]

    print(pivot_estimates.to_string())
    print()

    # 6. 機種×日付のピボット（キット・集荷数）
    print("=" * 80)
    print("📦 6. 機種別日次推移（キット・集荷数）")
    print("=" * 80)
    print()

    pivot_kits = df_15plus.pivot_table(
        index='機種',
        columns='日付',
        values='キット・集荷数',
        aggfunc='sum',
        fill_value=0
    )

    pivot_kits['合計'] = pivot_kits.sum(axis=1)
    pivot_kits = pivot_kits.sort_values('合計', ascending=False)

    # 日付カラムを文字列に変換
    pivot_kits.columns = [col.strftime('%m/%d') if isinstance(col, pd.Timestamp) else col for col in pivot_kits.columns]

    print(pivot_kits.to_string())
    print()

    # 7. トップ10組み合わせ（機種・容量・ランク）
    print("=" * 80)
    print("🎯 7. トップ10組み合わせ（機種・容量・ランク）")
    print("=" * 80)
    print()

    combo_summary = df_15plus.groupby(['機種', '容量', 'ランク']).agg({
        '仮査定数': 'sum',
        'キット・集荷数': 'sum'
    }).reset_index()

    combo_summary['コンバージョン率'] = (
        combo_summary['キット・集荷数'] / combo_summary['仮査定数'] * 100
    ).round(2)

    combo_summary = combo_summary.sort_values('仮査定数', ascending=False).head(10)

    print(combo_summary.to_string(index=False))
    print()

    # 8. コンバージョン率が高い組み合わせ（仮査定数3件以上）
    print("=" * 80)
    print("🚀 8. 高コンバージョン率組み合わせ（仮査定数3件以上）")
    print("=" * 80)
    print()

    high_conv = df_15plus.groupby(['機種', '容量', 'ランク']).agg({
        '仮査定数': 'sum',
        'キット・集荷数': 'sum'
    }).reset_index()

    high_conv['コンバージョン率'] = (
        high_conv['キット・集荷数'] / high_conv['仮査定数'] * 100
    ).round(2)

    high_conv = high_conv[high_conv['仮査定数'] >= 3]
    high_conv = high_conv.sort_values('コンバージョン率', ascending=False).head(10)

    print(high_conv.to_string(index=False))
    print()

    # 9. 日別成長率
    print("=" * 80)
    print("📈 9. 前日比成長率")
    print("=" * 80)
    print()

    daily_summary_sorted = daily_summary.sort_values('日付')
    daily_summary_sorted['仮査定数_前日比'] = daily_summary_sorted['仮査定数'].diff()
    daily_summary_sorted['キット・集荷数_前日比'] = daily_summary_sorted['キット・集荷数'].diff()
    daily_summary_sorted['仮査定数_成長率%'] = (
        daily_summary_sorted['仮査定数_前日比'] / daily_summary_sorted['仮査定数'].shift(1) * 100
    ).round(2)

    print(daily_summary_sorted[['日付', '仮査定数', '仮査定数_前日比', '仮査定数_成長率%', 'キット・集荷数', 'キット・集荷数_前日比']].to_string(index=False))
    print()

    print("=" * 80)
    print("✅ 分析完了")
    print("=" * 80)


if __name__ == "__main__":
    main()
