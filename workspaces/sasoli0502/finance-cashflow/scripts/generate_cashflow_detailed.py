#!/usr/bin/env python3
"""
詳細版日次資金繰り表の生成スクリプト（28列構成）

売上・経費・仕入を細かく分類して日々の動きを可視化
"""

import polars as pl
from pathlib import Path
from datetime import datetime


def classify_transaction(row):
    """
    取引を28列の適切な列に振り分ける

    Returns: (result dict, is_credit_card bool)
        result: dict of column_name -> amount
        is_credit_card: クレカ決済かどうか（出金のみ、入金はFalse）
    """
    result = {col: 0 for col in [
        "バックマーケット売上", "店舗売上", "エフワイエル売上", "その他EC売上", "その他売上",
        "Google広告", "Yahoo広告", "LINE広告",
        "ホンダ自動車", "ゴールデンブル", "エフワイエル仕入", "ヤフーフリマ", "その他仕入",
        "給料", "役員報酬",
        "AWS", "Google Workspace", "OpenAI", "Claude", "Notion", "ドコモ", "その他通信費",
        "支払手数料", "その他経費"
    ]}

    is_credit_card = False

    # 入金（借方が現金・普通預金）
    if row["借方勘定科目"] in ["現金", "普通預金"]:
        amount = row["借方金額(円)"]
        sub = str(row["貸方補助科目"]) if row["貸方補助科目"] else ""

        # 売上高・売掛金（どちらも販売先で分類）
        if row["貸方勘定科目"] in ["売上高", "売掛金"]:
            if "バックマーケット" in sub:
                result["バックマーケット売上"] = amount
            elif "スマレジ" in sub or "店舗" in sub:
                result["店舗売上"] = amount
            elif "エフワイエル" in sub:
                result["エフワイエル売上"] = amount
            elif "ムスビー" in sub or "アマゾン" in sub:
                result["その他EC売上"] = amount
            else:
                result["その他売上"] = amount

    # 出金（貸方が現金・普通預金）
    elif row["貸方勘定科目"] in ["現金", "普通預金"]:
        amount = -row["貸方金額(円)"]  # マイナス表記

        desc = str(row["摘要"]).upper() if row["摘要"] else ""
        sub = str(row["借方補助科目"]) if row["借方補助科目"] else ""
        account = row["借方勘定科目"]

        # クレカ決済の判定（借方が未払金の場合）
        is_credit_card = (account == "未払金")

        # 広告費
        if "GOOGLE" in desc and (account == "仮払金" or account == "広告宣伝費" or account == "未払金"):
            result["Google広告"] = amount
        elif ("YAHOO" in desc or "ヤフー" in desc) and (account == "仮払金" or account == "広告宣伝費" or account == "支払手数料" or account == "未払金"):
            result["Yahoo広告"] = amount
        elif "LINE" in desc and (account == "広告宣伝費" or account == "未払金"):
            result["LINE広告"] = amount

        # 仕入
        elif account == "仕入高" or (account == "未払金" and ("ホンダ" in desc or "ゴールデンブル" in desc or "エフワイエル" in desc or "ヤフー" in desc or "YAHOO" in desc)):
            if "ホンダ" in desc or "ホンダ" in sub:
                result["ホンダ自動車"] = amount
            elif "ゴールデンブル" in desc:
                result["ゴールデンブル"] = amount
            elif "エフワイエル" in desc or "エフワイエル" in sub:
                result["エフワイエル仕入"] = amount
            elif "ヤフー" in desc or "YAHOO" in desc:
                result["ヤフーフリマ"] = amount
            else:
                result["その他仕入"] = amount

        # 人件費
        elif account == "給料":
            result["給料"] = amount
        elif account == "役員報酬":
            result["役員報酬"] = amount

        # IT・通信費
        elif account == "通信費" or (account == "未払金" and ("AWS" in desc or "AMAZON WEB" in desc or "GSUITE" in desc or "WORKSPACE" in desc or "OPENAI" in desc or "CLAUDE" in desc or "NOTION" in desc or "ドコモ" in desc)):
            if "AWS" in desc or "AMAZON WEB" in desc:
                result["AWS"] = amount
            elif "GSUITE" in desc or "WORKSPACE" in desc:
                result["Google Workspace"] = amount
            elif "OPENAI" in desc or "CHATGPT" in desc:
                result["OpenAI"] = amount
            elif "CLAUDE" in desc:
                result["Claude"] = amount
            elif "NOTION" in desc:
                result["Notion"] = amount
            elif "ドコモ" in desc:
                result["ドコモ"] = amount
            else:
                result["その他通信費"] = amount

        # 支払手数料
        elif account == "支払手数料":
            result["支払手数料"] = amount

        # その他経費（未払金でまだ分類されていないもの含む）
        else:
            result["その他経費"] = amount

    return result, is_credit_card


def main():
    # パス設定
    project_root = Path(__file__).parent.parent
    input_file = project_root / "data" / "processed" / "transactions_cleaned.csv"
    actual_balance_file = project_root / "data" / "source" / "社内資金繰り表_20251030.csv"
    output_file = project_root / "data" / "reports" / f"cashflow_detailed_{datetime.now().strftime('%Y%m%d')}.html"

    output_file.parent.mkdir(exist_ok=True)

    print("💰 詳細版日次資金繰り表を生成します\n")
    print(f"入力: {input_file}")
    print(f"実残高: {actual_balance_file}")
    print(f"出力: {output_file}\n")

    # 社内資金繰り表から実残高データを読み込み
    print("📊 社内資金繰り表から実残高を読み込み中...")
    actual_df = pl.read_csv(actual_balance_file, skip_rows=1, encoding='utf-8', infer_schema_length=0)

    # 日付列と実残高列を抽出（空でない行のみ）
    first_col = actual_df.columns[0]
    actual_balance_data = actual_df.filter(
        (pl.col(first_col).is_not_null()) &
        (pl.col(first_col) != '') &
        (pl.col('実残高').is_not_null()) &
        (pl.col('実残高') != '')
    ).select([
        pl.col(first_col).str.strptime(pl.Date, format="%Y-%m-%d").alias("取引日"),
        pl.col('実残高').str.replace_all(',', '').cast(pl.Float64).alias("実残高")
    ])

    print(f"実残高データ: {len(actual_balance_data)}件\n")

    # データ読み込み
    df = pl.read_csv(input_file)

    # 取引日を日付型に変換
    df = df.with_columns([
        pl.col("取引日").str.strptime(pl.Date, format="%Y-%m-%d", strict=False).alias("取引日"),
    ])

    print("📊 取引を分類中...")

    expense_cols = ["Google広告", "Yahoo広告", "LINE広告",
                    "ホンダ自動車", "ゴールデンブル", "エフワイエル仕入", "ヤフーフリマ", "その他仕入",
                    "給料", "役員報酬",
                    "AWS", "Google Workspace", "OpenAI", "Claude", "Notion", "ドコモ", "その他通信費",
                    "支払手数料", "その他経費"]

    # ステップ1: クレカ購入取引を記録（まだ支払っていない）
    credit_purchases = []  # {date, card, item, amount}のリスト

    for row in df.iter_rows(named=True):
        if row["貸方勘定科目"] == "未払金" and row["借方勘定科目"] not in ["現金", "普通預金"]:
            # クレカ購入時の取引
            desc = str(row["摘要"]).upper() if row["摘要"] else ""
            account = row["借方勘定科目"]
            card_name = str(row["貸方補助科目"]) if row["貸方補助科目"] else ""
            amount = row["借方金額(円)"]

            # 項目を判定
            item = None
            if "GOOGLE" in desc and "ADS" in desc:
                item = "Google広告"
            elif ("YAHOO" in desc or "ヤフー" in desc) and account in ["仮払金", "広告宣伝費"]:
                item = "Yahoo広告"
            elif "LINE" in desc and account == "広告宣伝費":
                item = "LINE広告"
            elif "AWS" in desc or "AMAZON WEB" in desc:
                item = "AWS"
            elif "GSUITE" in desc or "WORKSPACE" in desc:
                item = "Google Workspace"
            elif "OPENAI" in desc or "CHATGPT" in desc:
                item = "OpenAI"
            elif "CLAUDE" in desc:
                item = "Claude"
            elif "NOTION" in desc:
                item = "Notion"
            elif "ドコモ" in desc:
                item = "ドコモ"
            elif account == "通信費":
                item = "その他通信費"
            else:
                item = "その他経費"

            credit_purchases.append({
                "date": row["取引日"],
                "card": card_name,
                "item": item,
                "amount": amount,
                "paid": False
            })

    print(f"クレカ購入取引: {len(credit_purchases)}件")

    # ステップ2: 各日付の取引を分類
    classified_rows = []

    for row in df.iter_rows(named=True):
        date = row["取引日"]
        row_data = {"取引日": date}

        # 収入・支出列を初期化
        for col in ["バックマーケット売上", "店舗売上", "エフワイエル売上", "その他EC売上", "その他売上"] + expense_cols:
            row_data[col] = 0
            if col in expense_cols:
                row_data[f"{col}_クレカ"] = 0
                row_data[f"{col}_カード名"] = []  # カード名リスト

        # クレカ支払い取引か？
        if row["借方勘定科目"] == "未払金" and row["貸方勘定科目"] in ["現金", "普通預金"]:
            # クレカ支払い！このカードで購入した内訳を集計
            card_name = str(row["借方補助科目"]) if row["借方補助科目"] else "不明"

            # このカードの未払い購入を集計
            for purchase in credit_purchases:
                if purchase["card"] == card_name and not purchase["paid"] and purchase["date"] <= date:
                    item = purchase["item"]
                    row_data[item] -= purchase["amount"]  # マイナス表記
                    row_data[f"{item}_クレカ"] -= purchase["amount"]
                    if card_name not in row_data[f"{item}_カード名"]:
                        row_data[f"{item}_カード名"].append(card_name)
                    purchase["paid"] = True  # 支払い済みマーク

        # 通常の入出金取引
        elif row["借方勘定科目"] in ["現金", "普通預金"] or row["貸方勘定科目"] in ["現金", "普通預金"]:
            classified, _ = classify_transaction(row)
            for key, value in classified.items():
                row_data[key] = value

        classified_rows.append(row_data)

    # 日付ごとに集計（カード名情報を保持）
    print("📊 日付ごとに集計中...")

    daily_summary = {}
    for row_data in classified_rows:
        date = row_data["取引日"]
        date_key = str(date)  # 文字列キーを使用

        if date_key not in daily_summary:
            daily_summary[date_key] = {
                "取引日": date,
                **{col: 0 for col in ["バックマーケット売上", "店舗売上", "エフワイエル売上", "その他EC売上", "その他売上"] + expense_cols},
                **{f"{col}_クレカ": 0 for col in expense_cols},
                **{f"{col}_カード名": [] for col in expense_cols}
            }

        # 収入列
        for col in ["バックマーケット売上", "店舗売上", "エフワイエル売上", "その他EC売上", "その他売上"]:
            daily_summary[date_key][col] += row_data[col]

        # 経費列
        for col in expense_cols:
            daily_summary[date_key][col] += row_data[col]
            daily_summary[date_key][f"{col}_クレカ"] += row_data[f"{col}_クレカ"]
            # カード名をマージ
            for card in row_data[f"{col}_カード名"]:
                if card not in daily_summary[date_key][f"{col}_カード名"]:
                    daily_summary[date_key][f"{col}_カード名"].append(card)

    # DataFrameに変換（カード名は除外）
    daily_rows = []
    for date_key, data in sorted(daily_summary.items()):
        row = {"取引日": data["取引日"]}  # dateオブジェクトを使用
        for col in ["バックマーケット売上", "店舗売上", "エフワイエル売上", "その他EC売上", "その他売上"] + expense_cols:
            row[col] = data[col]
        for col in expense_cols:
            row[f"{col}_クレカ"] = data[f"{col}_クレカ"]
        daily_rows.append(row)

    daily_df = pl.DataFrame(daily_rows)

    # 全日付を生成
    start_date = daily_df["取引日"].min()
    end_date = daily_df["取引日"].max()

    all_dates = pl.date_range(start_date, end_date, interval="1d", eager=True).alias("取引日")
    all_dates_df = pl.DataFrame({"取引日": all_dates})

    # 全日付とマージ
    daily_complete = all_dates_df.join(daily_df, on="取引日", how="left").fill_null(0)

    # 総入金・総出金を計算
    revenue_cols = ["バックマーケット売上", "店舗売上", "エフワイエル売上", "その他EC売上", "その他売上"]

    daily_complete = daily_complete.with_columns([
        pl.sum_horizontal(revenue_cols).alias("総入金"),
        pl.sum_horizontal(expense_cols).alias("総出金")
    ])

    daily_complete = daily_complete.with_columns([
        (pl.col("総入金") + pl.col("総出金")).alias("純増減")
    ])

    # 実残高データをマージ
    daily_complete = daily_complete.join(actual_balance_data, on="取引日", how="left")

    # 残高を計算（実残高で補正）
    print("💡 残高を計算中（実残高で補正）...")

    # 期首残高を取得（会計データの開始日に最も近い実残高を使用）
    accounting_start = daily_complete["取引日"].min()
    actual_before_start = actual_balance_data.filter(pl.col("取引日") <= accounting_start)

    if len(actual_before_start) > 0:
        # 開始日以前の最も近い実残高
        opening_balance = actual_before_start[-1, "実残高"] * 1000
        opening_date = actual_before_start[-1, "取引日"]
    elif len(actual_balance_data) > 0:
        # 開始日以降の最初の実残高
        opening_balance = actual_balance_data[0, "実残高"] * 1000
        opening_date = actual_balance_data[0, "取引日"]
    else:
        opening_balance = 0
        opening_date = accounting_start

    print(f"期首残高: {opening_balance:,.0f}円（{opening_date}時点）\n")

    # 残高を日次で計算（実残高がある日はそれを使用）
    balance_list = []
    adjustment_list = []
    current_balance = opening_balance

    for row in daily_complete.iter_rows(named=True):
        # 今日の純増減を加算
        calculated_balance = current_balance + row["純増減"]

        # 実残高がある場合はそれを使用
        if row["実残高"] is not None:
            actual = row["実残高"] * 1000  # 千円単位を円単位に変換
            adjustment = actual - calculated_balance
            current_balance = actual
            adjustment_list.append(adjustment)
        else:
            current_balance = calculated_balance
            adjustment_list.append(0)

        balance_list.append(current_balance)

    # 残高と調整額を追加
    daily_complete = daily_complete.with_columns([
        pl.Series("残高", balance_list, dtype=pl.Float64),
        pl.Series("調整額", adjustment_list, dtype=pl.Float64)
    ])

    print(f"📅 対象期間: {start_date} ～ {end_date}")
    print(f"📈 総取引日数: {len(daily_complete)}日\n")

    print("🎨 HTMLを生成中...")

    # HTML生成（長いので分割）
    html_head = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>詳細版日次資金繰り表 ({start_date} ～ {end_date})</title>
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
        .meta {{
            color: #7f8c8d;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 11px;
        }}
        th {{
            background-color: #34495e;
            color: white;
            padding: 8px 4px;
            text-align: right;
            font-weight: bold;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        th.date {{ text-align: center; min-width: 90px; }}
        th.section {{ background-color: #2c3e50; }}
        td {{
            padding: 6px 4px;
            text-align: right;
            border-bottom: 1px solid #ecf0f1;
        }}
        td.date {{
            text-align: center;
            font-weight: 500;
        }}
        tr:hover {{ background-color: #f8f9fa; }}
        .weekend {{ background-color: #fff3cd; }}
        .positive {{ color: #27ae60; font-weight: bold; }}
        .negative {{ color: #e74c3c; }}
        .zero {{ color: #95a5a6; }}
        .revenue {{ background-color: #d4edda; }}
        .expense {{ background-color: #f8d7da; }}
        .balance {{ background-color: #cfe2ff; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>💰 詳細版日次資金繰り表</h1>
        <div class="meta">
            対象期間: {start_date} ～ {end_date} ({len(daily_complete)}日間) |
            作成日: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
        </div>

        <table>
            <thead>
                <tr>
                    <th class="date" rowspan="2">日付</th>
                    <th class="section" colspan="5">収入（入金）</th>
                    <th class="section" colspan="3">広告費</th>
                    <th class="section" colspan="5">仕入</th>
                    <th class="section" colspan="2">人件費</th>
                    <th class="section" colspan="7">IT・通信費</th>
                    <th class="section" colspan="2">その他経費</th>
                    <th class="section" colspan="6">合計</th>
                </tr>
                <tr>
                    <th>バックマーケット</th>
                    <th>店舗</th>
                    <th>エフワイエル</th>
                    <th>その他EC</th>
                    <th>その他</th>
                    <th>Google</th>
                    <th>Yahoo</th>
                    <th>LINE</th>
                    <th>ホンダ</th>
                    <th>ゴールデンブル</th>
                    <th>エフワイエル</th>
                    <th>ヤフーフリマ</th>
                    <th>その他</th>
                    <th>給料</th>
                    <th>役員報酬</th>
                    <th>AWS</th>
                    <th>G Suite</th>
                    <th>OpenAI</th>
                    <th>Claude</th>
                    <th>Notion</th>
                    <th>ドコモ</th>
                    <th>その他</th>
                    <th>手数料</th>
                    <th>その他</th>
                    <th>純増減</th>
                    <th>総入金</th>
                    <th>総出金</th>
                    <th>残高</th>
                    <th>実残高</th>
                    <th>調整額</th>
                </tr>
            </thead>
            <tbody>
"""

    # テーブル行を生成
    html_rows = ""
    for row in daily_complete.iter_rows(named=True):
        date = row["取引日"]
        weekday = ["月", "火", "水", "木", "金", "土", "日"][date.weekday()]
        row_class = "weekend" if date.weekday() >= 5 else ""

        def fmt(val):
            if val == 0:
                return '<td class="zero">-</td>'
            elif val > 0:
                return f'<td class="positive">{val:,.0f}</td>'
            else:
                return f'<td class="negative">{val:,.0f}</td>'

        html_rows += f'<tr class="{row_class}">\n'
        html_rows += f'<td class="date">{date.strftime("%m/%d")}({weekday})</td>\n'

        # 収入
        for col in revenue_cols:
            html_rows += fmt(row[col])

        # 支出（クレカマーク+カード名付き）
        for col in expense_cols:
            val = row[col]
            credit_val = row[f"{col}_クレカ"]

            if val == 0:
                html_rows += '<td class="zero">-</td>\n'
            else:
                # カード名を取得（日付を文字列に変換して検索）
                date_str = str(date)
                card_names = []
                if date_str in daily_summary and credit_val != 0:
                    card_names = daily_summary[date_str][f"{col}_カード名"]

                credit_mark = ''
                if credit_val != 0:
                    if card_names:
                        card_text = '・'.join(card_names)
                        credit_mark = f' 💳{card_text}'
                    else:
                        credit_mark = ' 💳'

                css_class = "positive" if val > 0 else "negative"
                html_rows += f'<td class="{css_class}">{val:,.0f}{credit_mark}</td>\n'

        # 合計
        net = row["純増減"]
        html_rows += f'<td class="{"positive" if net > 0 else "negative"}">{net:+,.0f}</td>\n'
        html_rows += f'<td class="positive">{row["総入金"]:,.0f}</td>\n'
        html_rows += f'<td class="negative">{row["総出金"]:,.0f}</td>\n'
        html_rows += f'<td class="balance">{row["残高"]:,.0f}</td>\n'

        # 実残高と調整額
        if row["実残高"] is not None:
            html_rows += f'<td class="balance" style="background-color: #fff3cd;">{row["実残高"] * 1000:,.0f}</td>\n'
            adj = row["調整額"]
            html_rows += f'<td class="{"positive" if adj > 0 else "negative" if adj < 0 else "zero"}">{adj:+,.0f}</td>\n'
        else:
            html_rows += '<td class="zero">-</td>\n'
            html_rows += '<td class="zero">-</td>\n'

        html_rows += '</tr>\n'

    html_foot = """            </tbody>
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
        f.write(html_head + html_rows + html_foot)

    print(f"✅ 詳細版日次資金繰り表を生成しました: {output_file}")
    print(f"\n📊 サマリー:")
    print(f"   期首残高: {daily_complete['残高'][0]:,.0f}円")
    print(f"   期末残高: {daily_complete['残高'][-1]:,.0f}円")
    print(f"   総入金額: {daily_complete['総入金'].sum():,.0f}円")
    print(f"   総出金額: {daily_complete['総出金'].sum():,.0f}円")


if __name__ == "__main__":
    main()
