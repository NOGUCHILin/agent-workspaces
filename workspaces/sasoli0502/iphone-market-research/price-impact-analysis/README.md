# 買取価格変更 効果計測システム

買取価格を変更した際の効果を計測し、最適な価格戦略を策定するためのシステムです。

---

## 🎯 目的

現在設定されている粗利・粗利率の基準値が適切かを検証する：

1. **買取数の増加**に寄与しているか
2. **粗利の最適化**ができているか
3. **機種・容量・ランク別**の最適な価格設定を発見

---

## 📊 計測内容

### 調査対象
- **不良のない端末のみ**（仮査定時に不良入力がない端末限定）
- 機種・容量・ランク別に分析

### 主要指標
- **LINE仮査定数**（不良なし端末）: 顧客が価格を見て興味を持った数
- **梱包キット数 = 集荷要請数**: 実際に端末を送付した数
- **コンバージョン率**: 梱包キット数 ÷ LINE仮査定数

### 分析期間
- **価格変更前 1週間 vs 変更後 1週間**
- 日次推移と週次集計の両方を出力

---

## 🚀 クイックスタート

### 1. 初期セットアップ

```bash
cd /Users/noguchisara/projects/work/iphone-market-research/price-impact-analysis
uv sync
```

### 2. データ準備

以下のCSVファイルを `data/raw/` 配下に配置：

#### LINE仮査定データ (`data/raw/line_estimates/`)
- ファイル名: `line_estimates_YYYYMMDD.csv`
- 形式:
```csv
日付,機種,容量,ランク,仮査定数
2025-11-12,iPhone 15 Pro,256GB,美品,25
2025-11-12,iPhone 14,128GB,使用感あり,18
```

#### 梱包キット数データ (`data/raw/packing_kits/`)
- ファイル名: `packing_kits_YYYYMMDD.csv`
- 形式:
```csv
日付,機種,容量,ランク,キット数
2025-11-12,iPhone 15 Pro,256GB,美品,15
2025-11-12,iPhone 14,128GB,使用感あり,12
```

#### 集荷要請数データ (`data/raw/pickup_requests/`)
- ファイル名: `pickup_requests_YYYYMMDD.csv`
- 形式:
```csv
日付,機種,容量,ランク,集荷数
2025-11-12,iPhone 15 Pro,256GB,美品,15
2025-11-12,iPhone 14,128GB,使用感あり,12
```

#### 価格変更履歴 (`data/price_changes/`)
- ファイル名: `price_changes.csv`
- 形式:
```csv
変更日,機種,容量,ランク,変更前価格,変更後価格,備考
2025-11-18,iPhone 15 Pro,256GB,美品,85000,90000,粗利基準見直し
2025-11-18,iPhone 14,128GB,使用感あり,45000,48000,粗利基準見直し
```

### 3. データ収集・整形

```bash
uv run python scripts/collect_data.py
```

### 4. 効果分析の実行

```bash
# 特定の価格変更日を指定して分析
uv run python scripts/analyze_impact.py --change-date 2025-11-18

# 複数の価格変更を一括分析
uv run python scripts/analyze_impact.py --all
```

### 5. レポート生成

```bash
uv run python scripts/generate_report.py --change-date 2025-11-18
```

生成されるファイル:
- `data/results/impact_report_YYYYMMDD.xlsx`

---

## 📁 ディレクトリ構成

```
price-impact-analysis/
├── README.md                      # このファイル
├── pyproject.toml                 # 依存関係
├── .gitignore                    # Git除外設定
│
├── data/                         # データファイル（Git管理外）
│   ├── raw/                      # 生データ
│   │   ├── line_estimates/       # LINE仮査定データ
│   │   ├── packing_kits/         # 梱包キット数データ
│   │   └── pickup_requests/      # 集荷要請数データ
│   ├── price_changes/            # 価格変更履歴
│   └── results/                  # 分析結果
│
└── scripts/
    ├── collect_data.py           # データ収集・整形
    ├── analyze_impact.py         # 効果分析
    └── generate_report.py        # レポート生成
```

---

## 📈 分析レポートの内容

### 1. サマリー
- 価格変更の概要
- 全体のコンバージョン率変化
- 総仮査定数・総梱包キット数の変化

### 2. 機種・容量・ランク別分析
各組み合わせについて：
- 変更前1週間の平均値（仮査定数、キット数、CV率）
- 変更後1週間の平均値（仮査定数、キット数、CV率）
- 変化率（%）
- 判定（改善/悪化/変化なし）

### 3. 日次推移グラフ
- 仮査定数の推移
- 梱包キット数の推移
- コンバージョン率の推移

### 4. 粗利への影響試算
- 価格変更による粗利額の変化
- 買取数の変化による粗利額の変化
- トータルの粗利インパクト

---

## 🔧 カスタマイズ

### 分析期間の変更

`scripts/analyze_impact.py` の設定を変更：

```python
BEFORE_DAYS = 7  # 価格変更前の分析日数（デフォルト: 7日）
AFTER_DAYS = 7   # 価格変更後の分析日数（デフォルト: 7日）
```

### 除外機種の設定

特定機種を分析から除外する場合：

```python
EXCLUDE_MODELS = ['iPhone 7', 'iPhone 8', 'iPhone 8 Plus']
```

---

## ⚠️ 注意事項

1. **不良なし端末のみ**を対象としています
2. **梱包キット数 = 集荷要請数**として扱います（両方記録されている場合は一致を確認）
3. **曜日の影響**は考慮していません（価格変更前後で同じ曜日構成を推奨）
4. データは機種・容量・ランクの**完全一致**で集計されます

---

## 📝 運用フロー

### 価格変更時
1. `data/price_changes/price_changes.csv` に変更内容を記録
2. 変更後1週間、日次でデータを収集

### 週次レビュー（価格変更後1週間経過時）
1. データ収集スクリプトを実行
2. 効果分析スクリプトを実行
3. レポートを確認
4. 必要に応じて価格戦略を調整

---

最終更新: 2025-11-19 (水)
