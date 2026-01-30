#!/usr/bin/env python3
"""
最終正式版：担当者からの訂正を反映
- 11/26申請 → 12/05着金
- 11/25までの申請 → 月末着金
"""

from datetime import datetime, timedelta
from collections import defaultdict

HOLIDAYS = [
    '2025-11-03', '2025-11-23', '2025-11-24',
    '2025-12-23',
    '2026-01-01', '2026-01-12', '2026-02-11', '2026-02-23'
]

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
    if date.weekday() in [5, 6]:
        return True
    return date.strftime('%Y-%m-%d') in HOLIDAYS

def get_last_day_of_month(year, month):
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    return (next_month - timedelta(days=1)).day

def get_settlement_date(application_date_str):
    """
    担当者ルールに基づく着金日計算
    - 11/25まで → 月末（11/30）
    - 11/26 → 12/05
    """
    app_date = datetime.strptime(application_date_str, '%Y-%m-%d')

    # 特殊ケース：11/25までの申請
    if app_date.month == 11 and app_date.day <= 25:
        settlement = datetime(2025, 11, 30)
        print(f"    11/25までの申請 → 月末着金ルール適用")
    # 11/26の申請
    elif application_date_str == '2025-11-26':
        settlement = datetime(2025, 12, 5)
        print(f"    11/26申請 → 12/05着金（担当者回答）")
    # 12/25の申請（同様のルールが適用されると仮定）
    elif application_date_str == '2025-12-25':
        settlement = datetime(2025, 12, 31)
        print(f"    12/25申請 → 月末着金と仮定")
    else:
        # その他の通常計算（4営業日後）
        current = app_date
        business_days = 0
        while business_days < 4:
            current += timedelta(days=1)
            if not is_holiday(current):
                business_days += 1
        settlement = current
        print(f"    通常計算：4営業日後")

    return settlement

def adjust_payment_date(payment_date):
    adjusted = payment_date
    while is_holiday(adjusted):
        adjusted += timedelta(days=1)
    return adjusted

def calculate_payment_date(card_id, application_date_str):
    card = CARDS[card_id]

    print(f"\n  【{card['name']}】")

    # 着金日取得
    settlement_date = get_settlement_date(application_date_str)
    print(f"    着金日: {settlement_date.strftime('%Y-%m-%d (%a)')}")

    year = settlement_date.year
    month = settlement_date.month
    day = settlement_date.day

    # 締め日判定
    if card['closing_day'] == 31:
        closing_day = get_last_day_of_month(year, month)
    else:
        closing_day = card['closing_day']

    print(f"    締め日: {month}月{closing_day}日")

    if day > closing_day:
        print(f"    → {day}日 > {closing_day}日 なので次の締め")
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
    else:
        print(f"    → {day}日 ≤ {closing_day}日 なので今回の締め")

    # 支払月
    if card['payment_month_offset'] == 0:
        payment_year = settlement_date.year
        payment_month = settlement_date.month
    else:
        payment_month = month + card['payment_month_offset']
        payment_year = year
        if payment_month > 12:
            payment_month -= 12
            payment_year += 1

    # 支払日
    payment_day = card['payment_day']
    last_day = get_last_day_of_month(payment_year, payment_month)
    if payment_day > last_day:
        payment_day = last_day

    payment_date = datetime(payment_year, payment_month, payment_day)
    payment_date = adjust_payment_date(payment_date)

    print(f"    引落日: {payment_date.strftime('%Y-%m-%d (%a)')}")

    return {
        'settlement_date': settlement_date,
        'payment_date': payment_date
    }

# パターン1: 11/26申請（実際の申請日）
print("="*100)
print("パターン1: 11/26申請（ユニホー・ドンキ）")
print("="*100)

pattern1_results = []
for card_id in ['amazon', 'mi', 'toyota', 'shinkin_visa']:
    result = calculate_payment_date(card_id, '2025-11-26')
    pattern1_results.append({
        'card': CARDS[card_id]['name'],
        'card_id': card_id,
        'payment_date': result['payment_date'],
        'available': CARDS[card_id]['available']
    })

pattern1_results.sort(key=lambda x: x['payment_date'], reverse=True)

print(f"\n【引き落とし日ランキング（11/26申請）】")
for i, r in enumerate(pattern1_results, 1):
    marker = "👑" if i == 1 else f"{i}."
    ok = "✅" if r['available'] >= 258000 else "❌"
    print(f"  {marker} {r['card']:15} : {r['payment_date'].strftime('%Y-%m-%d (%a)')} ({ok} {r['available']:,}円)")

# パターン2: 11/25申請（月末着金）
print(f"\n{'='*100}")
print("パターン2: 11/25申請（ユニホー・ドンキ - if 11/25までに申請できたら）")
print("="*100)

pattern2_results = []
for card_id in ['amazon', 'mi', 'toyota', 'shinkin_visa']:
    result = calculate_payment_date(card_id, '2025-11-25')
    pattern2_results.append({
        'card': CARDS[card_id]['name'],
        'card_id': card_id,
        'payment_date': result['payment_date'],
        'available': CARDS[card_id]['available']
    })

pattern2_results.sort(key=lambda x: x['payment_date'], reverse=True)

print(f"\n【引き落とし日ランキング（11/25申請）】")
for i, r in enumerate(pattern2_results, 1):
    marker = "👑" if i == 1 else f"{i}."
    ok = "✅" if r['available'] >= 258000 else "❌"
    print(f"  {marker} {r['card']:15} : {r['payment_date'].strftime('%Y-%m-%d (%a)')} ({ok} {r['available']:,}円)")

# 全申請の最適化
print(f"\n{'='*100}")
print("全申請の最適カード計算")
print("="*100)

APPLICATIONS = [
    ('2025-11-10', 'ヤマト', 1200000),
    ('2025-11-10', 'ビズビ', 74000),
    ('2025-11-16', '徐さん', 978000),
    ('2025-11-26', 'ユニホー', 258000),  # 11/26申請
    ('2025-11-26', 'ドンキ', 258000),    # 11/26申請
    ('2025-12-25', 'ヤマト', 1380000),
]

optimal_plan = []
for app_date, name, amount in APPLICATIONS:
    print(f"\n{'='*100}")
    print(f"【{name} {amount:,}円】申請日: {app_date}")
    print(f"{'='*100}")

    card_results = []
    for card_id in ['amazon', 'mi', 'toyota', 'shinkin_visa']:
        result = calculate_payment_date(card_id, app_date)
        card_results.append({
            'card': CARDS[card_id]['name'],
            'card_id': card_id,
            'payment_date': result['payment_date'],
            'settlement_date': result['settlement_date'],
            'available': CARDS[card_id]['available']
        })

    card_results.sort(key=lambda x: x['payment_date'], reverse=True)

    print(f"\n  【ランキング】")
    optimal = None
    for i, r in enumerate(card_results, 1):
        marker = "👑" if i == 1 else f"{i}."
        if r['available'] >= amount:
            ok = "✅"
            if optimal is None:
                optimal = r
        else:
            ok = "❌"
        print(f"    {marker} {r['card']:15} : {r['payment_date'].strftime('%Y-%m-%d (%a)')} ({ok} {r['available']:,}円)")

    if optimal:
        print(f"\n  💡 最適: {optimal['card']} (引落: {optimal['payment_date'].strftime('%Y-%m-%d')})")
        optimal_plan.append({
            'app_date': app_date,
            'name': name,
            'amount': amount,
            'card': optimal['card'],
            'card_id': optimal['card_id'],
            'settlement_date': optimal['settlement_date'],
            'payment_date': optimal['payment_date']
        })

# サマリー
print(f"\n{'='*100}")
print("最適化プラン サマリー")
print("="*100)
print(f"{'申請日':<12} {'支払先':<12} {'金額':>12} {'カード':<18} {'決済日':<15} {'引落日':<15}")
print("-"*100)
for p in optimal_plan:
    print(f"{p['app_date']:<12} {p['name']:<12} {p['amount']:>12,} {p['card']:<18} {p['settlement_date'].strftime('%Y-%m-%d'):<15} {p['payment_date'].strftime('%Y-%m-%d'):<15}")

print(f"\n{'='*100}")
print("11/25申請にした場合の比較")
print("="*100)
print("ユニホー・ドンキを11/25までに申請できた場合：")
for card_id in ['amazon', 'mi']:
    result = calculate_payment_date(card_id, '2025-11-25')
    print(f"  {CARDS[card_id]['name']:15} : 引落 {result['payment_date'].strftime('%Y-%m-%d')}")
