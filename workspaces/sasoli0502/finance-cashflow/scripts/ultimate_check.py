#!/usr/bin/env python3
"""
究極の矛盾チェック - 前倒しルール含む全ルール適用
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
    'shinkin_jcb': {
        'name': 'しんきんJCB',
        'closing_day': 15,
        'payment_day': 10,
        'payment_month_offset': 1,
        'available': 58000
    },
    'jfr': {
        'name': 'JFR',
        'closing_day': 15,
        'payment_day': 10,
        'payment_month_offset': 1,
        'available': 0
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

def add_business_days_with_forward_adjustment(start_date, days):
    """
    営業日を加算（月末・年末が土日祝の場合は前倒し）
    """
    current = start_date
    added = 0

    while added < days:
        current += timedelta(days=1)
        if not is_holiday(current):
            added += 1

    # 月末または年末の場合、土日祝なら前倒し
    if current.day >= 28:  # 月末付近
        last_day = get_last_day_of_month(current.year, current.month)
        if current.day == last_day and is_holiday(current):
            # 前の営業日に前倒し
            while is_holiday(current):
                current -= timedelta(days=1)
            print(f"    ⚠️  月末が土日祝のため前倒し: {current.strftime('%Y-%m-%d (%a)')}")

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
    """引き落とし日を計算（前倒しルール含む）"""
    card = CARDS[card_id]
    application_date = datetime.strptime(application_date_str, '%Y-%m-%d')

    print(f"\n  【{card['name']}】申請日: {application_date_str}")

    # ステップ1: 着金日（決済日）を計算（前倒しルール適用）
    settlement_date = add_business_days_with_forward_adjustment(application_date, 4)
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

# 申請データ
APPLICATIONS = [
    ('2025-11-10', 'ヤマト', 1200000),
    ('2025-11-10', 'ビズビ', 74000),
    ('2025-11-16', '徐さん', 978000),
    ('2025-11-26', 'ユニホー', 258000),
    ('2025-11-26', 'ドンキ', 258000),
    ('2025-12-25', 'ヤマト', 1380000),
]

print("="*100)
print("全申請について、全カードでの引き落とし日を計算")
print("="*100)

# 各申請について、全カードでの引き落とし日を計算
results = []
for app_date, name, amount in APPLICATIONS:
    print(f"\n{'='*100}")
    print(f"【{name} {amount:,}円】 申請日: {app_date}")
    print(f"{'='*100}")

    card_results = []
    for card_id in ['shinkin_visa', 'shinkin_jcb', 'jfr', 'mi', 'toyota', 'amazon']:
        card = CARDS[card_id]
        # 請求書払い不可のカードはスキップ
        if card_id in ['amazon', 'mi', 'toyota', 'shinkin_visa', 'shinkin_jcb', 'jfr']:
            result = calculate_payment_date(card_id, app_date)
            card_results.append({
                'card_id': card_id,
                'card_name': card['name'],
                'settlement_date': result['settlement_date'],
                'payment_date': result['payment_date'],
                'available': card['available']
            })

    # 引き落とし日が遅い順にソート
    card_results.sort(key=lambda x: x['payment_date'], reverse=True)

    print(f"\n  【引き落とし日ランキング】")
    for i, cr in enumerate(card_results, 1):
        marker = "👑" if i == 1 else f"  {i}."
        available_str = f"(利用可能: {cr['available']:,}円)" if cr['available'] >= amount else f"(❌ 枠不足)"
        print(f"    {marker} {cr['card_name']:15} : {cr['payment_date'].strftime('%Y-%m-%d (%a)')} {available_str}")

    results.append({
        'name': name,
        'amount': amount,
        'application_date': app_date,
        'card_results': card_results
    })

print("\n" + "="*100)
print("最適カードの選択（枠も考慮）")
print("="*100)

for r in results:
    print(f"\n【{r['name']}】{r['amount']:,}円 (申請日: {r['application_date']})")
    # 枠が足りるカードで最も遅いものを選択
    for cr in r['card_results']:
        if cr['available'] >= r['amount']:
            print(f"  👑 推奨: {cr['card_name']} (引落: {cr['payment_date'].strftime('%Y-%m-%d')})")
            break
    else:
        print(f"  ❌ どのカードも枠不足！")
