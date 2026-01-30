#!/usr/bin/env python3
"""
クレジットカード明細HTML生成スクリプト

Usage:
    uv run python scripts/generate_credit_card_statement.py
"""

import polars as pl
from pathlib import Path
from datetime import datetime


def classify_expense(account: str) -> str:
    """勘定科目から経費/非経費を分類"""
    if not account:
        return "未分類"

    # 経費として認められる勘定科目
    expense_accounts = [
        "通信費", "広告宣伝費", "支払手数料", "仕入高", "備品・消耗品費",
        "旅費交通費", "水道光熱費", "接待交際費", "会議費", "諸会費",
        "保険料", "支払利息", "消耗品費", "荷造運賃", "修繕費",
        "地代家賃", "給料手当", "福利厚生費", "租税公課", "減価償却費"
    ]

    # 非経費（精算待ち、借入金返済等）
    non_expense_accounts = [
        "仮払金", "役員借入金", "短期借入金", "長期借入金", "事業主貸"
    ]

    # 経費判定
    for exp in expense_accounts:
        if exp in account:
            return "経費"

    # 非経費判定
    for non_exp in non_expense_accounts:
        if non_exp in account:
            return "非経費"

    return "未分類"


def main():
    # パス設定
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    source_csv = data_dir / "credit_card_transactions.csv"
    output_dir = data_dir / "reports"
    output_dir.mkdir(exist_ok=True)

    # CSVを読み込み
    if not source_csv.exists():
        print(f"❌ エラー: {source_csv} が見つかりません")
        return

    print(f"📂 {source_csv} を読み込んでいます...")
    df = pl.read_csv(source_csv)

    # 必要なカラムのみ抽出し、欠損値を処理
    df = df.select([
        pl.col("取引日"),
        pl.col("貸方補助科目").alias("カード名"),
        pl.col("借方勘定科目").alias("勘定科目"),
        pl.col("摘要").alias("サービス名"),
        pl.col("借方金額(円)").alias("金額")
    ]).filter(
        pl.col("カード名").is_not_null() &
        pl.col("金額").is_not_null() &
        (pl.col("金額") > 0)  # 金額が0より大きいもののみ
    )

    # 分類列を追加
    df = df.with_columns(
        pl.col("勘定科目").map_elements(classify_expense, return_dtype=pl.Utf8).alias("分類")
    )

    # 日付でソート
    df = df.sort("取引日", descending=True)

    # カード別の合計を計算
    card_totals = df.group_by("カード名").agg(
        pl.col("金額").sum().alias("合計"),
        pl.len().alias("件数")
    ).sort("合計", descending=True)

    # 分類別の集計
    category_totals = df.group_by("分類").agg(
        pl.col("金額").sum().alias("合計"),
        pl.len().alias("件数")
    ).sort("合計", descending=True)

    # 総合計
    total_amount = df["金額"].sum()
    total_count = len(df)

    # 日付範囲
    min_date = df["取引日"].min()
    max_date = df["取引日"].max()

    print(f"✅ {total_count:,}件の取引を読み込みました")
    print(f"📅 対象期間: {min_date} ～ {max_date}")

    # 分類別の内訳を表示
    print(f"\n📊 分類別集計:")
    for row in category_totals.iter_rows(named=True):
        print(f"  {row['分類']}: {row['合計']:,.0f}円 ({row['件数']}件)")

    # HTML生成
    today = datetime.now().strftime("%Y%m%d")
    output_file = output_dir / f"credit_card_statement_{today}.html"

    html = generate_html(df, card_totals, category_totals, total_amount, total_count, min_date, max_date)

    output_file.write_text(html, encoding="utf-8")
    print(f"✅ HTML生成完了: {output_file}")
    print(f"💰 総支払額: {total_amount:,.0f}円 ({total_count:,}件)")


def generate_html(df, card_totals, category_totals, total_amount, total_count, min_date, max_date):
    """HTMLを生成"""

    # 分類別のテーブル行を生成
    category_summary_rows = []
    for row in category_totals.iter_rows(named=True):
        category_class = "expense" if row["分類"] == "経費" else "non-expense" if row["分類"] == "非経費" else "unclassified"
        category_summary_rows.append(
            f'<tr class="{category_class}">'
            f'<td>{row["分類"]}</td>'
            f'<td class="number">{row["件数"]:,}件</td>'
            f'<td class="number amount">{row["合計"]:,.0f}円</td>'
            f'</tr>'
        )

    # カード別のテーブル行を生成
    card_summary_rows = []
    for row in card_totals.iter_rows(named=True):
        card_summary_rows.append(
            f'<tr>'
            f'<td>{row["カード名"]}</td>'
            f'<td class="number">{row["件数"]:,}件</td>'
            f'<td class="number amount">{row["合計"]:,.0f}円</td>'
            f'</tr>'
        )

    # 明細テーブル行を生成
    detail_rows = []
    for row in df.iter_rows(named=True):
        category_class = "expense" if row["分類"] == "経費" else "non-expense" if row["分類"] == "非経費" else "unclassified"
        detail_rows.append(
            f'<tr class="{category_class}">'
            f'<td class="date">{row["取引日"]}</td>'
            f'<td class="card">{row["カード名"]}</td>'
            f'<td class="category">{row["分類"]}</td>'
            f'<td class="account">{row["勘定科目"] or "-"}</td>'
            f'<td class="service">{row["サービス名"] or "-"}</td>'
            f'<td class="number amount">{row["金額"]:,.0f}円</td>'
            f'</tr>'
        )

    # HTML構築
    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>クレジットカード明細 ({min_date} ～ {max_date})</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 100%;
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
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 8px;
            margin-top: 30px;
        }}
        .meta {{
            color: #7f8c8d;
            margin-bottom: 20px;
        }}
        .summary {{
            background-color: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary strong {{
            color: #2e7d32;
            font-size: 1.2em;
        }}
        .search-box {{
            margin: 20px 0;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }}
        .search-box input {{
            width: 300px;
            padding: 8px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            font-size: 14px;
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
            text-align: left;
            font-weight: bold;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        td {{
            padding: 10px 8px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .date {{
            text-align: center;
            font-weight: 500;
            white-space: nowrap;
        }}
        .card {{
            font-weight: 600;
            color: #2c3e50;
        }}
        .service {{
            color: #555;
        }}
        .number {{
            text-align: right;
            white-space: nowrap;
        }}
        .amount {{
            font-weight: 600;
            color: #e74c3c;
        }}
        .total {{
            background-color: #d5e8f7;
            font-weight: bold;
        }}
        .expense {{
            background-color: #e8f5e9;
        }}
        .non-expense {{
            background-color: #fff3cd;
        }}
        .unclassified {{
            background-color: #f8d7da;
        }}
        .category {{
            font-weight: 600;
            text-align: center;
        }}
        .account {{
            color: #666;
            font-size: 0.9em;
        }}
        .filter-buttons {{
            margin: 20px 0;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }}
        .filter-buttons button {{
            padding: 8px 16px;
            margin-right: 10px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            background-color: white;
            cursor: pointer;
            font-size: 14px;
        }}
        .filter-buttons button:hover {{
            background-color: #e9ecef;
        }}
        .filter-buttons button.active {{
            background-color: #007bff;
            color: white;
            border-color: #007bff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>💳 クレジットカード明細</h1>
        <div class="meta">
            対象期間: {min_date} ～ {max_date} |
            作成日: {datetime.now().strftime("%Y年%m月%d日 %H:%M")}
        </div>

        <div class="summary">
            <strong>総支払額: {total_amount:,.0f}円</strong> ({total_count:,}件の取引)
        </div>

        <h2>📊 分類別集計</h2>
        <table>
            <thead>
                <tr>
                    <th>分類</th>
                    <th>取引件数</th>
                    <th>合計金額</th>
                </tr>
            </thead>
            <tbody>
                {''.join(category_summary_rows)}
                <tr class="total">
                    <td>合計</td>
                    <td class="number">{total_count:,}件</td>
                    <td class="number amount">{total_amount:,.0f}円</td>
                </tr>
            </tbody>
        </table>

        <h2>💳 カード別集計</h2>
        <table>
            <thead>
                <tr>
                    <th>カード名</th>
                    <th>取引件数</th>
                    <th>合計金額</th>
                </tr>
            </thead>
            <tbody>
                {''.join(card_summary_rows)}
                <tr class="total">
                    <td>合計</td>
                    <td class="number">{total_count:,}件</td>
                    <td class="number amount">{total_amount:,.0f}円</td>
                </tr>
            </tbody>
        </table>

        <h2>📋 明細一覧</h2>

        <div class="filter-buttons">
            <button onclick="filterByCategory('all')" class="active" id="btn-all">すべて</button>
            <button onclick="filterByCategory('expense')" id="btn-expense">経費のみ</button>
            <button onclick="filterByCategory('non-expense')" id="btn-non-expense">非経費のみ</button>
            <button onclick="filterByCategory('unclassified')" id="btn-unclassified">未分類のみ</button>
        </div>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="検索（カード名、サービス名、勘定科目で絞り込み）" onkeyup="filterTable()">
        </div>

        <table id="detailTable">
            <thead>
                <tr>
                    <th class="date">取引日</th>
                    <th>カード名</th>
                    <th class="category">分類</th>
                    <th>勘定科目</th>
                    <th>サービス名</th>
                    <th class="number">金額</th>
                </tr>
            </thead>
            <tbody>
                {''.join(detail_rows)}
            </tbody>
        </table>
    </div>

    <script>
        let currentCategoryFilter = 'all';

        function filterByCategory(category) {{
            currentCategoryFilter = category;

            // ボタンのアクティブ状態を更新
            const buttons = document.querySelectorAll('.filter-buttons button');
            buttons.forEach(btn => btn.classList.remove('active'));
            document.getElementById('btn-' + category).classList.add('active');

            filterTable();
        }}

        function filterTable() {{
            const input = document.getElementById('searchInput');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('detailTable');
            const tr = table.getElementsByTagName('tr');

            for (let i = 1; i < tr.length; i++) {{
                const row = tr[i];
                const tdCard = row.getElementsByClassName('card')[0];
                const tdCategory = row.getElementsByClassName('category')[0];
                const tdAccount = row.getElementsByClassName('account')[0];
                const tdService = row.getElementsByClassName('service')[0];

                // 分類フィルター
                let categoryMatch = true;
                if (currentCategoryFilter !== 'all') {{
                    categoryMatch = row.classList.contains(currentCategoryFilter);
                }}

                // テキスト検索フィルター
                let textMatch = true;
                if (filter) {{
                    const cardText = tdCard ? tdCard.textContent || tdCard.innerText : '';
                    const accountText = tdAccount ? tdAccount.textContent || tdAccount.innerText : '';
                    const serviceText = tdService ? tdService.textContent || tdService.innerText : '';

                    textMatch = cardText.toUpperCase().indexOf(filter) > -1 ||
                                accountText.toUpperCase().indexOf(filter) > -1 ||
                                serviceText.toUpperCase().indexOf(filter) > -1;
                }}

                // 両方の条件を満たす場合のみ表示
                if (categoryMatch && textMatch) {{
                    row.style.display = '';
                }} else {{
                    row.style.display = 'none';
                }}
            }}
        }}
    </script>
</body>
</html>'''

    return html


if __name__ == "__main__":
    main()
