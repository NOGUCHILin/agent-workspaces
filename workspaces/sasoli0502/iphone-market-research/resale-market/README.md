# iPhone中古販売市場 相場調査システム

iPhone X（2017年）以降のモデルについて、主要な中古販売チャネルの価格相場を自動収集・分析するシステムです。

## 📊 対象チャネル

### API利用可能（自動収集）
- ✅ **楽天市場** - 楽天商品検索API
- ✅ **Yahoo!ショッピング** - Yahoo!ショッピングAPI v3

### 手動調査が必要
- ⚠️ バックマーケット
- ⚠️ イオシス
- ⚠️ ムスビー
- ⚠️ メルカリ
- ⚠️ PayPayフリマ

## 🚀 クイックスタート

### 1. 初期設定

```bash
cd work/iphone-market-research
uv sync
```

### 2. APIキー設定

#### 楽天API
1. [楽天ウェブサービス](https://webservice.rakuten.co.jp/)でアプリID取得
2. 環境変数に設定:
```bash
export RAKUTEN_APP_ID='your_rakuten_app_id'
```

#### Yahoo!ショッピングAPI
1. [Yahoo!デベロッパーネットワーク](https://developer.yahoo.co.jp/)でClient ID取得
2. 環境変数に設定:
```bash
export YAHOO_CLIENT_ID='your_yahoo_client_id'
```

### 3. API設定確認

```bash
uv run python scripts/config.py
```

## 📥 データ収集

### テスト実行（最初の3件のみ）

```bash
uv run python scripts/collect_all.py --test
```

### 全データ収集

```bash
# 楽天 + Yahoo!ショッピング（両方）
uv run python scripts/collect_all.py

# 楽天のみ
uv run python scripts/collect_all.py --channels rakuten

# Yahoo!ショッピングのみ
uv run python scripts/collect_all.py --channels yahoo
```

**注意**: 全86モデル×容量の組み合わせを収集すると、かなり時間がかかります（数時間程度）

### 個別チャネルのテスト

```bash
# 楽天市場（3件のみ）
uv run python scripts/scraper_rakuten.py

# Yahoo!ショッピング（3件のみ）
uv run python scripts/scraper_yahoo.py
```

## 📈 データ分析

収集したデータを分析してレポート作成:

```bash
uv run python scripts/analyze.py
```

出力ファイル:
- `reports/iphone_price_report_YYYYMMDD_HHMMSS.xlsx` - Excel形式（チャネル別シート）
- `reports/iphone_price_report_YYYYMMDD_HHMMSS.csv` - CSV形式

## 📁 ディレクトリ構成

```
iphone-market-research/
├── CLAUDE.md              # プロジェクト詳細仕様
├── README.md              # このファイル
├── pyproject.toml         # 依存関係
├── .gitignore            # Git除外設定
├── data/                 # データファイル（Git管理外）
│   ├── raw/             # 生データ
│   │   ├── rakuten/    # 楽天市場の収集データ
│   │   └── yahoo/      # Yahoo!ショッピングの収集データ
│   └── processed/       # 加工済みデータ
├── scripts/             # スクリプト
│   ├── models.py        # モデル・容量定義（86組み合わせ）
│   ├── config.py        # API設定
│   ├── scraper_rakuten.py   # 楽天スクレイパー
│   ├── scraper_yahoo.py     # Yahoo!スクレイパー
│   ├── collect_all.py       # 一括収集
│   └── analyze.py           # 分析・レポート作成
└── reports/             # 分析レポート
```

## 🎯 調査対象モデル（全86組み合わせ）

| 年 | モデル | 容量 |
|----|--------|------|
| 2017 | iPhone X | 64GB, 256GB |
| 2018 | iPhone XR | 64GB, 128GB, 256GB |
| 2018 | iPhone XS/XS Max | 64GB, 256GB, 512GB |
| 2019 | iPhone 11 | 64GB, 128GB, 256GB |
| 2019 | iPhone 11 Pro/Pro Max | 64GB, 256GB, 512GB |
| 2020 | iPhone 12 mini/12 | 64GB, 128GB, 256GB |
| 2020 | iPhone 12 Pro/Pro Max | 128GB, 256GB, 512GB |
| 2021 | iPhone 13 mini/13 | 128GB, 256GB, 512GB |
| 2021 | iPhone 13 Pro/Pro Max | 128GB, 256GB, 512GB, 1TB |
| 2022 | iPhone 14/14 Plus | 128GB, 256GB, 512GB |
| 2022 | iPhone 14 Pro/Pro Max | 128GB, 256GB, 512GB, 1TB |
| 2023 | iPhone 15/15 Plus | 128GB, 256GB, 512GB |
| 2023 | iPhone 15 Pro/Pro Max | 128GB, 256GB, 512GB, 1TB |
| 2024 | iPhone 16/16 Plus | 128GB, 256GB, 512GB |
| 2024 | iPhone 16 Pro/Pro Max | 256GB, 512GB, 1TB |

## ⚠️ 注意事項

### API利用制限
- **楽天API**: 短時間に大量リクエストすると一時制限される可能性あり
- **Yahoo!ショッピングAPI**: 1秒に1リクエストの制限あり（スクリプトで自動調整済み）

### 検索条件
- **SIMロック**: SIMフリーのみ
- **カラー**: 全カラー含む（区別なし）
- **コンディション**: 各サイトのグレード表記をそのまま記録

### データ更新
定期的にデータを更新する場合は、cronやタスクスケジューラーで `collect_all.py` を実行してください。

## 🔧 トラブルシューティング

### API設定エラー
```
❌ エラー: 楽天APIのアプリIDが設定されていません
```
→ 環境変数を設定してください: `export RAKUTEN_APP_ID='...'`

### レート制限エラー
→ スクリプト内の `SLEEP_INTERVAL` を長くしてください（デフォルト1秒）

### データが取得できない
→ 検索キーワードを確認。`models.py` の `get_search_keywords()` を調整

## 📝 今後の拡張

- [ ] メルカリのブラウザ自動化スクリプト
- [ ] バックマーケット・イオシス・ムスビーの手動調査テンプレート
- [ ] 価格推移グラフの自動生成
- [ ] Slack/Discord通知機能
- [ ] 定期実行用のスケジューラー設定

## 📄 ライセンス

このプロジェクトは個人利用・社内利用を目的としています。
各サイトの利用規約を遵守してください。
