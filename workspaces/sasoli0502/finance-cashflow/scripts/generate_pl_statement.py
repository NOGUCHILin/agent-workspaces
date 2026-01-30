#!/usr/bin/env python3
"""
月次損益計算書（P/L）の生成スクリプト

整形済みデータから収益・費用を集計してHTML形式で出力
"""

import polars as pl
from pathlib import Path
from datetime import datetime


def main():
    # パス設定
    project_root = Path(__file__).parent.parent
    input_file = project_root / "data" / "processed" / "transactions_cleaned.csv"
    output_file = project_root / "data" / "reports" / f"pl_statement_{datetime.now().strftime('%Y%m%d')}.html"

    output_file.parent.mkdir(exist_ok=True)

    print("📊 月次損益計算書を生成します\n")
    print(f"入力: {input_file}")
    print(f"出力: {output_file}\n")

    # データ読み込み
    df = pl.read_csv(input_file)

    # 取引日から年月を抽出
    df = df.with_columns([
        pl.col("取引日").str.strptime(pl.Date, format="%Y-%m-%d", strict=False).alias("取引日"),
    ])

    df = df.with_columns([
        pl.col("取引日").dt.strftime("%Y-%m").alias("年月")
    ])

    print("📈 収益科目を集計中...")

    # 収益科目（貸方）の集計
    revenue_accounts = ["売上高", "受取利息", "雑収入"]

    revenue_df = df.filter(
        pl.col("貸方勘定科目").is_in(revenue_accounts)
    ).group_by(["年月", "貸方勘定科目"]).agg([
        pl.col("貸方金額(円)").sum().alias("金額")
    ])

    # 費用科目（借方）の集計
    print("📉 費用科目を集計中...")

    expense_accounts = [
        "仕入高", "支払手数料", "通信費", "広告宣伝費", "備品・消耗品費",
        "旅費交通費", "接待交際費", "会議費", "給料", "法定福利費",
        "支払利息", "水道光熱費", "地代家賃", "支払報酬", "仮払金",
        "支払家賃", "消耗品費", "役員報酬", "外注費"
    ]

    expense_df = df.filter(
        pl.col("借方勘定科目").is_in(expense_accounts)
    ).group_by(["年月", "借方勘定科目"]).agg([
        pl.col("借方金額(円)").sum().alias("金額")
    ])

    # 月のリストを取得
    months = sorted(df["年月"].unique().to_list())

    print(f"📅 対象期間: {months[0]} ～ {months[-1]}\n")

    # 収益データをピボット化
    revenue_pivot = revenue_df.pivot(
        values="金額",
        index="貸方勘定科目",
        on="年月",
        aggregate_function="sum"
    ).fill_null(0)

    # 費用データをピボット化
    expense_pivot = expense_df.pivot(
        values="金額",
        index="借方勘定科目",
        on="年月",
        aggregate_function="sum"
    ).fill_null(0)

    # HTML生成
    print("🎨 HTMLを生成中...")

    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>月次損益計算書 ({months[0]} ～ {months[-1]})</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .meta {{
            color: #7f8c8d;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }}
        th {{
            background-color: #34495e;
            color: white;
            padding: 12px 8px;
            text-align: right;
            font-weight: bold;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        th.account {{
            text-align: left;
            min-width: 150px;
        }}
        td {{
            padding: 10px 8px;
            text-align: right;
            border-bottom: 1px solid #ecf0f1;
        }}
        td.account {{
            text-align: left;
            font-weight: 500;
        }}
        .revenue-section {{
            background-color: #e8f5e9;
        }}
        .expense-section {{
            background-color: #ffebee;
        }}
        .section-header {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
            text-align: left !important;
        }}
        .subtotal {{
            background-color: #ecf0f1;
            font-weight: bold;
        }}
        .total {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
            font-size: 16px;
        }}
        .profit {{
            background-color: #27ae60;
            color: white;
            font-weight: bold;
            font-size: 16px;
        }}
        .loss {{
            background-color: #e74c3c;
            color: white;
            font-weight: bold;
            font-size: 16px;
        }}
        .positive {{
            color: #27ae60;
        }}
        .negative {{
            color: #e74c3c;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 月次損益計算書</h1>
        <div class="meta">
            対象期間: {months[0]} ～ {months[-1]} |
            作成日: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
        </div>

        <table>
            <thead>
                <tr>
                    <th class="account">勘定科目</th>
"""

    # 月のヘッダー
    for month in months:
        html_content += f"                    <th>{month}</th>\n"

    html_content += "                    <th>合計</th>\n"
    html_content += "                </tr>\n"
    html_content += "            </thead>\n"
    html_content += "            <tbody>\n"

    # === 収益の部 ===
    html_content += '                <tr class="section-header">\n'
    html_content += '                    <td colspan="100">【収益の部】</td>\n'
    html_content += '                </tr>\n'

    revenue_total_by_month = {}
    for month in months:
        revenue_total_by_month[month] = 0

    # 収益科目の行を追加
    if len(revenue_pivot) > 0:
        for row in revenue_pivot.iter_rows(named=True):
            account = row.get("貸方勘定科目", "")
            html_content += '                <tr class="revenue-section">\n'
            html_content += f'                    <td class="account">{account}</td>\n'

            row_total = 0
            for month in months:
                amount = row.get(month, 0)
                revenue_total_by_month[month] += amount
                row_total += amount
                html_content += f'                    <td>{amount:,}</td>\n'

            html_content += f'                    <td><strong>{row_total:,}</strong></td>\n'
            html_content += '                </tr>\n'

    # 収益合計
    html_content += '                <tr class="subtotal">\n'
    html_content += '                    <td class="account">売上合計</td>\n'

    revenue_grand_total = 0
    for month in months:
        total = revenue_total_by_month.get(month, 0)
        revenue_grand_total += total
        html_content += f'                    <td>{total:,}</td>\n'

    html_content += f'                    <td>{revenue_grand_total:,}</td>\n'
    html_content += '                </tr>\n'

    # === 費用の部 ===
    html_content += '                <tr class="section-header">\n'
    html_content += '                    <td colspan="100">【費用の部】</td>\n'
    html_content += '                </tr>\n'

    expense_total_by_month = {}
    for month in months:
        expense_total_by_month[month] = 0

    # 費用科目の行を追加
    if len(expense_pivot) > 0:
        for row in expense_pivot.iter_rows(named=True):
            account = row.get("借方勘定科目", "")
            html_content += '                <tr class="expense-section">\n'
            html_content += f'                    <td class="account">{account}</td>\n'

            row_total = 0
            for month in months:
                amount = row.get(month, 0)
                expense_total_by_month[month] += amount
                row_total += amount
                html_content += f'                    <td>{amount:,}</td>\n'

            html_content += f'                    <td><strong>{row_total:,}</strong></td>\n'
            html_content += '                </tr>\n'

    # 費用合計
    html_content += '                <tr class="subtotal">\n'
    html_content += '                    <td class="account">費用合計</td>\n'

    expense_grand_total = 0
    for month in months:
        total = expense_total_by_month.get(month, 0)
        expense_grand_total += total
        html_content += f'                    <td>{total:,}</td>\n'

    html_content += f'                    <td>{expense_grand_total:,}</td>\n'
    html_content += '                </tr>\n'

    # === 営業利益 ===
    profit_grand_total = revenue_grand_total - expense_grand_total
    profit_class = "profit" if profit_grand_total >= 0 else "loss"

    html_content += f'                <tr class="{profit_class}">\n'
    html_content += '                    <td class="account">営業利益</td>\n'

    for month in months:
        revenue = revenue_total_by_month.get(month, 0)
        expense = expense_total_by_month.get(month, 0)
        profit = revenue - expense
        profit_class = "positive" if profit >= 0 else "negative"
        html_content += f'                    <td class="{profit_class}">{profit:,}</td>\n'

    profit_color_class = "positive" if profit_grand_total >= 0 else "negative"
    html_content += f'                    <td class="{profit_color_class}">{profit_grand_total:,}</td>\n'
    html_content += '                </tr>\n'

    html_content += """            </tbody>
        </table>

        <div class="footer">
            Generated by finance-cashflow system
        </div>
    </div>
</body>
</html>
"""

    # HTML出力
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ 損益計算書を生成しました: {output_file}")
    print(f"\n📊 サマリー:")
    print(f"   売上合計: {revenue_grand_total:,}円")
    print(f"   費用合計: {expense_grand_total:,}円")
    print(f"   営業利益: {profit_grand_total:,}円")

    if profit_grand_total >= 0:
        print("   ✅ 黒字")
    else:
        print("   ⚠️  赤字")


if __name__ == "__main__":
    main()
