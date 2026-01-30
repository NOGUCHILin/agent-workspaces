"""
きんとんCSVデータの前処理スクリプト

機能:
- Shift-JISで読み込み、UTF-8に変換
- 重複列の処理（機種、容量が2列ある問題）
- グループA/Bのフラグを追加
- 集計キーを作成
- 前処理済みCSVを出力

使用方法:
    uv run python scripts/preprocess_kintone_data.py kintone_YYYYMMDD.csv

出力:
    data/processed/preprocessed_YYYYMMDD.csv
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime


# =============================================================================
# グループA/B分類定義
# =============================================================================

# 不具合 - グループA: お客様が認識しやすい（減額率を上げにくい）
DEFECT_GROUP_A = [
    "不具合など[TouchIDやFaceIDの故障]",
    "不具合など[サイドボタンの故障]",
    "不具合など[正常に起動しない]",
    "不具合など[初期化できない]",
    "不具合など[ネットワーク利用制限]",
]

# 不具合 - グループB: お客様が認識しにくい（減額余地あり）
DEFECT_GROUP_B = [
    "不具合など[バッテリーの劣化]",  # 最重要
    "不具合など[表示やタッチ操作の劣化]",
    "不具合など[アウトカメラの故障]",
    "不具合など[バイブレーション不具合]",
    "不具合など[端末上部の不具合]",
    "不具合など[端末下部の不具合]",
    "不具合など[Wi-FiやBluetoothの不具合]",
    "不具合など[フラッシュの故障]",
    "不具合など[水没歴あり]",
    "不具合など[その他]",
]

# 修理 - グループA: お客様が認識しやすい（減額率を上げにくい）
REPAIR_GROUP_A = [
    "修理[画面修理]",
    "修理[アウトカメラガラス交換]",
]

# 修理 - グループB: お客様が認識しにくい（減額余地あり）
REPAIR_GROUP_B = [
    "修理[ドック修理]",
    "修理[インカメラ修理]",
    "修理[アウトカメラ修理]",
    "修理[タプティックエンジン修理]",
    "修理[バッテリー交換]",
]

# =============================================================================
# 進捗ステータスの分類（3段階ファネル）
# =============================================================================
# フロー:
#   仮査定 ─┬→ 梱包キット発送 → 成約
#           └→ 集荷 → 成約

# 段階2A: 梱包キットルート（お客様が自分で梱包して送る）
KIT_ROUTE_STATUSES = [
    "梱包キット発送完了",
    "梱包キット発送要望あり",
]

# 段階2B: 集荷ルート（ヤマトが集荷に行く）
PICKUP_ROUTE_STATUSES = [
    "集荷予定日確定",
    "集荷依頼受付済み",
]

# 段階3の途中: 本査定中（梱包キット or 集荷から進んだ）
ASSESSMENT_STATUSES = [
    "本査定開始",
    "本査定完了",
]

# 段階3: 成約
CONTRACT_STATUSES = [
    "来店買取成約",
    "宅配買取成約",
    "販売完了",
    "出品完了",
]

# 不成約（離脱）
LOST_STATUSES = [
    "本査定前不成約",
    "宅配買取不成約",
    "来店買取不成約",
]

# 来店フロー（宅配とは別）
VISIT_STATUSES = [
    "来店買取成約",
    "来店買取不成約",
]


def load_kintone_csv(filepath: str) -> pd.DataFrame:
    """きんとんCSVをShift-JISで読み込む"""
    df = pd.read_csv(filepath, encoding="shift-jis", dtype=str)
    return df


def fix_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """重複列を処理（機種と容量が2列ある問題）"""
    # 列名を取得
    cols = df.columns.tolist()

    # 重複列の処理
    # 機種: 1列目は空、2列目に値がある
    # 容量: 1列目は空、2列目に値がある

    # 新しい列名を作成（重複を解消）
    new_cols = []
    seen = {}
    for col in cols:
        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)

    df.columns = new_cols

    # 機種: 空でない方を採用
    if "機種" in df.columns and "機種_1" in df.columns:
        df["機種"] = df.apply(
            lambda row: row["機種_1"] if pd.isna(row["機種"]) or row["機種"] == "" else row["機種"],
            axis=1
        )
        df = df.drop(columns=["機種_1"])

    # 容量: 空でない方を採用
    if "容量" in df.columns and "容量_1" in df.columns:
        df["容量"] = df.apply(
            lambda row: row["容量_1"] if pd.isna(row["容量"]) or row["容量"] == "" else row["容量"],
            axis=1
        )
        df = df.drop(columns=["容量_1"])

    return df


def has_defect_or_repair(row: pd.Series, columns: list[str]) -> bool:
    """指定した列のいずれかに"1"があるか判定"""
    for col in columns:
        if col in row.index:
            val = row[col]
            if pd.notna(val) and str(val).strip() == "1":
                return True
    return False


def add_group_flags(df: pd.DataFrame) -> pd.DataFrame:
    """グループA/Bのフラグを追加"""
    # 不具合グループA
    df["不具合_グループA"] = df.apply(
        lambda row: has_defect_or_repair(row, DEFECT_GROUP_A), axis=1
    )

    # 不具合グループB
    df["不具合_グループB"] = df.apply(
        lambda row: has_defect_or_repair(row, DEFECT_GROUP_B), axis=1
    )

    # 修理グループA
    df["修理_グループA"] = df.apply(
        lambda row: has_defect_or_repair(row, REPAIR_GROUP_A), axis=1
    )

    # 修理グループB
    df["修理_グループB"] = df.apply(
        lambda row: has_defect_or_repair(row, REPAIR_GROUP_B), axis=1
    )

    # バッテリー劣化のみのフラグ（最重要項目）
    df["バッテリー劣化あり"] = df.apply(
        lambda row: has_defect_or_repair(row, ["不具合など[バッテリーの劣化]"]), axis=1
    )

    # 不具合なしフラグ
    all_defects = DEFECT_GROUP_A + DEFECT_GROUP_B
    df["不具合なし"] = df.apply(
        lambda row: not has_defect_or_repair(row, all_defects), axis=1
    )

    # 修理なしフラグ
    all_repairs = REPAIR_GROUP_A + REPAIR_GROUP_B
    df["修理なし"] = df.apply(
        lambda row: not has_defect_or_repair(row, all_repairs), axis=1
    )

    return df


def add_funnel_flags(df: pd.DataFrame) -> pd.DataFrame:
    """3段階ファネルのフラグを追加"""
    # 段階2以降に進んだもの（梱包キット or 集荷 or 本査定 or 成約 or 宅配不成約）
    stage2_or_later = (
        KIT_ROUTE_STATUSES +
        PICKUP_ROUTE_STATUSES +
        ASSESSMENT_STATUSES +
        CONTRACT_STATUSES +
        ["宅配買取不成約"]
    )
    df["段階2以降"] = df["進捗"].isin(stage2_or_later)

    # 段階2A: 梱包キットルート（梱包キット発送 or その後のステータス）
    # 梱包キットから進んだ人は本査定・成約にも進む
    df["梱包キットルート"] = df["進捗"].isin(KIT_ROUTE_STATUSES)

    # 段階2B: 集荷ルート（集荷 or その後のステータス）
    # 集荷から進んだ人は本査定・成約にも進む
    df["集荷ルート"] = df["進捗"].isin(PICKUP_ROUTE_STATUSES)

    # 段階2（梱包キット or 集荷）に進んだ
    df["梱包キットor集荷"] = df["梱包キットルート"] | df["集荷ルート"]

    # 本査定中
    df["本査定中"] = df["進捗"].isin(ASSESSMENT_STATUSES)

    # 成約（段階3）
    df["成約"] = df["進捗"].isin(CONTRACT_STATUSES)

    # 不成約（離脱）
    df["不成約"] = df["進捗"].isin(LOST_STATUSES)

    # 来店フロー（宅配とは別）
    df["来店"] = df["進捗"].isin(VISIT_STATUSES)

    return df


def add_aggregation_key(df: pd.DataFrame) -> pd.DataFrame:
    """集計キーを作成"""
    # 基本キー: 機種_容量_ランク
    df["集計キー_基本"] = df["機種"] + "_" + df["容量"] + "_" + df["ランク"]

    # 詳細キー: 基本キー + グループフラグ
    df["集計キー_詳細"] = (
        df["集計キー_基本"] + "_" +
        "不A:" + df["不具合_グループA"].astype(str) + "_" +
        "不B:" + df["不具合_グループB"].astype(str) + "_" +
        "修A:" + df["修理_グループA"].astype(str) + "_" +
        "修B:" + df["修理_グループB"].astype(str)
    )

    return df


def convert_price_columns(df: pd.DataFrame) -> pd.DataFrame:
    """価格列を数値型に変換"""
    price_cols = ["最高提示価格", "最低提示価格", "最終買取価格", "想定販売価格", "粗利(手数料引)", "卸売価格"]

    for col in price_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def convert_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """日付列をdatetime型に変換"""
    date_cols = ["作成日時", "買取日"]

    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


def preprocess(input_path: str, output_path: str) -> pd.DataFrame:
    """メイン前処理関数"""
    print(f"📂 読み込み: {input_path}")

    # 1. CSVを読み込み
    df = load_kintone_csv(input_path)
    print(f"   - 読み込み件数: {len(df):,}件")

    # 2. 重複列を処理
    df = fix_duplicate_columns(df)
    print("   - 重複列を処理")

    # 3. グループA/Bフラグを追加
    df = add_group_flags(df)
    print("   - グループA/Bフラグを追加")

    # 4. ファネルフラグを追加（梱包キット・集荷・成約）
    df = add_funnel_flags(df)
    print("   - ファネルフラグを追加")

    # 5. 集計キーを作成
    df = add_aggregation_key(df)
    print("   - 集計キーを作成")

    # 6. 価格列を数値型に変換
    df = convert_price_columns(df)
    print("   - 価格列を数値型に変換")

    # 7. 日付列を変換
    df = convert_date_columns(df)
    print("   - 日付列を変換")

    # 8. 出力
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ 出力: {output_path}")
    print(f"   - 出力件数: {len(df):,}件")

    # 統計サマリー
    total = len(df)
    kit_route = df['梱包キットルート'].sum()
    pickup_route = df['集荷ルート'].sum()
    assessment = df['本査定中'].sum()
    contracted = df['成約'].sum()
    lost = df['不成約'].sum()
    visit = df['来店'].sum()

    # 段階2以降に進んだ総数（成約 + 梱包キットor集荷 + 本査定中 + 不成約）
    stage2_total = contracted + kit_route + pickup_route + assessment + lost

    print("\n📊 統計サマリー:")
    print(f"   - 仮査定数: {total:,}件")
    print("")
    print("   【3段階ファネル】")
    print(f"   段階1: 仮査定 {total:,}件")
    print(f"   段階2以降: {stage2_total:,}件 (CVR: {stage2_total/total*100:.1f}%)")
    print(f"      - 梱包キットルート: {kit_route:,}件")
    print(f"      - 集荷ルート: {pickup_route:,}件")
    print(f"      - 本査定中: {assessment:,}件")
    print(f"      - 成約: {contracted:,}件")
    print(f"      - 不成約: {lost:,}件")
    print("")
    print(f"   段階3: 成約 {contracted:,}件")
    print(f"      - 成約率（段階2以降から）: {contracted/stage2_total*100:.1f}%")
    print(f"      - 成約率（全体から）: {contracted/total*100:.1f}%")
    print(f"      - 不成約率（段階2以降から）: {lost/stage2_total*100:.1f}%")
    print("")
    print(f"   【来店】{visit:,}件（別フロー）")
    print("")
    print("   【不具合・修理】")
    print(f"   - 不具合グループAあり: {df['不具合_グループA'].sum():,}件")
    print(f"   - 不具合グループBあり: {df['不具合_グループB'].sum():,}件")
    print(f"   - バッテリー劣化あり: {df['バッテリー劣化あり'].sum():,}件")
    print(f"   - 修理グループAあり: {df['修理_グループA'].sum():,}件")
    print(f"   - 修理グループBあり: {df['修理_グループB'].sum():,}件")
    print(f"   - 不具合・修理なし: {(df['不具合なし'] & df['修理なし']).sum():,}件")

    return df


def main():
    if len(sys.argv) < 2:
        print("使用方法: uv run python scripts/preprocess_kintone_data.py <入力CSVファイル>")
        print("例: uv run python scripts/preprocess_kintone_data.py kintone_20251125.csv")
        sys.exit(1)

    input_file = sys.argv[1]
    input_path = Path(input_file)

    if not input_path.exists():
        # カレントディレクトリで探す
        input_path = Path(__file__).parent.parent / input_file
        if not input_path.exists():
            print(f"❌ ファイルが見つかりません: {input_file}")
            sys.exit(1)

    # 出力ファイル名を生成
    today = datetime.now().strftime("%Y%m%d")
    output_dir = Path(__file__).parent.parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"preprocessed_{today}.csv"

    preprocess(str(input_path), str(output_path))


if __name__ == "__main__":
    main()
