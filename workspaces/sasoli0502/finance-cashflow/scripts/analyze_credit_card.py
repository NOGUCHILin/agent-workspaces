#!/usr/bin/env python3
"""
クレジットカード経費の月次集計スクリプト

Usage:
    uv run python scripts/analyze_credit_card.py
"""

import polars as pl
from pathlib import Path
from datetime import datetime


def classify_service(description: str) -> str:
    """摘要からサービス名を分類"""
    if not description or description == "":
        return "その他"

    desc_upper = description.upper()

    # サービス分類ルール
    service_rules = {
        "Google": ["GOOGLE", "グーグル"],
        "Amazon": ["AMAZON", "アマゾン"],
        "Yahoo": ["ヤフー", "YAHOO"],
        "Obsidian": ["OBSIDIAN"],
        "OpenAI": ["OPENAI", "CHATGPT"],
        "Canva": ["CANVA"],
        "LINE": ["LINE"],
        "ドコモ": ["ドコモ"],
        "イオシス": ["イオシス"],
        "Apple": ["APPLE", "ITUNES"],
        "Adobe": ["ADOBE"],
        "Microsoft": ["MICROSOFT"],
        "Cursor": ["CURSOR"],
        "GitHub": ["GITHUB"],
        "お名前.com": ["お名前", "ONAMAE"],
        "ムームードメイン": ["ムームー", "MUUMUU"],
        "ドンキ": ["ドン・キホーテ", "DON QUIJOTE"],
    }

    for service_name, keywords in service_rules.items():
        for keyword in keywords:
            if keyword in desc_upper or keyword in description:
                return service_name

    return "その他"


def main():
    # パス設定
    project_root = Path(__file__).parent.parent
    source_file = project_root / "data" / "source" / "仕訳帳_20251029_1608.csv"
    output_file = project_root / "data" / f"credit_card_monthly_{datetime.now().strftime('%Y%m%d')}.csv"

    print(f"📂 読み込み: {source_file}")

    # CSVファイル読み込み（Shift-JIS、エラー無視）
    try:
        df = pl.read_csv(
            source_file,
            encoding="shift_jis",
            ignore_errors=True,
            null_values=["", "N/A"],
        )
    except Exception as e:
        print(f"❌ ファイル読み込みエラー: {e}")
        print("   CP932エンコーディングで再試行...")
        df = pl.read_csv(
            source_file,
            encoding="cp932",
            ignore_errors=True,
            null_values=["", "N/A"],
        )

    print(f"✅ 総行数: {len(df):,}行")

    # クレカ決済取引を抽出
    # 条件：貸方勘定科目が「未払金」かつ借方勘定科目が存在
    credit_card_df = df.filter(
        (pl.col("貸方勘定科目") == "未払金") &
        (pl.col("借方勘定科目").is_not_null()) &
        (pl.col("貸方補助科目").is_not_null())
    )

    print(f"💳 クレカ決済取引: {len(credit_card_df):,}件")

    # 取引日を日付型に変換
    credit_card_df = credit_card_df.with_columns([
        pl.col("取引日").str.strptime(pl.Date, format="%Y/%m/%d", strict=False).alias("取引日")
    ])

    # 年月を抽出
    credit_card_df = credit_card_df.with_columns([
        pl.col("取引日").dt.strftime("%Y-%m").alias("年月")
    ])

    # サービス名を分類
    credit_card_df = credit_card_df.with_columns([
        pl.col("摘要").map_elements(classify_service, return_dtype=pl.Utf8).alias("サービス名")
    ])

    # カード別の取引件数を表示
    print("\n📊 カード別取引件数:")
    card_counts = credit_card_df.group_by("貸方補助科目").agg(
        pl.len().alias("件数")
    ).sort("件数", descending=True)
    print(card_counts)

    # 月次集計（カード別×サービス別）
    monthly_pivot = credit_card_df.group_by(["年月", "サービス名", "借方勘定科目", "貸方補助科目"]).agg([
        pl.col("貸方金額(円)").sum().alias("金額"),
        pl.len().alias("件数")
    ])

    # ピボットテーブル化（カード別を列展開）
    cards = credit_card_df["貸方補助科目"].unique().sort().to_list()

    # 各カード別の金額を列として追加
    pivot_result = monthly_pivot.pivot(
        values="金額",
        index=["年月", "サービス名", "借方勘定科目"],
        on="貸方補助科目",
        aggregate_function="sum"
    )

    # 合計列を追加
    card_columns = [col for col in pivot_result.columns if col not in ["年月", "サービス名", "借方勘定科目"]]
    pivot_result = pivot_result.with_columns(
        pl.sum_horizontal(card_columns).alias("合計")
    )

    # 金額の降順でソート
    pivot_result = pivot_result.sort(["年月", "合計"], descending=[False, True])

    # null値を0に置換
    pivot_result = pivot_result.fill_null(0)

    # CSV出力（Polarsは常にUTF-8で出力）
    pivot_result.write_csv(output_file)

    print(f"\n✅ 出力完了: {output_file}")
    print(f"📈 集計行数: {len(pivot_result)}行")

    # サマリー表示
    print("\n📊 月別合計金額:")
    monthly_total = pivot_result.group_by("年月").agg(
        pl.col("合計").sum().alias("月次合計")
    ).sort("年月")
    print(monthly_total)

    print("\n📊 サービス別合計金額（Top 10）:")
    service_total = pivot_result.group_by("サービス名").agg(
        pl.col("合計").sum().alias("サービス別合計")
    ).sort("サービス別合計", descending=True).head(10)
    print(service_total)


if __name__ == "__main__":
    main()
