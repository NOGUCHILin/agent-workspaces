#!/usr/bin/env python3
"""
分類の違いをデバッグするスクリプト
"""

import polars as pl
from pathlib import Path


def classify_service(description: str) -> str:
    """摘要からサービス名を分類（元のロジック）"""
    if not description or description == "":
        return "その他"

    desc_upper = description.upper()

    service_rules = {
        "Google": ["GOOGLE", "グーグル"],
        "Amazon": ["AMAZON", "アマゾン"],
        "Yahoo": ["ヤフー", "YAHOO"],
    }

    for service_name, keywords in service_rules.items():
        for keyword in keywords:
            if keyword in desc_upper or keyword in description:
                return service_name

    return "その他"


def main():
    project_root = Path(__file__).parent.parent
    source_file = project_root / "data" / "source" / "仕訳帳_20251029_1608.csv"

    # CSVファイル読み込み
    try:
        df = pl.read_csv(source_file, encoding="shift_jis", ignore_errors=True, null_values=["", "N/A"])
    except Exception:
        df = pl.read_csv(source_file, encoding="cp932", ignore_errors=True, null_values=["", "N/A"])

    # クレカ決済取引を抽出
    credit_card_df = df.filter(
        (pl.col("貸方勘定科目") == "未払金") &
        (pl.col("借方勘定科目").is_not_null()) &
        (pl.col("貸方補助科目").is_not_null())
    )

    # 方法1: 元のclassify_service関数で分類
    credit_card_df = credit_card_df.with_columns([
        pl.col("摘要").map_elements(classify_service, return_dtype=pl.Utf8).alias("サービス名")
    ])

    # 方法2: contains でフィルタ
    google_contains = credit_card_df.filter(
        pl.col("摘要").str.to_uppercase().str.contains("GOOGLE")
    )

    # 方法1でGoogleに分類された取引
    google_classified = credit_card_df.filter(pl.col("サービス名") == "Google")

    print("=" * 80)
    print("【方法1】classify_service関数で「Google」に分類")
    print("=" * 80)
    print(f"件数: {len(google_classified)}")
    print(f"合計金額: {google_classified['貸方金額(円)'].sum():,}円\n")

    print("=" * 80)
    print("【方法2】摘要に「GOOGLE」を含む")
    print("=" * 80)
    print(f"件数: {len(google_contains)}")
    print(f"合計金額: {google_contains['貸方金額(円)'].sum():,}円\n")

    print("=" * 80)
    print("【差分分析】方法1にあって方法2にない取引")
    print("=" * 80)

    # 差分を抽出
    diff = google_classified.filter(
        ~pl.col("摘要").str.to_uppercase().str.contains("GOOGLE")
    )

    if len(diff) > 0:
        print(f"\n⚠️  誤分類された取引: {len(diff)}件")
        print(f"誤分類金額: {diff['貸方金額(円)'].sum():,}円\n")

        # 誤分類された摘要を表示
        misclassified = diff.group_by("摘要").agg([
            pl.len().alias("件数"),
            pl.col("貸方金額(円)").sum().alias("合計金額")
        ]).sort("合計金額", descending=True)

        print("【誤分類された摘要】")
        print(misclassified)
    else:
        print("✅ 誤分類なし")

    print("\n" + "=" * 80)
    print("【逆差分】方法2にあって方法1にない取引")
    print("=" * 80)

    # 逆差分
    reverse_diff = google_contains.filter(
        pl.col("サービス名") != "Google"
    )

    if len(reverse_diff) > 0:
        print(f"\n⚠️  分類漏れ: {len(reverse_diff)}件")
        print(f"分類漏れ金額: {reverse_diff['貸方金額(円)'].sum():,}円\n")

        # 分類漏れの摘要を表示
        missed = reverse_diff.group_by(["摘要", "サービス名"]).agg([
            pl.len().alias("件数"),
            pl.col("貸方金額(円)").sum().alias("合計金額")
        ]).sort("合計金額", descending=True)

        print("【分類漏れの摘要】")
        print(missed)
    else:
        print("✅ 分類漏れなし")


if __name__ == "__main__":
    main()
