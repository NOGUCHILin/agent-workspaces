import pandas as pd

# 買取価格の読み込みと整形
buyback_df = pd.read_csv('買取価格20251118.csv')
print(f"買取価格 元データ行数: {len(buyback_df)}")
print(f"等級の種類: {buyback_df['等級'].unique()}")

# 新品・未開封、外装ジャンクを除外
buyback_filtered = buyback_df[~buyback_df['等級'].isin(['新品・未開封', '外装ジャンク'])].copy()
print(f"買取価格 フィルタ後行数: {len(buyback_filtered)}")

# 販売価格の読み込みと整形
sales_df = pd.read_csv('販売価格20251118.csv')
print(f"\n販売価格 元データ行数: {len(sales_df)}")
print(f"グレードの種類: {sales_df['グレード'].unique()}")

# プレミアムを除外
sales_filtered = sales_df[sales_df['グレード'] != 'プレミアム'].copy()
print(f"販売価格 フィルタ後行数: {len(sales_filtered)}")

# 保存
buyback_filtered.to_csv('買取価格_filtered.csv', index=False, encoding='utf-8-sig')
sales_filtered.to_csv('販売価格_filtered.csv', index=False, encoding='utf-8-sig')

print("\n✓ 保存完了:")
print("  - 買取価格_filtered.csv")
print("  - 販売価格_filtered.csv")
