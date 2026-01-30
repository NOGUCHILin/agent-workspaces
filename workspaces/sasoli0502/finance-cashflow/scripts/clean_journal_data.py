#!/usr/bin/env python3
"""
仕訳帳データの整形スクリプト

元データをクリーンにし、分析しやすい形式に変換
"""

import polars as pl
from pathlib import Path
from datetime import datetime


def main():
    # パス設定
    project_root = Path(__file__).parent.parent
    source_file = project_root / "data" / "source" / "仕訳帳_20251029_1608.csv"
    output_dir = project_root / "data" / "processed"

    output_cleaned = output_dir / "transactions_cleaned.csv"
    output_grouped = output_dir / "transactions_grouped.csv"
    report_file = output_dir / "cleaning_report.txt"

    output_dir.mkdir(exist_ok=True)

    # レポート出力用のリスト
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("仕訳帳データ整形レポート")
    report_lines.append("=" * 80)
    report_lines.append(f"処理日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"元データ: {source_file}")
    report_lines.append("")

    print("📂 仕訳帳データの整形を開始します\n")
    print(f"元データ: {source_file}\n")

    # ===== Phase 1: データ読み込み =====
    print("Phase 1: データ読み込み")
    print("-" * 80)

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

    print(f"✅ 読み込み完了: {len(df):,}行")
    report_lines.append(f"【Phase 1: データ読み込み】")
    report_lines.append(f"元データ行数: {len(df):,}行")
    report_lines.append(f"元データ列数: {len(df.columns)}列")
    report_lines.append("")

    # 元データの金額合計を計算（基準値）
    original_debit_total = df["借方金額(円)"].sum()
    original_credit_total = df["貸方金額(円)"].sum()

    print(f"借方合計: {original_debit_total:,.0f}円")
    print(f"貸方合計: {original_credit_total:,.0f}円")
    print(f"貸借差額: {abs(original_debit_total - original_credit_total):,.0f}円\n")

    report_lines.append(f"【元データの金額】")
    report_lines.append(f"借方合計: {original_debit_total:,.0f}円")
    report_lines.append(f"貸方合計: {original_credit_total:,.0f}円")
    report_lines.append(f"貸借差額: {abs(original_debit_total - original_credit_total):,.0f}円")
    report_lines.append("")

    # ===== Phase 2: 基本整形版の作成 =====
    print("Phase 2: 基本整形版の作成")
    print("-" * 80)

    # 不要列を削除
    columns_to_keep = [
        "取引No", "取引日",
        "借方勘定科目", "借方補助科目", "借方税区分", "借方金額(円)",
        "貸方勘定科目", "貸方補助科目", "貸方税区分", "貸方金額(円)",
        "摘要", "メモ"
    ]

    df_cleaned = df.select(columns_to_keep)

    # 日付を標準化
    df_cleaned = df_cleaned.with_columns([
        pl.col("取引日").str.strptime(pl.Date, format="%Y/%m/%d", strict=False).alias("取引日")
    ])

    # 空白・改行のクリーニング
    for col in ["借方補助科目", "貸方補助科目", "摘要", "メモ"]:
        df_cleaned = df_cleaned.with_columns([
            pl.col(col).str.strip_chars().alias(col)
        ])

    # 金額を整数化（nullは0に）
    df_cleaned = df_cleaned.with_columns([
        pl.col("借方金額(円)").fill_null(0).cast(pl.Int64),
        pl.col("貸方金額(円)").fill_null(0).cast(pl.Int64),
    ])

    # 金額検証
    cleaned_debit_total = df_cleaned["借方金額(円)"].sum()
    cleaned_credit_total = df_cleaned["貸方金額(円)"].sum()

    print(f"✅ 整形完了: {len(df_cleaned):,}行")
    print(f"借方合計: {cleaned_debit_total:,}円")
    print(f"貸方合計: {cleaned_credit_total:,}円")

    # 検証
    if cleaned_debit_total == original_debit_total and cleaned_credit_total == original_credit_total:
        print("✅ 金額整合性チェック: OK\n")
        report_lines.append(f"【Phase 2: 基本整形版】")
        report_lines.append(f"整形後行数: {len(df_cleaned):,}行（変更なし）")
        report_lines.append(f"整形後列数: {len(df_cleaned.columns)}列（{len(df.columns) - len(df_cleaned.columns)}列削除）")
        report_lines.append(f"削除した列: 借方部門, 借方取引先, 借方インボイス, 貸方部門, 貸方取引先, 貸方インボイス, タグ")
        report_lines.append(f"借方合計: {cleaned_debit_total:,}円 ✅")
        report_lines.append(f"貸方合計: {cleaned_credit_total:,}円 ✅")
        report_lines.append(f"金額整合性: OK")
        report_lines.append("")
    else:
        print("❌ 金額整合性チェック: NG（差異あり）\n")
        report_lines.append(f"❌ 金額整合性: NG")
        report_lines.append(f"借方差異: {cleaned_debit_total - original_debit_total:,}円")
        report_lines.append(f"貸方差異: {cleaned_credit_total - original_credit_total:,}円")
        report_lines.append("")

    # CSV出力
    df_cleaned.write_csv(output_cleaned)
    print(f"📄 出力: {output_cleaned}\n")

    # ===== Phase 3: 取引単位版の作成 =====
    print("Phase 3: 取引単位版の作成")
    print("-" * 80)

    # 取引No単位でグループ化
    df_grouped = df_cleaned.group_by("取引No").agg([
        pl.col("取引日").first(),
        # 借方の集約
        pl.col("借方勘定科目").drop_nulls().str.concat(delimiter=", ").alias("借方勘定科目"),
        pl.col("借方補助科目").drop_nulls().str.concat(delimiter=", ").alias("借方補助科目"),
        pl.col("借方金額(円)").sum().alias("借方金額合計"),
        # 貸方の集約
        pl.col("貸方勘定科目").drop_nulls().str.concat(delimiter=", ").alias("貸方勘定科目"),
        pl.col("貸方補助科目").drop_nulls().str.concat(delimiter=", ").alias("貸方補助科目"),
        pl.col("貸方金額(円)").sum().alias("貸方金額合計"),
        # 摘要（最初の行）
        pl.col("摘要").drop_nulls().first().alias("主要摘要"),
        # 行数（複合仕訳の判定用）
        pl.len().alias("明細行数"),
    ]).sort("取引No")

    # 取引種別の判定
    df_grouped = df_grouped.with_columns([
        pl.when(pl.col("明細行数") == 1)
        .then(pl.lit("単純仕訳"))
        .otherwise(pl.lit("複合仕訳"))
        .alias("取引種別")
    ])

    # 列順を整理
    df_grouped = df_grouped.select([
        "取引No", "取引日", "取引種別", "明細行数",
        "借方勘定科目", "借方補助科目", "借方金額合計",
        "貸方勘定科目", "貸方補助科目", "貸方金額合計",
        "主要摘要"
    ])

    # 金額検証
    grouped_debit_total = df_grouped["借方金額合計"].sum()
    grouped_credit_total = df_grouped["貸方金額合計"].sum()

    print(f"✅ 集約完了: {len(df_grouped):,}取引")
    print(f"単純仕訳: {df_grouped.filter(pl.col('取引種別') == '単純仕訳').height:,}件")
    print(f"複合仕訳: {df_grouped.filter(pl.col('取引種別') == '複合仕訳').height:,}件")
    print(f"借方合計: {grouped_debit_total:,}円")
    print(f"貸方合計: {grouped_credit_total:,}円")

    # 検証
    if grouped_debit_total == original_debit_total and grouped_credit_total == original_credit_total:
        print("✅ 金額整合性チェック: OK\n")
        report_lines.append(f"【Phase 3: 取引単位版】")
        report_lines.append(f"取引数: {len(df_grouped):,}件")
        report_lines.append(f"単純仕訳: {df_grouped.filter(pl.col('取引種別') == '単純仕訳').height:,}件")
        report_lines.append(f"複合仕訳: {df_grouped.filter(pl.col('取引種別') == '複合仕訳').height:,}件")
        report_lines.append(f"借方合計: {grouped_debit_total:,}円 ✅")
        report_lines.append(f"貸方合計: {grouped_credit_total:,}円 ✅")
        report_lines.append(f"金額整合性: OK")
        report_lines.append("")
    else:
        print("❌ 金額整合性チェック: NG（差異あり）\n")
        report_lines.append(f"❌ 金額整合性: NG")
        report_lines.append(f"借方差異: {grouped_debit_total - original_debit_total:,}円")
        report_lines.append(f"貸方差異: {grouped_credit_total - original_credit_total:,}円")
        report_lines.append("")

    # CSV出力
    df_grouped.write_csv(output_grouped)
    print(f"📄 出力: {output_grouped}\n")

    # ===== Phase 4: サンプル表示 =====
    print("Phase 4: サンプル表示")
    print("-" * 80)

    # 単純仕訳のサンプル
    print("\n【単純仕訳のサンプル（5件）】")
    simple = df_grouped.filter(pl.col("取引種別") == "単純仕訳").head(5)
    print(simple)

    # 複合仕訳のサンプル
    print("\n【複合仕訳のサンプル（3件）】")
    compound = df_grouped.filter(pl.col("取引種別") == "複合仕訳").head(3)
    print(compound)

    # クレカ決済のサンプル
    print("\n【クレカ決済のサンプル（5件）】")
    credit_card = df_cleaned.filter(
        pl.col("貸方勘定科目") == "未払金"
    ).head(5).select([
        "取引No", "取引日", "借方勘定科目", "借方金額(円)",
        "貸方補助科目", "貸方金額(円)", "摘要"
    ])
    print(credit_card)

    report_lines.append(f"【Phase 4: サンプル確認】")
    report_lines.append(f"単純仕訳、複合仕訳、クレカ決済のサンプルを出力しました")
    report_lines.append("")

    # ===== 最終サマリー =====
    print("\n" + "=" * 80)
    print("整形完了サマリー")
    print("=" * 80)
    print(f"✅ 基本整形版: {output_cleaned}")
    print(f"   {len(df_cleaned):,}行 × {len(df_cleaned.columns)}列")
    print(f"✅ 取引単位版: {output_grouped}")
    print(f"   {len(df_grouped):,}取引")
    print(f"✅ 処理レポート: {report_file}")
    print("")

    report_lines.append("=" * 80)
    report_lines.append("処理完了")
    report_lines.append("=" * 80)
    report_lines.append(f"基本整形版: {output_cleaned}")
    report_lines.append(f"取引単位版: {output_grouped}")
    report_lines.append(f"処理時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # レポート出力
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print("🎉 すべての整形処理が完了しました")


if __name__ == "__main__":
    main()
