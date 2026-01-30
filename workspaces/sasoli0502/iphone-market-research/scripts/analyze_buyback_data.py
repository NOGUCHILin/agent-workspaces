"""
買取データの集計・分析スクリプト

機能:
- 前処理済みCSVを読み込み
- 3段階ファネル分析（仮査定→梱包キット/集荷→成約）
- 機種・容量・ランク・グループA・グループBごとに集計
- 成約率に基づいて問題パターンを自動検出
- 分析結果をExcelに出力

使用方法:
    uv run python scripts/analyze_buyback_data.py
    uv run python scripts/analyze_buyback_data.py --after "2025-11-19 17:38:00"

入力:
    data/processed/preprocessed_YYYYMMDD.csv（最新のファイル）

出力:
    data/results/analysis_YYYYMMDD.xlsx
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys


# =============================================================================
# 閾値設定
# =============================================================================

# 最小サンプル数（これ未満は「データ不足」として判定しない）
MIN_SAMPLE_SIZE = 5

# =============================================================================
# 基準価格調整の閾値（段階2進行率で判定）
# =============================================================================
# 段階2進行率が高い = 基準価格に魅力がある = 価格を下げる余地あり
# 段階2進行率が低い = 基準価格が低すぎる = 価格を上げるべき

STAGE2_RATE_HIGH = 0.25  # 25%以上: 基準価格を下げる余地あり
STAGE2_RATE_LOW = 0.10   # 10%以下: 基準価格を上げるべき

# =============================================================================
# 減額率調整の閾値（段階2→成約率で判定）
# =============================================================================
# 成約率が高い = 減額幅が適正or緩い = 減額を強化する余地あり
# 成約率が低い = 減額幅がキツすぎる = 減額を緩和すべき

CONTRACT_RATE_HIGH = 0.70  # 70%以上: 減額強化の余地あり
CONTRACT_RATE_LOW = 0.40   # 40%以下: 減額緩和すべき


def load_preprocessed_csv(data_dir: Path, after_datetime: str = None, before_datetime: str = None) -> tuple[pd.DataFrame, str]:
    """最新の前処理済みCSVを読み込む

    Args:
        data_dir: データディレクトリ
        after_datetime: この日時以降のデータのみ抽出（例: "2025-11-19 17:38:00"）
        before_datetime: この日時以前のデータのみ抽出（例: "2025-11-19 17:38:00"）
    """
    processed_dir = data_dir / "processed"
    files = list(processed_dir.glob("preprocessed_*.csv"))

    if not files:
        raise FileNotFoundError(f"前処理済みCSVが見つかりません: {processed_dir}")

    # 最新のファイルを取得
    latest_file = max(files, key=lambda x: x.stat().st_mtime)
    print(f"📂 読み込み: {latest_file}")

    df = pd.read_csv(latest_file, encoding="utf-8-sig")
    print(f"   - 全データ: {len(df):,}件")

    # 日付フィルタ（after）
    if after_datetime:
        df["作成日時"] = pd.to_datetime(df["作成日時"], errors="coerce")
        filter_dt = pd.to_datetime(after_datetime)
        df = df[df["作成日時"] >= filter_dt]
        print(f"   - {after_datetime} 以降にフィルタ: {len(df):,}件")

    # 日付フィルタ（before）
    if before_datetime:
        df["作成日時"] = pd.to_datetime(df["作成日時"], errors="coerce")
        filter_dt = pd.to_datetime(before_datetime)
        df = df[df["作成日時"] < filter_dt]
        print(f"   - {before_datetime} 以前にフィルタ: {len(df):,}件")

    return df, latest_file.name


def analyze_by_group(df: pd.DataFrame, group_cols: list[str], label: str) -> pd.DataFrame:
    """グループごとに集計・分析（3段階ファネル対応）"""
    # 有効なデータのみ抽出（機種、容量、ランクが空でないもの）
    valid_df = df[
        (df["機種"].notna()) &
        (df["機種"] != "") &
        (df["容量"].notna()) &
        (df["容量"] != "") &
        (df["ランク"].notna()) &
        (df["ランク"] != "")
    ].copy()

    # グループ化して集計（3段階ファネル対応）
    grouped = valid_df.groupby(group_cols, dropna=False).agg(
        仮査定数=("レコード番号", "count"),
        梱包キット数=("梱包キットルート", "sum"),
        集荷数=("集荷ルート", "sum"),
        本査定中数=("本査定中", "sum"),
        成約数=("成約", "sum"),
        不成約数=("不成約", "sum"),
        平均提示価格=("最高提示価格", "mean"),
        平均最終買取価格=("最終買取価格", "mean"),
        平均粗利=("粗利(手数料引)", "mean"),
    ).reset_index()

    # 段階2以降の合計（成約 + 梱包キット + 集荷 + 本査定中 + 不成約）
    grouped["段階2以降数"] = (
        grouped["成約数"] +
        grouped["梱包キット数"] +
        grouped["集荷数"] +
        grouped["本査定中数"] +
        grouped["不成約数"]
    )

    # 各種CVRを計算
    grouped["段階2進行率"] = grouped["段階2以降数"] / grouped["仮査定数"]
    grouped["成約率_全体"] = grouped["成約数"] / grouped["仮査定数"]
    grouped["成約率_段階2"] = grouped.apply(
        lambda row: row["成約数"] / row["段階2以降数"] if row["段階2以降数"] > 0 else 0,
        axis=1
    )
    grouped["不成約率_段階2"] = grouped.apply(
        lambda row: row["不成約数"] / row["段階2以降数"] if row["段階2以降数"] > 0 else 0,
        axis=1
    )

    # 基準価格の判定（段階2進行率で判定）
    def judge_base_price(row):
        if row["仮査定数"] < MIN_SAMPLE_SIZE:
            return "データ不足"
        elif row["段階2進行率"] >= STAGE2_RATE_HIGH:
            return "価格下げ余地"
        elif row["段階2進行率"] <= STAGE2_RATE_LOW:
            return "価格上げるべき"
        else:
            return "適正"

    grouped["基準価格判定"] = grouped.apply(judge_base_price, axis=1)

    # 減額率の判定（段階2→成約率で判定）
    def judge_deduction(row):
        if row["段階2以降数"] < MIN_SAMPLE_SIZE:
            return "データ不足"
        elif row["成約率_段階2"] >= CONTRACT_RATE_HIGH:
            return "減額強化余地"
        elif row["成約率_段階2"] <= CONTRACT_RATE_LOW:
            return "減額緩和すべき"
        else:
            return "適正"

    grouped["減額率判定"] = grouped.apply(judge_deduction, axis=1)

    # 総合判定（両方の観点を組み合わせ）
    def judge_overall(row):
        base = row["基準価格判定"]
        ded = row["減額率判定"]
        if base == "データ不足" and ded == "データ不足":
            return "データ不足"
        elif base == "価格下げ余地" or ded == "減額強化余地":
            return "調整余地あり"
        elif base == "価格上げるべき" or ded == "減額緩和すべき":
            return "要改善"
        else:
            return "適正"

    grouped["総合判定"] = grouped.apply(judge_overall, axis=1)

    # 優先度を設定
    priority_map = {
        "要改善": 1,
        "調整余地あり": 2,
        "適正": 3,
        "データ不足": 4,
    }
    grouped["優先度"] = grouped["総合判定"].map(priority_map)

    # 分析レベルのラベルを追加
    grouped["分析レベル"] = label

    # ソート（優先度 → 成約数降順）
    grouped = grouped.sort_values(["優先度", "成約数"], ascending=[True, False])

    # 後方互換性のための列
    grouped["成約率"] = grouped["成約率_段階2"]
    grouped["判定"] = grouped["総合判定"]

    return grouped


def analyze_basic(df: pd.DataFrame) -> pd.DataFrame:
    """基本分析: 機種・容量・ランク別"""
    group_cols = ["機種", "容量", "ランク"]
    return analyze_by_group(df, group_cols, "基本（機種・容量・ランク）")


def analyze_with_defect_group(df: pd.DataFrame) -> pd.DataFrame:
    """詳細分析: 機種・容量・ランク・不具合グループ別"""
    group_cols = ["機種", "容量", "ランク", "不具合_グループA", "不具合_グループB"]
    return analyze_by_group(df, group_cols, "詳細（不具合グループ含む）")


def analyze_with_repair_group(df: pd.DataFrame) -> pd.DataFrame:
    """詳細分析: 機種・容量・ランク・修理グループ別"""
    group_cols = ["機種", "容量", "ランク", "修理_グループA", "修理_グループB"]
    return analyze_by_group(df, group_cols, "詳細（修理グループ含む）")


def analyze_battery_degradation(df: pd.DataFrame) -> pd.DataFrame:
    """バッテリー劣化特化分析"""
    group_cols = ["機種", "容量", "ランク", "バッテリー劣化あり"]
    return analyze_by_group(df, group_cols, "バッテリー劣化特化")


def analyze_no_defect_no_repair(df: pd.DataFrame) -> pd.DataFrame:
    """不具合・修理なしのみ分析"""
    clean_df = df[(df["不具合なし"] == True) & (df["修理なし"] == True)].copy()
    group_cols = ["機種", "容量", "ランク"]
    result = analyze_by_group(clean_df, group_cols, "不具合・修理なし")
    result["不具合なし"] = True
    result["修理なし"] = True
    return result


def generate_summary(df: pd.DataFrame, analysis_results: dict) -> pd.DataFrame:
    """全体サマリーを生成（3段階ファネル対応）"""
    summary_data = []

    # 全体統計
    total = len(df)
    kit_route = df['梱包キットルート'].sum()
    pickup_route = df['集荷ルート'].sum()
    assessment = df['本査定中'].sum()
    contracted = df['成約'].sum()
    lost = df['不成約'].sum()
    visit = df['来店'].sum()

    # 段階2以降に進んだ総数
    stage2_total = contracted + kit_route + pickup_route + assessment + lost

    summary_data.append({
        "項目": "【3段階ファネル統計】",
        "値": "",
        "詳細": "",
    })
    summary_data.append({
        "項目": "段階1: 仮査定数",
        "値": f"{total:,}件",
        "詳細": "",
    })
    summary_data.append({
        "項目": "段階2以降: 合計",
        "値": f"{stage2_total:,}件",
        "詳細": f"進行率: {stage2_total/total*100:.1f}%",
    })
    summary_data.append({
        "項目": "  - 梱包キットルート",
        "値": f"{kit_route:,}件",
        "詳細": "",
    })
    summary_data.append({
        "項目": "  - 集荷ルート",
        "値": f"{pickup_route:,}件",
        "詳細": "",
    })
    summary_data.append({
        "項目": "  - 本査定中",
        "値": f"{assessment:,}件",
        "詳細": "",
    })
    summary_data.append({
        "項目": "  - 成約",
        "値": f"{contracted:,}件",
        "詳細": "",
    })
    summary_data.append({
        "項目": "  - 不成約",
        "値": f"{lost:,}件",
        "詳細": "",
    })
    summary_data.append({
        "項目": "段階3: 成約",
        "値": f"{contracted:,}件",
        "詳細": "",
    })
    summary_data.append({
        "項目": "",
        "値": "",
        "詳細": "",
    })
    summary_data.append({
        "項目": "【成約率】",
        "値": "",
        "詳細": "",
    })
    summary_data.append({
        "項目": "成約率（全体から）",
        "値": f"{contracted/total*100:.1f}%",
        "詳細": f"{contracted:,} / {total:,}",
    })
    summary_data.append({
        "項目": "成約率（段階2以降から）",
        "値": f"{contracted/stage2_total*100:.1f}%" if stage2_total > 0 else "N/A",
        "詳細": f"{contracted:,} / {stage2_total:,}",
    })
    summary_data.append({
        "項目": "不成約率（段階2以降から）",
        "値": f"{lost/stage2_total*100:.1f}%" if stage2_total > 0 else "N/A",
        "詳細": f"{lost:,} / {stage2_total:,}",
    })
    summary_data.append({
        "項目": "",
        "値": "",
        "詳細": "",
    })
    summary_data.append({
        "項目": "【来店】",
        "値": f"{visit:,}件",
        "詳細": "別フロー",
    })
    summary_data.append({
        "項目": "",
        "値": "",
        "詳細": "",
    })

    # 不具合・修理統計
    summary_data.append({
        "項目": "【不具合・修理統計】",
        "値": "",
        "詳細": "",
    })
    summary_data.append({
        "項目": "不具合グループA（認識しやすい）",
        "値": f"{df['不具合_グループA'].sum():,}件",
        "詳細": f"{df['不具合_グループA'].mean()*100:.1f}%",
    })
    summary_data.append({
        "項目": "不具合グループB（認識しにくい）",
        "値": f"{df['不具合_グループB'].sum():,}件",
        "詳細": f"{df['不具合_グループB'].mean()*100:.1f}%",
    })
    summary_data.append({
        "項目": "  うちバッテリー劣化",
        "値": f"{df['バッテリー劣化あり'].sum():,}件",
        "詳細": f"{df['バッテリー劣化あり'].mean()*100:.1f}%",
    })
    summary_data.append({
        "項目": "不具合・修理なし（クリーン）",
        "値": f"{(df['不具合なし'] & df['修理なし']).sum():,}件",
        "詳細": f"{(df['不具合なし'] & df['修理なし']).mean()*100:.1f}%",
    })
    summary_data.append({
        "項目": "",
        "値": "",
        "詳細": "",
    })

    # 各分析レベルの統計
    summary_data.append({
        "項目": "【分析結果サマリー】",
        "値": "",
        "詳細": "",
    })
    for label, result_df in analysis_results.items():
        # 基準価格判定
        base_counts = result_df["基準価格判定"].value_counts()
        # 減額率判定
        ded_counts = result_df["減額率判定"].value_counts()
        summary_data.append({
            "項目": f"{label}分析",
            "値": "",
            "詳細": f"基準価格[下げ余地:{base_counts.get('価格下げ余地', 0)}件, 上げるべき:{base_counts.get('価格上げるべき', 0)}件] / "
                    f"減額率[強化余地:{ded_counts.get('減額強化余地', 0)}件, 緩和すべき:{ded_counts.get('減額緩和すべき', 0)}件]",
        })

    return pd.DataFrame(summary_data)


def main():
    # コマンドライン引数の処理
    after_datetime = None
    before_datetime = None
    output_suffix = ""

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--after" and i + 1 < len(sys.argv):
            after_datetime = sys.argv[i + 1]
            print(f"📅 日付フィルタ: {after_datetime} 以降")
            i += 2
        elif sys.argv[i] == "--before" and i + 1 < len(sys.argv):
            before_datetime = sys.argv[i + 1]
            print(f"📅 日付フィルタ: {before_datetime} 以前")
            i += 2
        elif sys.argv[i] == "--suffix" and i + 1 < len(sys.argv):
            output_suffix = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # パス設定
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    results_dir = data_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # データ読み込み
    df, input_filename = load_preprocessed_csv(data_dir, after_datetime=after_datetime, before_datetime=before_datetime)
    print(f"   - 分析対象: {len(df):,}件")

    # 各レベルで分析
    print("\n📊 分析中...")

    analysis_results = {}

    # 1. 基本分析
    print("   - 基本分析（機種・容量・ランク）")
    analysis_results["基本"] = analyze_basic(df)

    # 2. 不具合グループ含む分析
    print("   - 詳細分析（不具合グループ含む）")
    analysis_results["不具合グループ"] = analyze_with_defect_group(df)

    # 3. 修理グループ含む分析
    print("   - 詳細分析（修理グループ含む）")
    analysis_results["修理グループ"] = analyze_with_repair_group(df)

    # 4. バッテリー劣化特化分析
    print("   - バッテリー劣化特化分析")
    analysis_results["バッテリー劣化"] = analyze_battery_degradation(df)

    # 5. 不具合・修理なし分析
    print("   - 不具合・修理なし分析")
    analysis_results["クリーン"] = analyze_no_defect_no_repair(df)

    # サマリー生成
    summary_df = generate_summary(df, analysis_results)

    # 出力ファイル名
    today = datetime.now().strftime("%Y%m%d")
    if output_suffix:
        output_path = results_dir / f"analysis_{today}_{output_suffix}.xlsx"
    else:
        output_path = results_dir / f"analysis_{today}.xlsx"

    # Excelに複数シートで出力
    print(f"\n✅ 出力: {output_path}")
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="サマリー", index=False)
        analysis_results["基本"].to_excel(writer, sheet_name="基本分析", index=False)
        analysis_results["不具合グループ"].to_excel(writer, sheet_name="不具合グループ分析", index=False)
        analysis_results["修理グループ"].to_excel(writer, sheet_name="修理グループ分析", index=False)
        analysis_results["バッテリー劣化"].to_excel(writer, sheet_name="バッテリー劣化分析", index=False)
        analysis_results["クリーン"].to_excel(writer, sheet_name="クリーン分析", index=False)

    # 結果サマリーを表示
    print("\n📋 分析結果サマリー:")

    # 3段階ファネル統計
    total = len(df)
    kit_route = df['梱包キットルート'].sum()
    pickup_route = df['集荷ルート'].sum()
    assessment = df['本査定中'].sum()
    contracted = df['成約'].sum()
    lost = df['不成約'].sum()
    stage2_total = contracted + kit_route + pickup_route + assessment + lost

    print("\n   【3段階ファネル】")
    print(f"   段階1: 仮査定 {total:,}件")
    print(f"   段階2以降: {stage2_total:,}件 (進行率: {stage2_total/total*100:.1f}%)")
    print(f"   段階3: 成約 {contracted:,}件")
    print(f"      - 成約率（段階2以降から）: {contracted/stage2_total*100:.1f}%")
    print(f"      - 不成約率（段階2以降から）: {lost/stage2_total*100:.1f}%")

    for label, result_df in analysis_results.items():
        base_down = len(result_df[result_df["基準価格判定"] == "価格下げ余地"])
        base_up = len(result_df[result_df["基準価格判定"] == "価格上げるべき"])
        ded_strong = len(result_df[result_df["減額率判定"] == "減額強化余地"])
        ded_weak = len(result_df[result_df["減額率判定"] == "減額緩和すべき"])

        print(f"\n   【{label}分析】")
        print(f"      基準価格: 下げ余地{base_down}件 / 上げるべき{base_up}件")
        print(f"      減額率: 強化余地{ded_strong}件 / 緩和すべき{ded_weak}件")

        # 基準価格を下げる余地がある上位を表示
        if base_down > 0:
            top_base = result_df[result_df["基準価格判定"] == "価格下げ余地"].head(3)
            print("      [基準価格下げ余地の上位]")
            for _, row in top_base.iterrows():
                print(f"        {row['機種']} {row['容量']} {row['ランク']}: 段階2進行率{row['段階2進行率']*100:.1f}% ({row['仮査定数']:.0f}件)")

        # 減額強化余地がある上位を表示
        if ded_strong > 0:
            top_ded = result_df[result_df["減額率判定"] == "減額強化余地"].head(3)
            print("      [減額強化余地の上位]")
            for _, row in top_ded.iterrows():
                print(f"        {row['機種']} {row['容量']} {row['ランク']}: 成約率{row['成約率_段階2']*100:.1f}% ({row['段階2以降数']:.0f}件)")


if __name__ == "__main__":
    main()
