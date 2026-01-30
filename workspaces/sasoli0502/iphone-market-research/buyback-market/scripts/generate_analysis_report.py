"""
価格分析レポート生成スクリプト

弊社 vs 競合の価格比較データから、ビジネス判断用の詳細分析レポートを作成する
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# パス設定
REPORTS_DIR = Path(__file__).parent.parent / "reports"

def load_latest_report():
    """最新の比較レポートを読み込む"""
    csv_files = list(REPORTS_DIR.glob("internal_vs_competitor_*.csv"))
    if not csv_files:
        raise FileNotFoundError("比較レポートが見つかりません")

    latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
    print(f"📂 レポート読み込み: {latest_file.name}\n")

    df = pd.read_csv(latest_file)
    return df


def analyze_price_positioning(df):
    """価格ポジショニング分析"""
    print("=" * 80)
    print("📊 価格ポジショニング分析")
    print("=" * 80)

    # 競合データがあるもののみ
    valid_data = df[df['avg_price'].notna()].copy()

    print(f"\n分析対象: {len(valid_data)}件\n")

    # 競争力別の集計
    print("🏆 競争力の分布:")
    comp_dist = valid_data['competitiveness'].value_counts()
    for comp, count in comp_dist.items():
        pct = count / len(valid_data) * 100
        print(f"  {comp}: {count}件 ({pct:.1f}%)")

    # 価格差の統計
    print(f"\n💰 価格差の統計:")
    print(f"  平均価格差: ¥{valid_data['price_diff'].mean():,.0f}")
    print(f"  中央値: ¥{valid_data['price_diff'].median():,.0f}")
    print(f"  標準偏差: ¥{valid_data['price_diff'].std():,.0f}")
    print(f"  最大価格差: ¥{valid_data['price_diff'].max():,.0f}")
    print(f"  最小価格差: ¥{valid_data['price_diff'].min():,.0f}")

    # 価格差率の統計
    print(f"\n📈 価格差率の統計:")
    print(f"  平均価格差率: {valid_data['price_diff_pct'].mean():.1f}%")
    print(f"  中央値: {valid_data['price_diff_pct'].median():.1f}%")
    print(f"  標準偏差: {valid_data['price_diff_pct'].std():.1f}%")

    return valid_data


def analyze_by_model(df):
    """モデル別分析"""
    print("\n" + "=" * 80)
    print("📱 モデル別分析")
    print("=" * 80)

    model_stats = df.groupby('model').agg({
        'price_diff': ['mean', 'count'],
        'price_diff_pct': 'mean',
        'competitiveness': lambda x: (x == 'かなり高い').sum() / len(x) * 100
    }).round(1)

    model_stats.columns = ['平均価格差', 'データ件数', '平均価格差率(%)', '高価格比率(%)']
    model_stats = model_stats.sort_values('平均価格差', ascending=False)

    print("\n⬆️ 弊社が高いモデル TOP10:")
    print(model_stats.head(10).to_string())

    print("\n⬇️ 弊社が低いモデル TOP10:")
    print(model_stats.tail(10).to_string())

    return model_stats


def analyze_by_capacity(df):
    """容量別分析"""
    print("\n" + "=" * 80)
    print("💾 容量別分析")
    print("=" * 80)

    capacity_stats = df.groupby('capacity').agg({
        'price_diff': ['mean', 'count'],
        'price_diff_pct': 'mean'
    }).round(1)

    capacity_stats.columns = ['平均価格差', 'データ件数', '平均価格差率(%)']
    capacity_stats = capacity_stats.sort_values('平均価格差', ascending=False)

    print("\n容量別の価格ポジショニング:")
    print(capacity_stats.to_string())

    return capacity_stats


def analyze_by_condition(df):
    """状態別分析"""
    print("\n" + "=" * 80)
    print("🔍 状態別分析")
    print("=" * 80)

    condition_stats = df.groupby('condition_original').agg({
        'price_diff': ['mean', 'count'],
        'price_diff_pct': 'mean'
    }).round(1)

    condition_stats.columns = ['平均価格差', 'データ件数', '平均価格差率(%)']

    # 状態の順序
    condition_order = ['新品・未開封', '新品同様', '美品', '使用感あり', '目立つ傷あり', '外装ジャンク']
    condition_stats = condition_stats.reindex(
        [c for c in condition_order if c in condition_stats.index]
    )

    print("\n状態別の価格ポジショニング:")
    print(condition_stats.to_string())

    return condition_stats


def find_opportunities(df):
    """価格改定の機会を発見"""
    print("\n" + "=" * 80)
    print("💡 価格改定の機会")
    print("=" * 80)

    # 弊社が大幅に高い（値下げ検討）
    print("\n📉 値下げ検討対象（弊社が競合より30%以上高い）:")
    overpriced = df[df['price_diff_pct'] > 30].sort_values('price_diff_pct', ascending=False)

    if len(overpriced) > 0:
        print(f"  対象件数: {len(overpriced)}件\n")
        for i, row in overpriced.head(10).iterrows():
            print(f"  {row['model']} {row['capacity']} ({row['condition_original']})")
            print(f"    弊社: ¥{row['buyback_price']:,.0f} | 競合平均: ¥{row['avg_price']:,.0f} | 差額: +{row['price_diff_pct']:.1f}%")
    else:
        print("  該当なし")

    # 弊社が大幅に低い（値上げ検討）- ただし異常値は除外
    print("\n📈 値上げ検討対象（弊社が競合より20%以上低く、異常値でないもの）:")
    underpriced = df[
        (df['price_diff_pct'] < -20) &
        (df['price_diff_pct'] > -60) &  # 異常値除外
        (df['data_count'] >= 3)  # データが少なすぎるものを除外
    ].sort_values('price_diff_pct')

    if len(underpriced) > 0:
        print(f"  対象件数: {len(underpriced)}件\n")
        for i, row in underpriced.head(10).iterrows():
            print(f"  {row['model']} {row['capacity']} ({row['condition_original']})")
            print(f"    弊社: ¥{row['buyback_price']:,.0f} | 競合平均: ¥{row['avg_price']:,.0f} | 差額: {row['price_diff_pct']:.1f}%")
    else:
        print("  該当なし")

    # 競争優位性が高いモデル（維持推奨）
    print("\n🏅 競争優位モデル（弊社が10-20%高く、競争力を維持）:")
    competitive = df[
        (df['price_diff_pct'] >= 10) &
        (df['price_diff_pct'] <= 20)
    ].sort_values('price_diff_pct', ascending=False)

    if len(competitive) > 0:
        print(f"  対象件数: {len(competitive)}件\n")
        for i, row in competitive.head(10).iterrows():
            print(f"  {row['model']} {row['capacity']} ({row['condition_original']})")
            print(f"    弊社: ¥{row['buyback_price']:,.0f} | 競合平均: ¥{row['avg_price']:,.0f} | 差額: +{row['price_diff_pct']:.1f}%")
    else:
        print("  該当なし")


def save_detailed_excel(df, model_stats, capacity_stats, condition_stats):
    """詳細分析をExcelに保存"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = REPORTS_DIR / f"price_analysis_report_{timestamp}.xlsx"

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # シート1: 全データ
        df.to_excel(writer, sheet_name='全データ', index=False)

        # シート2: モデル別集計
        model_stats.to_excel(writer, sheet_name='モデル別分析')

        # シート3: 容量別集計
        capacity_stats.to_excel(writer, sheet_name='容量別分析')

        # シート4: 状態別集計
        condition_stats.to_excel(writer, sheet_name='状態別分析')

        # シート5: 値下げ検討対象
        overpriced = df[df['price_diff_pct'] > 30].sort_values('price_diff_pct', ascending=False)
        overpriced.to_excel(writer, sheet_name='値下げ検討', index=False)

        # シート6: 値上げ検討対象
        underpriced = df[
            (df['price_diff_pct'] < -20) &
            (df['price_diff_pct'] > -60) &
            (df['data_count'] >= 3)
        ].sort_values('price_diff_pct')
        underpriced.to_excel(writer, sheet_name='値上げ検討', index=False)

    print(f"\n💾 詳細レポート保存: {output_file.name}")
    return output_file


def main():
    """メイン処理"""
    print("=" * 80)
    print("価格分析レポート生成")
    print("=" * 80)
    print()

    # データ読み込み
    df = load_latest_report()

    # 競合データがあるもののみを対象
    valid_data = df[df['avg_price'].notna()].copy()

    # 各種分析
    analyze_price_positioning(valid_data)
    model_stats = analyze_by_model(valid_data)
    capacity_stats = analyze_by_capacity(valid_data)
    condition_stats = analyze_by_condition(valid_data)
    find_opportunities(valid_data)

    # Excel保存
    output_file = save_detailed_excel(df, model_stats, capacity_stats, condition_stats)

    print("\n" + "=" * 80)
    print("✅ 分析完了")
    print("=" * 80)
    print(f"\n詳細レポート: {output_file}")


if __name__ == "__main__":
    main()
