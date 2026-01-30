"""
異常値の調査

価格差が大きいデータの詳細を確認し、原因を特定する
"""

import pandas as pd
import json
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / "reports"
RAW_DATA_DIR = BASE_DIR / "data" / "raw"


def load_latest_comparison():
    """最新の比較レポートを読み込み"""
    reports = list(REPORTS_DIR.glob("internal_vs_competitor_*.csv"))
    if not reports:
        raise FileNotFoundError("比較レポートが見つかりません")

    latest = max(reports, key=lambda p: p.stat().st_mtime)
    print(f"📂 レポート読み込み: {latest.name}")

    df = pd.read_csv(latest)
    return df


def investigate_anomaly(row):
    """特定のモデルの異常値を詳細調査"""
    model = row['model']
    capacity = row['capacity']
    condition = row['condition']

    print(f"\n{'=' * 80}")
    print(f"🔍 調査対象: {model} {capacity} ({row['condition_original']})")
    print(f"{'=' * 80}")
    print(f"弊社価格: ¥{row['buyback_price']:,.0f}")
    print(f"競合平均: ¥{row['avg_price']:,.0f}")
    print(f"価格差: ¥{row['price_diff']:,.0f} ({row['price_diff_pct']:+.1f}%)")

    # 競合の生データを確認
    print(f"\n📊 競合の生データを確認中...")

    # じゃんぱらのデータを確認
    janpara_dir = RAW_DATA_DIR / "janpara"
    janpara_data = []

    for file in janpara_dir.glob("*.json"):
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                if (item.get('model') == model and
                    item.get('capacity') == capacity and
                    item.get('condition') == condition):
                    janpara_data.append(item)

    # イオシスのデータを確認
    iosys_dir = RAW_DATA_DIR / "iosys"
    iosys_data = []

    for file in iosys_dir.glob("*.json"):
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                if (item.get('model') == model and
                    item.get('capacity') == capacity and
                    item.get('condition') == condition):
                    iosys_data.append(item)

    # じゃんぱらのデータ表示
    if janpara_data:
        print(f"\n【じゃんぱら】({len(janpara_data)}件)")
        for i, item in enumerate(janpara_data[:10], 1):  # 最大10件表示
            print(f"  {i}. {item['product_name']}")
            print(f"     価格: ¥{item['buyback_price']:,}")
            print(f"     状態: {item['condition']}")
            print(f"     URL: {item['url']}")
            print()
    else:
        print("\n【じゃんぱら】データなし")

    # イオシスのデータ表示
    if iosys_data:
        print(f"\n【イオシス】({len(iosys_data)}件)")
        for i, item in enumerate(iosys_data[:10], 1):  # 最大10件表示
            print(f"  {i}. {item['product_name']}")
            print(f"     価格: ¥{item['buyback_price']:,}")
            print(f"     状態: {item['condition']}")
            if 'carrier' in item:
                print(f"     キャリア: {item['carrier']}")
            print()
    else:
        print("\n【イオシス】データなし")

    # 価格の統計
    all_prices = [item['buyback_price'] for item in janpara_data + iosys_data]
    if all_prices:
        print(f"\n📈 価格統計:")
        print(f"  最小: ¥{min(all_prices):,}")
        print(f"  最大: ¥{max(all_prices):,}")
        print(f"  平均: ¥{sum(all_prices)/len(all_prices):,.0f}")
        print(f"  中央値: ¥{sorted(all_prices)[len(all_prices)//2]:,}")


def main():
    """メイン処理"""
    print("\n" + "=" * 80)
    print("異常値調査")
    print("=" * 80)

    # 最新の比較レポートを読み込み
    df = load_latest_comparison()

    # 価格差が大きいデータを抽出（弊社が低い）
    # 競合データがあるもののみ
    valid_df = df[df['avg_price'].notna()].copy()

    # 価格差が大きい順にソート（絶対値）
    valid_df['abs_price_diff'] = valid_df['price_diff'].abs()
    anomalies = valid_df.nlargest(5, 'abs_price_diff')

    print(f"\n📊 価格差が大きいTOP5を調査します")
    print("=" * 80)

    # 各異常値を調査
    for idx, row in anomalies.iterrows():
        investigate_anomaly(row)
        print("\n" + "=" * 80)
        input("次の調査に進むにはEnterを押してください...")


if __name__ == "__main__":
    main()
