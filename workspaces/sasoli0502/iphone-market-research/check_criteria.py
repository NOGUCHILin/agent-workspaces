import pandas as pd

# 計算基準
criteria = [
    {"range": "0~20000", "min": 0, "max": 20000, "profit": 4000, "rate_min": 20, "rate_max": 30},
    {"range": "20000~30000", "min": 20000, "max": 30000, "profit": 5000, "rate_min": 10, "rate_max": 30},
    {"range": "30000~45000", "min": 30000, "max": 45000, "profit": 6000, "rate_min": 15, "rate_max": 25},
    {"range": "45000~60000", "min": 45000, "max": 60000, "profit": 7000, "rate_min": 15, "rate_max": 25},
    {"range": "60000~90000", "min": 60000, "max": 90000, "profit": 10000, "rate_min": 11, "rate_max": 21},
    {"range": "90000~110000", "min": 90000, "max": 110000, "profit": 11000, "rate_min": 11, "rate_max": 18},
    {"range": "110000~140000", "min": 110000, "max": 140000, "profit": 14000, "rate_min": 11, "rate_max": 17},
    {"range": "140000~180000", "min": 140000, "max": 180000, "profit": 17000, "rate_min": 11, "rate_max": 16},
    {"range": "180000~224000", "min": 180000, "max": 224000, "profit": 20000, "rate_min": 10, "rate_max": 15},
]

print("=== 計算基準の整合性チェック ===\n")
print("利率 = 粗利 ÷ (売価 × 0.89) × 100\n")

for c in criteria:
    price_min = c["min"]
    price_max = c["max"]
    profit = c["profit"]

    # 理論上の利率範囲を計算
    if price_min == 0:
        # 下限が0の場合は計算不可なので、実質的な最小値を使う
        calc_rate_max = profit / (1 * 0.89) * 100  # 極端に小さい値
        calc_rate_max = "∞"
    else:
        calc_rate_max = profit / (price_min * 0.89) * 100

    calc_rate_min = profit / (price_max * 0.89) * 100

    # 基準値
    rate_min = c["rate_min"]
    rate_max = c["rate_max"]

    # 整合性チェック
    if isinstance(calc_rate_max, str):
        status = "⚠ 下限0のため要確認"
    elif calc_rate_min < rate_min or calc_rate_max > rate_max:
        status = "⚠ 不整合"
    else:
        status = "✓ OK"

    print(f"売価帯: {c['range']}")
    print(f"  粗利: {profit:,}")
    print(f"  基準利率: {rate_min}%~{rate_max}%")
    if isinstance(calc_rate_max, str):
        print(f"  理論利率: ~{calc_rate_min:.1f}%")
    else:
        print(f"  理論利率: {calc_rate_min:.1f}%~{calc_rate_max:.1f}%")
    print(f"  {status}\n")

print("\n=== 確認 ===")
print("上記の理論利率が基準利率の範囲に収まっていない場合、")
print("条件付き書式で正しく判定できない可能性があります。")
print("このまま進めてよろしいですか？")
