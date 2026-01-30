import pandas as pd

# データ読み込み
buyback_df = pd.read_csv('買取価格_filtered.csv')
sales_df = pd.read_csv('販売価格_filtered.csv')

print("=== 買取価格のユニークな機種名 ===")
buyback_models = sorted(buyback_df['機体型番'].unique())
for model in buyback_models[:10]:
    print(f"  '{model}'")
print(f"  ... 他 {len(buyback_models)} 機種\n")

print("=== 販売価格のユニークな機種名 ===")
sales_models = sorted(sales_df['機種'].unique())
for model in sales_models[:10]:
    print(f"  '{model}'")
print(f"  ... 他 {len(sales_models)} 機種\n")

print("=== 買取価格のユニークな容量 ===")
buyback_capacity = sorted(buyback_df['記憶容量'].unique(), key=lambda x: str(x))
print(f"  {buyback_capacity}\n")

print("=== 販売価格のユニークな容量 ===")
sales_capacity = sorted(sales_df['容量'].unique(), key=lambda x: str(x))
print(f"  {sales_capacity}\n")

# 機種名の差異チェック
buyback_set = set(buyback_df['機体型番'].unique())
sales_set = set(sales_df['機種'].unique())

print("=== 機種名の差異 ===")
print(f"買取にあって販売にない: {buyback_set - sales_set}")
print(f"販売にあって買取にない: {sales_set - buyback_set}")

# 容量の差異チェック
buyback_cap_set = set(buyback_df['記憶容量'].unique())
sales_cap_set = set(sales_df['容量'].unique())

print("\n=== 容量の差異 ===")
print(f"買取にあって販売にない: {buyback_cap_set - sales_cap_set}")
print(f"販売にあって買取にない: {sales_cap_set - buyback_cap_set}")
