"""
減額率調整案スクリプト

機能:
- 段階2→成約率に基づいて減額率の調整案を算出
  - 成約率70%以上 → 減額を強化する余地あり（粗利アップ）
  - 成約率40%以下 → 減額を緩和すべき（返送率を下げる）
- 特にバッテリー劣化の減額率を優先的に分析

判定ロジック:
- 成約率が高い = 減額幅が適正or緩い = 減額を強化しても成約する
- 成約率が低い = 減額幅がキツすぎる = 減額を緩和して返送を減らす

使用方法:
    uv run python scripts/recommend_deduction_rate.py

入力:
    data/results/analysis_YYYYMMDD.xlsx（バッテリー劣化分析シート）

出力:
    data/results/deduction_rate_recommendations_YYYYMMDD.xlsx
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


# =============================================================================
# 現在の減額率（参考値、実際は別途マスタを参照）
# =============================================================================

CURRENT_DEDUCTION_RATES = {
    "バッテリーの劣化": 0.70,  # ×0.7 = 30%減額
    "表示やタッチ操作の劣化": 0.85,
    "アウトカメラの故障": 0.80,
    "バイブレーション不具合": 0.90,
    "端末上部の不具合": 0.85,
    "端末下部の不具合": 0.85,
    "Wi-FiやBluetoothの不具合": 0.80,
    "フラッシュの故障": 0.90,
    "水没歴あり": 0.60,
    "その他": 0.80,
}

# 調整の刻み
DEDUCTION_STEP = 0.05  # 5%刻みで調整

# =============================================================================
# 成約率の閾値（段階2→成約率で判定）
# =============================================================================
# 成約率が高い = 減額幅に納得している = 減額を強化する余地あり
# 成約率が低い = 減額幅に納得できない = 減額を緩和すべき

CONTRACT_RATE_HIGH = 0.70  # 70%以上: 減額強化の余地あり
CONTRACT_RATE_VERY_HIGH = 0.85  # 85%以上: 大幅に減額強化の余地
CONTRACT_RATE_LOW = 0.40  # 40%以下: 減額緩和すべき
CONTRACT_RATE_VERY_LOW = 0.25  # 25%以下: 大幅に減額緩和すべき


def load_battery_analysis(results_dir: Path, input_suffix: str = None) -> pd.DataFrame:
    """バッテリー劣化分析を読み込む

    Args:
        results_dir: 結果ディレクトリ
        input_suffix: 特定のサフィックスを持つファイルを読み込む（例: "before"）
    """
    if input_suffix:
        files = list(results_dir.glob(f"analysis_*_{input_suffix}.xlsx"))
    else:
        files = [f for f in results_dir.glob("analysis_*.xlsx") if "_before" not in f.name and "_after" not in f.name]

    if not files:
        raise FileNotFoundError(f"分析結果が見つかりません: {results_dir}")

    latest_file = max(files, key=lambda x: x.stat().st_mtime)
    print(f"📂 読み込み: {latest_file}")

    df = pd.read_excel(latest_file, sheet_name="バッテリー劣化分析")
    return df


def analyze_battery_deduction(df: pd.DataFrame) -> pd.DataFrame:
    """バッテリー劣化の減額率調整案を分析（段階2→成約率ベース）"""
    # バッテリー劣化ありのデータのみ抽出
    battery_df = df[df["バッテリー劣化あり"] == True].copy()

    if len(battery_df) == 0:
        print("   ⚠️ バッテリー劣化ありのデータがありません")
        return pd.DataFrame()

    recommendations = []

    for _, row in battery_df.iterrows():
        # 段階2→成約率を使用
        contract_rate = row.get("成約率_段階2", row.get("成約率", 0))
        stage2_count = row.get("段階2以降数", 0)
        ded_judgment = row.get("減額率判定", "データ不足")

        # 現在の減額率
        current_rate = CURRENT_DEDUCTION_RATES["バッテリーの劣化"]

        # 調整案を計算（段階2→成約率ベース）
        if ded_judgment == "データ不足" or pd.isna(contract_rate) or stage2_count < 5:
            new_rate = current_rate
            direction = "判定不可"
            reason = "サンプル数不足"
        elif contract_rate >= CONTRACT_RATE_VERY_HIGH:
            # 成約率が非常に高い → 減額を大幅に強化する余地あり
            new_rate = max(0.50, current_rate - DEDUCTION_STEP * 2)  # 下限50%
            direction = "大幅減額強化"
            reason = f"成約率{contract_rate*100:.1f}%は非常に高い。減額を強化しても成約が維持できる可能性"
        elif contract_rate >= CONTRACT_RATE_HIGH:
            # 成約率が高い → 減額を強化する余地あり
            new_rate = max(0.50, current_rate - DEDUCTION_STEP)  # 下限50%
            direction = "減額強化"
            reason = f"成約率{contract_rate*100:.1f}%は高い。減額を強化しても成約が維持できる可能性"
        elif contract_rate <= CONTRACT_RATE_VERY_LOW:
            # 成約率が非常に低い → 減額を大幅に緩和すべき
            new_rate = min(0.95, current_rate + DEDUCTION_STEP * 2)  # 上限95%
            direction = "大幅減額緩和"
            reason = f"成約率{contract_rate*100:.1f}%は非常に低い。減額を緩和して返送を減らすべき"
        elif contract_rate <= CONTRACT_RATE_LOW:
            # 成約率が低い → 減額を緩和すべき
            new_rate = min(0.95, current_rate + DEDUCTION_STEP)  # 上限95%
            direction = "減額緩和"
            reason = f"成約率{contract_rate*100:.1f}%は低い。減額を緩和して返送を減らすべき"
        else:
            new_rate = current_rate
            direction = "維持"
            reason = f"成約率{contract_rate*100:.1f}%は適正範囲"

        rec = {
            "機種": row["機種"],
            "容量": row["容量"],
            "ランク": row["ランク"],
            "仮査定数": row["仮査定数"],
            "段階2以降数": stage2_count,
            "成約数": row["成約数"],
            "成約率_段階2": contract_rate,
            "不成約率_段階2": row.get("不成約率_段階2", 0),
            "不具合項目": "バッテリーの劣化",
            "現在減額率": f"×{current_rate:.2f}",
            "調整方向": direction,
            "推奨減額率": f"×{new_rate:.2f}",
            "減額変化": f"{(new_rate - current_rate)*100:+.0f}%",
            "減額率判定": ded_judgment,
            "理由": reason,
        }
        recommendations.append(rec)

    result_df = pd.DataFrame(recommendations)

    # ソート（調整が必要なものを上に、段階2以降数が多いものを優先）
    direction_order = {"大幅減額強化": 1, "減額強化": 2, "大幅減額緩和": 3, "減額緩和": 4, "維持": 5, "判定不可": 6}
    result_df["sort_key"] = result_df["調整方向"].map(direction_order)
    result_df = result_df.sort_values(["sort_key", "段階2以降数"], ascending=[True, False])
    result_df = result_df.drop(columns=["sort_key"])

    return result_df


def analyze_group_b_defects(results_dir: Path, input_suffix: str = None) -> pd.DataFrame:
    """グループBの不具合全体を分析（段階2→成約率ベース）

    Args:
        results_dir: 結果ディレクトリ
        input_suffix: 特定のサフィックスを持つファイルを読み込む（例: "before"）
    """
    if input_suffix:
        files = list(results_dir.glob(f"analysis_*_{input_suffix}.xlsx"))
    else:
        files = [f for f in results_dir.glob("analysis_*.xlsx") if "_before" not in f.name and "_after" not in f.name]

    if not files:
        return pd.DataFrame()

    latest_file = max(files, key=lambda x: x.stat().st_mtime)

    # 不具合グループ分析を読み込み
    df = pd.read_excel(latest_file, sheet_name="不具合グループ分析")

    # グループBありのデータのみ抽出
    group_b_df = df[df["不具合_グループB"] == True].copy()

    if len(group_b_df) == 0:
        return pd.DataFrame()

    recommendations = []

    for _, row in group_b_df.iterrows():
        # 段階2→成約率を使用
        contract_rate = row.get("成約率_段階2", row.get("成約率", 0))
        stage2_count = row.get("段階2以降数", 0)
        ded_judgment = row.get("減額率判定", "データ不足")

        if ded_judgment == "データ不足" or pd.isna(contract_rate) or stage2_count < 5:
            direction = "判定不可"
            reason = "サンプル数不足"
        elif contract_rate >= CONTRACT_RATE_HIGH:
            direction = "減額強化可能"
            reason = f"成約率{contract_rate*100:.1f}%は高い。グループB不具合の減額を強化する余地あり"
        elif contract_rate <= CONTRACT_RATE_LOW:
            direction = "減額緩和すべき"
            reason = f"成約率{contract_rate*100:.1f}%は低い。グループB不具合の減額を緩和すべき"
        else:
            direction = "維持"
            reason = f"成約率{contract_rate*100:.1f}%は適正範囲"

        rec = {
            "機種": row["機種"],
            "容量": row["容量"],
            "ランク": row["ランク"],
            "不具合_グループA": row["不具合_グループA"],
            "不具合_グループB": row["不具合_グループB"],
            "仮査定数": row["仮査定数"],
            "段階2以降数": stage2_count,
            "成約数": row["成約数"],
            "成約率_段階2": contract_rate,
            "不成約率_段階2": row.get("不成約率_段階2", 0),
            "調整方向": direction,
            "減額率判定": ded_judgment,
            "理由": reason,
        }
        recommendations.append(rec)

    result_df = pd.DataFrame(recommendations)

    # ソート（段階2以降数が多いものを優先）
    direction_order = {"減額強化可能": 1, "減額緩和すべき": 2, "維持": 3, "判定不可": 4}
    result_df["sort_key"] = result_df["調整方向"].map(direction_order)
    result_df = result_df.sort_values(["sort_key", "段階2以降数"], ascending=[True, False])
    result_df = result_df.drop(columns=["sort_key"])

    return result_df


def main():
    import sys

    # コマンドライン引数の処理
    input_suffix = None
    output_suffix = None

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--input-suffix" and i + 1 < len(sys.argv):
            input_suffix = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--output-suffix" and i + 1 < len(sys.argv):
            output_suffix = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # パス設定
    script_dir = Path(__file__).parent
    results_dir = script_dir.parent / "data" / "results"

    # バッテリー劣化分析
    print("\n📊 バッテリー劣化の減額率分析...")
    battery_df = load_battery_analysis(results_dir, input_suffix=input_suffix)
    battery_recommendations = analyze_battery_deduction(battery_df)

    # グループB全体の分析
    print("\n📊 グループB不具合の減額率分析...")
    group_b_recommendations = analyze_group_b_defects(results_dir, input_suffix=input_suffix)

    # 出力
    today = datetime.now().strftime("%Y%m%d")
    if output_suffix:
        output_path = results_dir / f"deduction_rate_recommendations_{today}_{output_suffix}.xlsx"
    else:
        output_path = results_dir / f"deduction_rate_recommendations_{today}.xlsx"

    print(f"\n✅ 出力: {output_path}")
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        if len(battery_recommendations) > 0:
            battery_recommendations.to_excel(writer, sheet_name="バッテリー劣化", index=False)
        if len(group_b_recommendations) > 0:
            group_b_recommendations.to_excel(writer, sheet_name="グループB不具合", index=False)

    # サマリー表示
    print("\n📋 減額率調整案サマリー:")

    if len(battery_recommendations) > 0:
        print("\n   【バッテリー劣化】")
        direction_counts = battery_recommendations["調整方向"].value_counts()
        for direction, count in direction_counts.items():
            print(f"      - {direction}: {count}件")

        # 減額強化が必要な上位を表示
        needs_strong = battery_recommendations[battery_recommendations["調整方向"].isin(["大幅減額強化", "減額強化"])]
        if len(needs_strong) > 0:
            print("\n      減額強化が可能な構成（上位3件）:")
            for _, row in needs_strong.head(3).iterrows():
                print(f"         {row['機種']} {row['容量']} {row['ランク']}")
                print(f"            現在: {row['現在減額率']} → 推奨: {row['推奨減額率']}")
                print(f"            成約率: {row['成約率_段階2']*100:.1f}% (段階2以降: {row['段階2以降数']:.0f}件)")

        # 減額緩和が必要な上位を表示
        needs_weak = battery_recommendations[battery_recommendations["調整方向"].isin(["大幅減額緩和", "減額緩和"])]
        if len(needs_weak) > 0:
            print("\n      減額緩和が必要な構成（上位3件）:")
            for _, row in needs_weak.head(3).iterrows():
                print(f"         {row['機種']} {row['容量']} {row['ランク']}")
                print(f"            現在: {row['現在減額率']} → 推奨: {row['推奨減額率']}")
                print(f"            成約率: {row['成約率_段階2']*100:.1f}% (段階2以降: {row['段階2以降数']:.0f}件)")

    if len(group_b_recommendations) > 0:
        print("\n   【グループB不具合全体】")
        direction_counts = group_b_recommendations["調整方向"].value_counts()
        for direction, count in direction_counts.items():
            print(f"      - {direction}: {count}件")


if __name__ == "__main__":
    main()
