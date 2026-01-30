"""
総合レポート生成スクリプト

機能:
- 現在の成約率分布
- 価格調整案のサマリー
- シミュレーション結果
- 推奨アクション

使用方法:
    uv run python scripts/generate_report.py

入力:
    data/results/配下の各ファイル

出力:
    data/results/buyback_optimization_report_YYYYMMDD.xlsx
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def load_latest_file(directory: Path, pattern: str) -> Path | None:
    """最新のファイルを取得（なければNone）"""
    files = list(directory.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda x: x.stat().st_mtime)


def create_overview(preprocessed_df: pd.DataFrame) -> pd.DataFrame:
    """概要シートを作成"""
    total_count = len(preprocessed_df)
    contract_count = preprocessed_df["成約"].sum()
    contract_rate = contract_count / total_count if total_count > 0 else 0

    # 不具合・修理の統計
    defect_a_count = preprocessed_df["不具合_グループA"].sum()
    defect_b_count = preprocessed_df["不具合_グループB"].sum()
    battery_count = preprocessed_df["バッテリー劣化あり"].sum()
    repair_a_count = preprocessed_df["修理_グループA"].sum()
    repair_b_count = preprocessed_df["修理_グループB"].sum()
    clean_count = (preprocessed_df["不具合なし"] & preprocessed_df["修理なし"]).sum()

    overview_data = [
        {"項目": "レポート作成日", "値": datetime.now().strftime("%Y-%m-%d %H:%M")},
        {"項目": "", "値": ""},
        {"項目": "【全体統計】", "値": ""},
        {"項目": "仮査定数", "値": f"{total_count:,}件"},
        {"項目": "成約数", "値": f"{contract_count:,}件"},
        {"項目": "成約率", "値": f"{contract_rate*100:.1f}%"},
        {"項目": "", "値": ""},
        {"項目": "【不具合・修理の内訳】", "値": ""},
        {"項目": "不具合グループA（認識しやすい）", "値": f"{defect_a_count:,}件 ({defect_a_count/total_count*100:.1f}%)"},
        {"項目": "不具合グループB（認識しにくい）", "値": f"{defect_b_count:,}件 ({defect_b_count/total_count*100:.1f}%)"},
        {"項目": "  うちバッテリー劣化", "値": f"{battery_count:,}件 ({battery_count/total_count*100:.1f}%)"},
        {"項目": "修理グループA（認識しやすい）", "値": f"{repair_a_count:,}件 ({repair_a_count/total_count*100:.1f}%)"},
        {"項目": "修理グループB（認識しにくい）", "値": f"{repair_b_count:,}件 ({repair_b_count/total_count*100:.1f}%)"},
        {"項目": "不具合・修理なし（クリーン）", "値": f"{clean_count:,}件 ({clean_count/total_count*100:.1f}%)"},
    ]

    return pd.DataFrame(overview_data)


def create_contract_rate_distribution(preprocessed_df: pd.DataFrame) -> pd.DataFrame:
    """成約率分布を作成"""
    # 機種・容量・ランク別の成約率
    grouped = preprocessed_df.groupby(["機種", "容量", "ランク"], dropna=False).agg(
        仮査定数=("レコード番号", "count"),
        成約数=("成約", "sum"),
    ).reset_index()

    grouped["成約率"] = grouped["成約数"] / grouped["仮査定数"]

    # 成約率の分布を集計
    bins = [0, 0.05, 0.10, 0.15, 0.25, 0.35, 0.40, 0.50, 1.0]
    labels = ["0-5%", "5-10%", "10-15%", "15-25%", "25-35%", "35-40%", "40-50%", "50%以上"]
    grouped["成約率帯"] = pd.cut(grouped["成約率"], bins=bins, labels=labels, include_lowest=True)

    distribution = grouped.groupby("成約率帯", observed=True).agg(
        構成数=("機種", "count"),
        仮査定数合計=("仮査定数", "sum"),
        成約数合計=("成約数", "sum"),
    ).reset_index()

    distribution["判定"] = distribution["成約率帯"].apply(
        lambda x: "価格上げるべき" if x in ["0-5%", "5-10%"]
        else ("価格下げ余地" if x in ["40-50%", "50%以上"]
              else "適正範囲")
    )

    return distribution


def create_recommendations_summary(results_dir: Path) -> pd.DataFrame:
    """調整案サマリーを作成"""
    summary_data = []

    # 基準価格調整案
    base_price_path = load_latest_file(results_dir, "base_price_recommendations_*.csv")
    if base_price_path:
        base_price_df = pd.read_csv(base_price_path, encoding="utf-8-sig")
        direction_counts = base_price_df["調整方向"].value_counts()

        for direction, count in direction_counts.items():
            summary_data.append({
                "カテゴリ": "基準価格",
                "調整方向": direction,
                "件数": count,
            })

    # 減額率調整案
    deduction_path = load_latest_file(results_dir, "deduction_rate_recommendations_*.xlsx")
    if deduction_path:
        try:
            deduction_df = pd.read_excel(deduction_path, sheet_name="バッテリー劣化")
            direction_counts = deduction_df["調整方向"].value_counts()

            for direction, count in direction_counts.items():
                summary_data.append({
                    "カテゴリ": "減額率（バッテリー劣化）",
                    "調整方向": direction,
                    "件数": count,
                })
        except Exception:
            pass

    return pd.DataFrame(summary_data)


def create_action_items(results_dir: Path) -> pd.DataFrame:
    """推奨アクションを作成"""
    actions = []

    # シミュレーション結果から推奨アクションを抽出
    simulation_path = load_latest_file(results_dir, "simulation_*.xlsx")
    if simulation_path:
        try:
            summary_df = pd.read_excel(simulation_path, sheet_name="サマリー")

            for _, row in summary_df.iterrows():
                if row["施策"] == "【合計】":
                    continue

                if row["粗利変化額"] > 0:
                    priority = "高" if row["粗利変化額"] > 10000 else "中"
                    actions.append({
                        "優先度": priority,
                        "アクション": row["施策"],
                        "対象件数": f"{row['対象構成数']}構成 / {row['対象成約数']}成約",
                        "予測効果": f"+{row['粗利変化額']:,.0f}円 ({row['粗利変化率']})",
                        "ステータス": "未着手",
                    })
        except Exception:
            pass

    # 追加の推奨アクション
    actions.extend([
        {
            "優先度": "中",
            "アクション": "本番データでの再分析",
            "対象件数": "きんとんから過去1ヶ月のデータをエクスポート",
            "予測効果": "正確な調整案の算出",
            "ステータス": "未着手",
        },
        {
            "優先度": "低",
            "アクション": "減額率マスタの確認",
            "対象件数": "現在の減額率・減額固有値を確認",
            "予測効果": "調整案の精度向上",
            "ステータス": "未着手",
        },
    ])

    return pd.DataFrame(actions)


def main():
    # パス設定
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    results_dir = data_dir / "results"

    print("\n📊 総合レポート生成中...")

    # 前処理済みデータの読み込み
    preprocessed_path = load_latest_file(data_dir / "processed", "preprocessed_*.csv")
    if preprocessed_path:
        print(f"   - 前処理済みデータ: {preprocessed_path.name}")
        preprocessed_df = pd.read_csv(preprocessed_path, encoding="utf-8-sig")
    else:
        print("   ⚠️ 前処理済みデータが見つかりません")
        preprocessed_df = pd.DataFrame()

    # 各シートを作成
    sheets = {}

    # 1. 概要
    if len(preprocessed_df) > 0:
        print("   - 概要シートを作成")
        sheets["概要"] = create_overview(preprocessed_df)

        # 2. 成約率分布
        print("   - 成約率分布シートを作成")
        sheets["成約率分布"] = create_contract_rate_distribution(preprocessed_df)

    # 3. 調整案サマリー
    print("   - 調整案サマリーシートを作成")
    recommendations_summary = create_recommendations_summary(results_dir)
    if len(recommendations_summary) > 0:
        sheets["調整案サマリー"] = recommendations_summary

    # 4. 推奨アクション
    print("   - 推奨アクションシートを作成")
    sheets["推奨アクション"] = create_action_items(results_dir)

    # 5. 分析結果の詳細（既存ファイルから読み込み）
    analysis_path = load_latest_file(results_dir, "analysis_*.xlsx")
    if analysis_path:
        print("   - 分析詳細を追加")
        try:
            sheets["基本分析"] = pd.read_excel(analysis_path, sheet_name="基本分析")
            sheets["バッテリー劣化分析"] = pd.read_excel(analysis_path, sheet_name="バッテリー劣化分析")
        except Exception:
            pass

    # 出力
    today = datetime.now().strftime("%Y%m%d")
    output_path = results_dir / f"buyback_optimization_report_{today}.xlsx"

    print(f"\n✅ 出力: {output_path}")
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    # 結果表示
    print("\n📋 レポート構成:")
    for sheet_name in sheets.keys():
        print(f"   - {sheet_name}")

    print("\n🎯 次のステップ:")
    print("   1. きんとんから過去1ヶ月のデータをエクスポート")
    print("   2. preprocess_kintone_data.py で前処理")
    print("   3. analyze_buyback_data.py で分析")
    print("   4. recommend_base_price.py で基準価格調整案を生成")
    print("   5. recommend_deduction_rate.py で減額率調整案を生成")
    print("   6. simulate_new_prices.py でシミュレーション")
    print("   7. generate_report.py で総合レポート生成")


if __name__ == "__main__":
    main()
