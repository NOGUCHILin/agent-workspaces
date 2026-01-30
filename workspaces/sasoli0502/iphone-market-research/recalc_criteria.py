import pandas as pd

# 計算基準（粗利は最低ライン）
criteria = [
    {"range": "0~20000", "min": 0, "max": 20000, "profit": 4000},
    {"range": "20000~30000", "min": 20000, "max": 30000, "profit": 5000},
    {"range": "30000~45000", "min": 30000, "max": 45000, "profit": 6000},
    {"range": "45000~60000", "min": 45000, "max": 60000, "profit": 7000},
    {"range": "60000~90000", "min": 60000, "max": 90000, "profit": 10000},
    {"range": "90000~110000", "min": 90000, "max": 110000, "profit": 11000},
    {"range": "110000~140000", "min": 110000, "max": 140000, "profit": 14000},
    {"range": "140000~180000", "min": 140000, "max": 180000, "profit": 17000},
    {"range": "180000~224000", "min": 180000, "max": 224000, "profit": 20000},
]

print("=== 利率基準の再計算 ===\n")
print("前提: 粗利の基準値 = 最低ライン\n")
print("計算方法:")
print("  - 各価格帯で粗利の最低ラインを確保したときの利率範囲を計算")
print("  - 利率 = 粗利 ÷ (売価 × 0.89) × 100\n")

results = []

for c in criteria:
    price_min = c["min"] if c["min"] > 0 else 1  # 0除算回避
    price_max = c["max"]
    profit = c["profit"]

    # 粗利が最低ライン（固定）の場合の利率範囲
    # 売価が低いほど利率が高くなる
    rate_at_min_price = profit / (price_min * 0.89) * 100
    rate_at_max_price = profit / (price_max * 0.89) * 100

    # 利率範囲（小数点以下切り捨て～切り上げで整数化）
    rate_min = int(rate_at_max_price)  # 下限
    rate_max = int(rate_at_min_price) + 1  # 上限（余裕を持たせる）

    results.append({
        "売価帯": c["range"],
        "粗利(最低)": profit,
        "利率下限": f"{rate_min}%",
        "利率上限": f"{rate_max}%",
        "理論利率": f"{rate_at_max_price:.1f}%~{rate_at_min_price:.1f}%"
    })

    print(f"売価帯: {c['range']}")
    print(f"  粗利(最低): {profit:,}円")
    print(f"  理論利率: {rate_at_max_price:.1f}%~{rate_at_min_price:.1f}%")
    print(f"  → 推奨基準: {rate_min}%~{rate_max}%\n")

# 結果を表形式で出力
df = pd.DataFrame(results)
print("\n=== 修正案サマリー ===")
print(df.to_string(index=False))

print("\n✓ この基準値で条件付き書式を設定します。")
