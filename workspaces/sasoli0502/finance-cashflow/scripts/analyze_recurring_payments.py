#!/usr/bin/env python3
"""
定期支払い（サブスクリプション）の分析スクリプト

毎月継続して支払いがあるサービスを抽出し、金額の推移を確認
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
    output_file = project_root / "data" / f"recurring_payments_{datetime.now().strftime('%Y%m%d')}.csv"

    print(f"📂 読み込み: {source_file}")

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

    print(f"✅ 総行数: {len(df):,}行")

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

    # サービス名を分類
    credit_card_df = credit_card_df.with_columns([
        pl.col("摘要").map_elements(classify_service, return_dtype=pl.Utf8).alias("サービス名")
    ])

    # サービス×摘要の詳細レベルで月次出現回数をカウント
    service_monthly = credit_card_df.group_by(["サービス名", "摘要", "借方勘定科目"]).agg([
        pl.col("年月").n_unique().alias("出現月数"),
        pl.col("貸方金額(円)").mean().alias("平均金額"),
        pl.col("貸方金額(円)").std().alias("金額標準偏差"),
        pl.col("貸方金額(円)").min().alias("最小金額"),
        pl.col("貸方金額(円)").max().alias("最大金額"),
    ])

    # 定期支払いの条件：5ヶ月以上出現（7ヶ月中）
    recurring = service_monthly.filter(
        pl.col("出現月数") >= 5
    ).sort("出現月数", descending=True)

    print(f"\n📊 定期支払いサービス（5ヶ月以上継続）: {len(recurring)}件\n")

    # 金額の変動が小さいものを上位表示（標準偏差が小さい順）
    recurring = recurring.with_columns([
        (pl.col("金額標準偏差") / pl.col("平均金額")).fill_null(0).alias("変動係数")
    ])

    # 結果を表示
    print(recurring.select([
        "サービス名",
        "摘要",
        "借方勘定科目",
        "出現月数",
        "平均金額",
        "金額標準偏差",
        "変動係数"
    ]).head(30))

    # 詳細な月次推移を確認（ピボットテーブル）
    print("\n\n📊 主要な定期支払いの月次推移:")

    # トップ20の定期支払いについて月次推移を作成
    top_recurring = recurring.head(20)

    for row in top_recurring.iter_rows(named=True):
        service_name = row["サービス名"]
        description = row["摘要"]

        # 該当取引の月次データを抽出
        monthly_data = credit_card_df.filter(
            (pl.col("サービス名") == service_name) &
            (pl.col("摘要") == description)
        ).group_by("年月").agg([
            pl.col("貸方金額(円)").sum().alias("金額"),
            pl.len().alias("件数")
        ]).sort("年月")

        if len(monthly_data) > 0:
            print(f"\n【{service_name}】{description[:50]}")
            print(f"  平均: {row['平均金額']:,.0f}円 | 変動係数: {row['変動係数']:.2%}")
            print(monthly_data)

    # CSV出力
    recurring.write_csv(output_file)
    print(f"\n\n✅ 定期支払い一覧を出力: {output_file}")


if __name__ == "__main__":
    main()
