# 次セッションへの引き継ぎ - iPhone買取価格最適化システム

**作成日時**: 2025-11-13 15:50 水曜日
**プロジェクト**: work/iphone-market-research/
**最終目標**: 利益を最大化する買取価格の自動設定システム構築

---

## 🚀 次セッション開始時に最初に読むファイル

### 1. この引き継ぎファイル（今読んでいるファイル）
```
work/handover/personal/2025-11-13_iphone-buyback-system.md
```

### 2. プロジェクト全体の状況
```
work/iphone-market-research/resale-market/次セッションへの引き継ぎ.md
```
→ 販売価格調査の状況（楽天市場データ：9,638件収集済み）

### 3. 買取価格システムのREADME
```
work/iphone-market-research/buyback-market/README.md
```

---

## 📊 現在の進捗状況（2025-11-13時点）

### ✅ 完了したこと

#### 1. プロジェクト構造の構築
```
work/iphone-market-research/
├── resale-market/          # 販売価格調査（完成済み）
│   ├── data/raw/rakuten/  # 楽天市場データ：84モデル、9,638件
│   └── reports/           # 分析レポート生成済み
└── buyback-market/        # 買取価格調査（進行中★）
    ├── data/raw/
    │   ├── janpara/       # ✅ 3モデル、74件（テスト完了）
    │   └── iosys/         # ✅ 335ファイル（全モデル取得完了）
    └── scripts/
        ├── scraper_janpara.py  # ✅ 実装・テスト完了
        └── scraper_iosys.py    # ✅ 実装・テスト完了
```

#### 2. データ収集スクリプトの実装状況

| サイト | 状態 | データ量 | 備考 |
|--------|------|----------|------|
| **じゃんぱら** | ✅ 完成 | 74件（3モデル） | 検索ベース、全86モデル対応可能 |
| **イオシス** | ✅ 完成 | 335ファイル | 価格リストベース、全モデル取得済み |
| **ゲオ** | ⏳ 未着手 | - | 次の実装対象 |

#### 3. 最終目標の確認
- **目的**: 利益を最大化する買取価格の設定
- **最適化式**: `利益 = (販売価格 - 買取価格) × 買取件数`
- **制約**: 買取価格のみを変数とする（広告費・場所等は固定）
- **利用可能データ**:
  - 弊社買取実績データ（入手可能）
  - 弊社販売価格
  - 競合買取価格（じゃんぱら、イオシス収集済み）

---

## 📂 データの場所と状態

### 競合買取価格データ

#### じゃんぱら（検索ベース）
```bash
# 場所
work/iphone-market-research/buyback-market/data/raw/janpara/

# ファイル例
janpara_iPhone_X_64GB.json
janpara_iPhone_X_256GB.json
janpara_iPhone_XR_64GB.json

# データ件数（現時点）
3モデル、合計74件

# データ構造
{
  "product_name": "海外版 【SIMフリー】 iPhone XR 64GB イエロー",
  "model": "iPhone XR",
  "capacity": "64GB",
  "condition": "中古品",
  "buyback_price": 8000,
  "url": "https://buy.janpara.co.jp/buy/search/detail?itmCode=277173",
  "site": "じゃんぱら",
  "scraped_at": "2025-11-13T15:23:16"
}
```

#### イオシス（価格リスト一括取得）
```bash
# 場所
work/iphone-market-research/buyback-market/data/raw/iosys/

# ファイル数
335ファイル（重複含む、全モデルカバー）

# データ構造
{
  "product_name": "au版SIMフリー iPhone 16 Pro 256GB",
  "model": "iPhone 16 Pro",
  "capacity": "256GB",
  "condition": "未使用品",
  "buyback_price": 141000,
  "carrier": "au版SIMフリー",
  "url": "https://k-tai-iosys.com/pricelist/smartphone/iphone/",
  "site": "イオシス",
  "scraped_at": "2025-11-13T15:46:37"
}

# 特徴
- 未使用品、中古品（上限）、中古品（下限）の3種類の価格
- キャリア別（docomo、au、SoftBank、楽天、SIMフリー等）
```

### 販売価格データ（resale-market）

```bash
# 場所
work/iphone-market-research/resale-market/data/raw/rakuten/

# データ量
84モデル、9,638件

# 分析レポート
work/iphone-market-research/resale-market/reports/
└── iphone_price_report_20251113_144713.csv
└── iphone_price_report_20251113_144713.xlsx

# サンプル価格（iPhone XR 64GB）
- 楽天販売価格（中央値）: ¥18,000
- じゃんぱら買取価格: ¥8,000
- 差額: ¥10,000（利益率約56%）
```

---

## 🔄 次にやること（優先順位順）

### 優先度1: ゲオスクレイパーの実装（30分程度）
```bash
cd /Users/noguchisara/projects/work/iphone-market-research/buyback-market

# ゲオのサイト調査
# URL: https://buymobile.geo-online.co.jp/
# 前回調査時に403エラーが出たため、アクセス方法の検討が必要

# 実装ファイル
scripts/scraper_geo.py
```

**注意**: ゲオは前回WebFetchで403エラー。別のアプローチが必要かも。

### 優先度2: 全86モデル一括収集スクリプトの実装（1時間程度）
```bash
# 実装ファイル
scripts/collect_all.py

# 実装内容
- じゃんぱら: 全86モデルを検索で収集（推定2-3時間）
- イオシス: 既に全モデル取得済みなので再実行のみ
- ゲオ: 実装次第

# 実行コマンド（完成後）
uv run python scripts/collect_all.py --sites janpara,iosys
```

### 優先度3: 競合比較分析スクリプトの実装（2時間程度）
```bash
# 実装ファイル
scripts/analyze_competitors.py

# 出力内容
- モデル別の競合価格比較
- 平均価格、最高値、最安値
- 弊社価格との差分（データがあれば）

# 出力例
iPhone 15 Pro 256GB:
  じゃんぱら: ¥85,000
  イオシス: ¥125,000（上限）、¥86,000（下限）
  平均: ¥98,667
```

### 優先度4: 弊社買取実績データの整備（時間未定）

**必要な確認事項**:
- データの保存場所は？（Excel、スプレッドシート、データベース等）
- データ期間は？（推奨：最低3ヶ月、理想：1年以上）
- データ粒度は？（日次、週次、月次）

**必要なデータ項目**:
```csv
日付,モデル,容量,状態,買取価格,買取件数,販売価格
2025-10-01,iPhone 15 Pro,256GB,中古,80000,5,98000
2025-10-08,iPhone 15 Pro,256GB,中古,82000,7,98000
```

---

## 💻 実行可能なコマンド

### データ収集（現時点）

#### じゃんぱら（テスト：3モデルのみ）
```bash
cd /Users/noguchisara/projects/work/iphone-market-research/buyback-market
uv run python scripts/scraper_janpara.py
```

#### イオシス（全モデル）
```bash
cd /Users/noguchisara/projects/work/iphone-market-research/buyback-market
uv run python scripts/scraper_iosys.py
```

### データ確認

#### 収集済みファイル数
```bash
# じゃんぱら
ls -1 data/raw/janpara/*.json | wc -l
# → 3ファイル

# イオシス
ls -1 data/raw/iosys/*.json | wc -l
# → 335ファイル
```

#### サンプルデータの確認
```bash
# じゃんぱら
head -20 data/raw/janpara/janpara_iPhone_XR_64GB.json

# イオシス
head -20 data/raw/iosys/iosys_iPhone_16_Pro_256GB.json
```

### 販売価格レポートの確認
```bash
# CSVで確認
head -30 ../resale-market/reports/iphone_price_report_20251113_144713.csv

# Excelをopen（macOS）
open ../resale-market/reports/iphone_price_report_20251113_144713.xlsx
```

---

## 🎯 実装プラン全体像（再掲）

```
┌─────────────────────────────────────────────────┐
│ フェーズ1: データ収集基盤の完成 ★現在ここ       │
├─────────────────────────────────────────────────┤
│ 1. 競合買取価格収集（自動）                      │
│    ✅ じゃんぱら（完成）                         │
│    ✅ イオシス（完成）                           │
│    ⏳ ゲオ（次）                                │
│ 2. 競合シェア率調査（手動→自動化）              │
│ 3. 弊社買取実績データの整備                      │
│ 4. 弊社販売価格データの整備                      │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│ フェーズ2: 分析基盤構築                          │
├─────────────────────────────────────────────────┤
│ 1. 価格感応度分析（需要曲線の推定）              │
│ 2. 競合ポジショニング分析                        │
│ 3. 利益シミュレーター                            │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│ フェーズ3: 最適化エンジン                        │
├─────────────────────────────────────────────────┤
│ 1. 利益最大化アルゴリズム                        │
│ 2. 最適価格レコメンデーション                    │
│ 3. 定期レポート自動生成                          │
└─────────────────────────────────────────────────┘
```

---

## 🔧 トラブルシューティング

### イオシスのモデル名正規化について
現在のスクレイパーで改行文字が混入する問題がある。
ただしデータは正常に取得できているので、後で修正でOK。

### ゲオのアクセス制限
前回WebFetchで403エラー。以下を試す：
1. 直接curlでアクセス確認
2. ブラウザ自動化（Selenium）の検討
3. 最悪の場合は手動調査

---

## 📝 重要な質問事項（次セッションで確認）

### 1. 弊社買取実績データについて
- [ ] データの保存場所を教えてください
- [ ] どのくらいの期間のデータがありますか？
- [ ] データの形式は？（Excel、CSV、DB等）

### 2. 競合シェア率調査について
- [ ] 優先度の高い競合を教えてください
  - じゃんぱら: ？
  - イオシス: ？
  - ゲオ: ？
  - その他: ？

### 3. フェーズ2への移行タイミング
- [ ] 全競合データが揃ってから？
- [ ] じゃんぱら+イオシスのデータがあれば開始？

---

## 🗂️ 関連ファイルパス一覧

### プロジェクトルート
```
/Users/noguchisara/projects/work/iphone-market-research/
```

### 買取価格プロジェクト
```
buyback-market/
├── README.md                           # 使い方ガイド
├── CLAUDE.md                           # プロジェクト詳細
├── pyproject.toml                      # 依存関係
├── data/raw/
│   ├── janpara/                       # じゃんぱらデータ
│   └── iosys/                         # イオシスデータ
└── scripts/
    ├── models.py                       # 86モデル定義
    ├── scraper_janpara.py             # じゃんぱらスクレイパー
    ├── scraper_iosys.py               # イオシススクレイパー
    ├── investigate_janpara.py         # 調査スクリプト
    └── investigate_iosys.py           # 調査スクリプト
```

### 販売価格プロジェクト（参考）
```
resale-market/
├── 次セッションへの引き継ぎ.md       # 詳細な引き継ぎ
├── data/raw/rakuten/                   # 楽天データ（84モデル）
└── reports/
    ├── iphone_price_report_20251113_144713.csv
    └── iphone_price_report_20251113_144713.xlsx
```

---

## 🚀 次セッション開始時のチェックリスト

- [ ] この引き継ぎファイルを読む
- [ ] 現在日時を確認: `date +"%Y-%m-%d %H:%M:%S %A"`
- [ ] プロジェクトディレクトリへ移動: `cd /Users/noguchisara/projects/work/iphone-market-research/buyback-market`
- [ ] データ状況確認: `ls -lh data/raw/*/`
- [ ] 次の実装対象を決定（ゲオ or 一括収集 or 分析）
- [ ] 弊社買取実績データの確認

---

**作成者**: Claude
**最終更新**: 2025-11-13 15:50
**次回更新予定**: 次セッション開始時
