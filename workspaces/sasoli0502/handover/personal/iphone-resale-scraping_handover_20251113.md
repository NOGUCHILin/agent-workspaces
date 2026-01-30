# iPhone販売価格スクレイピング - セッション引き継ぎ（2025-11-13）

**最終更新**: 2025-11-13 19:00 (Wednesday)
**プロジェクトパス**: `/Users/noguchisara/projects/work/iphone-market-research/resale-market/`
**ステータス**: イオシスのデータ取得完了、じゃんぱら・ゲオは課題あり

---

## 📋 次セッション開始時の手順

### 1. 最初に読むべきファイル

```bash
# このファイルを最初に読む
/Users/noguchisara/projects/work/handover/personal/iphone-resale-scraping_handover_20251113.md

# プロジェクト概要
/Users/noguchisara/projects/work/iphone-market-research/resale-market/README.md

# 詳細仕様
/Users/noguchisara/projects/work/iphone-market-research/resale-market/CLAUDE.md
```

### 2. 作業ディレクトリへ移動

```bash
cd /Users/noguchisara/projects/work/iphone-market-research/resale-market
```

---

## ✅ 本セッションで完了したこと

### 1. イオシス販売価格スクレイパーの作成・実行（完了）

**作成したファイル**:
- [scripts/scraper_resale_iosys_v2.py](../iphone-market-research/resale-market/scripts/scraper_resale_iosys_v2.py)

**取得データ**:
```
data/resale/iosys/
├── iosys_iPhone_12_20251113_185147.json (24件)
├── iosys_iPhone_13_20251113_185208.json (24件)
└── iosys_iPhone_14_20251113_185229.json (24件)

総計: 72件の実際の販売価格データ
```

**データ構造**:
```json
{
  "product_name": "【SIMロック解除済】docomo iPhone12 Pro Max A2410 (MGCW3J/A) 128GB ゴールド",
  "price": 72800,
  "url": "https://iosys.co.jp/items/smartphone/iphone12/docomo/iphone12_pro_max_a2410/222517",
  "rank": "B",
  "rank_raw": "中古Bランク",
  "capacity": "128GB",
  "model": "iPhone 12",
  "scraped_at": "2025-11-13T18:51:47.733402",
  "source": "イオシス"
}
```

**ランク別集計**:
- iPhone 12: Aランク4件、Bランク12件、Cランク8件
- iPhone 13: Aランク6件、Bランク11件、Cランク7件
- iPhone 14: Aランク8件、Bランク13件、Cランク3件

**主要な発見（iPhone 12の平均価格）**:
| ランク | 平均価格 | 最低価格 | 最高価格 |
|--------|----------|----------|----------|
| A | ¥49,050 | ¥35,800 | ¥79,800 |
| B | ¥51,717 | ¥26,800 | ¥82,800 |
| C | ¥34,175 | ¥25,800 | ¥52,800 |

### 2. じゃんぱらスクレイパーの作成（部分的に完了）

**作成したファイル**:
- [scripts/scraper_resale_janpara_v2.py](../iphone-market-research/resale-market/scripts/scraper_resale_janpara_v2.py)

**実行結果**:
- 1件のみ取得（技術的課題あり）
- エラー: ElementHandle.query_selectorでProtocol error発生

**課題**:
- 詳細ページへの遷移時にElementHandleが無効化される
- ページ遷移の処理方法を変更する必要がある

### 3. ゲオオンラインの調査（未完了）

**状況**:
- 検索結果が表示されない
- URL構造が不明
- 別のアプローチが必要

---

## 🔍 技術的な発見・実装詳細

### イオシススクレイパーの成功ポイント

**URL構造**:
```
モデル一覧: https://iosys.co.jp/items/smartphone/iphone
iPhone 12: https://iosys.co.jp/items/smartphone/iphone12
iPhone 13: https://iosys.co.jp/items/smartphone/iphone13
iPhone 14: https://iosys.co.jp/items/smartphone/iphone14
```

**重要なセレクタ**:
```python
# 商品リストのコンテナ
container = ".items-container"

# 各商品カード
items = "li.item"

# 商品情報の取得
product_name = 'input[name="name"]'  # value属性から取得
rank = 'input[name="rank"]'  # value属性から取得（例: "中古Bランク"）
price = '.price p'  # テキストから抽出（例: "72,800円"）
url = 'a[href]'  # href属性から取得
```

**ボット対策**:
- headless=False（実際のブラウザウィンドウを表示）
- User-Agent偽装
- WebDriverプロパティの隠蔽
- 適切な待機時間（5-10秒）
- スクロールしてコンテンツをロード

**データ正規化**:
```python
def normalize_rank(self, rank_text: str) -> Optional[str]:
    """ランクテキストを正規化"""
    # "中古Aランク" → "A"
    # "中古Bランク" → "B"
    # "未使用" → "S"
```

### じゃんぱらスクレイパーの課題

**URL構造**:
```
検索: https://www.janpara.co.jp/sale/search/result/?KEYWORDS=iPhone12&OUTCLSCODE=78&NOTKEYWORDS=Pro+mini
```

**セレクタ**:
```python
# 商品カード
items = ".search_item_s"

# 商品情報
product_name = '.search_itemname'
price = '.item_amount'  # "¥34,980～"
condition = '.search_itemcondition'  # "中古"のみ、ランク情報なし
url = 'a.search_itemlink'
```

**問題点**:
1. **商品リストにランク情報がない**
   - 詳細ページにアクセスしないとランクが不明
   - 各商品ごとにページ遷移が必要

2. **ElementHandle無効化エラー**:
   ```
   ElementHandle.query_selector: Protocol error (DOM.describeNode):
   Cannot find context with specified id
   ```
   - ページ遷移後にElementHandleが無効化される
   - 各ループで新しくElementを取得し直す必要がある

**修正案**:
```python
# 修正前（エラー発生）
for item in items:
    link = await item.query_selector('a')  # ← ページ遷移後に無効
    await page.goto(url)

# 修正後（提案）
for i in range(len(items)):
    # ページ遷移前にURLだけ取得
    items = await page.query_selector_all(".search_item_s")
    link = await items[i].query_selector('a')
    url = await link.get_attribute('href')

    # 詳細ページへ
    await page.goto(self.BASE_URL + url)
    rank = await self.scrape_product_detail(page, url)

    # リストページに戻る
    await page.go_back()
```

---

## 📊 既存の買取価格データ（2025-11-13取得済み）

### イオシスの買取価格（ランク別）

**データソース**: 前セッションで取得済み

**iPhone 12の買取価格**:
| ランク | 64GB | 128GB | 256GB |
|--------|------|-------|-------|
| S（未使用） | 28,000円 | 31,000円 | 36,000円 |
| A（キズなし） | 25,000円 | 28,000円 | 32,000円 |
| B（小キズ） | 22,000円 | 25,000円 | 28,000円 |
| C（目立つキズ） | 18,000円 | 23,000円 | 22,000円 |
| D/J（破損） | 最大12,000円 | 最大15,000円 | 最大14,000円 |

**iPhone 13の買取価格**:
| ランク | 128GB | 256GB | 512GB |
|--------|-------|-------|-------|
| S | 48,000円 | 51,000円 | 57,000円 |
| A | 43,000円 | 46,000円 | 51,000円 |
| B | 38,000円 | 41,000円 | 45,000円 |
| C | 30,000円 | 32,000円 | 36,000円 |
| D/J | 最大20,000円 | 最大21,000円 | 最大23,000円 |

**iPhone 14の買取価格**:
| ランク | 128GB | 256GB | 512GB |
|--------|-------|-------|-------|
| S | 61,000円 | 67,000円 | 71,000円 |
| A | 55,000円 | 62,000円 | 67,000円 |
| B | 49,000円 | 55,000円 | 60,000円 |
| C | 41,000円 | 47,000円 | 50,000円 |
| D/J | 最大27,000円 | 最大31,000円 | 最大33,000円 |

---

## 🚨 重要な決定事項

### 楽天市場のデータは使用しない

**理由**:
- ランク表記が82%不明（「中古（ランク不明）」）
- 個人出品者が多く、価格が不安定
- 相場比較に不適切

**方針**:
- ランク表記が明確な買取専門店のデータのみを使用
- イオシス、じゃんぱら、ゲオ等の専門業者に絞る

---

## 📈 次のステップ（優先順位順）

### 優先度A: イオシスデータでレポート作成（推奨）

**実施内容**:
1. イオシスの買取価格 vs 販売価格のマージン分析
2. ランク別・容量別の価格レポート作成
3. Excel/CSVでレポート出力

**実装ファイル**:
```bash
# 分析スクリプトを作成
scripts/analyze_iosys_margin.py

# 実行
uv run python scripts/analyze_iosys_margin.py
```

**期待される出力**:
```
reports/
├── iosys_buyback_vs_resale_20251114.xlsx
└── iosys_buyback_vs_resale_20251114.csv
```

**分析項目**:
- モデル×ランク×容量ごとの買取価格・販売価格
- マージン額（販売価格 - 買取価格）
- マージン率（%）
- 平均販売価格 vs 最低販売価格

### 優先度B: じゃんぱらスクレイパーの修正

**課題**:
- ElementHandle無効化エラーの解決
- ページ遷移処理の改善

**修正方針**:
1. URLリストを事前に取得
2. 各URLに直接アクセス
3. ElementHandleを再利用しない

**修正箇所**:
```python
# scripts/scraper_resale_janpara_v2.py の scrape_model_page() を修正
```

### 優先度C: ゲオオンラインの調査

**実施内容**:
1. ゲオのiPhone販売ページのURL構造を調査
2. 適切な検索URLを特定
3. スクレイパーを実装

**調査URL候補**:
- ゲオモバイル: `https://geo-mobile.jp/`
- ゲオオンラインストア（スマホカテゴリ）

---

## 💻 実行コマンド一覧

### イオシスデータの確認

```bash
cd /Users/noguchisara/projects/work/iphone-market-research/resale-market

# データファイルの確認
ls -lh data/resale/iosys/

# データ内容の確認（最初の30行）
head -30 data/resale/iosys/iosys_iPhone_12_20251113_185147.json
```

### 簡易分析（Python）

```bash
uv run python -c "
import json
import pandas as pd
from pathlib import Path

# データ読み込み
data_dir = Path('data/resale/iosys')
json_files = list(data_dir.glob('iosys_iPhone_*_20251113_*.json'))

all_products = []
for file in json_files:
    with open(file, 'r', encoding='utf-8') as f:
        products = json.load(f)
        all_products.extend(products)

df = pd.DataFrame(all_products)

# サマリー表示
print('=== サマリー ===')
print(f'総商品数: {len(df)}件')
print(f'\nモデル別:')
print(df['model'].value_counts())
print(f'\nランク別:')
print(df['rank'].value_counts())

# モデル×ランク別の平均価格
print(f'\n=== モデル×ランク別平均価格 ===')
pivot = df.pivot_table(
    values='price',
    index='model',
    columns='rank',
    aggfunc='mean'
).round(0)
print(pivot)
"
```

### じゃんぱらスクレイパーの再実行（修正後）

```bash
# 修正版を作成してから実行
uv run python scripts/scraper_resale_janpara_v2.py
```

---

## 🔗 関連ファイルへのリンク

### スクリプト

- [scraper_resale_iosys_v2.py](../iphone-market-research/resale-market/scripts/scraper_resale_iosys_v2.py) - イオシススクレイパー（完成版）
- [scraper_resale_janpara_v2.py](../iphone-market-research/resale-market/scripts/scraper_resale_janpara_v2.py) - じゃんぱらスクレイパー（要修正）
- [analyze.py](../iphone-market-research/resale-market/scripts/analyze.py) - 分析スクリプト（既存）

### データ

- `data/resale/iosys/` - イオシス販売価格データ（72件）
- `data/resale/janpara/` - じゃんぱら販売価格データ（1件のみ）
- 買取価格データ: 前セッションで取得済み（手動入力形式）

### ドキュメント

- [README.md](../iphone-market-research/resale-market/README.md) - プロジェクト概要
- [CLAUDE.md](../iphone-market-research/resale-market/CLAUDE.md) - 詳細仕様

---

## 📝 技術メモ・留意事項

### Playwrightの実行環境

**インストール済み**:
```bash
# 既にインストール済み
playwright --version

# ブラウザもインストール済み
# chromium, firefox, webkit
```

**実行時の注意**:
- `headless=False`を推奨（bot検出回避）
- ブラウザウィンドウが開くため、実行中は他の作業が可能

### データ形式

**JSON形式**:
- 各モデルごとに個別のJSONファイル
- 配列形式で商品データを保存

**CSV/Excel変換**:
```python
import pandas as pd
df = pd.DataFrame(products)
df.to_csv('output.csv', index=False, encoding='utf-8-sig')
df.to_excel('output.xlsx', index=False, engine='openpyxl')
```

### エラーハンドリング

**よくあるエラー**:
1. **Timeout**: ページ読み込みが60秒を超える
   - 対策: wait_until="domcontentloaded"に変更

2. **ElementHandle無効化**: ページ遷移後にElementが使えない
   - 対策: 各ループで再取得

3. **Bot検出**: アクセス拒否される
   - 対策: User-Agent偽装、待機時間追加

---

## 🎯 推奨する次回の作業フロー

### ステップ1: イオシスデータでレポート作成（30分）

1. イオシスの買取価格データを準備
2. 販売価格データと結合
3. マージン計算
4. Excel/CSVレポート生成

### ステップ2: じゃんぱらスクレイパー修正（60分）

1. ElementHandle問題の解決
2. テスト実行（10件程度）
3. 成功したら全件実行

### ステップ3: 3社データの統合分析（30分）

1. イオシス・じゃんぱら・ゲオ（取得できた場合）のデータを統合
2. 業者間の価格差分析
3. 最終レポート作成

---

## ✅ チェックリスト（次セッション用）

### 開始時に確認すること

- [ ] この引継ぎファイルを読んだ
- [ ] プロジェクトディレクトリに移動した
- [ ] イオシスのデータファイル（72件）の存在を確認した
- [ ] 買取価格データ（既存）の場所を確認した

### 分析を始める前に

- [ ] どの分析から始めるか決めた（推奨: イオシスデータのみでレポート作成）
- [ ] 必要に応じてスクリプトを作成/修正する準備ができた

### じゃんぱらスクレイパーを修正する場合

- [ ] ElementHandle問題の修正方針を理解した
- [ ] テスト実行（少数件）から始める準備ができた

---

**作成者**: Claude
**作成日**: 2025-11-13 19:00 (Wednesday)
**次回更新**: じゃんぱらスクレイパー修正後、またはレポート作成後
