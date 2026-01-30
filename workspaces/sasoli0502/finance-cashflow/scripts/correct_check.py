#!/usr/bin/env python3
"""
正しい前倒しルールを適用した矛盾チェック
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
    """
    営業日を加算
    重要: 4営業日後が土日祝の場合は「前倒し」（前の営業日に着金）
    """
    current = start_date
    added = 0

    # まず4営業日後を計算
    while added < days:
        current += timedelta(days=1)
        if not is_holiday(current):
            added += 1

    # 4営業日後が土日祝なら「前倒し」
    if is_holiday(current):
        print(f"    ⚠️  4営業日後 {current.strftime('%Y-%m-%d (%a)')} が土日祝 → 前倒し")
        while is_holiday(current):
            current -= timedelta(days=1)
        print(f"    → 前倒し後: {current.strftime('%Y-%m-%d (%a)')}")

    return current

def get_last_day_of_month(year, month):
    """月末日を取得"""
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    return (next_month - timedelta(days=1)).day

def adjust_payment_date_for_holiday(payment_date):
    """引き落とし日が土日祝なら後ろ倒し"""
    adjusted = payment_date
    while is_holiday(adjusted):
        adjusted += timedelta(days=1)
    return adjusted

def calculate_payment_date(card_id, application_date_str):
    """引き落とし日を計算"""
    card = CARDS[card_id]
    application_date = datetime.strptime(application_date_str, '%Y-%m-%d')

    print(f"\n  【{card['name']}】申請日: {application_date_str}")

    # ステップ1: 着金日（決済日）を計算（前倒しルール適用）
    settlement_date = add_business_days(application_date, 4)
    print(f"    着金日（決済日）: {settlement_date.strftime('%Y-%m-%d (%a)')}")

    # ステップ2: 締め日判定
    year = settlement_date.year
    month = settlement_date.month
    day = settlement_date.day

    # 月末締めの場合
    if card['closing_day'] == 31:
        closing_day = get_last_day_of_month(year, month)
    else:
        closing_day = card['closing_day']

    print(f"    締め日: {month}月{closing_day}日")

    # 締め日より後なら次の締め期間
    if day > closing_day:
        print(f"    → 着金日{day}日 > 締日{closing_day}日 なので次の締め期間")
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
    else:
        print(f"    → 着金日{day}日 ≤ 締日{closing_day}日 なので今回の締め期間")

    # ステップ3: 支払い月を計算
    if card['payment_month_offset'] == 0:
        # 当月支払い（MIカード）
        payment_year = settlement_date.year
        payment_month = settlement_date.month
        print(f"    支払月: 当月支払い → {payment_year}年{payment_month}月")
    else:
        # 翌月支払い
        payment_month = month + card['payment_month_offset']
        payment_year = year
        if payment_month > 12:
            payment_month -= 12
            payment_year += 1
        print(f"    支払月: {year}年{month}月締め → {payment_year}年{payment_month}月支払い")

    # ステップ4: 支払い日を計算
    payment_day = card['payment_day']
    last_day = get_last_day_of_month(payment_year, payment_month)
    if payment_day > last_day:
        payment_day = last_day

    payment_date = datetime(payment_year, payment_month, payment_day)

    # ステップ5: 土日祝の後ろ倒し
    original_payment_date = payment_date
    payment_date = adjust_payment_date_for_holiday(payment_date)
    if payment_date != original_payment_date:
        print(f"    引落日（調整前）: {original_payment_date.strftime('%Y-%m-%d (%a)')} → 土日祝のため後ろ倒し")

    print(f"    引落日（確定）: {payment_date.strftime('%Y-%m-%d (%a)')}")

    return {
        'application_date': application_date,
        'settlement_date': settlement_date,
        'closing_period': f"{year}-{month:02d}",
        'payment_date': payment_date
    }

# 11/26申請の計算
print("="*100)
print("11/26申請の着金日計算（正しい前倒しルール適用）")
print("="*100)

for card_id in ['amazon', 'mi', 'toyota', 'shinkin_visa']:
    result = calculate_payment_date(card_id, '2025-11-26')

print("\n" + "="*100)
print("全申請の最適カード計算")
print("="*100)

APPLICATIONS = [
    ('2025-11-10', 'ヤマト', 1200000),
    ('2025-11-10', 'ビズビ', 74000),
    ('2025-11-16', '徐さん', 978000),
    ('2025-11-26', 'ユニホー', 258000),
    ('2025-11-26', 'ドンキ', 258000),
    ('2025-12-25', 'ヤマト', 1380000),
]

results = []
for app_date, name, amount in APPLICATIONS:
    print(f"\n{'='*100}")
    print(f"【{name} {amount:,}円】 申請日: {app_date}")
    print(f"{'='*100}")

    card_results = []
    for card_id in ['shinkin_visa', 'mi', 'toyota', 'amazon']:
        result = calculate_payment_date(card_id, app_date)
        card_results.append({
            'card_id': card_id,
            'card_name': CARDS[card_id]['name'],
            'settlement_date': result['settlement_date'],
            'payment_date': result['payment_date'],
            'available': CARDS[card_id]['available']
        })

    # 引き落とし日が遅い順にソート
    card_results.sort(key=lambda x: x['payment_date'], reverse=True)

    print(f"\n  【引き落とし日ランキング】")
    for i, cr in enumerate(card_results, 1):
        marker = "👑" if i == 1 else f"  {i}."
        available_str = f"(利用可能: {cr['available']:,}円)" if cr['available'] >= amount else f"(❌ 枠不足)"
        print(f"    {marker} {cr['card_name']:15} : {cr['payment_date'].strftime('%Y-%m-%d (%a)')} {available_str}")

    # 枠が足りる最も遅いカードを選択
    optimal = None
    for cr in card_results:
        if cr['available'] >= amount:
            optimal = cr
            break

    if optimal:
        print(f"\n  👑 最適カード: {optimal['card_name']} (引落: {optimal['payment_date'].strftime('%Y-%m-%d')})")
        results.append({
            'name': name,
            'amount': amount,
            'app_date': app_date,
            'card': optimal['card_name'],
            'card_id': optimal['card_id'],
            'settlement_date': optimal['settlement_date'],
            'payment_date': optimal['payment_date']
        })
    else:
        print(f"\n  ❌ どのカードも枠不足！")

print("\n" + "="*100)
print("最終案サマリー")
print("="*100)
for r in results:
    print(f"{r['app_date']} {r['name']:10} {r['amount']:>10,}円 → {r['card']:15} (引落: {r['payment_date'].strftime('%Y-%m-%d')})")
