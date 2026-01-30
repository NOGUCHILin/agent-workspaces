#!/usr/bin/env python3
"""
請求書払いのカード選択が最適かチェックするスクリプト
"""

from datetime import datetime, timedelta

# カード情報
CARDS = {
    'amazon': {
        'name': 'Amazon Mastercard',
        'closing_day': 31,  # 月末
        'payment_day': 26,
        'payment_month_offset': 1,
        'application_days': 4
    },
    'mi': {
        'name': 'MIカード',
        'closing_day': 5,
        'payment_day': 26,
        'payment_month_offset': 0,  # 当月
        'application_days': 4
    },
    'toyota': {
        'name': 'トヨタファイナンス',
        'closing_day': 5,
        'payment_day': 2,
        'payment_month_offset': 1,
        'application_days': 4
    },
    'shinkin_visa': {
        'name': 'しんきんVisa',
        'closing_day': 15,
        'payment_day': 10,
        'payment_month_offset': 1,
        'application_days': 4
    },
    'shinkin_jcb': {
        'name': 'しんきんJCB',
        'closing_day': 15,
        'payment_day': 10,
        'payment_month_offset': 1,
        'application_days': 4
    },
    'jfr': {
        'name': 'JFR（大丸）',
        'closing_day': 15,
        'payment_day': 10,
        'payment_month_offset': 1,
        'application_days': 4
    }
}

# 祝日リスト（2025年、2026年）
HOLIDAYS = [
    '2025-01-01', '2025-01-13', '2025-02-11', '2025-02-23', '2025-02-24',
    '2025-03-20', '2025-04-29', '2025-05-03', '2025-05-04', '2025-05-05',
    '2025-05-06', '2025-07-21', '2025-08-11', '2025-09-15', '2025-09-23',
    '2025-10-13', '2025-11-03', '2025-11-23', '2025-11-24',
    '2025-12-23',
    '2026-01-01', '2026-01-12', '2026-02-11', '2026-02-23',
    '2026-03-20', '2026-04-29', '2026-05-03', '2026-05-04', '2026-05-05',
    '2026-05-06', '2026-07-20', '2026-08-11', '2026-09-21', '2026-09-22',
    '2026-10-12', '2026-11-03', '2026-11-23'
]

def is_holiday(date):
    """土日祝日判定"""
    if date.weekday() in [5, 6]:  # 土日
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
    """引き落とし日を計算"""
    card = CARDS[card_id]
    application_date = datetime.strptime(application_date_str, '%Y-%m-%d')

    # 着金日を計算（申請日 + 4営業日）
    arrival_date = add_business_days(application_date, card['application_days'])

    # 締め日判定
    year = arrival_date.year
    month = arrival_date.month

    # 月末締めの場合
    if card['closing_day'] == 31:
        closing_day = get_last_day_of_month(year, month)
    else:
        closing_day = card['closing_day']

    # 着金日が締め日より後なら次の締め期間
    if arrival_date.day > closing_day:
        # 次の月の締めに回る
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1

    # 支払い月を計算
    payment_month = month + card['payment_month_offset']
    payment_year = year
    if payment_month > 12:
        payment_month -= 12
        payment_year += 1

    # 支払い日を計算
    payment_day = card['payment_day']
    if payment_day > get_last_day_of_month(payment_year, payment_month):
        payment_day = get_last_day_of_month(payment_year, payment_month)

    payment_date = datetime(payment_year, payment_month, payment_day)

    # 土日祝の後ろ倒し
    while is_holiday(payment_date):
        payment_date += timedelta(days=1)

    return payment_date

def check_optimal_card(application_date_str, current_card_id, payment_name):
    """最適なカードをチェック"""
    print(f"\n{'='*80}")
    print(f"【{payment_name}】申請日: {application_date_str}")
    print(f"  現在の選択: {CARDS[current_card_id]['name']}")
    print(f"{'='*80}")

    results = []
    for card_id, card in CARDS.items():
        payment_date = calculate_payment_date(card_id, application_date_str)
        results.append({
            'card_id': card_id,
            'card_name': card['name'],
            'payment_date': payment_date
        })

    # 引き落とし日が遅い順にソート
    results.sort(key=lambda x: x['payment_date'], reverse=True)

    # 結果表示
    for i, result in enumerate(results):
        marker = "👑" if i == 0 else "  "
        current_marker = "← 現在の選択" if result['card_id'] == current_card_id else ""
        print(f"{marker} {result['card_name']:20} : {result['payment_date'].strftime('%Y-%m-%d (%a)')} {current_marker}")

    # 判定
    optimal_card = results[0]
    if optimal_card['card_id'] == current_card_id:
        print(f"\n✅ OK: 現在の選択（{CARDS[current_card_id]['name']}）が最適です！")
    else:
        days_diff = (optimal_card['payment_date'] - calculate_payment_date(current_card_id, application_date_str)).days
        print(f"\n⚠️  WARNING: {optimal_card['card_name']} の方が {days_diff}日 遅くなります！")
        print(f"   現在: {calculate_payment_date(current_card_id, application_date_str).strftime('%Y-%m-%d')}")
        print(f"   最適: {optimal_card['payment_date'].strftime('%Y-%m-%d')}")

    return optimal_card['card_id'] == current_card_id

# 請求書払いデータ
INVOICE_PAYMENTS = [
    ('2025-11-10', 'shinkin_visa', 'ヤマト 1,165,205円'),
    ('2025-11-10', 'amazon', 'ビズビ 71,504円'),
    ('2025-11-16', 'toyota', '徐さん 949,400円'),
    ('2025-11-26', 'toyota', 'ユニホー 250,000円'),
    ('2025-11-26', 'toyota', 'ドンキ 250,000円'),
    ('2025-12-25', None, 'ヤマト 1,339,710円（カード未定）'),
]

print("="*80)
print("請求書払いカード選択の整合性チェック")
print("="*80)

all_ok = True
for application_date, card_id, payment_name in INVOICE_PAYMENTS:
    if card_id is None:
        print(f"\n{'='*80}")
        print(f"【{payment_name}】申請日: {application_date}")
        print(f"  現在の選択: カード未定")
        print(f"{'='*80}")

        results = []
        for cid, card in CARDS.items():
            payment_date = calculate_payment_date(cid, application_date)
            results.append({
                'card_id': cid,
                'card_name': card['name'],
                'payment_date': payment_date
            })

        results.sort(key=lambda x: x['payment_date'], reverse=True)

        print("\n推奨カード（引き落としが遅い順）:")
        for i, result in enumerate(results[:3]):
            marker = "👑" if i == 0 else f"{i+1}."
            print(f"{marker} {result['card_name']:20} : {result['payment_date'].strftime('%Y-%m-%d (%a)')}")

        print(f"\n💡 推奨: {results[0]['card_name']} （{results[0]['payment_date'].strftime('%Y-%m-%d')} 引き落とし）")
    else:
        is_ok = check_optimal_card(application_date, card_id, payment_name)
        if not is_ok:
            all_ok = False

print("\n" + "="*80)
if all_ok:
    print("✅ 全ての選択が最適です！")
else:
    print("⚠️  一部のカード選択が最適ではありません。上記の推奨を確認してください。")
print("="*80)
