"""
新価格シミュレーションスクリプト

機能:
- 過去データに新しい基準価格・減額率を適用
- 粗利の変化を予測
- 成約数の変化を予測（成約率が変わらないと仮定）

使用方法:
    uv run python scripts/simulate_new_prices.py

入力:
    - data/processed/preprocessed_YYYYMMDD.csv
    - data/results/base_price_recommendations_YYYYMMDD.csv
    - data/results/deduction_rate_recommendations_YYYYMMDD.xlsx

出力:
    data/results/simulation_YYYYMMDD.xlsx
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def load_latest_file(directory: Path, pattern: str) -> Path:
    """最新のファイルを取得"""
    files = list(directory.glob(pattern))
    if not files:
        raise FileNotFoundError(f"ファイルが見つかりません: {directory / pattern}")
    return max(files, key=lambda x: x.stat().st_mtime)


def load_data(data_dir: Path, results_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """必要なデータを読み込み"""
    # 前処理済みデータ
    preprocessed_path = load_latest_file(data_dir / "processed", "preprocessed_*.csv")
    print(f"📂 前処理済みデータ: {preprocessed_path.name}")
    preprocessed_df = pd.read_csv(preprocessed_path, encoding="utf-8-sig")

    # 基準価格調整案（Excel形式を優先、なければCSV）
    try:
        base_price_path = load_latest_file(results_dir, "base_price_recommendations_*.xlsx")
        print(f"📂 基準価格調整案: {base_price_path.name}")
        base_price_df = pd.read_excel(base_price_path, sheet_name="基準価格調整案")
    except FileNotFoundError:
        base_price_path = load_latest_file(results_dir, "base_price_recommendations_*.csv")
        print(f"📂 基準価格調整案: {base_price_path.name}")
        base_price_df = pd.read_csv(base_price_path, encoding="utf-8-sig")

    # 減額率調整案
    deduction_path = load_latest_file(results_dir, "deduction_rate_recommendations_*.xlsx")
    print(f"📂 減額率調整案: {deduction_path.name}")
    try:
        deduction_df = pd.read_excel(deduction_path, sheet_name="バッテリー劣化")
    except Exception:
        deduction_df = pd.DataFrame()

    return preprocessed_df, base_price_df, deduction_df


def simulate_base_price_change(preprocessed_df: pd.DataFrame, base_price_df: pd.DataFrame) -> pd.DataFrame:
    """基準価格変更のシミュレーション"""
    # 調整が必要な構成のみ抽出
    needs_adjustment = base_price_df[
        base_price_df["調整方向"].isin(["大幅減額", "小幅減額", "大幅増額", "小幅増額"])
    ].copy()

    if len(needs_adjustment) == 0:
        return pd.DataFrame(columns=[
            "機種", "容量", "ランク", "仮査定数", "成約数", "成約率",
            "現在平均価格", "推奨価格", "調整額", "調整方向",
            "現在粗利合計", "予測粗利合計", "粗利変化額", "粗利変化率"
        ])

    simulation_results = []

    for _, row in needs_adjustment.iterrows():
        model = row["機種"]
        capacity = row["容量"]
        rank = row["ランク"]

        # 該当する成約データを抽出
        mask = (
            (preprocessed_df["機種"] == model) &
            (preprocessed_df["容量"] == capacity) &
            (preprocessed_df["ランク"] == rank) &
            (preprocessed_df["成約"] == True)
        )
        matched = preprocessed_df[mask]

        if len(matched) == 0:
            continue

        # 現在の粗利合計
        current_profit_total = matched["粗利(手数料引)"].sum()

        # 調整額
        adjustment = row["調整額"] if pd.notna(row["調整額"]) else 0

        # 新しい粗利合計（買取価格が下がれば粗利が増える）
        # 注: 調整額がマイナス = 買取価格を下げる = 粗利が増える
        predicted_profit_total = current_profit_total - (adjustment * len(matched))

        profit_change = predicted_profit_total - current_profit_total
        profit_change_rate = profit_change / current_profit_total if current_profit_total != 0 else 0

        simulation_results.append({
            "機種": model,
            "容量": capacity,
            "ランク": rank,
            "仮査定数": row["仮査定数"],
            "段階2以降数": row.get("段階2以降数", 0),
            "段階2進行率": row.get("段階2進行率", 0),
            "成約数": row["成約数"],
            "現在平均価格": row["現在平均価格"],
            "推奨価格": row["推奨価格"],
            "調整額": adjustment,
            "調整方向": row["調整方向"],
            "現在粗利合計": round(current_profit_total),
            "予測粗利合計": round(predicted_profit_total),
            "粗利変化額": round(profit_change),
            "粗利変化率": f"{profit_change_rate*100:+.1f}%",
        })

    return pd.DataFrame(simulation_results)


def simulate_deduction_rate_change(preprocessed_df: pd.DataFrame, deduction_df: pd.DataFrame) -> pd.DataFrame:
    """減額率変更のシミュレーション"""
    if len(deduction_df) == 0:
        return pd.DataFrame()

    # 減額強化が可能な構成のみ抽出（大幅・通常両方）
    needs_adjustment = deduction_df[deduction_df["調整方向"].isin(["大幅減額強化", "減額強化"])].copy()

    if len(needs_adjustment) == 0:
        return pd.DataFrame()

    simulation_results = []

    for _, row in needs_adjustment.iterrows():
        model = row["機種"]
        capacity = row["容量"]
        rank = row["ランク"]

        # 該当する成約データを抽出（バッテリー劣化あり）
        mask = (
            (preprocessed_df["機種"] == model) &
            (preprocessed_df["容量"] == capacity) &
            (preprocessed_df["ランク"] == rank) &
            (preprocessed_df["バッテリー劣化あり"] == True) &
            (preprocessed_df["成約"] == True)
        )
        matched = preprocessed_df[mask]

        if len(matched) == 0:
            continue

        # 現在の粗利合計
        current_profit_total = matched["粗利(手数料引)"].sum()

        # 減額率の変化を計算
        # 現在: ×0.70 → 推奨: ×0.65 の場合、5%分の追加減額
        current_rate_str = row["現在減額率"]  # "×0.70"
        recommended_rate_str = row["推奨減額率"]  # "×0.65"

        current_rate = float(current_rate_str.replace("×", ""))
        recommended_rate = float(recommended_rate_str.replace("×", ""))

        # 追加減額率
        additional_deduction = current_rate - recommended_rate  # 0.05 (5%)

        # 平均提示価格から追加減額額を計算
        avg_price = matched["最高提示価格"].mean()
        additional_deduction_amount = avg_price * additional_deduction

        # 新しい粗利合計（追加減額 = 粗利増加）
        predicted_profit_total = current_profit_total + (additional_deduction_amount * len(matched))

        profit_change = predicted_profit_total - current_profit_total
        profit_change_rate = profit_change / current_profit_total if current_profit_total != 0 else 0

        simulation_results.append({
            "機種": model,
            "容量": capacity,
            "ランク": rank,
            "不具合項目": "バッテリー劣化",
            "成約数": len(matched),
            "現在減額率": current_rate_str,
            "推奨減額率": recommended_rate_str,
            "追加減額率": f"{additional_deduction*100:.1f}%",
            "平均追加減額額": round(additional_deduction_amount),
            "現在粗利合計": round(current_profit_total),
            "予測粗利合計": round(predicted_profit_total),
            "粗利変化額": round(profit_change),
            "粗利変化率": f"{profit_change_rate*100:+.1f}%",
        })

    return pd.DataFrame(simulation_results)


def generate_summary(base_price_sim: pd.DataFrame, deduction_sim: pd.DataFrame) -> pd.DataFrame:
    """シミュレーション結果のサマリー"""
    summary_data = []

    # 基準価格変更の効果
    if len(base_price_sim) > 0:
        total_current = base_price_sim["現在粗利合計"].sum()
        total_predicted = base_price_sim["予測粗利合計"].sum()
        total_change = total_predicted - total_current

        summary_data.append({
            "施策": "基準価格の調整",
            "対象構成数": len(base_price_sim),
            "対象成約数": base_price_sim["成約数"].sum(),
            "現在粗利合計": total_current,
            "予測粗利合計": total_predicted,
            "粗利変化額": total_change,
            "粗利変化率": f"{total_change/total_current*100:+.1f}%" if total_current != 0 else "N/A",
        })

    # 減額率変更の効果
    if len(deduction_sim) > 0:
        total_current = deduction_sim["現在粗利合計"].sum()
        total_predicted = deduction_sim["予測粗利合計"].sum()
        total_change = total_predicted - total_current

        summary_data.append({
            "施策": "バッテリー劣化の減額率強化",
            "対象構成数": len(deduction_sim),
            "対象成約数": deduction_sim["成約数"].sum(),
            "現在粗利合計": total_current,
            "予測粗利合計": total_predicted,
            "粗利変化額": total_change,
            "粗利変化率": f"{total_change/total_current*100:+.1f}%" if total_current != 0 else "N/A",
        })

    # 合計
    if len(summary_data) > 0:
        all_current = sum(d["現在粗利合計"] for d in summary_data)
        all_predicted = sum(d["予測粗利合計"] for d in summary_data)
        all_change = all_predicted - all_current

        summary_data.append({
            "施策": "【合計】",
            "対象構成数": sum(d["対象構成数"] for d in summary_data),
            "対象成約数": sum(d["対象成約数"] for d in summary_data),
            "現在粗利合計": all_current,
            "予測粗利合計": all_predicted,
            "粗利変化額": all_change,
            "粗利変化率": f"{all_change/all_current*100:+.1f}%" if all_current != 0 else "N/A",
        })

    return pd.DataFrame(summary_data)


def main():
    # パス設定
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    results_dir = data_dir / "results"

    # データ読み込み
    print("\n📂 データ読み込み中...")
    preprocessed_df, base_price_df, deduction_df = load_data(data_dir, results_dir)
    print(f"   - 前処理済みデータ: {len(preprocessed_df):,}件")

    # シミュレーション実行
    print("\n📊 シミュレーション実行中...")

    # 1. 基準価格変更のシミュレーション
    print("   - 基準価格変更")
    base_price_sim = simulate_base_price_change(preprocessed_df, base_price_df)

    # 2. 減額率変更のシミュレーション
    print("   - 減額率変更")
    deduction_sim = simulate_deduction_rate_change(preprocessed_df, deduction_df)

    # 3. サマリー生成
    summary = generate_summary(base_price_sim, deduction_sim)

    # 出力
    today = datetime.now().strftime("%Y%m%d")
    output_path = results_dir / f"simulation_{today}.xlsx"

    # シートが1つもない場合は空のサマリーを作成
    has_data = len(summary) > 0 or len(base_price_sim) > 0 or len(deduction_sim) > 0

    print(f"\n✅ 出力: {output_path}")
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        if len(summary) > 0:
            summary.to_excel(writer, sheet_name="サマリー", index=False)
        if len(base_price_sim) > 0:
            base_price_sim.to_excel(writer, sheet_name="基準価格変更", index=False)
        if len(deduction_sim) > 0:
            deduction_sim.to_excel(writer, sheet_name="減額率変更", index=False)

        # シートが1つもない場合は空のサマリーを作成
        if not has_data:
            empty_df = pd.DataFrame([{"メッセージ": "調整が必要な構成がないため、シミュレーション対象なし"}])
            empty_df.to_excel(writer, sheet_name="サマリー", index=False)

    # 結果表示
    print("\n📋 シミュレーション結果:")
    if len(summary) > 0:
        for _, row in summary.iterrows():
            print(f"\n   【{row['施策']}】")
            print(f"      対象構成数: {row['対象構成数']}件")
            print(f"      対象成約数: {row['対象成約数']}件")
            print(f"      現在粗利: {row['現在粗利合計']:,.0f}円")
            print(f"      予測粗利: {row['予測粗利合計']:,.0f}円")
            print(f"      変化額: {row['粗利変化額']:+,.0f}円 ({row['粗利変化率']})")
    else:
        print("   調整が必要な構成がないため、シミュレーション対象なし")


if __name__ == "__main__":
    main()
