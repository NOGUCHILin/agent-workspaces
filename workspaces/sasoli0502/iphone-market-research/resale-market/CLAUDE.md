# iPhone中古販売市場 相場調査システム

## プロジェクト概要
iPhone X（2017年）以降のモデルについて、主要な中古販売チャネルの価格相場を調査・分析するシステム

## 調査対象

### 対象モデル（iPhone X以降）
- iPhone X（2017）: 64GB, 256GB
- iPhone XR（2018）: 64GB, 128GB, 256GB
- iPhone XS/XS Max（2018）: 64GB, 256GB, 512GB
- iPhone 11（2019）: 64GB, 128GB, 256GB
- iPhone 11 Pro/Pro Max（2019）: 64GB, 256GB, 512GB
- iPhone 12 mini/12（2020）: 64GB, 128GB, 256GB
- iPhone 12 Pro/Pro Max（2020）: 128GB, 256GB, 512GB
- iPhone 13 mini/13（2021）: 128GB, 256GB, 512GB
- iPhone 13 Pro/Pro Max（2021）: 128GB, 256GB, 512GB, 1TB
- iPhone 14/14 Plus（2022）: 128GB, 256GB, 512GB
- iPhone 14 Pro/Pro Max（2022）: 128GB, 256GB, 512GB, 1TB
- iPhone 15/15 Plus（2023）: 128GB, 256GB, 512GB
- iPhone 15 Pro/Pro Max（2023）: 128GB, 256GB, 512GB, 1TB
- iPhone 16/16 Plus（2024）: 128GB, 256GB, 512GB
- iPhone 16 Pro/Pro Max（2024）: 256GB, 512GB, 1TB

### 販売チャネル
1. メルカリ
2. Amazon（中古マーケットプレイス）
3. Yahoo!ショッピング
4. 楽天市場
5. その他（ラクマ、PayPayフリマなど）

### 調査条件
- **SIMロック**: SIMフリーのみ
- **容量**: モデルごとに区別
- **カラー**: 区別なし（全カラー含む）
- **コンディション**: 各サイトのグレード表記をそのまま記録

## データ用途
- 販売価格の決定
- 市場トレンド分析（将来的）

## ディレクトリ構成
```
iphone-market-research/
├── CLAUDE.md              # このファイル
├── README.md              # プロジェクト説明
├── pyproject.toml         # 依存関係管理
├── data/                  # 収集データ（Git管理外）
│   ├── raw/              # 生データ
│   └── processed/        # 加工済みデータ
├── scripts/              # 相場調査スクリプト
│   ├── models.py         # モデル・容量定義
│   ├── scraper_mercari.py
│   ├── scraper_amazon.py
│   ├── scraper_yahoo.py
│   ├── scraper_rakuten.py
│   └── analyze.py        # 分析スクリプト
└── reports/              # 分析レポート
```

## 実行方法

### 初回セットアップ
```bash
cd work/iphone-market-research
uv venv
uv pip install -r requirements.txt  # または pyproject.toml
```

### データ収集
```bash
# 全チャネルから収集
uv run python scripts/collect_all.py

# 特定チャネルのみ
uv run python scripts/scraper_mercari.py
```

### 分析レポート作成
```bash
uv run python scripts/analyze.py
```

## 注意事項
- スクレイピングは各サイトの利用規約を遵守すること
- API利用可能な場合は優先的に使用
- レート制限に注意（リクエスト間隔を適切に設定）
- データファイルは `.gitignore` に登録済み
