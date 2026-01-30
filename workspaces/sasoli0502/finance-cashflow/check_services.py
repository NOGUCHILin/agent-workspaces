#!/usr/bin/env python3
"""削除対象サービスの確認"""

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

# 削除対象サービスのキーワード
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

matched_items = []

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
            # サービス名が削除対象に含まれるかチェック
            service_lower = service.lower()
            for keyword in exclude_keywords:
                if keyword.lower() in service_lower:
                    matched_items.append({
                        'date': date_str,
                        'card': card,
                        'account': account,
                        'service': service,
                        'amount': amount,
                        'keyword': keyword
                    })
                    break
    except (ValueError, AttributeError):
        continue

# 結果を表示
print("# 削除対象サービスの確認\n")
print("以下のサービスを削除します。よろしいですか？\n")

total = 0
by_keyword = defaultdict(list)

for item in matched_items:
    by_keyword[item['keyword']].append(item)
    total += item['amount']

for keyword in sorted(by_keyword.keys()):
    items = by_keyword[keyword]
    keyword_total = sum(item['amount'] for item in items)
    print(f"## {keyword} (件数: {len(items)}件、合計: ¥{keyword_total:,})\n")

    for item in items:
        print(f"- {item['date']} | {item['card']} | {item['account']} | {item['service']} | ¥{item['amount']:,}")
    print()

print(f"\n**削除対象の総合計**: ¥{total:,}")
print(f"**削除対象の件数**: {len(matched_items)}件")
