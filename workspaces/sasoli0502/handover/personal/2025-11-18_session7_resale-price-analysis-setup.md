# セッション7引き継ぎ - 販売価格分析プロジェクトのセットアップ完了

**作成日時**: 2025-11-18 14:56 Tuesday
**前回セッション**: [2025-11-17_session6_resale-price-normalization-prep.md](./2025-11-17_session6_resale-price-normalization-prep.md)
**プロジェクト**: work/iphone-market-research/resale-market/
**目標**: 競合他社の販売価格を分析し、弊社の最適販売価格を決定する

---

## 🚀 次セッション開始時に最初に読むファイル

### 1. この引き継ぎファイル
```
work/handover/personal/2025-11-18_session7_resale-price-analysis-setup.md
```

### 2. 関連ドキュメント
- `work/iphone-market-research/resale-market/README.md`（プロジェクト概要）
- `work/iphone-market-research/resale-market/CLAUDE.md`（詳細仕様）

---

## 📊 このセッションで完了したこと

### ✅ 1. プロジェクト目標の明確化

**目的**: 競合他社の販売価格を分析し、弊社の販売価格設定の参考にする

**分析軸**:
- **機種**（例：iPhone 15 Pro）
- **容量**（例：256GB）
- **販売ランク**（**A/B/Cのみ**、S・プレミアム・D・ジャンク除外）

**対象サイト（上位5社）**:
1. **ゲオオンライン**（売上高356億円、市場シェア1位）
2. **イオシス**（売上高100億円超、在庫1万台）
3. **じゃんぱら**（ソフマップグループ、全国52店舗）
4. **楽天市場**（複数業者、データ収集済み）
5. **弊社（バックマーケット）**（弊社販売価格として扱う）

---

### ✅ 2. 各サイトのランク定義調査完了

| ランク | イオシス | じゃんぱら | ゲオオンライン | 弊社（バックマーケット） |
|--------|---------|-----------|---------------|------------------------|
| **S/プレミアム** | 未使用品 | 未使用品 | 状態S（未使用品） | プレミアム |
| **A** | 傷が少ない美品 | 美品・ほぼ新品同様 | 液晶・外装にほとんど傷なし | 目立つ傷なし |
| **B** | 使用感あり・目立つ傷なし | 小傷あり・機能問題なし | 薄い傷あり・塗装剥げあり | 使用感あり |
| **C** | 目立つ傷・ひび割れ | 傷汚れ目立つ・動作OK | ❌（設定なし） | 傷・汚れ目立つ |
| **D/ジャンク** | ❌（設定なし） | 外観・動作に問題あり | ❌（設定なし） | ❌（除外） |

**重要**:
- ゲオはS/A/Bの3段階のみ（Cなし）
- **分析対象ランク**: **A/B/Cのみ**（S・プレミアム・D・ジャンク除外）

---

### ✅ 3. 楽天データからD・ジャンク除外完了

**実行スクリプト**: [scripts/clean_junk_data.py](../../../work/iphone-market-research/resale-market/scripts/clean_junk_data.py)

**実行結果**:
- 総商品数: 9,735件
- 削除件数: 266件（2.7%）
- 残り件数: 9,469件（97.3%）
- ジャンク含有ファイル: 54/84ファイル

**削除パターン**:
- 「ジャンク」表記
- Dランク
- 「故障」「動作不良」「画面割れ」「水没」などの不具合商品

---

### ✅ 4. 弊社販売価格CSVの確認完了

**ファイルパス**: `data/company/backmarket_prices.csv`

**データ構造**:
```csv
機種,容量,グレード,平均売価
iPhone 15 Pro,256GB,A,119682
iPhone 15 Pro,256GB,B,114725
iPhone 15 Pro,256GB,C,108331
```

**統計**:
- 総レコード数: 424行
- 機種数: 34種類（iPhone X〜iPhone 17シリーズ）
- 容量: 64GB, 128GB, 256GB, 512GB, 1TB, 2TB
- **グレード**: プレミアム, A, B, C（**分析対象: A/B/Cのみ**）

---

### ✅ 5. Playwrightブラウザインストール完了

スクレイパー実行の準備が整いました。

```bash
uv run playwright install chromium
```

---

## 📂 プロジェクト構成（現在）

```
work/iphone-market-research/resale-market/
├── CLAUDE.md                    # プロジェクト詳細仕様
├── README.md                    # 使い方ガイド
├── 次セッションへの引き継ぎ.md   # 2025-11-06の初期引き継ぎ
├── pyproject.toml               # uv依存関係管理
├── data/                        # Git管理外
│   ├── raw/
│   │   └── rakuten/            # 楽天84ファイル（ジャンク除外済み9,469件）
│   ├── company/                # 🆕 弊社データ
│   │   └── backmarket_prices.csv  # 弊社販売価格（424行）
│   └── resale/                 # 他サイトデータ（未収集）
├── scripts/                    # 21スクリプト
│   ├── models.py               # 86モデル定義
│   ├── config.py               # API設定
│   ├── clean_junk_data.py      # 🆕 D・ジャンク除外スクリプト
│   ├── scraper_rakuten.py      # 楽天スクレイパー（✅動作確認済み）
│   ├── scraper_resale_geo.py   # ゲオスクレイパー（未検証）
│   ├── scraper_resale_iosys_v2.py  # イオシススクレイパー（未検証）
│   ├── scraper_resale_janpara_v2.py  # じゃんぱらスクレイパー（未検証）
│   ├── collect_all.py          # 一括収集
│   ├── analyze.py              # 販売価格分析（ランク別対応必要）
│   └── analyze_buyback_margin.py  # 買取粗利分析
└── reports/                    # 分析結果
    ├── iphone_price_report_20251113_154452.xlsx  # 最新販売価格（ランク別未対応）
    └── buyback_margin_analysis_20251113_165017.xlsx  # 買取粗利

```

---

## 🎯 次セッションでやること（優先順位順）

### 優先度1: ランク別分析レポート実装（推定1-2時間）

**目的**: 楽天データからA/B/Cランク別の価格統計を生成

**タスク**:
1. `scripts/analyze.py`の修正
   - ランク抽出ロジックの強化
   - A/B/Cのみフィルタリング（S・プレミアム・D・ジャンク除外）
   - 機種×容量×ランクの3軸集計

2. 弊社価格との比較分析スクリプト作成
   - `scripts/compare_prices.py`（新規作成）
   - 弊社価格 vs 楽天平均価格
   - 価格差（円・%）の計算
   - 推奨販売価格の算出

**期待される出力**:
```csv
機種,容量,ランク,弊社価格,楽天商品数,楽天最低,楽天平均,楽天中央値,楽天最高,価格差(円),価格差(%),推奨価格
iPhone 15 Pro,256GB,A,119682,45,50000,58000,57500,72000,-61682,-51.5%,60900
iPhone 15 Pro,256GB,B,114725,40,35000,45000,43780,60000,-69725,-60.8%,47250
iPhone 15 Pro,256GB,C,108331,35,28000,37000,35000,50000,-71331,-65.8%,38850
```

---

### 優先度2: 他サイトスクレイパー動作検証（推定2-3時間）

**対象サイト**:
1. **ゲオオンライン** → `scripts/scraper_resale_geo.py`
2. **イオシス** → `scripts/scraper_resale_iosys_v2.py`
3. **じゃんぱら** → `scripts/scraper_resale_janpara_v2.py`

**テスト手順**（各サイト）:
```bash
# 1. テスト実行（1機種のみ）
uv run python scripts/scraper_resale_geo.py

# 2. データ確認
ls data/resale/geo/
cat data/resale/geo/geo_iPhone_15_Pro_256GB.json | head -20

# 3. ランク抽出確認
uv run python -c "
import json
with open('data/resale/geo/geo_iPhone_15_Pro_256GB.json', 'r') as f:
    products = json.load(f)
    ranks = set(p.get('rank') for p in products if p.get('rank'))
    print(f'抽出されたランク: {sorted(ranks)}')
    print(f'A/B/Cランク件数: {sum(1 for p in products if p.get(\"rank\") in [\"A\", \"B\", \"C\"])}')
"

# 4. エラーがあれば修正
```

---

### 優先度3: 全サイト統合分析レポート作成（推定1-2時間）

**実装スクリプト**: `scripts/analyze_competitive_prices.py`（新規作成）

**機能**:
- 弊社 + 楽天 + ゲオ + イオシス + じゃんぱら の5サイト統合
- 機種×容量×ランク（A/B/C）の3軸集計
- 各サイトの平均価格・最低価格
- 競合全体の平均価格・最安価格
- 弊社価格との差額・差率
- 推奨販売価格の提案

**出力フォーマット**:
```csv
機種,容量,ランク,弊社価格,楽天平均,ゲオ平均,イオシス平均,じゃんぱら平均,競合最安,競合平均,価格差(円),価格差(%),推奨価格
iPhone 15 Pro,256GB,A,119682,58000,55000,52000,54000,52000,54750,-64932,-54.2%,57488
```

---

### 優先度4: 週次更新用スラッシュコマンド・スクリプト作成（推定1時間）

**スラッシュコマンド**: `/update-resale-prices`

**機能**:
1. 全サイトからデータ収集（楽天・ゲオ・イオシス・じゃんぱら）
2. D・ジャンク除外
3. A/B/Cランク別分析
4. 弊社価格との比較レポート生成
5. Excelファイル出力

**実装ファイル**:
- `.claude/commands/update-resale-prices.md`
- `scripts/weekly_update.py`

---

## 💻 便利なコマンド

### データ確認

```bash
# 楽天データ確認（ジャンク除外後）
cd /Users/noguchisara/projects/work/iphone-market-research/resale-market
uv run python -c "
import json
from pathlib import Path
total = 0
for f in Path('data/raw/rakuten').glob('*.json'):
    with open(f, 'r') as fp:
        total += len(json.load(fp))
print(f'楽天データ総件数: {total:,}件')
"

# 弊社価格データ確認
head -10 data/company/backmarket_prices.csv

# A/B/Cランクのみ抽出
cat data/company/backmarket_prices.csv | grep -E "^iPhone 15 Pro,256GB,(A|B|C),"
```

### スクレイパー実行

```bash
# ゲオオンライン（テスト）
uv run python scripts/scraper_resale_geo.py

# イオシス（テスト）
uv run python scripts/scraper_resale_iosys_v2.py

# じゃんぱら（テスト）
uv run python scripts/scraper_resale_janpara_v2.py
```

### 分析レポート生成

```bash
# 楽天のみ（現状）
uv run python scripts/analyze.py

# 弊社価格比較（次セッションで実装）
uv run python scripts/compare_prices.py

# 全サイト統合分析（次セッションで実装）
uv run python scripts/analyze_competitive_prices.py
```

---

## 🔧 技術情報

### ランク統一マッピング

```python
RANK_MAPPING = {
    # イオシス
    "未使用": "S",      # 除外
    "Aランク": "A",     # ✅ 対象
    "Bランク": "B",     # ✅ 対象
    "Cランク": "C",     # ✅ 対象

    # じゃんぱら
    "未使用品": "S",    # 除外
    "ランクA": "A",     # ✅ 対象
    "ランクB": "B",     # ✅ 対象
    "ランクC": "C",     # ✅ 対象
    "ランクD": None,    # 除外

    # ゲオ
    "状態S": "S",       # 除外
    "状態A": "A",       # ✅ 対象
    "状態B": "B",       # ✅ 対象
    # Cランクなし

    # 楽天（商品名から抽出）
    "Sランク": "S",     # 除外
    "新品": "S",        # 除外
    "Aランク": "A",     # ✅ 対象
    "Bランク": "B",     # ✅ 対象
    "Cランク": "C",     # ✅ 対象
    "ジャンク": None,   # 除外

    # 弊社
    "プレミアム": "S",  # 除外
    "A": "A",          # ✅ 対象
    "B": "B",          # ✅ 対象
    "C": "C",          # ✅ 対象
}

# 分析対象フィルター
VALID_RANKS = ["A", "B", "C"]
```

### 環境変数

```bash
# 楽天市場API
export RAKUTEN_APP_ID='1037682033117300178'

# 現在のセッションで有効化
source ~/.zshrc
```

---

## 📝 重要な決定事項

### ✅ 確定事項

1. **対象サイト**: ゲオ、イオシス、じゃんぱら、楽天、弊社（バックマーケット）の5社
2. **分析ランク**: **A/B/Cのみ**（S・プレミアム・D・ジャンク除外）
3. **分析軸**: 機種×容量×ランクの3軸
4. **データ収集範囲**: 全86モデル×容量×ランク
5. **更新頻度**: 週次（スラッシュコマンドで実行）
6. **ゲオのCランク**: 設定なし（A/Bのみ）
7. **弊社プレミアム**: 分析対象外

### ⚠️ 注意事項

1. **ゲオにはCランクがない**: ゲオのデータはA/Bのみで比較
2. **楽天データの品質**: 無関係な商品が混入している可能性あり（フィルタリング強化必要）
3. **スクレイパー未検証**: ゲオ・イオシス・じゃんぱらのスクレイパーは動作未確認
4. **バックマーケット = 弊社**: 弊社がバックマーケットで販売しているため、弊社価格として扱う

---

## 🔄 セッション間のデータフロー

```
Session 1-5: プロジェクト環境構築・楽天API動作確認・データ収集
    ↓
Session 6: プロジェクト切り替えと正規化準備（正規化は中止）
    ↓
Session 7（このセッション）: 分析要件の明確化とセットアップ
    ├─ 各サイトのランク定義調査完了
    ├─ 楽天データからD・ジャンク除外（266件削除）
    ├─ 弊社販売価格CSV確認（424行）
    ├─ Playwrightインストール完了
    └─ 分析方針確定（A/B/Cのみ比較）
    ↓
Session 8（次回）: ランク別分析実装 → スクレイパー検証 → 統合分析レポート作成
```

---

## 📊 期待される最終成果物

### 1. 競合価格比較レポート（Excel）

**ファイル名**: `reports/competitive_price_analysis_YYYYMMDD.xlsx`

**シート構成**:
1. **サマリー**: 全体統計（機種数、価格帯、競合との平均価格差）
2. **機種別比較**: 機種×容量×ランク別の詳細比較
3. **ランク別統計**: A/B/Cランクごとの価格分布
4. **推奨価格**: 競合平均+マージンによる推奨販売価格
5. **生データ**: 各サイトの個別データ

### 2. 週次更新スクリプト

**実行コマンド**: `/update-resale-prices` または `uv run python scripts/weekly_update.py`

**処理フロー**:
1. 全サイトからデータ収集（2-4時間）
2. D・ジャンク除外
3. A/B/Cランク抽出
4. 統計計算
5. 弊社価格比較
6. Excelレポート生成

---

## 🏁 このセッションの結論

### 実施したこと

✅ プロジェクト目標の明確化（機種×容量×ランク 3軸分析）
✅ 対象サイト5社の選定（ゲオ、イオシス、じゃんぱら、楽天、弊社）
✅ 各サイトのランク定義調査とマッピング
✅ 楽天データからD・ジャンク266件除外
✅ 弊社販売価格CSV確認（424行、A/B/C+プレミアム）
✅ 分析方針確定（A/B/Cのみ、プレミアム・S除外）
✅ Playwrightブラウザインストール

### 未実施（次セッションで実施）

⏭️ ランク別分析レポート実装（A/B/C分離）
⏭️ 弊社価格との比較分析スクリプト作成
⏭️ スクレイパー動作検証（ゲオ・イオシス・じゃんぱら）
⏭️ 全サイト統合分析レポート作成
⏭️ 週次更新用スラッシュコマンド作成

### 次セッションで最初にやること

1. **ランク別分析レポート実装**（優先度1）
   - `scripts/analyze.py`の修正
   - 楽天データでA/B/C別集計
   - 弊社価格との比較

2. **スクレイパー動作検証**（優先度2）
   - ゲオ → イオシス → じゃんぱらの順でテスト

---

**最終更新**: 2025-11-18 14:56 Tuesday
**次回セッション**: この引き継ぎファイルを最初に読み、優先度1のランク別分析レポート実装から開始
