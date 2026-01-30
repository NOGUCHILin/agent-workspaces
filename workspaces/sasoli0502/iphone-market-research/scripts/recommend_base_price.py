"""
基準価格調整案スクリプト

機能:
- 分析結果を読み込み
- 段階2進行率に基づいて基準価格の調整案を算出
  - 段階2進行率25%以上 → 基準価格を下げる余地あり（粗利アップ）
  - 段階2進行率10%以下 → 基準価格を上げるべき（CVRアップ）

判定ロジック:
- 段階2進行率が高い = お客様が基準価格に魅力を感じている = 価格を下げても申し込みが来る
- 段階2進行率が低い = 基準価格が低くて競争力がない = 価格を上げるべき

使用方法:
    uv run python scripts/recommend_base_price.py

入力:
    data/results/analysis_YYYYMMDD.xlsx

出力:
    data/results/base_price_recommendations_YYYYMMDD.xlsx
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from openpyxl.styles import Font, PatternFill


# =============================================================================
# 機種の発売順（新しい順）
# =============================================================================
MODEL_ORDER = {
    # 2024年発売（16シリーズ）
    "iPhone 16 Pro Max": 1,
    "iPhone 16 Pro": 2,
    "iPhone 16 Plus": 3,
    "iPhone 16": 4,
    # 2023年発売（15シリーズ）
    "iPhone 15 Pro Max": 10,
    "iPhone 15 Pro": 11,
    "iPhone 15 Plus": 12,
    "iPhone 15": 13,
    # 2022年発売（14シリーズ）
    "iPhone 14 Pro Max": 20,
    "iPhone 14 Pro": 21,
    "iPhone 14 Plus": 22,
    "iPhone 14": 23,
    # 2021年発売（13シリーズ）
    "iPhone 13 Pro Max": 30,
    "iPhone 13 Pro": 31,
    "iPhone 13 mini": 32,
    "iPhone 13": 33,
    # 2020年発売（12シリーズ）
    "iPhone 12 Pro Max": 40,
    "iPhone 12 Pro": 41,
    "iPhone 12 mini": 42,
    "iPhone 12": 43,
    # 2019年発売（11シリーズ）
    "iPhone 11 Pro Max": 50,
    "iPhone 11 Pro": 51,
    "iPhone 11": 52,
    # SE シリーズ
    "iPhone SE(第3世代)": 60,
    "iPhone SE(第2世代)": 61,
    # 古い機種
    "iPhone XS Max": 70,
    "iPhone XS": 71,
    "iPhone XR": 72,
    "iPhone X": 73,
    "iPhone 8 Plus": 80,
    "iPhone 8": 81,
    "iPhone 7 Plus": 90,
    "iPhone 7": 91,
}

# 容量の順序（大きい順）
CAPACITY_ORDER = {
    "1TB": 1,
    "512GB": 2,
    "256GB": 3,
    "128GB": 4,
    "64GB": 5,
    "32GB": 6,
    "16GB": 7,
}

# ランクの順序
RANK_ORDER = {
    "新品・未開封": 1,
    "新品同様": 2,
    "美品": 3,
    "使用感あり": 4,
    "目立つ傷あり": 5,
    "外装ジャンク": 6,
}

# =============================================================================
# 調整率の設定（段階2進行率ベース）
# =============================================================================

# 段階2進行率が高い場合: 基準価格を下げる（粗利増加）
ADJUSTMENT_HIGH_MILD = -0.05  # 段階2進行率25%〜35%
ADJUSTMENT_HIGH_AGGRESSIVE = -0.10  # 段階2進行率35%以上

# 段階2進行率が低い場合: 基準価格を上げる（CVR改善）
ADJUSTMENT_LOW_MILD = 0.05  # 段階2進行率5%〜10%
ADJUSTMENT_LOW_AGGRESSIVE = 0.10  # 段階2進行率5%以下

# 段階2進行率の閾値
STAGE2_RATE_HIGH = 0.25  # 25%以上: 下げる余地あり
STAGE2_RATE_VERY_HIGH = 0.35  # 35%以上: 大幅に下げる余地
STAGE2_RATE_LOW = 0.10  # 10%以下: 上げるべき
STAGE2_RATE_VERY_LOW = 0.05  # 5%以下: 大幅に上げるべき


def load_analysis_results(results_dir: Path, input_suffix: str = None) -> pd.DataFrame:
    """分析結果を読み込む

    Args:
        results_dir: 結果ディレクトリ
        input_suffix: 特定のサフィックスを持つファイルを読み込む（例: "before"）
    """
    if input_suffix:
        files = list(results_dir.glob(f"analysis_*_{input_suffix}.xlsx"))
    else:
        # サフィックスなしのファイルのみ対象
        files = [f for f in results_dir.glob("analysis_*.xlsx") if "_before" not in f.name and "_after" not in f.name]

    if not files:
        raise FileNotFoundError(f"分析結果が見つかりません: {results_dir}")

    # 最新のファイルを取得
    latest_file = max(files, key=lambda x: x.stat().st_mtime)
    print(f"📂 読み込み: {latest_file}")

    # 基本分析シートを読み込み
    df = pd.read_excel(latest_file, sheet_name="基本分析")
    return df


def calculate_adjustment(row: pd.Series) -> dict:
    """段階2進行率に基づいて調整率を計算"""
    stage2_rate = row.get("段階2進行率", 0)
    base_judgment = row.get("基準価格判定", "データ不足")
    current_price = row["平均提示価格"]
    assessment_count = row.get("仮査定数", 0)

    # データ不足の場合
    if base_judgment == "データ不足" or pd.isna(stage2_rate) or assessment_count < 5:
        return {
            "調整率": 0,
            "調整方向": "判定不可",
            "調整額": 0,
            "新基準価格": current_price,
            "理由": "サンプル数不足",
        }

    # 段階2進行率が非常に高い: 大幅に下げる余地
    if stage2_rate >= STAGE2_RATE_VERY_HIGH:
        rate = ADJUSTMENT_HIGH_AGGRESSIVE
        direction = "大幅減額"
        reason = f"段階2進行率{stage2_rate*100:.1f}%は非常に高い。価格を下げても申し込みが維持できる可能性"
    # 段階2進行率が高い: 小幅に下げる余地
    elif stage2_rate >= STAGE2_RATE_HIGH:
        rate = ADJUSTMENT_HIGH_MILD
        direction = "小幅減額"
        reason = f"段階2進行率{stage2_rate*100:.1f}%は高い。価格を下げて粗利を増やす余地あり"

    # 段階2進行率が非常に低い: 大幅に上げるべき
    elif stage2_rate <= STAGE2_RATE_VERY_LOW:
        rate = ADJUSTMENT_LOW_AGGRESSIVE
        direction = "大幅増額"
        reason = f"段階2進行率{stage2_rate*100:.1f}%は非常に低い。価格を上げて競争力を高めるべき"
    # 段階2進行率が低い: 小幅に上げるべき
    elif stage2_rate <= STAGE2_RATE_LOW:
        rate = ADJUSTMENT_LOW_MILD
        direction = "小幅増額"
        reason = f"段階2進行率{stage2_rate*100:.1f}%は低い。価格を上げて申し込み数を増やすべき"

    # 適正範囲
    else:
        rate = 0
        direction = "維持"
        reason = f"段階2進行率{stage2_rate*100:.1f}%は適正範囲"

    # 調整額と新基準価格を計算
    adjustment_amount = current_price * rate if pd.notna(current_price) else 0
    new_price = current_price + adjustment_amount if pd.notna(current_price) else None

    return {
        "調整率": rate,
        "調整方向": direction,
        "調整額": round(adjustment_amount) if pd.notna(adjustment_amount) else 0,
        "新基準価格": round(new_price) if pd.notna(new_price) else None,
        "理由": reason,
    }


def generate_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    """基準価格の調整案を生成"""
    recommendations = []

    for _, row in df.iterrows():
        adjustment = calculate_adjustment(row)

        # 段階2進行率と成約率をパーセンテージ表記
        stage2_rate = row.get("段階2進行率", 0)
        contract_rate = row.get("成約率_段階2", 0)

        # 現在平均価格を10の位で四捨五入
        current_price = row["平均提示価格"]
        current_price_rounded = round(current_price / 10) * 10 if pd.notna(current_price) else None

        rec = {
            "機種": row["機種"],
            "容量": row["容量"],
            "ランク": row["ランク"],
            "仮査定数": row["仮査定数"],
            "段階2以降数": row.get("段階2以降数", 0),
            "段階2進行率": f"{stage2_rate*100:.1f}%",
            "段階2進行率_raw": stage2_rate,  # 色付け用の生値
            "成約数": row["成約数"],
            "成約率_段階2": f"{contract_rate*100:.1f}%",
            "現在平均価格": current_price_rounded,
            "調整方向": adjustment["調整方向"],
            "調整率": f"{adjustment['調整率']*100:+.0f}%" if adjustment['調整率'] != 0 else "0%",
            "調整額": adjustment["調整額"],
            "推奨価格": adjustment["新基準価格"],
            "基準価格判定": row.get("基準価格判定", ""),
            "理由": adjustment["理由"],
        }
        recommendations.append(rec)

    result_df = pd.DataFrame(recommendations)

    # ソート順序のキーを追加
    result_df["model_order"] = result_df["機種"].map(MODEL_ORDER).fillna(999)
    result_df["capacity_order"] = result_df["容量"].map(CAPACITY_ORDER).fillna(999)
    result_df["rank_order"] = result_df["ランク"].map(RANK_ORDER).fillna(999)

    # ソート（機種発売日新しい順 → 容量大きい順 → ランク順）
    result_df = result_df.sort_values(
        ["model_order", "capacity_order", "rank_order"],
        ascending=[True, True, True]
    )
    result_df = result_df.drop(columns=["model_order", "capacity_order", "rank_order"])

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

    # データ読み込み
    df = load_analysis_results(results_dir, input_suffix=input_suffix)
    print(f"   - 読み込み件数: {len(df):,}件")

    # 調整案を生成
    print("\n📊 基準価格調整案を生成中...")
    recommendations = generate_recommendations(df)

    # 出力（Excel形式、段階2進行率25%以上を緑色に）
    today = datetime.now().strftime("%Y%m%d")
    if output_suffix:
        output_path = results_dir / f"base_price_recommendations_{today}_{output_suffix}.xlsx"
    else:
        output_path = results_dir / f"base_price_recommendations_{today}.xlsx"

    # 段階2進行率_rawを保持しつつExcel出力
    stage2_raw_values = recommendations["段階2進行率_raw"].tolist()
    recommendations_output = recommendations.drop(columns=["段階2進行率_raw"])

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        recommendations_output.to_excel(writer, sheet_name="基準価格調整案", index=False)
        ws = writer.sheets["基準価格調整案"]

        # 段階2進行率の列インデックスを取得（1-indexed、ヘッダーが1行目なので+2）
        stage2_col_idx = recommendations_output.columns.get_loc("段階2進行率") + 1

        # 緑色のフォント
        green_font = Font(color="008000")  # 緑色

        # 25%以上のセルを緑色に
        for row_idx, raw_value in enumerate(stage2_raw_values, start=2):  # 2行目から開始
            if raw_value >= 0.25:
                cell = ws.cell(row=row_idx, column=stage2_col_idx)
                cell.font = green_font

    print(f"\n✅ 出力: {output_path}")

    # サマリー表示
    print("\n📋 調整案サマリー:")
    direction_counts = recommendations["調整方向"].value_counts()
    for direction, count in direction_counts.items():
        print(f"   - {direction}: {count}件")

    # 調整が必要な上位を表示
    needs_adjustment = recommendations[recommendations["調整方向"].isin(["大幅減額", "小幅減額", "大幅増額", "小幅増額"])]
    if len(needs_adjustment) > 0:
        print("\n   【調整が必要な構成（上位5件）】")
        for _, row in needs_adjustment.head(5).iterrows():
            print(f"      {row['機種']} {row['容量']} {row['ランク']}")
            print(f"         現在: {row['現在平均価格']:,.0f}円 → 推奨: {row['推奨価格']:,.0f}円 ({row['調整率']})")
            print(f"         段階2進行率: {row['段階2進行率']} (仮査定{row['仮査定数']:.0f}件→段階2:{row['段階2以降数']:.0f}件)")


if __name__ == "__main__":
    main()
