#!/usr/bin/env python3
"""
徹底的な矛盾チェック - 全ルール適用
"""

from datetime import datetime, timedelta
from collections import defaultdict

# 祝日リスト
HOLIDAYS = [
    '2025-11-03', '2025-11-23', '2025-11-24',
    '2025-12-23',
    '2026-01-01', '2026-01-12', '2026-02-11', '2026-02-23'
]

# カード情報
CARDS = {
    'shinkin_visa': {
        'name': 'しんきんVisa',
        'closing_day': 15,
        'payment_day': 10,
        'payment_month_offset': 1,
        'available': 1600000
    },
    'mi': {
        'name': 'MIカード',
        'closing_day': 5,
        'payment_day': 26,
        'payment_month_offset': 0,  # 当月
        'available': 722000
    },
    'toyota': {
        'name': 'トヨタ',
        'closing_day': 5,
        'payment_day': 2,
        'payment_month_offset': 1,
        'available': 1200000
    },
    'amazon': {
        'name': 'Amazon',
        'closing_day': 31,  # 月末
        'payment_day': 26,
        'payment_month_offset': 1,
        'available': 436000
    }
}

def is_holiday(date):
    """土日祝日判定"""
    if date.weekday() in [5, 6]:
        return True
    return date.strftime('%Y-%m-%d') in HOLIDAYS

def add_business_days(start_date, days):
    """営業日を加算"""
    current = start_date
    added = 0
    while added < days:
        current += timedelta(days=1)
        if not is_holiday(current):
            added += 1
    return current

def get_last_day_of_month(year, month):
    """月末日を取得"""
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    return (next_month - timedelta(days=1)).day

def calculate_payment_date(card_id, application_date_str):
    """引き落とし日を計算（詳細版）"""
    card = CARDS[card_id]
    application_date = datetime.strptime(application_date_str, '%Y-%m-%d')

    # ステップ1: 着金日（決済日）を計算
    settlement_date = add_business_days(application_date, 4)

    # ステップ2: 締め日判定
    year = settlement_date.year
    month = settlement_date.month
    day = settlement_date.day

    # 月末締めの場合
    if card['closing_day'] == 31:
        closing_day = get_last_day_of_month(year, month)
    else:
        closing_day = card['closing_day']

    # 締め日より後なら次の締め期間
    if day > closing_day:
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1

    # ステップ3: 支払い月を計算
    if card['payment_month_offset'] == 0:
        # 当月支払い（MIカード）
        payment_year = settlement_date.year
        payment_month = settlement_date.month
    else:
        # 翌月支払い
        payment_month = month + card['payment_month_offset']
        payment_year = year
        if payment_month > 12:
            payment_month -= 12
            payment_year += 1

    # ステップ4: 支払い日を計算
    payment_day = card['payment_day']
    last_day = get_last_day_of_month(payment_year, payment_month)
    if payment_day > last_day:
        payment_day = last_day

    payment_date = datetime(payment_year, payment_month, payment_day)

    # ステップ5: 土日祝の後ろ倒し
    while is_holiday(payment_date):
        payment_date += timedelta(days=1)

    return {
        'application_date': application_date,
        'settlement_date': settlement_date,  # 決済日（着金日）
        'closing_period': f"{year}-{month:02d}",
        'payment_date': payment_date
    }

# 提案されたプラン
PLAN = [
    ('2025-11-10', 'shinkin_visa', 'ヤマト', 1200000),
    ('2025-11-10', 'mi', 'ビズビ', 74000),
    ('2025-11-16', 'toyota', '徐さん', 978000),
    ('2025-11-26', 'amazon', 'ユニホー', 258000),
    ('2025-11-26', 'toyota', 'ドンキ', 258000),
    ('2025-12-25', 'shinkin_visa', 'ヤマト', 1380000),
]

print("="*100)
print("徹底的な矛盾チェック - 全申請の詳細")
print("="*100)

# 各申請の詳細を計算
details = []
for app_date, card_id, name, amount in PLAN:
    result = calculate_payment_date(card_id, app_date)
    details.append({
        'application_date': app_date,
        'card_id': card_id,
        'card_name': CARDS[card_id]['name'],
        'name': name,
        'amount': amount,
        'settlement_date': result['settlement_date'],
        'closing_period': result['closing_period'],
        'payment_date': result['payment_date']
    })

# 詳細表示
for i, d in enumerate(details, 1):
    print(f"\n【{i}】{d['name']} - {d['amount']:,}円")
    print(f"  カード: {d['card_name']}")
    print(f"  申請日: {d['application_date']}")
    print(f"  着金日（決済日）: {d['settlement_date'].strftime('%Y-%m-%d (%a)')}")
    print(f"  締め期間: {d['closing_period']}")
    print(f"  引き落とし日: {d['payment_date'].strftime('%Y-%m-%d (%a)')}")

print("\n" + "="*100)
print("カード別の枠使用状況チェック")
print("="*100)

# カード別に時系列でイベントを整理
card_events = defaultdict(list)

for d in details:
    card_id = d['card_id']
    # 決済日（枠占有開始）
    card_events[card_id].append({
        'date': d['settlement_date'],
        'type': 'settlement',
        'amount': d['amount'],
        'name': d['name'],
        'payment_date': d['payment_date']
    })
    # 引き落とし日（枠解放）
    card_events[card_id].append({
        'date': d['payment_date'],
        'type': 'payment',
        'amount': d['amount'],
        'name': d['name']
    })

# カードごとに矛盾チェック
all_ok = True

for card_id in sorted(card_events.keys()):
    card = CARDS[card_id]
    events = sorted(card_events[card_id], key=lambda x: x['date'])

    print(f"\n【{card['name']}】利用可能額: {card['available']:,}円")
    print("-" * 100)

    current_available = card['available']
    occupied_amount = 0

    for event in events:
        date_str = event['date'].strftime('%Y-%m-%d (%a)')

        if event['type'] == 'settlement':
            # 決済時: 枠を占有
            print(f"  {date_str}: 【決済】{event['name']} {event['amount']:,}円")
            print(f"    → 決済前の利用可能額: {current_available:,}円")

            if current_available < event['amount']:
                print(f"    ❌ エラー: 枠不足！ {event['amount'] - current_available:,}円 足りません")
                all_ok = False
            else:
                current_available -= event['amount']
                occupied_amount += event['amount']
                print(f"    ✅ OK: 決済後の利用可能額: {current_available:,}円 (占有: {occupied_amount:,}円)")

        elif event['type'] == 'payment':
            # 引き落とし時: 枠を解放
            print(f"  {date_str}: 【引落】{event['name']} {event['amount']:,}円")
            current_available += event['amount']
            occupied_amount -= event['amount']
            print(f"    → 引落後の利用可能額: {current_available:,}円 (占有: {occupied_amount:,}円)")

print("\n" + "="*100)
if all_ok:
    print("✅ 全ての申請が問題なく処理できます！")
else:
    print("❌ 矛盾が見つかりました！上記のエラーを確認してください。")
print("="*100)
