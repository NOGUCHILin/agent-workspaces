#!/usr/bin/env python3
"""
資金繰り予測スクリプト

過去の入出金パターンから今後の資金繰りを予測します。

入力: data/processed/transactions_cleaned.csv
出力: data/reports/forecast_YYYYMMDD.html
"""

import polars as pl
from pathlib import Path
from datetime import datetime, timedelta

def main():
    # パス設定
    project_root = Path(__file__).parent.parent
    input_file = project_root / "data" / "processed" / "transactions_cleaned.csv"
    output_file = project_root / "data" / "reports" / f"forecast_{datetime.now().strftime('%Y%m%d')}.html"

    output_file.parent.mkdir(exist_ok=True)

    print("📊 資金繰り予測を開始します\n")
    print(f"入力: {input_file}")
    print(f"出力: {output_file}\n")

    if not input_file.exists():
        print("❌ エラー: transactions_cleaned.csv が見つかりません")
        print("先に /cash-analyze を実行してデータをクリーニングしてください")
        return

    # データ読み込み
    df = pl.read_csv(input_file)

    # 取引日を日付型に変換
    df = df.with_columns([
        pl.col("取引日").str.strptime(pl.Date, format="%Y-%m-%d", strict=False).alias("取引日"),
    ])

    # 最新日付を取得
    latest_date = df["取引日"].max()
    print(f"最新データ: {latest_date}")

    # 過去3ヶ月のデータを抽出
    three_months_ago = latest_date - timedelta(days=90)
    recent_df = df.filter(pl.col("取引日") >= three_months_ago)

    print(f"分析期間: {three_months_ago} ～ {latest_date}")
    print(f"分析対象: {len(recent_df)}件\n")

    # 主要項目の月平均を算出
    print("📈 主要項目の月平均を算出中...")

    # 収入項目
    revenue_items = {
        "バックマーケット売上": ("バックマーケット", "売掛金", "貸方"),
        "店舗売上": ("スマレジ", "売掛金", "貸方"),
        "その他売上": (None, "売上高", "貸方"),
    }

    # 支出項目
    expense_items = {
        "Google広告": ("GOOGLE", "仮払金", "借方"),
        "Yahoo広告": ("YAHOO", "仮払金", "借方"),
        "仕入": (None, "仕入高", "借方"),
        "給料": (None, "給料", "借方"),
        "役員報酬": (None, "役員報酬", "借方"),
    }

    # 月平均を計算
    monthly_avg = {}

    # 収入の月平均
    for item_name, (keyword, account, side) in revenue_items.items():
        if side == "貸方":
            filtered = recent_df.filter(
                (pl.col("貸方勘定科目") == account) |
                (pl.col("貸方勘定科目") == "売掛金")
            )
            if keyword:
                filtered = filtered.filter(pl.col("貸方補助科目").str.contains(keyword))

            total = filtered["借方金額(円)"].sum()  # 入金は借方
            monthly_avg[item_name] = total / 3

    # 支出の月平均
    for item_name, (keyword, account, side) in expense_items.items():
        if side == "借方":
            filtered = recent_df.filter(pl.col("借方勘定科目") == account)
            if keyword:
                filtered = filtered.filter(pl.col("摘要").str.to_uppercase().str.contains(keyword))

            total = filtered["貸方金額(円)"].sum()  # 出金は貸方
            monthly_avg[item_name] = -total / 3  # マイナス表記

    # 現在残高を取得（最新日の累積）
    cash_df = recent_df.filter(
        pl.col("借方勘定科目").is_in(["現金", "普通預金"]) |
        pl.col("貸方勘定科目").is_in(["現金", "普通預金"])
    )

    # 簡易的な残高計算
    inflow = cash_df.filter(pl.col("借方勘定科目").is_in(["現金", "普通預金"]))["借方金額(円)"].sum()
    outflow = cash_df.filter(pl.col("貸方勘定科目").is_in(["現金", "普通預金"]))["貸方金額(円)"].sum()
    current_balance = inflow - outflow

    print(f"現在残高（推定）: {current_balance:,.0f}円")
    print(f"月平均収入: {sum([v for v in monthly_avg.values() if v > 0]):,.0f}円")
    print(f"月平均支出: {sum([v for v in monthly_avg.values() if v < 0]):,.0f}円\n")

    # 今後30日間の予測
    print("🔮 今後30日間を予測中...")

    forecast_days = 30
    forecast_start = latest_date + timedelta(days=1)
    forecast_dates = [forecast_start + timedelta(days=i) for i in range(forecast_days)]

    # 日平均を算出（月平均÷30）
    daily_avg = {k: v / 30 for k, v in monthly_avg.items()}

    # HTML生成
    print("🎨 HTMLレポートを生成中...")

    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>資金繰り予測 ({forecast_start} ～ {forecast_dates[-1]})</title>
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
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
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
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary h2 {{
            margin-top: 0;
            color: #34495e;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: right;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #34495e;
            color: white;
            font-weight: bold;
        }}
        th.item {{ text-align: left; }}
        td.item {{ text-align: left; font-weight: 500; }}
        .positive {{ color: #27ae60; font-weight: bold; }}
        .negative {{ color: #e74c3c; font-weight: bold; }}
        .warning {{
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .alert {{
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 資金繰り予測</h1>
        <div class="meta">
            予測期間: {forecast_start} ～ {forecast_dates[-1]} (30日間) |
            基準データ: 過去90日間 |
            作成日: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
        </div>

        <div class="summary">
            <h2>現状サマリー</h2>
            <p><strong>現在残高（推定）:</strong> {current_balance:,.0f}円</p>
            <p><strong>月平均収入:</strong> <span class="positive">{sum([v for v in monthly_avg.values() if v > 0]):,.0f}円</span></p>
            <p><strong>月平均支出:</strong> <span class="negative">{sum([v for v in monthly_avg.values() if v < 0]):,.0f}円</span></p>
            <p><strong>月平均純増減:</strong> <span class="{'positive' if sum(monthly_avg.values()) > 0 else 'negative'}">{sum(monthly_avg.values()):+,.0f}円</span></p>
        </div>
"""

    # 予測残高が危険水準を下回るか確認
    predicted_balance = current_balance + sum(daily_avg.values()) * 30
    if predicted_balance < 5000000:  # 500万円以下
        html_content += f"""
        <div class="alert">
            <strong>⚠️ 資金ショートリスク</strong><br>
            30日後の予測残高: {predicted_balance:,.0f}円<br>
            安全水準（500万円）を下回る可能性があります。資金調達を検討してください。
        </div>
"""
    elif predicted_balance < 10000000:  # 1000万円以下
        html_content += f"""
        <div class="warning">
            <strong>⚠️ 注意</strong><br>
            30日後の予測残高: {predicted_balance:,.0f}円<br>
            残高が減少傾向です。資金繰りに注意してください。
        </div>
"""

    html_content += """
        <h2>主要項目の月平均</h2>
        <table>
            <thead>
                <tr>
                    <th class="item">項目</th>
                    <th>月平均</th>
                    <th>日平均</th>
                </tr>
            </thead>
            <tbody>
"""

    for item, monthly in sorted(monthly_avg.items(), key=lambda x: -abs(x[1])):
        daily = monthly / 30
        css_class = "positive" if monthly > 0 else "negative"
        html_content += f"""
                <tr>
                    <td class="item">{item}</td>
                    <td class="{css_class}">{monthly:,.0f}円</td>
                    <td class="{css_class}">{daily:,.0f}円</td>
                </tr>
"""

    html_content += f"""
            </tbody>
        </table>

        <div class="summary">
            <h2>30日後の予測</h2>
            <p><strong>予測残高:</strong> <span class="{'positive' if predicted_balance > current_balance else 'negative'}">{predicted_balance:,.0f}円</span></p>
            <p><strong>増減:</strong> <span class="{'positive' if predicted_balance > current_balance else 'negative'}">{predicted_balance - current_balance:+,.0f}円</span></p>
        </div>

        <div class="meta">
            <p><strong>注意事項:</strong></p>
            <ul>
                <li>この予測は過去90日間のデータに基づく単純な平均値です</li>
                <li>季節変動や一時的な大口支払いは考慮されていません</li>
                <li>実際の資金繰りは、社内資金繰り表で毎日確認してください</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

    # HTML出力
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ 予測レポートを生成しました: {output_file}")
    print(f"\n📊 予測サマリー:")
    print(f"   現在残高: {current_balance:,.0f}円")
    print(f"   30日後予測: {predicted_balance:,.0f}円")
    print(f"   増減: {predicted_balance - current_balance:+,.0f}円")

if __name__ == "__main__":
    main()
