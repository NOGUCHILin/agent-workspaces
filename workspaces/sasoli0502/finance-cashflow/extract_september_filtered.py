#!/usr/bin/env python3
"""2025年9月のクレカ明細を抽出（特定サービスを除外）"""

import re
from datetime import datetime
from collections import defaultdict

# HTMLファイルを読み込み
html_file = '/Users/noguchisara/projects/work/finance-cashflow/data/reports/credit_card_statement_20251031.html'

with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

# テーブル行のパターンを探す
row_pattern = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL)
cell_pattern = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL)
tag_pattern = re.compile(r'<[^>]+>')

# 除外対象サービスのキーワード
exclude_keywords = [
    'amazon.co.jp',
    'アマゾン jp マーケットプレイス',
    'amazon jp マーケットプレイス',
    'アマゾン シーオージェーピー',
    'ドン キホーテ',
    'スマモン',
    'masatomi store',
    'イオシス'
]

# 除外対象カード
exclude_cards = ['立替経費']

september_data = defaultdict(list)
totals_by_card = defaultdict(int)
totals_by_account = defaultdict(int)
card_account_totals = defaultdict(lambda: defaultdict(int))
service_totals = defaultdict(int)  # サービス別集計
card_service_totals = defaultdict(lambda: defaultdict(int))  # カード×サービス集計

for row_match in row_pattern.finditer(content):
    row_html = row_match.group(1)
    cells = [tag_pattern.sub('', cell).strip() for cell in cell_pattern.findall(row_html)]

    if len(cells) < 6:
        continue

    date_str = cells[0].strip()
    card = cells[1].strip()
    category = cells[2].strip()
    account = cells[3].strip()
    service = cells[4].strip()
    amount_str = cells[5].strip().replace(',', '').replace('¥', '').replace('円', '')

    if not re.match(r'\d{4}/\d{2}/\d{2}', date_str):
        continue

    try:
        date = datetime.strptime(date_str, '%Y/%m/%d')
        amount = int(amount_str)

        # 2025年9月のデータのみ、かつ経費のみ
        if date.year == 2025 and date.month == 9 and category == '経費':
            # 除外対象カードをスキップ
            if card in exclude_cards:
                continue

            # 除外対象サービスをスキップ
            service_lower = service.lower()
            should_exclude = False
            for keyword in exclude_keywords:
                if keyword.lower() in service_lower:
                    should_exclude = True
                    break

            if should_exclude:
                continue

            september_data[card].append({
                'date': date_str,
                'account': account,
                'service': service,
                'amount': amount
            })
            totals_by_card[card] += amount
            totals_by_account[account] += amount
            card_account_totals[card][account] += amount
            service_totals[service] += amount
            card_service_totals[card][service] += amount
    except (ValueError, AttributeError):
        continue

# マークダウン形式で出力
print("# 2025年9月 クレジットカード経費明細（仕入・備品除く）\n")
print("> **除外対象**: Amazon関連、ドンキホーテ、スマモン、MASATOMI STORE、イオシス、立替経費\n")

# カードごとの合計を表示
print("## カード別合計\n")
grand_total = 0
for card in sorted(totals_by_card.keys()):
    print(f"- **{card}**: ¥{totals_by_card[card]:,}")
    grand_total += totals_by_card[card]
print(f"\n**総合計**: ¥{grand_total:,}\n")

# 勘定科目別合計を表示
print("---\n")
print("## 勘定科目別合計\n")
for account in sorted(totals_by_account.keys(), key=lambda x: totals_by_account[x], reverse=True):
    print(f"- **{account}**: ¥{totals_by_account[account]:,}")

# サービス別合計（金額の大きい順）
print("\n---\n")
print("## サービス別合計（上位30件）\n")
sorted_services = sorted(service_totals.items(), key=lambda x: x[1], reverse=True)[:30]
for service, total in sorted_services:
    count = sum(1 for card_data in september_data.values() for item in card_data if item['service'] == service)
    print(f"- **{service}**: ¥{total:,} ({count}件)")

# カード別＋勘定科目別のクロス集計
print("\n---\n")
print("## カード別・勘定科目別クロス集計\n")
for card in sorted(card_account_totals.keys()):
    print(f"### {card} (合計: ¥{totals_by_card[card]:,})\n")
    for account in sorted(card_account_totals[card].keys(), key=lambda x: card_account_totals[card][x], reverse=True):
        print(f"- {account}: ¥{card_account_totals[card][account]:,}")
    print()

# カードごとの詳細
print("---\n")
print("## カード別詳細明細\n")

for card in sorted(september_data.keys()):
    print(f"### {card}\n")
    print(f"合計: ¥{totals_by_card[card]:,}\n")

    # サービス別集計（このカード内）
    print("#### サービス別集計\n")
    card_services = sorted(card_service_totals[card].items(), key=lambda x: x[1], reverse=True)
    for service, total in card_services:
        count = sum(1 for item in september_data[card] if item['service'] == service)
        if count > 1:
            print(f"- **{service}**: ¥{total:,} ({count}件)")
        else:
            print(f"- {service}: ¥{total:,}")
    print()

    # 明細テーブル
    print("#### 明細\n")
    print("| 日付 | 勘定科目 | サービス | 金額 |")
    print("|------|---------|---------|-----:|")

    # 日付順にソート
    items = sorted(september_data[card], key=lambda x: x['date'])
    for item in items:
        print(f"| {item['date']} | {item['account']} | {item['service']} | ¥{item['amount']:,} |")

    print()
