#!/usr/bin/env python3
"""
全カード（しんきんJCB、JFR含む）を考慮した最適化
11/30決済グループの枠制約を厳密にチェック
"""

from datetime import datetime, timedelta
from collections import defaultdict

HOLIDAYS = [
    '2025-11-03', '2025-11-23', '2025-11-24',
    '2025-12-23',
    '2026-01-01', '2026-01-12', '2026-02-11', '2026-02-23'
]

# 全カード情報（利用可能額を含む）
CARDS = {
    'shinkin_visa': {
        'name': 'しんきんVisa',
        'closing_day': 15,
        'payment_day': 10,
        'payment_month_offset': 1,
        'available': 1600000,
        'total_limit': 1600000
    },
    'shinkin_jcb': {
        'name': 'しんきんJCB',
        'closing_day': 15,
        'payment_day': 10,
        'payment_month_offset': 1,
        'available': 58000,
        'total_limit': 1000000
    },
    'jfr': {
        'name': 'JFR',
        'closing_day': 15,
        'payment_day': 10,
        'payment_month_offset': 1,
        'available': 0,  # 現在利用不可
        'total_limit': 1000000
    },
    'mi': {
        'name': 'MIカード',
        'closing_day': 5,
        'payment_day': 26,
        'payment_month_offset': 0,  # 当月
        'available': 722000,
        'total_limit': 1000000
    },
    'toyota': {
        'name': 'トヨタ',
        'closing_day': 5,
        'payment_day': 2,
        'payment_month_offset': 1,
        'available': 1200000,
        'total_limit': 1200000
    },
    'amazon': {
        'name': 'Amazon',
        'closing_day': 31,  # 月末
        'payment_day': 26,
        'payment_month_offset': 1,
        'available': 436000,
        'total_limit': 2000000
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

    if app_date.month == 11 and app_date.day <= 25:
        settlement = datetime(2025, 11, 30)
    elif application_date_str == '2025-11-26':
        settlement = datetime(2025, 12, 5)
    elif application_date_str == '2025-12-25':
        settlement = datetime(2025, 12, 31)
    else:
        # 通常計算は省略
        settlement = app_date + timedelta(days=4)

    return settlement

def adjust_payment_date(payment_date):
    adjusted = payment_date
    while is_holiday(adjusted):
        adjusted += timedelta(days=1)
    return adjusted

def calculate_payment_date(card_id, application_date_str):
    card = CARDS[card_id]
    settlement_date = get_settlement_date(application_date_str)

    year = settlement_date.year
    month = settlement_date.month
    day = settlement_date.day

    if card['closing_day'] == 31:
        closing_day = get_last_day_of_month(year, month)
    else:
        closing_day = card['closing_day']

    if day > closing_day:
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1

    if card['payment_month_offset'] == 0:
        payment_year = settlement_date.year
        payment_month = settlement_date.month
    else:
        payment_month = month + card['payment_month_offset']
        payment_year = year
        if payment_month > 12:
            payment_month -= 12
            payment_year += 1

    payment_day = card['payment_day']
    last_day = get_last_day_of_month(payment_year, payment_month)
    if payment_day > last_day:
        payment_day = last_day

    payment_date = datetime(payment_year, payment_month, payment_day)
    payment_date = adjust_payment_date(payment_date)

    return {
        'settlement_date': settlement_date,
        'payment_date': payment_date
    }

# 11/30決済グループ（同時決済される申請）
NOVEMBER_30_GROUP = [
    ('2025-11-10', 'ヤマト', 1200000),
    ('2025-11-10', 'ビズビ', 74000),
    ('2025-11-16', '徐さん', 978000),
    ('2025-11-25', 'ドンキ', 258000),  # ドンキは11/25申請（月末着金）
]

print("="*100)
print("【11/30決済グループの枠制約分析】")
print("="*100)

total_amount = sum(amount for _, _, amount in NOVEMBER_30_GROUP)
print(f"\n合計必要額: {total_amount:,}円")

print("\n利用可能カードと枠:")
available_cards = {card_id: card for card_id, card in CARDS.items() if card['available'] > 0}
total_available = sum(card['available'] for card in available_cards.values())

for card_id, card in available_cards.items():
    print(f"  {card['name']:15} : {card['available']:>10,}円")
print(f"  {'合計':15} : {total_available:>10,}円")

if total_available >= total_amount:
    print(f"\n✅ 合計枠は足りています（余裕: {total_available - total_amount:,}円）")
else:
    print(f"\n❌ 合計枠が不足しています（不足: {total_amount - total_available:,}円）")

print("\n" + "="*100)
print("【各申請に対する各カードの引き落とし日】")
print("="*100)

# 各申請について各カードでの引き落とし日を計算
for app_date, name, amount in NOVEMBER_30_GROUP:
    print(f"\n【{name} {amount:,}円】（申請日: {app_date}）")

    card_results = []
    for card_id in available_cards.keys():
        result = calculate_payment_date(card_id, app_date)
        card_results.append({
            'card_id': card_id,
            'card_name': CARDS[card_id]['name'],
            'payment_date': result['payment_date'],
            'available': CARDS[card_id]['available']
        })

    # 引き落とし日が遅い順
    card_results.sort(key=lambda x: x['payment_date'], reverse=True)

    for i, cr in enumerate(card_results, 1):
        marker = "👑" if i == 1 else f"  {i}."
        ok = "✅" if cr['available'] >= amount else "❌"
        print(f"  {marker} {cr['card_name']:15} : {cr['payment_date'].strftime('%Y-%m-%d')} ({ok} {cr['available']:,}円)")

print("\n" + "="*100)
print("【制約を考慮した最適化案】")
print("="*100)

print("\n制約:")
print("  1. ヤマト120万は分割不可")
print("  2. 徐さん97.8万は分割可能")
print("  3. しんきんVisaは12/31のヤマト138万用に温存したい")
print("  4. 11/30決済グループは同時に枠を占有する")

print("\n分析:")
print("  - トヨタ: 120万の枠 → ヤマト120万で丁度")
print("  - しんきんVisa: 160万の枠 → 12/31ヤマト138万用に温存するなら22万まで")
print("  - しんきんJCB: 5.8万の枠（見落としていた！）")
print("  - Amazon: 43.6万の枠")
print("  - MIカード: 72.2万の枠")

print("\n提案1: しんきんVisaを温存しない場合")
print("  ヤマト120万 → トヨタ")
print("  ビズビ7.4万 → MIカード")
print("  徐さん97.8万 → しんきんVisa 97.8万（OK）")
print("  ドンキ25.8万 → Amazon")
print("  合計: 120 + 7.4 + 97.8 + 25.8 = 251万")
print("  → ✅ 各カードの枠内に収まる")
print("  → ❌ しかし、12/31のヤマト138万はどこで払う？")

print("\n提案2: しんきんVisaを温存する場合（22万まで）")
print("  ヤマト120万 → トヨタ")
print("  ビズビ7.4万 → MIカード")
print("  ドンキ25.8万 → Amazon")
print("  徐さん97.8万を分割:")
print("    - しんきんVisa: 22万（残り138万枠を12/31用に確保）")
print("    - しんきんJCB: 5.8万")
print("    - MIカード: 64.8万（7.4万使用後、残り64.8万）")
print("    - Amazon: 18万（25.8万使用後、残り17.8万）→ ❌枠不足")

print("\n提案3: Amazonとドンキの配置を変更")
print("  ヤマト120万 → トヨタ")
print("  ビズビ7.4万 → しんきんJCB 5.8万 + MIカード 1.6万")
print("  ドンキ25.8万 → MIカード（1.6万使用後、残り70.6万）→ ❌枠不足")

print("\n提案4: 徐さんを4分割")
print("  ヤマト120万 → トヨタ（120万/120万）")
print("  ビズビ7.4万 → MIカード（7.4万/72.2万）")
print("  ドンキ25.8万 → Amazon（25.8万/43.6万）")
print("  徐さん97.8万を分割:")
print("    - しんきんVisa: 22万（22万/160万、残138万を12/31用に確保）")
print("    - しんきんJCB: 5.8万（5.8万/5.8万）")
print("    - MIカード: 64.8万（7.4万+64.8万=72.2万/72.2万）")
print("    - Amazon: 5.2万（25.8万+5.2万=31万/43.6万）")
print("  合計: 22 + 5.8 + 64.8 + 5.2 = 97.8万 ✅")
print("\n  各カードの使用状況:")
print("    - トヨタ: 120万/120万（100%）")
print("    - MIカード: 72.2万/72.2万（100%）")
print("    - Amazon: 31万/43.6万（71%）")
print("    - しんきんVisa: 22万/160万（14%）")
print("    - しんきんJCB: 5.8万/5.8万（100%）")

print("\n" + "="*100)
print("【12/05決済（ユニホー25.8万）の問題】")
print("="*100)

print("\n11/30決済後の各カードの状態（引き落とし前）:")
print("  - トヨタ: 120万占有 → 利用可能0円（引落: 2026-01-02）")
print("  - MIカード: 72.2万占有 → 利用可能0円（引落: 2025-11-26 ← 11/30より前！）")
print("    ⚠️ MIカードは当月払いなので、11/26引落後は枠が復活する？")
print("  - Amazon: 31万占有 → 利用可能12.6万（引落: 2025-12-26）")
print("  - しんきんVisa: 22万占有 → 利用可能138万（引落: 2026-01-13）")
print("  - しんきんJCB: 5.8万占有 → 利用可能0円（引落: 2026-01-13）")

print("\n12/05時点でユニホー25.8万を払えるカード:")
print("  ❌ トヨタ: 0円")
print("  ❓ MIカード: 11/26に引落があれば72.2万復活 → 払える可能性あり")
print("  ❌ Amazon: 12.6万（不足）")
print("  ⚠️ しんきんVisa: 138万（払えるが、12/31のヤマト138万が払えなくなる）")
print("  ❌ しんきんJCB: 0円")

print("\n🔍 MIカードの引き落としタイミングを確認:")
mi_result_nov30 = calculate_payment_date('mi', '2025-11-10')
print(f"  11/10申請（11/30決済）→ MIカード引落日: {mi_result_nov30['payment_date'].strftime('%Y-%m-%d')}")
print("  → 2025-11-26に引き落とし")
print("  → 11/26引落 < 12/05決済 なので、12/05時点では枠が復活している！")
print("  → ✅ MIカードで12/05のユニホー25.8万が払える可能性あり")

mi_result_dec05 = calculate_payment_date('mi', '2025-11-26')
print(f"\n  12/05決済のMIカード引落日: {mi_result_dec05['payment_date'].strftime('%Y-%m-%d')}")

print("\n" + "="*100)
print("【最終案: MIカードの引き落としタイミングを活用】")
print("="*100)

print("\n11/30決済グループ:")
print("  ヤマト120万 → トヨタ（引落: 2026-01-02）")
print("  ビズビ7.4万 → MIカード（引落: 2025-11-26）")
print("  ドンキ25.8万 → Amazon（引落: 2025-12-26）")
print("  徐さん97.8万を分割:")
print("    - しんきんVisa: 22万（引落: 2026-01-13）")
print("    - しんきんJCB: 5.8万（引落: 2026-01-13）")
print("    - MIカード: 64.8万（引落: 2025-11-26）")
print("    - Amazon: 5.2万（引落: 2025-12-26）")

print("\n12/05決済:")
print("  ユニホー25.8万 → MIカード（引落: 2025-12-26）")
print("    ※ 11/26にビズビ7.4万+徐さん64.8万=72.2万が引き落とされるので、")
print("    　12/05時点では枠が復活している")

print("\n12/31決済:")
print("  ヤマト138万 → しんきんVisa（引落: 2026-02-10）")
print("    ※ 11/30決済の22万は2026-01-13引落なので、12/31時点では占有中")
print("    　しかし、160万 - 22万 = 138万の枠があるので払える")

print("\n" + "="*100)
print("【タイムライン検証】")
print("="*100)

events = []

# 11/30決済グループ
events.append(('2025-11-30', 'settlement', 'トヨタ', 1200000, '2026-01-02'))
events.append(('2025-11-30', 'settlement', 'MIカード', 72000, '2025-11-26'))  # ビズビ7.4万
events.append(('2025-11-30', 'settlement', 'MIカード', 648000, '2025-11-26'))  # 徐さん64.8万
events.append(('2025-11-30', 'settlement', 'Amazon', 258000, '2025-12-26'))  # ドンキ25.8万
events.append(('2025-11-30', 'settlement', 'Amazon', 52000, '2025-12-26'))  # 徐さん5.2万
events.append(('2025-11-30', 'settlement', 'しんきんVisa', 220000, '2026-01-13'))  # 徐さん22万
events.append(('2025-11-30', 'settlement', 'しんきんJCB', 58000, '2026-01-13'))  # 徐さん5.8万

# 引き落とし
events.append(('2025-11-26', 'payment', 'MIカード', 720000, None))  # ビズビ+徐さん

# 12/05決済
events.append(('2025-12-05', 'settlement', 'MIカード', 258000, '2025-12-26'))  # ユニホー25.8万

# 引き落とし
events.append(('2025-12-26', 'payment', 'Amazon', 310000, None))  # ドンキ+徐さん
events.append(('2025-12-26', 'payment', 'MIカード', 258000, None))  # ユニホー

# 12/31決済
events.append(('2025-12-31', 'settlement', 'しんきんVisa', 1380000, '2026-02-10'))

events.sort(key=lambda x: x[0])

card_status = {
    'トヨタ': CARDS['toyota']['available'],
    'MIカード': CARDS['mi']['available'],
    'Amazon': CARDS['amazon']['available'],
    'しんきんVisa': CARDS['shinkin_visa']['available'],
    'しんきんJCB': CARDS['shinkin_jcb']['available'],
}

print(f"\n{'日付':<12} {'種別':<10} {'カード':<15} {'金額':>12} {'利用可能額':<30}")
print("-" * 100)

all_ok = True

for date_str, event_type, card_name, amount, payment_date in events:
    if event_type == 'settlement':
        # 決済時
        if card_status[card_name] < amount:
            status_str = f"❌ 枠不足！ {card_status[card_name]:,}円 < {amount:,}円"
            all_ok = False
        else:
            card_status[card_name] -= amount
            status_str = f"→ {card_status[card_name]:,}円"

        print(f"{date_str:<12} {'決済':<10} {card_name:<15} {amount:>12,} {status_str:<30}")

    elif event_type == 'payment':
        # 引き落とし時
        card_status[card_name] += amount
        status_str = f"→ {card_status[card_name]:,}円"
        print(f"{date_str:<12} {'引落':<10} {card_name:<15} {amount:>12,} {status_str:<30}")

print("\n" + "="*100)
if all_ok:
    print("✅ 全ての決済が問題なく処理できます！")
else:
    print("❌ 枠不足が発生しました")
print("="*100)
