#!/usr/bin/env python3
"""
既存の日別ファイルから統合ファイル(all_data.csv)を生成
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "data" / "results"

def main():
    print("=" * 60)
    print("📊 統合ファイル生成")
    print("=" * 60)
    print()

    # 既存の日別ファイルを検索
    daily_files = list(RESULTS_DIR.glob("collected_data_*.csv"))

    if not daily_files:
        print("❌ 日別ファイルが見つかりません")
        return

    print(f"📂 {len(daily_files)} 個の日別ファイルを発見:")
    for f in sorted(daily_files):
        print(f"   - {f.name}")
    print()

    # 全てのファイルを読み込み
    dfs = []
    for file in daily_files:
        df = pd.read_csv(file, encoding='utf-8-sig')
        df['日付'] = pd.to_datetime(df['日付'])

        # カラム名が旧版の場合は修正
        if 'キット数' in df.columns:
            df = df.rename(columns={'キット数': 'キット・集荷数'})

        dfs.append(df)
        print(f"   ✅ {file.name} - {len(df)} 行")

    # 統合
    df_all = pd.concat(dfs, ignore_index=True)

    # 日付でソート
    df_all = df_all.sort_values(by='日付')

    # 機種・容量順にソート用の関数をインポート
    import sys
    sys.path.append(str(Path(__file__).parent))
    from collect_data import get_iphone_model_order, get_capacity_value

    # ソート用のカラムを追加
    df_all['_model_order'] = df_all['機種'].apply(get_iphone_model_order)
    df_all['_capacity_value'] = df_all['容量'].apply(get_capacity_value)

    # ソート: 日付（古い順）→ 機種（新しい順）→ 容量（大きい順）→ ランク
    df_all = df_all.sort_values(
        by=['日付', '_model_order', '_capacity_value', 'ランク'],
        ascending=[True, True, False, True]
    )

    # ソート用カラムを削除
    df_all = df_all.drop(columns=['_model_order', '_capacity_value'])

    # インデックスをリセット
    df_all = df_all.reset_index(drop=True)

    # 保存
    all_data_file = RESULTS_DIR / "all_data.csv"
    df_all.to_csv(all_data_file, index=False, encoding='utf-8-sig')

    print()
    print("=" * 60)
    print("✅ 統合ファイル生成完了")
    print("=" * 60)
    print(f"💾 保存先: {all_data_file}")
    print(f"📅 収録期間: {df_all['日付'].min().date()} ～ {df_all['日付'].max().date()}")
    print(f"📊 総日数: {df_all['日付'].nunique()} 日")
    print(f"📊 総レコード数: {len(df_all)} 行")

if __name__ == "__main__":
    main()
