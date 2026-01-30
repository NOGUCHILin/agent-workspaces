# iPhone買取市場 価格調査システム

## プロジェクト概要
iPhone X（2017年）以降のモデルについて、主要な買取サイトの買取価格を調査・分析するシステム

## 調査対象

### 対象モデル（iPhone X以降）
resale-marketプロジェクトと同じ86組み合わせを調査対象とします。
詳細は `../resale-market/scripts/models.py` を参照。

### 買取サイト
1. **じゃんぱら** - 買取価格検索システムあり（優先度：高）
2. **イオシス** - 買取価格表あり（優先度：高）
3. **ゲオモバイル** - オンライン買取価格確認可能（優先度：中）
4. **ソフマップ** - 買取価格検索可能（優先度：中）
5. **ブックオフ** - 買取価格表あり（優先度：低）
6. **大黒屋** - 買取価格表公開（優先度：低）

### 調査条件
- **SIMロック**: SIMフリーのみ
- **容量**: モデルごとに区別
- **カラー**: 区別なし（一般的に買取価格はカラーで変動しない）
- **状態**: 各サイトのグレード表記（美品、良品、傷あり等）をそのまま記録

## データ用途
- 買取価格の相場把握
- 販売価格との比較（resale-marketデータと組み合わせ）
- 適正な買取・販売価格の設定

## ディレクトリ構成
```
buyback-market/
├── CLAUDE.md              # このファイル
├── README.md              # プロジェクト説明
├── pyproject.toml         # 依存関係管理
├── data/                  # 収集データ（Git管理外）
│   ├── raw/              # 生データ
│   └── processed/        # 加工済みデータ
├── scripts/              # 買取価格調査スクリプト
│   ├── models.py         # モデル・容量定義（シンボリックリンク推奨）
│   ├── scraper_janpara.py
│   ├── scraper_iosys.py
│   ├── scraper_geo.py
│   ├── collect_all.py    # 一括収集
│   └── analyze.py        # 分析スクリプト
└── reports/              # 分析レポート
```

## 実行方法

### 初回セットアップ
```bash
cd work/iphone-market-research/buyback-market
uv sync
```

### データ収集
```bash
# 全サイトから収集
uv run python scripts/collect_all.py

# 特定サイトのみ
uv run python scripts/scraper_janpara.py
```

### 分析レポート作成
```bash
uv run python scripts/analyze.py
```

## 技術仕様

### データモデル
```python
{
    "product_name": str,      # 商品名
    "model": str,             # モデル（例：iPhone 15 Pro）
    "capacity": str,          # 容量（例：256GB）
    "condition": str,         # 状態（美品、良品等）
    "buyback_price": int,     # 買取価格（円）
    "url": str,               # 商品URL
    "site": str,              # サイト名
    "scraped_at": str         # 取得日時（ISO 8601形式）
}
```

### スクレイピング方針
1. **じゃんぱら**: 買取価格検索ページからHTML解析
2. **イオシス**: 買取価格表ページからHTML解析（要アクセス調査）
3. **ゲオモバイル**: API利用可否を調査、なければHTML解析
4. その他: サイト構造を調査後に実装

## 注意事項
- スクレイピングは各サイトの利用規約を遵守すること
- robots.txtを確認
- レート制限に注意（リクエスト間隔を適切に設定）
- データファイルは `.gitignore` に登録済み

## resale-marketとの関係

### データの活用
- **販売価格** (resale-market): 楽天市場、Yahoo!ショッピング
- **買取価格** (buyback-market): じゃんぱら、イオシス等

### 分析例
```python
# 利益率の計算
profit_margin = (resale_price - buyback_price) / resale_price * 100

# モデル別の比較
# - どのモデルの利益率が高いか
# - 仕入れ（買取）から販売までのマージン分析
```

## 今後の展開
1. 買取価格データの定期収集
2. resale-marketとの統合分析
3. 価格推移の可視化
4. アラート機能（特定モデルの価格変動通知）
