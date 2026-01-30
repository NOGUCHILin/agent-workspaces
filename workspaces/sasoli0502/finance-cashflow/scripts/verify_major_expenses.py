#!/usr/bin/env python3
"""
主要経費（Google広告・Yahoo広告・AWS）の詳細検証スクリプト

摘要の全パターンを抽出し、金額を正確に集計
"""

import polars as pl
from pathlib import Path


def main():
    # パス設定
    project_root = Path(__file__).parent.parent
    source_file = project_root / "data" / "source" / "仕訳帳_20251029_1608.csv"

    print(f"📂 読み込み: {source_file}\n")

    # CSVファイル読み込み
    try:
        df = pl.read_csv(
            source_file,
            encoding="shift_jis",
            ignore_errors=True,
            null_values=["", "N/A"],
        )
    except Exception:
        df = pl.read_csv(
            source_file,
            encoding="cp932",
            ignore_errors=True,
            null_values=["", "N/A"],
        )

    # クレカ決済取引を抽出
    credit_card_df = df.filter(
        (pl.col("貸方勘定科目") == "未払金") &
        (pl.col("借方勘定科目").is_not_null()) &
        (pl.col("貸方補助科目").is_not_null())
    )

    # 取引日を日付型に変換
    credit_card_df = credit_card_df.with_columns([
        pl.col("取引日").str.strptime(pl.Date, format="%Y/%m/%d", strict=False).alias("取引日")
    ])

    # 年月を抽出
    credit_card_df = credit_card_df.with_columns([
        pl.col("取引日").dt.strftime("%Y-%m").alias("年月")
    ])

    print("=" * 80)
    print("【1】Google関連の全取引パターン")
    print("=" * 80)

    # Google関連を抽出（大文字小文字を区別しない）
    google_df = credit_card_df.filter(
        pl.col("摘要").str.to_uppercase().str.contains("GOOGLE")
    )

    print(f"\n💰 Google関連取引: {len(google_df)}件\n")

    # 摘要パターン別の集計
    google_summary = google_df.group_by(["摘要", "借方勘定科目"]).agg([
        pl.len().alias("件数"),
        pl.col("貸方金額(円)").sum().alias("合計金額"),
        pl.col("貸方金額(円)").mean().alias("平均金額"),
    ]).sort("合計金額", descending=True)

    print("【摘要パターン別】")
    print(google_summary)

    # 月次集計
    google_monthly = google_df.group_by("年月").agg([
        pl.len().alias("件数"),
        pl.col("貸方金額(円)").sum().alias("合計金額"),
    ]).sort("年月")

    print("\n【月次合計】")
    print(google_monthly)
    print(f"\n🔴 Google合計: {google_df['貸方金額(円)'].sum():,}円\n")

    print("=" * 80)
    print("【2】Yahoo関連の全取引パターン")
    print("=" * 80)

    # Yahoo関連を抽出
    yahoo_df = credit_card_df.filter(
        pl.col("摘要").str.to_uppercase().str.contains("YAHOO|ヤフー")
    )

    print(f"\n💰 Yahoo関連取引: {len(yahoo_df)}件\n")

    # 摘要パターン別の集計
    yahoo_summary = yahoo_df.group_by(["摘要", "借方勘定科目"]).agg([
        pl.len().alias("件数"),
        pl.col("貸方金額(円)").sum().alias("合計金額"),
        pl.col("貸方金額(円)").mean().alias("平均金額"),
    ]).sort("合計金額", descending=True)

    print("【摘要パターン別】")
    print(yahoo_summary)

    # 月次集計
    yahoo_monthly = yahoo_df.group_by("年月").agg([
        pl.len().alias("件数"),
        pl.col("貸方金額(円)").sum().alias("合計金額"),
    ]).sort("年月")

    print("\n【月次合計】")
    print(yahoo_monthly)
    print(f"\n🔴 Yahoo合計: {yahoo_df['貸方金額(円)'].sum():,}円\n")

    print("=" * 80)
    print("【3】AWS関連の全取引パターン")
    print("=" * 80)

    # AWS関連を抽出
    aws_df = credit_card_df.filter(
        pl.col("摘要").str.to_uppercase().str.contains("AWS|AMAZON WEB")
    )

    print(f"\n💰 AWS関連取引: {len(aws_df)}件\n")

    if len(aws_df) > 0:
        # 摘要パターン別の集計
        aws_summary = aws_df.group_by(["摘要", "借方勘定科目"]).agg([
            pl.len().alias("件数"),
            pl.col("貸方金額(円)").sum().alias("合計金額"),
            pl.col("貸方金額(円)").mean().alias("平均金額"),
        ]).sort("合計金額", descending=True)

        print("【摘要パターン別】")
        print(aws_summary)

        # 月次集計
        aws_monthly = aws_df.group_by("年月").agg([
            pl.len().alias("件数"),
            pl.col("貸方金額(円)").sum().alias("合計金額"),
        ]).sort("年月")

        print("\n【月次合計】")
        print(aws_monthly)
        print(f"\n🔴 AWS合計: {aws_df['貸方金額(円)'].sum():,}円\n")
    else:
        print("⚠️  AWS関連の取引が見つかりませんでした\n")

    print("=" * 80)
    print("【4】LINE関連の全取引パターン")
    print("=" * 80)

    # LINE関連を抽出
    line_df = credit_card_df.filter(
        pl.col("摘要").str.to_uppercase().str.contains("LINE")
    )

    print(f"\n💰 LINE関連取引: {len(line_df)}件\n")

    if len(line_df) > 0:
        # 摘要パターン別の集計
        line_summary = line_df.group_by(["摘要", "借方勘定科目"]).agg([
            pl.len().alias("件数"),
            pl.col("貸方金額(円)").sum().alias("合計金額"),
            pl.col("貸方金額(円)").mean().alias("平均金額"),
        ]).sort("合計金額", descending=True)

        print("【摘要パターン別】")
        print(line_summary)

        # 月次集計
        line_monthly = line_df.group_by("年月").agg([
            pl.len().alias("件数"),
            pl.col("貸方金額(円)").sum().alias("合計金額"),
        ]).sort("年月")

        print("\n【月次合計】")
        print(line_monthly)
        print(f"\n🔴 LINE合計: {line_df['貸方金額(円)'].sum():,}円\n")

    print("=" * 80)
    print("【総括】7ヶ月間の主要広告費")
    print("=" * 80)
    print(f"Google広告: {google_df['貸方金額(円)'].sum():,}円")
    print(f"Yahoo広告:  {yahoo_df['貸方金額(円)'].sum():,}円")
    print(f"LINE広告:   {line_df['貸方金額(円)'].sum():,}円")
    if len(aws_df) > 0:
        print(f"AWS:        {aws_df['貸方金額(円)'].sum():,}円")
    print(f"\n合計:       {google_df['貸方金額(円)'].sum() + yahoo_df['貸方金額(円)'].sum() + line_df['貸方金額(円)'].sum() + (aws_df['貸方金額(円)'].sum() if len(aws_df) > 0 else 0):,}円")


if __name__ == "__main__":
    main()
