# iPhone買取市場 価格調査システム

iPhone X（2017年）以降のモデルについて、主要な買取サイトの買取価格を調査・分析するシステムです。

## 📊 対象サイト

### 調査可能サイト
- ✅ **じゃんぱら** - 買取価格検索システムあり
- ⚠️ **イオシス** - 要調査（アクセス制限あり）
- ⚠️ **ゲオモバイル** - 要調査（アクセス制限あり）
- ⚠️ **ソフマップ** - 要調査
- ⚠️ **ブックオフ** - 要調査
- ⚠️ **大黒屋** - 要調査

### 手動調査が必要
- メルカリ（買取価格の公開なし）
- その他フリマアプリ

## 🚀 クイックスタート

### 1. 初期設定

```bash
cd work/iphone-market-research/buyback-market
uv sync
```

### 2. データ収集

```bash
# テスト実行（最初の3件のみ）
uv run python scripts/collect_all.py --test

# 全データ収集
uv run python scripts/collect_all.py

# 特定サイトのみ
uv run python scripts/collect_all.py --sites janpara
```

### 3. データ分析

```bash
uv run python scripts/analyze.py
```

## 📁 ディレクトリ構成

```
buyback-market/
├── CLAUDE.md              # プロジェクト詳細仕様
├── README.md              # このファイル
├── pyproject.toml         # 依存関係
├── .gitignore            # Git除外設定
├── data/                 # データファイル（Git管理外）
│   ├── raw/             # 生データ
│   │   ├── janpara/    # じゃんぱらの収集データ
│   │   ├── iosys/      # イオシスの収集データ
│   │   └── geo/        # ゲオの収集データ
│   └── processed/       # 加工済みデータ
├── scripts/             # スクリプト
│   ├── models.py        # モデル・容量定義（resale-marketから共有）
│   ├── scraper_janpara.py   # じゃんぱらスクレイパー
│   ├── scraper_iosys.py     # イオシススクレイパー
│   ├── scraper_geo.py       # ゲオスクレイパー
│   ├── collect_all.py       # 一括収集
│   └── analyze.py           # 分析・レポート作成
└── reports/             # 分析レポート
```

## 🎯 調査対象モデル（全86組み合わせ）

resale-marketプロジェクトと同じモデルリストを使用します。
詳細は `scripts/models.py` を参照。

## 📊 データ構造

### JSONファイル例 (`data/raw/janpara/janpara_iPhone_15_Pro_256GB.json`)

```json
[
  {
    "product_name": "iPhone 15 Pro 256GB SIMフリー",
    "model": "iPhone 15 Pro",
    "capacity": "256GB",
    "condition": "美品",
    "buyback_price": 85000,
    "url": "https://buy.janpara.co.jp/...",
    "scraped_at": "2025-11-13T14:50:00"
  }
]
```

## ⚠️ 注意事項

### スクレイピング制限
- 各サイトの利用規約を遵守すること
- レート制限に注意（リクエスト間隔を適切に設定）
- robots.txtを確認

### データの信頼性
- 買取価格は状態（美品、良品、傷あり等）により大きく変動
- 時期やキャンペーンにより価格が変動
- 定期的なデータ更新を推奨

## 🔧 トラブルシューティング

### アクセス制限エラー（403 Forbidden）
一部のサイトはスクレイピング対策を実施している可能性があります。
→ 手動調査または公式APIの利用を検討

### データが取得できない
→ サイトの構造変更の可能性。スクレイパーの更新が必要

## 📝 今後の拡張

- [ ] イオシス対応
- [ ] ゲオモバイル対応
- [ ] ソフマップ対応
- [ ] 買取価格と販売価格の比較分析
- [ ] 定期実行用のスケジューラー設定

## 📄 関連プロジェクト

- **resale-market**: 中古販売価格の調査（楽天市場、Yahoo!ショッピング）
- 買取価格と販売価格を比較することで、適正な価格設定が可能
