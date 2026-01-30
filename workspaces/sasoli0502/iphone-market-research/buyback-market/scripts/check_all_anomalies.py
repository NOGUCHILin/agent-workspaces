"""
全異常値の一覧確認

価格差が大きいすべてのデータを一覧表示し、
パターンを分析する
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


def check_model_mismatch(row):
    """
    モデル名のミスマッチをチェック

    Returns:
        bool: ミスマッチがあればTrue
    """
    model = row['model']
    capacity = row['capacity']
    condition = row['condition']

    # じゃんぱらのデータを確認
    janpara_dir = RAW_DATA_DIR / "janpara"
    janpara_models = set()

    for file in janpara_dir.glob("*.json"):
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                if (item.get('capacity') == capacity and
                    item.get('condition') == condition):
                    # モデル名を抽出
                    product_name = item.get('product_name', '')
                    # iPhone XX の部分を抽出
                    import re
                    match = re.search(r'iPhone\s+(?:\d+|X|XR|XS|SE)[^\s]*(?:\s+(?:Pro|Plus|Max|mini))*', product_name)
                    if match:
                        janpara_models.add(match.group())

    # イオシスのデータを確認
    iosys_dir = RAW_DATA_DIR / "iosys"
    iosys_models = set()

    for file in iosys_dir.glob("*.json"):
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                if (item.get('capacity') == capacity and
                    item.get('condition') == condition):
                    iosys_models.add(item.get('model', ''))

    # モデル名が一致するか確認
    all_models = janpara_models | iosys_models

    # 弊社のモデル名が競合のモデル名と一致しない場合はミスマッチ
    if model not in all_models and len(all_models) > 0:
        return True, all_models

    return False, all_models


def main():
    """メイン処理"""
    print("\n" + "=" * 100)
    print("全異常値の一覧確認")
    print("=" * 100)

    # 最新の比較レポートを読み込み
    df = load_latest_comparison()

    # 競合データがあるもののみ
    valid_df = df[df['avg_price'].notna()].copy()

    # 異常値の定義：価格差率が±50%以上
    anomaly_threshold = 50
    anomalies = valid_df[valid_df['price_diff_pct'].abs() >= anomaly_threshold].copy()

    print(f"\n📊 異常値（価格差±{anomaly_threshold}%以上）: {len(anomalies)}件")
    print("=" * 100)

    if len(anomalies) == 0:
        print("\n✅ 異常値は見つかりませんでした")
        return

    # 異常値をソート（絶対値）
    anomalies['abs_price_diff_pct'] = anomalies['price_diff_pct'].abs()
    anomalies = anomalies.sort_values('abs_price_diff_pct', ascending=False)

    # モデル名ミスマッチをチェック
    print("\n🔍 モデル名ミスマッチのチェック中...")
    print("=" * 100)

    mismatch_count = 0
    match_count = 0

    for idx, row in anomalies.iterrows():
        is_mismatch, competitor_models = check_model_mismatch(row)

        if is_mismatch:
            mismatch_count += 1
            print(f"\n⚠️ ミスマッチ #{mismatch_count}")
            print(f"  弊社: {row['model']} {row['capacity']} ({row['condition_original']})")
            print(f"  弊社価格: ¥{row['buyback_price']:,.0f}")
            print(f"  競合平均: ¥{row['avg_price']:,.0f}")
            print(f"  価格差: {row['price_diff_pct']:+.1f}%")
            print(f"  競合のモデル名: {', '.join(sorted(competitor_models))}")
        else:
            match_count += 1

    print("\n" + "=" * 100)
    print("📈 結果サマリー")
    print("=" * 100)
    print(f"異常値の総数: {len(anomalies)}件")
    print(f"  ✅ モデル名が一致: {match_count}件")
    print(f"  ⚠️ モデル名ミスマッチ: {mismatch_count}件")

    # 比率を計算
    if len(anomalies) > 0:
        mismatch_rate = (mismatch_count / len(anomalies)) * 100
        print(f"\nミスマッチ率: {mismatch_rate:.1f}%")

    # ミスマッチが多い場合の推奨アクション
    if mismatch_count > 10:
        print("\n⚠️ 推奨アクション:")
        print("  モデル名のマッチングロジックを修正する必要があります")
        print("  スクレイピング側で商品名からモデルを正確に抽出してください")
    elif mismatch_count > 0:
        print("\n💡 推奨アクション:")
        print("  一部のモデルでミスマッチがあります")
        print("  比較スクリプトで異常値を自動除外することを検討してください")
    else:
        print("\n✅ すべてのモデル名が一致しています")

    # 詳細レポートを保存
    output_path = REPORTS_DIR / f"anomalies_check_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
    anomalies.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n📄 詳細レポート: {output_path}")


if __name__ == "__main__":
    main()
