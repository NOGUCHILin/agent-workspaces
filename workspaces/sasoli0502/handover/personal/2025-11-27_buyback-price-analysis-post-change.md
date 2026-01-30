# セッション引き継ぎ - 買取価格分析（価格変更後データ分析）

**作成日時**: 2025-11-27 10:53 Thursday
**前回セッション**: 2025-11-25_buyback-price-research-flow-design.md
**プロジェクト**: work/iphone-market-research/

---

## 🚀 次セッション開始時に最初に読むファイル

### 1. この引き継ぎファイル
```
work/handover/personal/2025-11-27_buyback-price-analysis-post-change.md
```

### 2. 関連ファイル
- `work/iphone-market-research/scripts/recommend_base_price.py`（ソート・フォーマット・Excel出力対応済み）
- `work/iphone-market-research/scripts/analyze_buyback_data.py`（日付フィルタ機能追加済み）
- `work/iphone-market-research/scripts/simulate_new_prices.py`（Excel読み込み対応済み）

---

## 🎉 このセッションで完成したもの

### 1. ✅ 基準価格調整案のExcel出力改善

**ファイル**: `work/iphone-market-research/scripts/recommend_base_price.py`

**追加した機能**:

1. **ソート機能**:
   - 機種: 発売日が新しい順（iPhone 16 → iPhone 15 → ...）
   - 容量: 大きい順（1TB → 512GB → 256GB → ...）
   - ランク: 新品・未開封 → 新品同様 → 美品 → 使用感あり → 目立つ傷あり → 外装ジャンク

2. **フォーマット**:
   - 段階2進行率: パーセンテージ表記（例: 25.0%）
   - 成約率_段階2: パーセンテージ表記（例: 32.7%）
   - 現在平均価格: 10の位で四捨五入

3. **Excel条件付きフォーマット**:
   - 段階2進行率 >= 25% のセルを緑色のフォントで表示
   - openpyxlのFontスタイルを使用

**コード追加箇所**:
```python
from openpyxl.styles import Font, PatternFill

MODEL_ORDER = {
    "iPhone 16 Pro Max": 1, "iPhone 16 Pro": 2, ...
}
CAPACITY_ORDER = {"1TB": 1, "512GB": 2, ...}
RANK_ORDER = {"新品・未開封": 1, "新品同様": 2, ...}
```

---

### 2. ✅ 分析スクリプトに日付フィルタ機能追加

**ファイル**: `work/iphone-market-research/scripts/analyze_buyback_data.py`

**追加した機能**:
- `--after` コマンドライン引数で特定日時以降のデータのみ分析可能

**使用方法**:
```bash
# 2025/11/19 17:38:00 以降のデータのみ分析
uv run python scripts/analyze_buyback_data.py --after "2025/11/19 17:38:00"
```

**コード追加箇所**:
```python
import sys

def load_preprocessed_csv(data_dir: Path, after_datetime: str = None):
    # ...
    if after_datetime:
        df["作成日時"] = pd.to_datetime(df["作成日時"], errors="coerce")
        filter_dt = pd.to_datetime(after_datetime)
        df = df[df["作成日時"] >= filter_dt]

def main():
    after_datetime = None
    if len(sys.argv) >= 3 and sys.argv[1] == "--after":
        after_datetime = sys.argv[2]
```

---

### 3. ✅ シミュレーションスクリプトのExcel対応

**ファイル**: `work/iphone-market-research/scripts/simulate_new_prices.py`

**変更内容**:
- 基準価格調整案の読み込みをExcel形式に対応（CSVフォールバック付き）

```python
try:
    base_price_path = load_latest_file(results_dir, "base_price_recommendations_*.xlsx")
    base_price_df = pd.read_excel(base_price_path, sheet_name="基準価格調整案")
except FileNotFoundError:
    base_price_path = load_latest_file(results_dir, "base_price_recommendations_*.csv")
    base_price_df = pd.read_csv(base_price_path, encoding="utf-8-sig")
```

---

## 📊 2025/11/19 17:38:00 以降の分析結果

### データ概要
- **対象期間**: 2025/11/19 17:38:00 以降（大幅価格変更後）
- **データ件数**: 1,330件（全5,422件からフィルタ）
- **段階2進行率**: 19.8%（263件）
- **成約率**: 32.7%（86件）

### 基準価格調整案サマリー
| 調整方向 | 件数 |
|----------|------|
| 大幅増額 | 24件 |
| 小幅増額 | 7件 |
| 小幅減額 | 16件 |
| 大幅減額 | 13件 |
| 維持 | 0件 |
| 判定不可 | 268件 |

**特徴**:
- 増額提案（31件）が減額提案（29件）より多い
- 価格変更後まだ日が浅いため「判定不可」が多い（サンプル数不足）

### 減額率調整案
- **全構成が「判定不可」**（サンプル数不足）
- 価格変更後8日間では、バッテリー劣化等の不具合データが十分に蓄積されていない

### シミュレーション結果
| 施策 | 対象構成数 | 対象成約数 | 現在粗利合計 | 予測粗利合計 | 粗利変化額 |
|------|------------|------------|--------------|--------------|------------|
| 基準価格の調整 | 60件 | 67件 | 1,812,261円 | 1,908,476円 | +96,215円 (+5.3%) |

---

## 📋 確定した仕様（追加分）

### ソート順序
```python
MODEL_ORDER = {
    # 2024年発売（16シリーズ）
    "iPhone 16 Pro Max": 1,
    "iPhone 16 Pro": 2,
    "iPhone 16 Plus": 3,
    "iPhone 16": 4,
    # 2023年発売（15シリーズ）
    "iPhone 15 Pro Max": 10,
    ...
}

CAPACITY_ORDER = {"1TB": 1, "512GB": 2, "256GB": 3, "128GB": 4, "64GB": 5, "32GB": 6, "16GB": 7}

RANK_ORDER = {
    "新品・未開封": 1,  # ← 最上位
    "新品同様": 2,
    "美品": 3,
    "使用感あり": 4,
    "目立つ傷あり": 5,
    "外装ジャンク": 6,
}
```

### 分析指標の閾値
```python
# 段階2進行率の閾値
STAGE2_RATE_VERY_HIGH = 0.35  # 35%以上: 大幅減額余地
STAGE2_RATE_HIGH = 0.25       # 25%以上: 小幅減額余地
STAGE2_RATE_LOW = 0.10        # 10%以下: 小幅増額必要
STAGE2_RATE_VERY_LOW = 0.05   # 5%以下: 大幅増額必要

# 成約率の閾値（段階2からの成約率）
CONTRACT_RATE_VERY_HIGH = 0.50  # 50%以上: 大幅減額余地
CONTRACT_RATE_HIGH = 0.40       # 40%以上: 小幅減額余地
CONTRACT_RATE_LOW = 0.20        # 20%以下: 小幅増額必要
CONTRACT_RATE_VERY_LOW = 0.10   # 10%以下: 大幅増額必要
```

---

## 🔧 次にやること（優先順位順）

### 優先度1: データ蓄積を待つ
- 価格変更後8日間ではサンプル数が不足
- **推奨**: 2〜3週間後（12月上旬）に再分析
- 目安: 2,000〜3,000件程度のデータが必要

### 優先度2: 定期的な分析の自動化
- 週次で分析を実行するスクリプト/ワークフロー
- データ収集 → 前処理 → 分析 → レポート生成

### 優先度3: 減額率分析の改善
- 現在は「判定不可」が多い
- サンプル数の閾値を緩和するか、期間を延ばす

---

## 📁 出力ファイル（今回のセッションで生成）

```
work/iphone-market-research/data/results/
├── analysis_20251127.xlsx           # 分析結果（2025/11/19以降フィルタ済み）
├── base_price_recommendations_20251127.xlsx  # 基準価格調整案（ソート・フォーマット済み）
├── deduction_rate_recommendations_20251127.xlsx  # 減額率調整案（全て判定不可）
└── simulation_20251127.xlsx         # シミュレーション結果
```

---

## 🐛 解決したエラー

### ValueError: Unknown format code 'f' for object of type 'str'
**原因**: 段階2進行率が既にパーセンテージ文字列（"25.0%"）になっているのに、さらに `*100:.1f` でフォーマットしようとした

**修正前**:
```python
print(f"段階2進行率: {row['段階2進行率']*100:.1f}%")
```

**修正後**:
```python
print(f"段階2進行率: {row['段階2進行率']}")
```

---

## 📝 重要な注意事項

### 1. 価格変更日時
- **2025/11/19 17:38:00** に大幅な価格変更を実施
- この日時以前のデータは旧価格体系
- 効果測定には必ず `--after "2025/11/19 17:38:00"` オプションを使用

### 2. サンプル数の考慮
- 1構成あたり最低5件のサンプルが必要（現在の閾値）
- 価格変更後すぐは「判定不可」が多くなる
- 2〜3週間でデータが十分蓄積される

### 3. Excel出力形式
- 基準価格調整案: `.xlsx`形式（CSVではない）
- シミュレーションスクリプトもExcel読み込みに対応済み

---

## 🔗 関連スクリプト実行コマンド

```bash
# プロジェクトディレクトリ
cd /Users/noguchisara/projects/work/iphone-market-research

# 1. 前処理（きんとんCSVを指定）
uv run python scripts/preprocess_kintone_data.py kintone_YYYYMMDD.csv

# 2. 分析（日付フィルタあり）
uv run python scripts/analyze_buyback_data.py --after "2025/11/19 17:38:00"

# 3. 基準価格調整案
uv run python scripts/recommend_base_price.py

# 4. 減額率調整案
uv run python scripts/recommend_deduction_rate.py

# 5. シミュレーション
uv run python scripts/simulate_new_prices.py
```

---

## 📌 次セッションへの申し送り

### 最優先事項

1. **12月上旬に再分析を実行**
   - データが十分蓄積されたら再度分析
   - `--after "2025/11/19 17:38:00"` オプションを使用

2. **減額率分析の結果確認**
   - 現在は全て「判定不可」
   - サンプル数が増えれば有意な結果が出る可能性

### セッション開始時のチェックリスト

- [ ] この引き継ぎファイルを読む
- [ ] 現在の日付を確認（価格変更後何日経過したか）
- [ ] 最新のきんとんCSVをエクスポート
- [ ] 全スクリプトを順次実行

---

**最終更新**: 2025-11-27 10:53 Thursday
**次回セッション**: データ蓄積後（12月上旬推奨）に再分析

---

## 📋 未完了タスク

このセッションで直接は扱わなかったが、引き続き対応が必要なタスク:

【野口器単独】
1. 🔴【最重要・進行中】シン・買取価格分析（本セッションで進捗あり）
2. 【進行中】査定フローの簡略化
3. 新品バッテリー追加の上でのBM販売価格の出品価格を設定
4. 徐さんにファクタリングベースの融資提案
5. 【進行中】大和運輸に請求書の微妙な分割の申請
6. 会社のアメックスをいくら分割すべきか計算
7. Google広告の料金の支払い方法を確認して最適なものを選択
8. 動作確認時の星ねじのさび確認方法の変更
