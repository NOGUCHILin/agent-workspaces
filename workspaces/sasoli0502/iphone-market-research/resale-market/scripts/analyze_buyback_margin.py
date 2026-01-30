"""
買取価格と販売価格の比較分析スクリプト

イオシスの買取価格（2025-11-13取得）と楽天市場の販売価格を比較して、
マージン（利益率）を分析します。
"""
import pandas as pd
from pathlib import Path
from datetime import datetime


# イオシスの買取価格データ（2025-11-13時点）
BUYBACK_PRICES = {
    "iPhone 12": {
        "64GB": {"S": 28000, "A": 25000, "B": 22000, "C": 18000, "D/J": 12000},
        "128GB": {"S": 31000, "A": 28000, "B": 25000, "C": 23000, "D/J": 15000},
        "256GB": {"S": 36000, "A": 32000, "B": 28000, "C": 22000, "D/J": 14000},
    },
    "iPhone 13": {
        "128GB": {"S": 48000, "A": 43000, "B": 38000, "C": 30000, "D/J": 20000},
        "256GB": {"S": 51000, "A": 46000, "B": 41000, "C": 32000, "D/J": 21000},
        "512GB": {"S": 57000, "A": 51000, "B": 45000, "C": 36000, "D/J": 23000},
    },
    "iPhone 14": {
        "128GB": {"S": 61000, "A": 55000, "B": 49000, "C": 41000, "D/J": 27000},
        "256GB": {"S": 67000, "A": 62000, "B": 55000, "C": 47000, "D/J": 31000},
        "512GB": {"S": 71000, "A": 67000, "B": 60000, "C": 50000, "D/J": 33000},
    },
}


def analyze_margin():
    """販売価格と買取価格の差額（マージン）を分析"""

    # 楽天の販売価格データを読み込み
    resale_file = Path(__file__).parent.parent / "reports" / "iphone_price_report_rank_20251113_154452.csv"

    if not resale_file.exists():
        print(f"エラー: 販売価格データが見つかりません: {resale_file}")
        return

    df_resale = pd.read_csv(resale_file)

    # 楽天市場のデータのみに絞る
    df_rakuten = df_resale[df_resale['チャネル'] == '楽天市場'].copy()

    print(f"楽天市場の販売価格データ: {len(df_rakuten)}件")
    print(f"対象モデル: {df_rakuten['model'].unique()}")

    # 比較結果を格納
    comparison_results = []

    for model in BUYBACK_PRICES.keys():
        for capacity in BUYBACK_PRICES[model].keys():
            # 販売価格を取得
            resale_data = df_rakuten[
                (df_rakuten['model'] == model) &
                (df_rakuten['capacity'] == capacity)
            ]

            if resale_data.empty:
                print(f"  {model} {capacity}: 販売価格データなし")
                continue

            print(f"\n=== {model} {capacity} ===")

            # ランクごとに比較
            for rank_key, buyback_price in BUYBACK_PRICES[model][capacity].items():
                # ランク名をマッピング
                rank_mapping = {
                    "S": "Sランク",
                    "A": "Aランク",
                    "B": "Bランク",
                    "C": "Cランク",
                    "D/J": "ジャンク"
                }

                rank_name = rank_mapping.get(rank_key, rank_key)

                # 該当ランクの販売価格を取得
                rank_data = resale_data[resale_data['rank'] == rank_name]

                if not rank_data.empty:
                    resale_avg = rank_data['平均価格'].iloc[0]
                    resale_min = rank_data['最低価格'].iloc[0]
                    resale_median = rank_data['中央値'].iloc[0]
                    product_count = rank_data['商品数'].iloc[0]

                    # マージン計算
                    margin_avg = resale_avg - buyback_price
                    margin_rate_avg = (margin_avg / buyback_price * 100) if buyback_price > 0 else 0

                    margin_min = resale_min - buyback_price
                    margin_rate_min = (margin_min / buyback_price * 100) if buyback_price > 0 else 0

                    comparison_results.append({
                        "モデル": model,
                        "容量": capacity,
                        "ランク": rank_name,
                        "買取価格": buyback_price,
                        "販売最低価格": int(resale_min),
                        "販売平均価格": int(resale_avg),
                        "販売中央値": int(resale_median),
                        "商品数": int(product_count),
                        "マージン（平均）": int(margin_avg),
                        "マージン率（平均）": f"{margin_rate_avg:.1f}%",
                        "マージン（最低）": int(margin_min),
                        "マージン率（最低）": f"{margin_rate_min:.1f}%",
                    })

                    print(f"  {rank_name}:")
                    print(f"    買取: ¥{buyback_price:,}")
                    print(f"    販売: ¥{int(resale_min):,} ~ ¥{int(resale_avg):,}")
                    print(f"    マージン: ¥{int(margin_avg):,} ({margin_rate_avg:.1f}%)")
                else:
                    # 販売データがない場合
                    # 「中古（ランク不明）」の平均価格を参考値として使用
                    unknown_data = resale_data[resale_data['rank'] == '中古（ランク不明）']
                    if not unknown_data.empty:
                        resale_avg = unknown_data['平均価格'].iloc[0]
                        margin_avg = resale_avg - buyback_price
                        margin_rate_avg = (margin_avg / buyback_price * 100) if buyback_price > 0 else 0

                        comparison_results.append({
                            "モデル": model,
                            "容量": capacity,
                            "ランク": f"{rank_name}（参考）",
                            "買取価格": buyback_price,
                            "販売最低価格": None,
                            "販売平均価格": int(resale_avg),
                            "販売中央値": None,
                            "商品数": None,
                            "マージン（平均）": int(margin_avg),
                            "マージン率（平均）": f"{margin_rate_avg:.1f}%",
                            "マージン（最低）": None,
                            "マージン率（最低）": None,
                        })

                        print(f"  {rank_name}（参考: 中古ランク不明の平均）:")
                        print(f"    買取: ¥{buyback_price:,}")
                        print(f"    販売平均: ¥{int(resale_avg):,}")
                        print(f"    マージン: ¥{int(margin_avg):,} ({margin_rate_avg:.1f}%)")

    # 結果をDataFrameに変換
    df_comparison = pd.DataFrame(comparison_results)

    # レポート保存
    output_dir = Path(__file__).parent.parent / "reports"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # CSV保存
    csv_file = output_dir / f"buyback_margin_analysis_{timestamp}.csv"
    df_comparison.to_csv(csv_file, index=False, encoding="utf-8-sig")
    print(f"\n✓ CSV保存: {csv_file}")

    # Excel保存
    excel_file = output_dir / f"buyback_margin_analysis_{timestamp}.xlsx"
    df_comparison.to_excel(excel_file, index=False, engine="openpyxl")
    print(f"✓ Excel保存: {excel_file}")

    # サマリー統計
    print("\n=== マージン統計 ===")
    print(f"分析対象: {len(df_comparison)}件")

    # マージン率を数値に変換
    df_comparison['マージン率_数値'] = df_comparison['マージン率（平均）'].str.rstrip('%').astype(float)

    print(f"\nマージン率の分布:")
    print(f"  平均: {df_comparison['マージン率_数値'].mean():.1f}%")
    print(f"  中央値: {df_comparison['マージン率_数値'].median():.1f}%")
    print(f"  最小: {df_comparison['マージン率_数値'].min():.1f}%")
    print(f"  最大: {df_comparison['マージン率_数値'].max():.1f}%")

    print(f"\nマージン金額（平均販売価格基準）:")
    margin_values = df_comparison['マージン（平均）'].dropna()
    print(f"  平均: ¥{int(margin_values.mean()):,}")
    print(f"  中央値: ¥{int(margin_values.median()):,}")
    print(f"  最小: ¥{int(margin_values.min()):,}")
    print(f"  最大: ¥{int(margin_values.max()):,}")


if __name__ == "__main__":
    analyze_margin()
