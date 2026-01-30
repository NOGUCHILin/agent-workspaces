#!/usr/bin/env python3
"""
日次資金繰り表の生成スクリプト

全銀行口座（現金・普通預金）の日々の入出金と残高推移を集計
"""

import polars as pl
from pathlib import Path
from datetime import datetime, timedelta


def main():
    # パス設定
    project_root = Path(__file__).parent.parent
    input_file = project_root / "data" / "processed" / "transactions_cleaned.csv"
    output_file = project_root / "data" / "reports" / f"cashflow_daily_{datetime.now().strftime('%Y%m%d')}.html"

    output_file.parent.mkdir(exist_ok=True)

    print("💰 日次資金繰り表を生成します\n")
    print(f"入力: {input_file}")
    print(f"出力: {output_file}\n")

    # データ読み込み
    df = pl.read_csv(input_file)

    # 取引日を日付型に変換
    df = df.with_columns([
        pl.col("取引日").str.strptime(pl.Date, format="%Y-%m-%d", strict=False).alias("取引日"),
    ])

    # 現金・普通預金の勘定科目
    cash_accounts = ["現金", "普通預金"]

    print("📊 入出金を集計中...")

    # 入金（借方が現金・普通預金）
    inflow_df = df.filter(
        pl.col("借方勘定科目").is_in(cash_accounts)
    ).group_by("取引日").agg([
        pl.col("借方金額(円)").sum().alias("入金")
    ])

    # 出金（貸方が現金・普通預金）
    outflow_df = df.filter(
        pl.col("貸方勘定科目").is_in(cash_accounts)
    ).group_by("取引日").agg([
        pl.col("貸方金額(円)").sum().alias("出金")
    ])

    # 入金と出金をマージ
    daily_df = inflow_df.join(outflow_df, on="取引日", how="outer").fill_null(0)

    # 日付順にソート
    daily_df = daily_df.sort("取引日")

    # 純増減を計算
    daily_df = daily_df.with_columns([
        (pl.col("入金") - pl.col("出金")).alias("純増減")
    ])

    # 累積残高を計算（期首残高は0と仮定）
    daily_df = daily_df.with_columns([
        pl.col("純増減").cum_sum().alias("残高")
    ])

    print(f"📅 対象期間: {daily_df['取引日'].min()} ～ {daily_df['取引日'].max()}")
    print(f"📈 総取引日数: {len(daily_df)}日\n")

    # 全日付を生成（取引がない日も含める）
    start_date = daily_df["取引日"].min()
    end_date = daily_df["取引日"].max()

    all_dates = pl.date_range(start_date, end_date, interval="1d", eager=True).alias("取引日")
    all_dates_df = pl.DataFrame({"取引日": all_dates})

    # 全日付とマージ（取引がない日は0埋め）
    daily_complete = all_dates_df.join(daily_df, on="取引日", how="left")

    # 取引がない日は入金・出金を0に
    daily_complete = daily_complete.with_columns([
        pl.col("入金").fill_null(0),
        pl.col("出金").fill_null(0),
        pl.col("純増減").fill_null(0)
    ])

    # 残高を前方埋め（取引がない日は前日の残高を引き継ぐ）
    daily_complete = daily_complete.with_columns([
        pl.col("残高").fill_null(strategy="forward")
    ])

    # 最初の残高がnullの場合は0に
    daily_complete = daily_complete.with_columns([
        pl.col("残高").fill_null(0)
    ])

    print("🎨 HTMLを生成中...")

    # HTML生成
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>日次資金繰り表 ({start_date} ～ {end_date})</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
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
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            opacity: 0.9;
        }}
        .summary-card .value {{
            font-size: 24px;
            font-weight: bold;
            margin: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 13px;
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
        th.date {{
            text-align: center;
        }}
        td {{
            padding: 8px;
            text-align: right;
            border-bottom: 1px solid #ecf0f1;
        }}
        td.date {{
            text-align: center;
            font-weight: 500;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .weekend {{
            background-color: #fff3cd;
        }}
        .positive {{
            color: #27ae60;
            font-weight: bold;
        }}
        .negative {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .zero {{
            color: #95a5a6;
        }}
        .balance-high {{
            background-color: #d4edda;
        }}
        .balance-low {{
            background-color: #f8d7da;
        }}
        .no-transaction {{
            opacity: 0.6;
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
        <h1>💰 日次資金繰り表</h1>
        <div class="meta">
            対象期間: {start_date} ～ {end_date} ({len(daily_complete)}日間) |
            作成日: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
        </div>

        <div class="summary">
            <div class="summary-card">
                <h3>期首残高</h3>
                <p class="value">{daily_complete['残高'][0]:,.0f}円</p>
            </div>
            <div class="summary-card">
                <h3>期末残高</h3>
                <p class="value">{daily_complete['残高'][-1]:,.0f}円</p>
            </div>
            <div class="summary-card">
                <h3>総入金額</h3>
                <p class="value">{daily_complete['入金'].sum():,.0f}円</p>
            </div>
            <div class="summary-card">
                <h3>総出金額</h3>
                <p class="value">{daily_complete['出金'].sum():,.0f}円</p>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th class="date">日付</th>
                    <th>曜日</th>
                    <th>前日残高</th>
                    <th>入金</th>
                    <th>出金</th>
                    <th>純増減</th>
                    <th>当日残高</th>
                </tr>
            </thead>
            <tbody>
"""

    # テーブル行を生成
    previous_balance = 0
    for i, row in enumerate(daily_complete.iter_rows(named=True)):
        date = row["取引日"]
        inflow = row["入金"]
        outflow = row["出金"]
        net_change = row["純増減"]
        balance = row["残高"]

        # 曜日を取得
        weekday_names = ["月", "火", "水", "木", "金", "土", "日"]
        weekday = weekday_names[date.weekday()]

        # 土日の行をハイライト
        row_class = "weekend" if date.weekday() >= 5 else ""

        # 取引がない日
        if inflow == 0 and outflow == 0:
            row_class += " no-transaction"

        # 残高の色分け
        balance_class = ""
        if balance < 0:
            balance_class = "balance-low"
        elif balance > 10000000:  # 1000万円以上
            balance_class = "balance-high"

        # 純増減の色
        net_class = "positive" if net_change > 0 else ("negative" if net_change < 0 else "zero")

        html_content += f'                <tr class="{row_class}">\n'
        html_content += f'                    <td class="date">{date}</td>\n'
        html_content += f'                    <td class="date">{weekday}</td>\n'
        html_content += f'                    <td>{previous_balance:,}</td>\n'
        html_content += f'                    <td class="{"positive" if inflow > 0 else "zero"}">{inflow:,}</td>\n'
        html_content += f'                    <td class="{"negative" if outflow > 0 else "zero"}">{outflow:,}</td>\n'
        html_content += f'                    <td class="{net_class}">{net_change:+,}</td>\n'
        html_content += f'                    <td class="{balance_class}"><strong>{balance:,}</strong></td>\n'
        html_content += '                </tr>\n'

        previous_balance = balance

    html_content += """            </tbody>
        </table>

        <div class="footer">
            Generated by finance-cashflow system<br>
            ⚠️ 期首残高は取引データから計算しています。実際の残高と異なる場合があります。
        </div>
    </div>
</body>
</html>
"""

    # HTML出力
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ 日次資金繰り表を生成しました: {output_file}")
    print(f"\n📊 サマリー:")
    print(f"   期首残高: {daily_complete['残高'][0]:,}円")
    print(f"   期末残高: {daily_complete['残高'][-1]:,}円")
    print(f"   総入金額: {daily_complete['入金'].sum():,}円")
    print(f"   総出金額: {daily_complete['出金'].sum():,}円")
    print(f"   純増減: {daily_complete['残高'][-1] - daily_complete['残高'][0]:+,}円")


if __name__ == "__main__":
    main()
