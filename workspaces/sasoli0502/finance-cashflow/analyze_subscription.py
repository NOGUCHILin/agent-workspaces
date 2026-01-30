#!/usr/bin/env python3
"""サブスクリプションと単発支払いを分類"""

import re
from datetime import datetime
from collections import defaultdict

# HTMLファイルを読み込み
html_file = '/Users/noguchisara/projects/work/finance-cashflow/data/reports/credit_card_statement_20251031.html'

with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

row_pattern = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL)
cell_pattern = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL)
tag_pattern = re.compile(r'<[^>]+>')

# 除外対象
exclude_keywords = [
    'amazon.co.jp', 'アマゾン jp マーケットプレイス', 'amazon jp マーケットプレイス',
    'アマゾン シーオージェーピー', 'ドン キホーテ', 'スマモン', 'masatomi store', 'イオシス'
]
exclude_cards = ['立替経費']

service_data = defaultdict(lambda: {'count': 0, 'total': 0, 'dates': [], 'accounts': set()})

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

        if date.year == 2025 and date.month == 9 and category == '経費':
            if card in exclude_cards:
                continue

            service_lower = service.lower()
            should_exclude = False
            for keyword in exclude_keywords:
                if keyword.lower() in service_lower:
                    should_exclude = True
                    break

            if should_exclude:
                continue

            service_data[service]['count'] += 1
            service_data[service]['total'] += amount
            service_data[service]['dates'].append(date_str)
            service_data[service]['accounts'].add(account)
    except (ValueError, AttributeError):
        continue

# サブスクリプションと思われるキーワード
subscription_keywords = [
    'openai', 'chatgpt', 'claude', 'cursor', 'github', 'figma', 'canva', 'notion',
    'slack', 'obsidian', 'adobe', 'illustrator', 'zoom', 'midjourney', 'google',
    'gsuite', 'aws', 'amazon web services', 'vercel', 'railway', 'supabase',
    'heygen', 'ngrok', 'perplexity', 'runway', 'recraft', 'pixverse', 'superultra',
    'newcompute', 'contabo', 'imobie', 'anymiro', 'ドコモ', 'docomo', 'ソフトバンク',
    'softbank', '日本通信', 'gmo', 'line公式', 'サイボウズ', 'kintone', 'スマレジ',
    'マネーフォワード', 'x corp', 'youtube', 'notta', 'lucid', 'paddle', 'n8n',
    'grok', 'nttドコモ'
]

# 単発と思われるキーワード
oneoff_keywords = [
    'jr ', 'タイムズ', '魚や', '大庄', '洋服の青山', '無印', 'ラクスル', 'ム-ム-ドメイン',
    'apple itunes', 'maneql', 'dcs', '会議費', '接待', '旅費'
]

# 分類
subscriptions = []
oneoffs = []
unsure = []

for service, data in service_data.items():
    service_lower = service.lower()

    # サブスクチェック
    is_subscription = any(keyword in service_lower for keyword in subscription_keywords)
    is_oneoff = any(keyword in service_lower for keyword in oneoff_keywords)

    if is_subscription:
        subscriptions.append((service, data))
    elif is_oneoff:
        oneoffs.append((service, data))
    else:
        unsure.append((service, data))

print("# サービス分類結果\n")

print("## 【サブスクリプション（定期支払い）】と判定したもの\n")
sub_total = 0
for service, data in sorted(subscriptions, key=lambda x: x[1]['total'], reverse=True):
    accounts = ', '.join(data['accounts'])
    print(f"- **{service}**: ¥{data['total']:,} ({data['count']}件) - {accounts}")
    sub_total += data['total']
print(f"\n小計: ¥{sub_total:,}\n")

print("---\n")
print("## 【単発支払い】と判定したもの（削除候補）\n")
oneoff_total = 0
for service, data in sorted(oneoffs, key=lambda x: x[1]['total'], reverse=True):
    accounts = ', '.join(data['accounts'])
    print(f"- {service}: ¥{data['total']:,} ({data['count']}件) - {accounts}")
    oneoff_total += data['total']
print(f"\n小計: ¥{oneoff_total:,}\n")

print("---\n")
print("## 【判定不明】確認が必要なもの\n")
unsure_total = 0
for service, data in sorted(unsure, key=lambda x: x[1]['total'], reverse=True):
    accounts = ', '.join(data['accounts'])
    print(f"- **{service}**: ¥{data['total']:,} ({data['count']}件) - {accounts}")
    unsure_total += data['total']
print(f"\n小計: ¥{unsure_total:,}\n")

print("---\n")
print(f"**総合計**: ¥{sub_total + oneoff_total + unsure_total:,}")
