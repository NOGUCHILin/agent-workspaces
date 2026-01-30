#!/usr/bin/env python3
"""
手動で日付を指定してデータ収集を実行するスクリプト

使い方:
    uv run python scripts/collect_data_manual.py 2025-11-23
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from collect_data import (
    load_raw_csv,
    aggregate_records,
    get_iphone_model_order,
    get_capacity_value,
    EXCLUDE_MODELS,
    SOURCE_DIR,
    RESULTS_DIR
)

def main():
    if len(sys.argv) < 2:
        print("使い方: uv run python scripts/collect_data_manual.py YYYY-MM-DD")
        sys.exit(1)

    # 日付を引数から取得
    date_str = sys.argv[1]
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"❌ 無効な日付形式です: {date_str}")
        print("正しい形式: YYYY-MM-DD")
        sys.exit(1)

    print("=" * 60)
    print(f"📊 買取価格変更 効果計測 - データ収集 ({date_str})")
    print("=" * 60)
    print()

    # ファイル名を生成
    date_suffix = target_date.strftime("%Y%m%d")
    line_file = SOURCE_DIR / f"LINE仮査定データ{date_suffix}.csv"
    kit_file = SOURCE_DIR / f"集荷・キット数{date_suffix}.csv"

    # 1. LINE仮査定データの読み込み
    print("🔹 STEP 1: LINE仮査定データ")
    if not line_file.exists():
        print(f"   ❌ エラー: {line_file.name} が見つかりません")
        sys.exit(1)

    print(f"   📂 対象ファイル: {line_file.name}")
    df_estimates_raw = load_raw_csv(line_file, 'line_estimates')
    print(f"   📊 不良なし端末（絞り込み済み）: {len(df_estimates_raw)} レコード")

    df_estimates = aggregate_records(df_estimates_raw, date_str)
    print(f"   📊 集計結果: {len(df_estimates)} 行（機種・容量・ランク別）")
    print()

    # 2. 梱包キット・集荷データの読み込み
    print("🔹 STEP 2: 梱包キット・集荷データ")
    if not kit_file.exists():
        print(f"   ❌ エラー: {kit_file.name} が見つかりません")
        sys.exit(1)

    print(f"   📂 対象ファイル: {kit_file.name}")
    df_kits_raw = load_raw_csv(kit_file, 'packing_kits')
    print(f"   📊 梱包キット・集荷レコード: {len(df_kits_raw)} レコード")

    df_kits = aggregate_records(df_kits_raw, date_str)
    print(f"   📊 集計結果: {len(df_kits)} 行（機種・容量・ランク別）")
    print()

    # 3. データ統合
    print("🔹 STEP 3: データ統合")

    if not df_estimates.empty and not df_kits.empty:
        df_combined = pd.merge(
            df_estimates,
            df_kits,
            on=['date', 'model', 'capacity', 'rank'],
            how='outer',
            suffixes=('_estimate', '_kit')
        )

        df_combined['count_estimate'] = df_combined['count_estimate'].fillna(0).astype(int)
        df_combined['count_kit'] = df_combined['count_kit'].fillna(0).astype(int)

        df_combined['conversion_rate'] = (
            df_combined['count_kit'] / df_combined['count_estimate'] * 100
        ).round(2)
        df_combined.loc[df_combined['count_estimate'] == 0, 'conversion_rate'] = 0

        # カラム名を日本語に変更
        df_combined = df_combined.rename(columns={
            'date': '日付',
            'model': '機種',
            'capacity': '容量',
            'rank': 'ランク',
            'count_estimate': '仮査定数',
            'count_kit': 'キット・集荷数',
            'conversion_rate': 'コンバージョン率'
        })

        # ソート
        df_combined['_model_order'] = df_combined['機種'].apply(get_iphone_model_order)
        df_combined['_capacity_value'] = df_combined['容量'].apply(get_capacity_value)

        df_combined = df_combined.sort_values(
            by=['_model_order', '_capacity_value', 'ランク'],
            ascending=[True, False, True]
        )

        df_combined = df_combined.drop(columns=['_model_order', '_capacity_value'])
        df_combined = df_combined.reset_index(drop=True)

        print(f"   ✅ 統合完了: {len(df_combined)} 行")
        print()

        # 4. 保存
        print("🔹 STEP 4: データ保存")

        daily_file = RESULTS_DIR / f"collected_data_{date_suffix}.csv"
        all_data_file = RESULTS_DIR / "all_data.csv"

        # 日別ファイルを保存
        df_combined.to_csv(daily_file, index=False, encoding='utf-8-sig')
        print(f"   💾 日別ファイル保存完了: {daily_file}")

        # 統合ファイルの更新
        if all_data_file.exists():
            df_all = pd.read_csv(all_data_file, encoding='utf-8-sig')
            df_all['日付'] = pd.to_datetime(df_all['日付'])

            # 該当日のデータを削除（重複を避ける）
            df_all = df_all[df_all['日付'] != pd.to_datetime(date_str)]

            # 新しいデータを追加
            df_all = pd.concat([df_all, df_combined], ignore_index=True)
        else:
            df_all = df_combined.copy()

        # ソート
        df_all = df_all.sort_values(by='日付')

        df_all['_model_order'] = df_all['機種'].apply(get_iphone_model_order)
        df_all['_capacity_value'] = df_all['容量'].apply(get_capacity_value)

        df_all = df_all.sort_values(
            by=['日付', '_model_order', '_capacity_value', 'ランク'],
            ascending=[True, True, False, True]
        )

        df_all = df_all.drop(columns=['_model_order', '_capacity_value'])
        df_all = df_all.reset_index(drop=True)

        # 統合ファイルを保存
        df_all.to_csv(all_data_file, index=False, encoding='utf-8-sig')
        print(f"   💾 統合ファイル更新完了: {all_data_file}")
        print(f"      - 収録期間: {df_all['日付'].min()} ～ {df_all['日付'].max()}")
        print(f"      - 総日数: {df_all['日付'].nunique()} 日")
        print()

        # 5. サマリー表示
        print("=" * 60)
        print("📈 データサマリー")
        print("=" * 60)

        print(f"対象日: {date_str}")
        print(f"総レコード数: {len(df_combined)} 行")
        print(f"機種数: {df_combined['機種'].nunique()} 機種")
        print(f"総仮査定数: {df_combined['仮査定数'].sum()} 件")
        print(f"総キット・集荷数: {df_combined['キット・集荷数'].sum()} 件")

        total_estimates = df_combined['仮査定数'].sum()
        total_kits = df_combined['キット・集荷数'].sum()
        overall_conversion = (total_kits / total_estimates * 100) if total_estimates > 0 else 0
        print(f"全体コンバージョン率: {overall_conversion:.2f}%")

    else:
        print("   ⚠️  データが不足しているため、統合をスキップします")


if __name__ == "__main__":
    main()
