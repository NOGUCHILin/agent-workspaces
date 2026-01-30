"""
買取価格変更 効果分析スクリプト

使い方:
    # 特定の価格変更日を指定して分析
    uv run python scripts/analyze_impact.py --change-date 2025-11-18

    # すべての価格変更を一括分析
    uv run python scripts/analyze_impact.py --all

機能:
    - 価格変更前1週間 vs 変更後1週間の比較
    - 機種・容量・ランク別の分析
    - コンバージョン率の変化を中心に分析
    - 日次推移と週次集計
"""

import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# ============================================================
# 設定
# ============================================================

BASE_DIR = Path(__file__).parent.parent
PRICE_CHANGES_DIR = BASE_DIR / "data" / "price_changes"
RESULTS_DIR = BASE_DIR / "data" / "results"

# 分析期間設定
BEFORE_DAYS = 7  # 価格変更前の分析日数
AFTER_DAYS = 7   # 価格変更後の分析日数

# ============================================================
# 価格変更履歴の読み込み
# ============================================================

def load_price_changes() -> pd.DataFrame:
    """
    価格変更履歴を読み込み

    Returns:
        価格変更履歴のDataFrame
    """
    price_changes_file = PRICE_CHANGES_DIR / "price_changes.csv"

    if not price_changes_file.exists():
        print(f"❌ エラー: {price_changes_file} が見つかりません")
        return pd.DataFrame()

    df = pd.read_csv(price_changes_file)
    df['変更日'] = pd.to_datetime(df['変更日'])

    print(f"📂 価格変更履歴を読み込み: {len(df)} 件")
    return df


# ============================================================
# 収集済みデータの読み込み
# ============================================================

def load_collected_data() -> pd.DataFrame:
    """
    最新の収集済みデータを読み込み

    Returns:
        収集済みデータのDataFrame
    """
    csv_files = list(RESULTS_DIR.glob("collected_data_*.csv"))

    if not csv_files:
        print("❌ エラー: 収集済みデータが見つかりません")
        print("   → まず `scripts/collect_data.py` を実行してください")
        return pd.DataFrame()

    # 最新ファイルを取得
    latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)

    df = pd.read_csv(latest_file)
    df['date'] = pd.to_datetime(df['date'])

    print(f"📂 収集済みデータを読み込み: {latest_file.name}")
    print(f"   対象期間: {df['date'].min()} ～ {df['date'].max()}")
    print(f"   レコード数: {len(df):,} 行")
    print()

    return df


# ============================================================
# 効果分析
# ============================================================

def analyze_price_change_impact(
    df_data: pd.DataFrame,
    change_date: datetime,
    model: str = None,
    capacity: str = None,
    rank: str = None
) -> dict:
    """
    特定の価格変更に対する効果を分析

    Args:
        df_data: 収集済みデータ
        change_date: 価格変更日
        model: 機種（Noneの場合は全機種）
        capacity: 容量（Noneの場合は全容量）
        rank: ランク（Noneの場合は全ランク）

    Returns:
        分析結果の辞書
    """
    # 期間設定
    before_start = change_date - timedelta(days=BEFORE_DAYS)
    before_end = change_date - timedelta(days=1)
    after_start = change_date
    after_end = change_date + timedelta(days=AFTER_DAYS - 1)

    # フィルタリング
    df_filtered = df_data.copy()

    if model:
        df_filtered = df_filtered[df_filtered['model'] == model]
    if capacity:
        df_filtered = df_filtered[df_filtered['capacity'] == capacity]
    if rank:
        df_filtered = df_filtered[df_filtered['rank'] == rank]

    # 変更前データ
    df_before = df_filtered[
        (df_filtered['date'] >= before_start) &
        (df_filtered['date'] <= before_end)
    ]

    # 変更後データ
    df_after = df_filtered[
        (df_filtered['date'] >= after_start) &
        (df_filtered['date'] <= after_end)
    ]

    # 集計
    def aggregate(df: pd.DataFrame) -> dict:
        if df.empty:
            return {
                'total_estimates': 0,
                'total_kits': 0,
                'avg_daily_estimates': 0,
                'avg_daily_kits': 0,
                'conversion_rate': 0,
                'days': 0,
            }

        return {
            'total_estimates': int(df['count_estimate'].sum()),
            'total_kits': int(df['count_kit'].sum()),
            'avg_daily_estimates': round(df['count_estimate'].sum() / len(df['date'].unique()), 1),
            'avg_daily_kits': round(df['count_kit'].sum() / len(df['date'].unique()), 1),
            'conversion_rate': round(
                (df['count_kit'].sum() / df['count_estimate'].sum() * 100) if df['count_estimate'].sum() > 0 else 0,
                2
            ),
            'days': len(df['date'].unique()),
        }

    before_stats = aggregate(df_before)
    after_stats = aggregate(df_after)

    # 変化率計算
    def calc_change_rate(before: float, after: float) -> float:
        if before == 0:
            return 0 if after == 0 else 999.9
        return round((after - before) / before * 100, 2)

    return {
        'change_date': change_date,
        'model': model or '全機種',
        'capacity': capacity or '全容量',
        'rank': rank or '全ランク',
        'before': before_stats,
        'after': after_stats,
        'change': {
            'estimates_rate': calc_change_rate(before_stats['avg_daily_estimates'], after_stats['avg_daily_estimates']),
            'kits_rate': calc_change_rate(before_stats['avg_daily_kits'], after_stats['avg_daily_kits']),
            'conversion_rate_diff': round(after_stats['conversion_rate'] - before_stats['conversion_rate'], 2),
        }
    }


# ============================================================
# 分析結果の表示
# ============================================================

def print_analysis_result(result: dict):
    """
    分析結果を表示

    Args:
        result: analyze_price_change_impact の返り値
    """
    print("=" * 80)
    print(f"📊 価格変更効果分析")
    print("=" * 80)
    print(f"変更日: {result['change_date'].strftime('%Y-%m-%d')}")
    print(f"機種: {result['model']} / 容量: {result['capacity']} / ランク: {result['rank']}")
    print()

    print("【変更前 1週間】")
    print(f"  期間: {BEFORE_DAYS} 日間")
    print(f"  仮査定数: {result['before']['total_estimates']:,} 件 (平均 {result['before']['avg_daily_estimates']:.1f} 件/日)")
    print(f"  梱包キット数: {result['before']['total_kits']:,} 件 (平均 {result['before']['avg_daily_kits']:.1f} 件/日)")
    print(f"  コンバージョン率: {result['before']['conversion_rate']:.2f}%")
    print()

    print("【変更後 1週間】")
    print(f"  期間: {AFTER_DAYS} 日間")
    print(f"  仮査定数: {result['after']['total_estimates']:,} 件 (平均 {result['after']['avg_daily_estimates']:.1f} 件/日)")
    print(f"  梱包キット数: {result['after']['total_kits']:,} 件 (平均 {result['after']['avg_daily_kits']:.1f} 件/日)")
    print(f"  コンバージョン率: {result['after']['conversion_rate']:.2f}%")
    print()

    print("【変化】")
    estimates_change = result['change']['estimates_rate']
    kits_change = result['change']['kits_rate']
    cv_change = result['change']['conversion_rate_diff']

    print(f"  仮査定数: {estimates_change:+.2f}% {'📈' if estimates_change > 0 else '📉' if estimates_change < 0 else '➡️'}")
    print(f"  梱包キット数: {kits_change:+.2f}% {'📈' if kits_change > 0 else '📉' if kits_change < 0 else '➡️'}")
    print(f"  コンバージョン率: {cv_change:+.2f}% ポイント {'✅' if cv_change > 0 else '⚠️' if cv_change < 0 else '➡️'}")
    print()


# ============================================================
# メイン処理
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='買取価格変更の効果分析')
    parser.add_argument('--change-date', type=str, help='価格変更日 (YYYY-MM-DD)')
    parser.add_argument('--all', action='store_true', help='すべての価格変更を分析')
    parser.add_argument('--model', type=str, help='対象機種（指定しない場合は全機種）')
    parser.add_argument('--capacity', type=str, help='対象容量（指定しない場合は全容量）')
    parser.add_argument('--rank', type=str, help='対象ランク（指定しない場合は全ランク）')

    args = parser.parse_args()

    # データ読み込み
    df_data = load_collected_data()
    if df_data.empty:
        return

    if args.all:
        # すべての価格変更を分析
        df_price_changes = load_price_changes()
        if df_price_changes.empty:
            return

        # 変更日ごとにグループ化
        change_dates = df_price_changes['変更日'].unique()

        print(f"🔍 {len(change_dates)} 件の価格変更を分析します\n")

        all_results = []

        for change_date in sorted(change_dates):
            result = analyze_price_change_impact(
                df_data,
                pd.to_datetime(change_date),
                model=args.model,
                capacity=args.capacity,
                rank=args.rank
            )
            print_analysis_result(result)
            all_results.append(result)

        # CSV保存
        today = datetime.now().strftime("%Y%m%d")
        output_file = RESULTS_DIR / f"impact_analysis_{today}.csv"

        results_df = pd.DataFrame([
            {
                '変更日': r['change_date'],
                '機種': r['model'],
                '容量': r['capacity'],
                'ランク': r['rank'],
                '変更前_仮査定数': r['before']['total_estimates'],
                '変更前_キット数': r['before']['total_kits'],
                '変更前_CV率': r['before']['conversion_rate'],
                '変更後_仮査定数': r['after']['total_estimates'],
                '変更後_キット数': r['after']['total_kits'],
                '変更後_CV率': r['after']['conversion_rate'],
                '仮査定数_変化率': r['change']['estimates_rate'],
                'キット数_変化率': r['change']['kits_rate'],
                'CV率_差分': r['change']['conversion_rate_diff'],
            }
            for r in all_results
        ])

        results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"💾 分析結果を保存: {output_file}")

    elif args.change_date:
        # 特定日の分析
        change_date = pd.to_datetime(args.change_date)

        result = analyze_price_change_impact(
            df_data,
            change_date,
            model=args.model,
            capacity=args.capacity,
            rank=args.rank
        )
        print_analysis_result(result)

    else:
        print("❌ エラー: --change-date または --all を指定してください")
        parser.print_help()


if __name__ == "__main__":
    main()
