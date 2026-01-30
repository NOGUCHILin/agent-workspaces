"""
買取価格の高額買取と特急買取の差額パターンを分析するスクリプト
"""
import pandas as pd
import numpy as np

# データ読み込み
df = pd.read_csv('買取価格20251119.csv')

# 差額を計算
df['価格差'] = df['高額買取価格'] - df['特急買取価格']
df['差額率'] = (df['価格差'] / df['高額買取価格'] * 100).round(2)

# 販売価格データも読み込み（販売価格帯との関連を確認）
# 等級のマッピング
grade_mapping = {
    '新品・未開封': 'プレミアム',
    '新品同様': 'A',
    '美品': 'B',
    '使用感あり': 'C',
    '目立つ傷あり': 'C',
    '外装ジャンク': 'C'
}

df['グレード'] = df['等級'].map(grade_mapping)

# 販売価格データを読み込み
try:
    sales_df = pd.read_csv('販売価格20251118.csv')
    # 機種・容量・グレードでマージ
    df = df.merge(
        sales_df[['機種', '容量', 'グレード', '平均売価']],
        left_on=['機体型番', '記憶容量', 'グレード'],
        right_on=['機種', '容量', 'グレード'],
        how='left'
    )
    df = df.drop(['機種', '容量', 'グレード'], axis=1)
except Exception as e:
    print(f"販売価格データの読み込みエラー: {e}")
    df['平均売価'] = None

# 高額買取価格の価格帯を作成（10,000円単位）
df['高額買取価格帯'] = (df['高額買取価格'] // 10000) * 10000

# 価格帯ごとの統計
price_range_stats = df.groupby('高額買取価格帯').agg({
    '価格差': ['min', 'max', 'mean', 'median', 'std', 'count'],
    '差額率': ['min', 'max', 'mean', 'median']
}).round(0)

print("=" * 80)
print("【価格帯別の差額統計】")
print("=" * 80)
print(price_range_stats)
print()

# 等級別の統計
grade_stats = df.groupby('等級').agg({
    '価格差': ['min', 'max', 'mean', 'median', 'count'],
    '差額率': ['min', 'max', 'mean', 'median'],
    '高額買取価格': ['min', 'max', 'mean']
}).round(0)

print("=" * 80)
print("【等級別の差額統計】")
print("=" * 80)
print(grade_stats)
print()

# 差額のユニークな値を確認
unique_diffs = sorted(df['価格差'].unique())
print("=" * 80)
print(f"【差額のユニークな値（{len(unique_diffs)}種類）】")
print("=" * 80)
print(unique_diffs)
print()

# 差額ごとの件数と価格帯
diff_distribution = df.groupby('価格差').agg({
    '高額買取価格': ['count', 'min', 'max', 'mean']
}).round(0)
diff_distribution = diff_distribution.sort_index(ascending=False)

print("=" * 80)
print("【差額ごとの分布】")
print("=" * 80)
print(diff_distribution.head(30))
print()

# 高額買取価格と差額の関係を詳細に分析
print("=" * 80)
print("【高額買取価格と差額の関係（詳細）】")
print("=" * 80)

# 価格帯を細かく区切って分析
price_bins = [0, 20000, 50000, 80000, 100000, 120000, 150000, 200000, 300000, 400000]
df['価格帯'] = pd.cut(df['高額買取価格'], bins=price_bins, include_lowest=True)

price_band_analysis = df.groupby('価格帯').agg({
    '価格差': ['min', 'max', 'mean', 'median'],
    '差額率': ['min', 'max', 'mean'],
    '高額買取価格': 'count'
}).round(2)

print(price_band_analysis)
print()

# 差額の頻度分布
print("=" * 80)
print("【差額の頻度分布（上位30）】")
print("=" * 80)
diff_counts = df['価格差'].value_counts().sort_index(ascending=False).head(30)
for diff, count in diff_counts.items():
    avg_price = df[df['価格差'] == diff]['高額買取価格'].mean()
    print(f"差額 {int(diff):>6,}円: {count:>3}件（平均高額買取価格: {int(avg_price):>9,}円）")
print()

# 外れ値を除外して、主要なパターンを確認
# 新品・未開封は特殊なので除外
normal_df = df[~df['等級'].isin(['新品・未開封', '外装ジャンク'])]

print("=" * 80)
print("【通常品（新品・未開封、外装ジャンク除く）の差額パターン】")
print("=" * 80)

normal_price_stats = normal_df.groupby('高額買取価格帯').agg({
    '価格差': ['min', 'max', 'mean', 'median', 'count']
}).round(0)

print(normal_price_stats.head(40))
print()

# 回帰分析で傾向を確認
from scipy import stats

# 外れ値を除外
normal_for_regression = normal_df[normal_df['価格差'] > 0].copy()

if len(normal_for_regression) > 0:
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        normal_for_regression['高額買取価格'],
        normal_for_regression['価格差']
    )

    print("=" * 80)
    print("【線形回帰分析結果（通常品）】")
    print("=" * 80)
    print(f"傾き（価格上昇に対する差額の増加率）: {slope:.6f}")
    print(f"切片: {intercept:.2f}")
    print(f"決定係数（R²）: {r_value**2:.4f}")
    print(f"p値: {p_value:.6f}")
    print()
    print("【予測式】")
    print(f"差額 = {slope:.6f} × 高額買取価格 + {intercept:.2f}")
    print()

    # 実際の差額と予測差額を比較
    normal_for_regression['予測差額'] = (
        slope * normal_for_regression['高額買取価格'] + intercept
    ).round(0)
    normal_for_regression['誤差'] = (
        normal_for_regression['価格差'] - normal_for_regression['予測差額']
    ).abs()

    print("=" * 80)
    print("【予測精度サンプル（誤差が小さい順）】")
    print("=" * 80)
    sample = normal_for_regression.nsmallest(20, '誤差')[
        ['機体型番', '記憶容量', '等級', '高額買取価格', '特急買取価格',
         '価格差', '予測差額', '誤差']
    ]
    print(sample.to_string(index=False))
    print()

    print("=" * 80)
    print("【予測精度サンプル（誤差が大きい順）】")
    print("=" * 80)
    sample = normal_for_regression.nlargest(20, '誤差')[
        ['機体型番', '記憶容量', '等級', '高額買取価格', '特急買取価格',
         '価格差', '予測差額', '誤差']
    ]
    print(sample.to_string(index=False))
    print()

# CSVとして保存
output_df = df.copy()
output_df = output_df.sort_values(['高額買取価格'], ascending=False)
output_df.to_csv('買取価格差額分析.csv', index=False, encoding='utf-8-sig')
print("分析結果を '買取価格差額分析.csv' に保存しました")
