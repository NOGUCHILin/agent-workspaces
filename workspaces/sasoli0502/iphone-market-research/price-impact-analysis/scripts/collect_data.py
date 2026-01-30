#!/usr/bin/env python3
"""
買取価格変更 効果計測 - データ収集スクリプト

LINE仮査定、梱包キット、集荷要請のデータを収集・整形し、
コンバージョン率を計算する。

【重要】実際のデータ形式:
- 1行 = 1件のレコード（集計済みではない）
- エンコーディング: Shift-JIS
- 日付: スクリプト実行時の日付を自動取得
- 集荷・キット数: 同一データ
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# ============================================================
# 設定
# ============================================================

# ディレクトリパス
BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
RESULTS_DIR = BASE_DIR / "data" / "results"
SOURCE_DIR = BASE_DIR.parent / "daily-data"  # iphone-market-research/daily-data ディレクトリ

# 結果ディレクトリを作成
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# 除外機種
EXCLUDE_MODELS = ['iPhone 7', 'iPhone 8', 'iPhone 8 Plus']

# カラム名のマッピング（実際のCSVに合わせて調整）
# 新形式: 1行 = 1件のレコード
COLUMN_MAPPING = {
    'line_estimates': {
        'record_id': 'レコード番号',
        'model': '機種',
        'capacity': '容量',
        'rank': 'ランク',
    },
    'packing_kits': {
        'record_id': 'レコード番号',
        'model': '機種',
        'capacity': '容量',
        'rank': 'ランク',
    },
}

# ============================================================
# データ読み込み関数
# ============================================================

def find_latest_data_file(base_dir: Path, prefix: str) -> Path:
    """
    最新のデータファイルを検索

    Args:
        base_dir: 検索ディレクトリ
        prefix: ファイル名の接頭辞

    Returns:
        最新ファイルのパス
    """
    pattern = f"{prefix}*.csv"
    files = list(base_dir.glob(pattern))

    if not files:
        raise FileNotFoundError(f"{prefix}*.csv が {base_dir} に見つかりません")

    # 最新ファイルを取得（更新日時でソート）
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    return latest_file


def load_raw_csv(file_path: Path, data_type: str) -> pd.DataFrame:
    """
    生CSVファイル（1行=1レコード形式）を読み込み、正規化する

    Args:
        file_path: CSVファイルのパス
        data_type: データタイプ ('line_estimates', 'packing_kits')

    Returns:
        正規化されたDataFrame
    """
    if not file_path.exists():
        print(f"⚠️  警告: {file_path} が見つかりません")
        return pd.DataFrame()

    try:
        # Shift-JISエンコーディングで読み込み
        df = pd.read_csv(file_path, encoding='shift-jis')
        print(f"   ✅ {file_path.name} - {len(df)} レコード")

        # カラム名を正規化
        mapping = COLUMN_MAPPING[data_type]
        rename_dict = {}
        for std_name, actual_name in mapping.items():
            if actual_name in df.columns:
                rename_dict[actual_name] = std_name

        df = df.rename(columns=rename_dict)

        # 空行を削除（機種が空のレコード）
        if 'model' in df.columns:
            before_count = len(df)
            df = df[df['model'].notna() & (df['model'] != '')]
            after_count = len(df)
            if before_count != after_count:
                print(f"   🗑️  空行を削除: {before_count - after_count} 行")

        # 除外機種を削除
        if 'model' in df.columns:
            before_count = len(df)
            df = df[~df['model'].isin(EXCLUDE_MODELS)]
            after_count = len(df)
            if before_count != after_count:
                print(f"   🗑️  除外機種を削除: {before_count - after_count} 行")

        # 容量が空の場合は「不明」とする
        if 'capacity' in df.columns:
            df['capacity'] = df['capacity'].fillna('不明')
            df.loc[df['capacity'] == '', 'capacity'] = '不明'

        return df

    except Exception as e:
        print(f"   ❌ {file_path.name} の読み込みエラー: {e}")
        return pd.DataFrame()


def get_iphone_model_order(model: str) -> int:
    """
    iPhone機種を発売が新しい順にソートするためのキーを返す

    Args:
        model: 機種名

    Returns:
        ソート用の数値（小さいほど新しい）
    """
    # iPhone機種の発売順序（新しい順）
    order = {
        'iPhone 17': 10,
        'iPhone 17 Pro': 11,
        'iPhone 17 Pro Max': 12,
        'iPhone 16e': 20,
        'iPhone 16': 21,
        'iPhone 16 Plus': 22,
        'iPhone 16 Pro': 23,
        'iPhone 16 Pro Max': 24,
        'iPhone Air': 25,
        'iPhone 15': 30,
        'iPhone 15 Plus': 31,
        'iPhone 15 Pro': 32,
        'iPhone 15 Pro Max': 33,
        'iPhone 14': 40,
        'iPhone 14 Plus': 41,
        'iPhone 14 Pro': 42,
        'iPhone 14 Pro Max': 43,
        'iPhone 13': 50,
        'iPhone 13 mini': 51,
        'iPhone 13 Pro': 52,
        'iPhone 13 Pro Max': 53,
        'iPhone 12': 60,
        'iPhone 12 mini': 61,
        'iPhone 12 Pro': 62,
        'iPhone 12 Pro Max': 63,
        'iPhone 11': 70,
        'iPhone 11 Pro': 71,
        'iPhone 11 Pro Max': 72,
        'iPhone XS': 80,
        'iPhone XS Max': 81,
        'iPhone XR': 82,
        'iPhone X': 90,
        'iPhone SE（第3世代）': 100,
        'iPhone SE（第2世代）': 101,
        'iPhone SE（第1世代）': 102,
        'iPhone 8': 110,
        'iPhone 8 Plus': 111,
        'iPhone 7': 120,
        'iPhone 7 Plus': 121,
        'iPhone 6s': 130,
        'iPhone 6s Plus': 131,
    }
    return order.get(model, 999)  # 不明な機種は最後


def get_capacity_value(capacity: str) -> int:
    """
    容量を数値に変換（大きい順にソート用）

    Args:
        capacity: 容量文字列（例: "128GB", "1TB"）

    Returns:
        容量のGB換算値（大きいほど大きい）
    """
    if pd.isna(capacity) or capacity == '不明' or capacity == '':
        return -1

    capacity_str = str(capacity).upper()

    if 'TB' in capacity_str:
        # TBをGBに変換
        try:
            return int(capacity_str.replace('TB', '').strip()) * 1024
        except:
            return -1
    elif 'GB' in capacity_str:
        try:
            return int(capacity_str.replace('GB', '').strip())
        except:
            return -1
    else:
        return -1


def aggregate_records(df: pd.DataFrame, date: str) -> pd.DataFrame:
    """
    レコードデータを機種・容量・ランク別に集計

    Args:
        df: レコード単位のDataFrame
        date: 日付文字列 (YYYY-MM-DD)

    Returns:
        集計されたDataFrame
    """
    if df.empty:
        return pd.DataFrame()

    # 機種・容量・ランク別に件数をカウント
    grouped = df.groupby(['model', 'capacity', 'rank']).size().reset_index(name='count')

    # 日付カラムを追加
    grouped['date'] = pd.to_datetime(date)

    # カラム順を整理
    grouped = grouped[['date', 'model', 'capacity', 'rank', 'count']]

    return grouped


# ============================================================
# メイン処理
# ============================================================

def main():
    print("=" * 60)
    print("📊 買取価格変更 効果計測 - データ収集")
    print("=" * 60)
    print()

    # 実行日時を取得
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    print(f"📅 実行日時: {date_str} {time_str}")
    print()

    # 1. LINE仮査定データの読み込み
    print("🔹 STEP 1: LINE仮査定データ")
    try:
        line_file = find_latest_data_file(SOURCE_DIR, "LINE仮査定データ")
        print(f"   📂 対象ファイル: {line_file.name}")
        df_estimates_raw = load_raw_csv(line_file, 'line_estimates')
        print(f"   📊 不良なし端末（絞り込み済み）: {len(df_estimates_raw)} レコード")

        # 機種・容量・ランク別に集計
        df_estimates = aggregate_records(df_estimates_raw, date_str)
        print(f"   📊 集計結果: {len(df_estimates)} 行（機種・容量・ランク別）")
        print()
    except FileNotFoundError as e:
        print(f"   ❌ エラー: {e}")
        return

    # 2. 梱包キット・集荷データの読み込み
    print("🔹 STEP 2: 梱包キット・集荷データ")
    try:
        kit_file = find_latest_data_file(SOURCE_DIR, "集荷・キット数")
        print(f"   📂 対象ファイル: {kit_file.name}")
        df_kits_raw = load_raw_csv(kit_file, 'packing_kits')
        print(f"   📊 梱包キット・集荷レコード: {len(df_kits_raw)} レコード")

        # 機種・容量・ランク別に集計
        df_kits = aggregate_records(df_kits_raw, date_str)
        print(f"   📊 集計結果: {len(df_kits)} 行（機種・容量・ランク別）")
        print()
    except FileNotFoundError as e:
        print(f"   ❌ エラー: {e}")
        return

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

        # 欠損値を0で埋める
        df_combined['count_estimate'] = df_combined['count_estimate'].fillna(0).astype(int)
        df_combined['count_kit'] = df_combined['count_kit'].fillna(0).astype(int)

        # コンバージョン率を計算
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

        # ソート用のカラムを追加
        df_combined['_model_order'] = df_combined['機種'].apply(get_iphone_model_order)
        df_combined['_capacity_value'] = df_combined['容量'].apply(get_capacity_value)

        # ソート: 機種（新しい順）→ 容量（大きい順）→ ランク
        df_combined = df_combined.sort_values(
            by=['_model_order', '_capacity_value', 'ランク'],
            ascending=[True, False, True]
        )

        # ソート用カラムを削除
        df_combined = df_combined.drop(columns=['_model_order', '_capacity_value'])

        # インデックスをリセット
        df_combined = df_combined.reset_index(drop=True)

        print(f"   ✅ 統合完了: {len(df_combined)} 行")
        print()

        # 4. 保存
        print("🔹 STEP 4: データ保存")

        # 日次データとして保存
        date_suffix = now.strftime("%Y%m%d")
        daily_file = RESULTS_DIR / f"collected_data_{date_suffix}.csv"
        all_data_file = RESULTS_DIR / "all_data.csv"

        # 日別ファイルを保存
        df_combined.to_csv(daily_file, index=False, encoding='utf-8-sig')
        print(f"   💾 日別ファイル保存完了: {daily_file}")

        # 統合ファイルの更新
        if all_data_file.exists():
            # 既存の統合ファイルを読み込み
            df_all = pd.read_csv(all_data_file, encoding='utf-8-sig')
            df_all['日付'] = pd.to_datetime(df_all['日付'])

            # 今日のデータを削除（重複を避ける）
            df_all = df_all[df_all['日付'] != pd.to_datetime(date_str)]

            # 新しいデータを追加
            df_all = pd.concat([df_all, df_combined], ignore_index=True)
        else:
            # 初回は今日のデータのみ
            df_all = df_combined.copy()

        # 日付でソート
        df_all = df_all.sort_values(by='日付')

        # ソート用のカラムを追加（機種・容量順）
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
        print(f"収集時刻: {time_str}")
        print(f"総レコード数: {len(df_combined)} 行")
        print(f"機種数: {df_combined['機種'].nunique()} 機種")
        print(f"総仮査定数: {df_combined['仮査定数'].sum()} 件")
        print(f"総キット・集荷数: {df_combined['キット・集荷数'].sum()} 件")

        total_estimates = df_combined['仮査定数'].sum()
        total_kits = df_combined['キット・集荷数'].sum()
        overall_conversion = (total_kits / total_estimates * 100) if total_estimates > 0 else 0
        print(f"全体コンバージョン率: {overall_conversion:.2f}%")

        # 機種別トップ5を表示
        print()
        print("📊 仮査定数トップ5:")
        top5 = df_combined.nlargest(5, '仮査定数')[['機種', '容量', 'ランク', '仮査定数', 'キット・集荷数', 'コンバージョン率']]
        for idx, row in top5.iterrows():
            print(f"   {row['機種']} {row['容量']} {row['ランク']}: 仮査定{row['仮査定数']}件 → キット{row['キット・集荷数']}件 ({row['コンバージョン率']:.1f}%)")

    else:
        print("   ⚠️  データが不足しているため、統合をスキップします")


if __name__ == "__main__":
    main()
