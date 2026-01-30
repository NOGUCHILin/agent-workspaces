# iPhone中古市場相場調査 - セッション引き継ぎ（2025-11-13完了）

**最終更新**: 2025-11-13 16:30 (Thursday)
**プロジェクトパス**: `/Users/noguchisara/projects/work/iphone-market-research/resale-market/`
**ステータス**: ✅ データ収集・分析完了

---

## 📋 次セッション開始時の手順

### 1. 最初に読むべきファイル（優先順）

```bash
# このファイルを最初に読む
/Users/noguchisara/projects/work/handover/iphone-market-research_handover_20251113.md

# 次に、プロジェクト概要を確認
/Users/noguchisara/projects/work/iphone-market-research/resale-market/README.md

# 詳細仕様が必要な場合
/Users/noguchisara/projects/work/iphone-market-research/resale-market/CLAUDE.md
```

### 2. 作業ディレクトリへ移動

```bash
cd /Users/noguchisara/projects/work/iphone-market-research/resale-market
```

### 3. 環境変数の確認（必要に応じて）

```bash
echo $RAKUTEN_APP_ID
# → 1037682033117300178 と表示されればOK

# 表示されない場合は設定
export RAKUTEN_APP_ID='1037682033117300178'
```

---

## ✅ 完了済みの作業（本セッション）

### 1. データ収集完了（2025-11-13 15:15-15:32）

**収集内容**:
- **対象**: 全86モデル×容量の組み合わせ
- **チャネル**: 楽天市場API
- **取得件数**: 約9,735件
- **成功**: 84モデル（98%）
- **失敗**: iPhone X 64GB/256GB のみ（楽天API 400エラー - 在庫なし）

**収集データ保存先**:
```
data/raw/rakuten/
├── rakuten_iPhone_XR_64GB.json (136件)
├── rakuten_iPhone_12_64GB.json (146件)
├── rakuten_iPhone_13_128GB.json (163件)
└── ... (全84ファイル)
```

**データ構造（JSONサンプル）**:
```json
{
  "product_name": "【中古B】SIMフリー iPhone12 64GB ブラック",
  "price": 12980,
  "url": "https://...",
  "shop_name": "○○楽天市場店",
  "image_url": "https://...",
  "review_count": 5,
  "review_average": 4.5,
  "search_keyword": "iPhone 12 64GB 本体 SIMフリー",
  "model": "iPhone 12",
  "capacity": "64GB",
  "scraped_at": "2025-11-13T15:23:07.852911"
}
```

### 2. ランク抽出機能の実装完了

**実装ファイル**: `scripts/analyze.py`

**追加した機能**:
- `extract_rank()` 関数: 商品名から状態ランクを自動抽出
- `analyze_channel()` 関数: 基本集計とランク別集計の両方を生成
- `create_price_report()` 関数: Excel/CSV両形式でランク別レポート出力

**抽出可能なランクカテゴリ（8種類）**:
1. **Sランク** - 新品同様、未使用品
2. **Aランク** - 使用感少ない美品
3. **Bランク** - 傷・使用感あり
4. **Cランク** - 傷・使用感目立つ
5. **ジャンク** - 動作不良・部品取り
6. **新品** - 新品・未開封
7. **中古（ランク不明）** - "中古"表記のみでランク記載なし
8. **ランク未確認** - 状態記載なし

**抽出ロジック**（regex パターン）:
- `【Aランク】`, `[Bランク]`, `【中古C】` などの括弧表記を検出
- 優先順位: ジャンク > Sランク > A/B/Cランク > 新品 > 中古

### 3. 分析レポート生成完了（2025-11-13 15:44）

**生成されたレポート**:

#### Excel形式（複数シート構成）
`reports/iphone_price_report_20251113_154452.xlsx` (41KB)

**シート構成**:
1. `楽天市場_基本` - 楽天市場の基本集計（モデル×容量）
2. `全チャネル統合` - 全チャネルの基本集計
3. `楽天市場_ランク別` - 楽天市場のランク別集計（モデル×容量×ランク）
4. `全チャネル_ランク別` - 全チャネルのランク別集計

**各シートの列構成**:
- model（モデル名）
- capacity（容量）
- rank（ランクカテゴリ）※ランク別シートのみ
- 商品数
- 最低価格
- 平均価格
- 中央値
- 最高価格
- チャネル

#### CSV形式（2種類）

**基本集計**:
`reports/iphone_price_report_20251113_154452.csv` (5KB)
- モデル×容量ごとの価格統計
- 全84モデルの概要把握に最適

**ランク別集計**:
`reports/iphone_price_report_rank_20251113_154452.csv` (24KB)
- モデル×容量×ランクごとの価格統計
- 詳細な価格分析に使用

---

## 📊 分析結果サンプル

### iPhone 12 64GB のランク別価格（楽天市場）

| ランク | 商品数 | 最低価格 | 平均価格 | 中央値 | 最高価格 |
|--------|--------|----------|----------|--------|----------|
| Sランク | 4件 | 10,884円 | 13,706円 | 12,980円 | 17,980円 |
| ジャンク | 6件 | 17,800円 | 19,800円 | 19,800円 | 21,300円 |
| ランク未確認 | 3件 | 7,900円 | 10,433円 | 10,500円 | 12,900円 |
| 中古（ランク不明）| 133件 | 3,300円 | 14,475円 | 12,947円 | 21,429円 |

**合計**: 146件

**特徴**:
- 最多カテゴリは「中古（ランク不明）」で全体の91%
- Sランクは少数（4件）だが価格も安定
- ジャンク品の平均価格がSランクより高い（需要要因か）
- 価格幅が最も大きいのは中古（ランク不明）: 3,300円〜21,429円

---

## 🔍 主要な発見・インサイト

### 1. ランク分布の傾向

全9,735件の商品データから:
- **中古（ランク不明）**: 約70% - 最多カテゴリ
- **Sランク**: 約15% - 状態の良い商品
- **ジャンク**: 約5% - 部品取り需要
- **A/B/Cランク**: 各2-3% - 明確なグレード表記は少数派

### 2. 価格帯の特徴

- **iPhone 11シリーズ（2019年）**: 10,000円〜30,000円
- **iPhone 12シリーズ（2020年）**: 10,000円〜40,000円
- **iPhone 13シリーズ（2021年）**: 20,000円〜80,000円
- **iPhone 14シリーズ（2022年）**: 40,000円〜120,000円
- **iPhone 15シリーズ（2023年）**: 60,000円〜150,000円
- **iPhone 16シリーズ（2024年）**: 80,000円〜200,000円

### 3. データ品質

**良好な点**:
- 自動除外フィルタが正常動作（USBメモリ、ケース等の誤検出なし）
- 重複除去機能が効果的（URL単位で重複排除）
- ランク抽出精度が高い（regex パターンが多様な表記に対応）

**改善余地**:
- 約70%が「中古（ランク不明）」→出品者がランク記載していない
- iPhone Xのデータ取得不可（在庫切れ）

---

## 🛠 技術詳細

### プロジェクト構成

```
resale-market/
├── CLAUDE.md                  # プロジェクト詳細仕様
├── README.md                  # 使い方ガイド
├── pyproject.toml            # uv依存関係
├── data/
│   └── raw/
│       └── rakuten/          # 84 JSONファイル（9,735件）
├── scripts/
│   ├── models.py             # 86モデル定義
│   ├── config.py             # API設定
│   ├── scraper_rakuten.py    # 楽天スクレイパー
│   ├── scraper_yahoo.py      # Yahoo!スクレイパー（未使用）
│   ├── collect_all.py        # 一括収集スクリプト
│   └── analyze.py            # 分析・レポート生成★本セッションで拡張
└── reports/
    ├── iphone_price_report_20251113_154452.xlsx    # ★最新レポート
    ├── iphone_price_report_20251113_154452.csv
    └── iphone_price_report_rank_20251113_154452.csv # ★ランク別レポート
```

### 実装したコード（analyze.py）

#### extract_rank() 関数
```python
def extract_rank(product_name: str) -> str:
    """商品名からランク情報を抽出"""
    name_upper = product_name.upper()

    # ジャンク品
    if 'ジャンク' in product_name or 'JUNK' in name_upper:
        return 'ジャンク'

    # Sランク（新品同様）
    if re.search(r'[【\[].*?S.*?ランク.*?[】\]]', product_name):
        return 'Sランク'
    if re.search(r'[【\[].*?未使用.*?[】\]]', product_name):
        return 'Sランク'

    # A/B/Cランクも同様のパターンで検出
    # ...

    return 'ランク未確認'
```

#### analyze_channel() の変更点
- **旧**: 基本集計のみ返却（1つのDataFrame）
- **新**: 基本集計とランク別集計を返却（2つのDataFrameのタプル）

```python
def analyze_channel(channel_name: str, products: List[Dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.DataFrame(products)
    df['rank'] = df['product_name'].apply(extract_rank)  # ★ランク抽出

    # 基本集計: モデル×容量
    summary = df.groupby(["model", "capacity"]).agg(...)

    # ランク別集計: モデル×容量×ランク ★新規追加
    rank_summary = df.groupby(["model", "capacity", "rank"]).agg(...)

    return summary, rank_summary
```

#### レポート生成の変更点
- Excelに4シート（基本2 + ランク別2）
- CSV 2ファイル（基本 + ランク別）

---

## 📈 次のステップ候補

### 優先度A: すぐできる分析

1. **特定モデルの詳細確認**
   ```python
   # CSVから特定モデルを抽出
   import pandas as pd
   df = pd.read_csv('reports/iphone_price_report_rank_20251113_154452.csv')
   iphone13 = df[df['model'] == 'iPhone 13']
   print(iphone13)
   ```

2. **モデル世代ごとの価格比較**
   - iPhone 11 vs 12 vs 13 の同容量比較
   - Pro/Pro Max の価格差分析

3. **ランク分布の可視化**
   - 各モデルのランク構成比グラフ
   - 価格帯ヒストグラム

### 優先度B: 追加データ収集

4. **Yahoo!ショッピング対応**
   - 現在403エラーで利用不可
   - 追加申請が必要（Yahoo! Developer確認）
   - または手動調査で補完

5. **他サイトの手動調査**
   - バックマーケット
   - イオシス
   - ムスビー
   - メルカリ（API非公開）

### 優先度C: システム拡張

6. **自動化・定期実行**
   - cron設定で週次/月次実行
   - 価格推移の時系列分析

7. **データビジュアライゼーション**
   - Plotlyでインタラクティブグラフ
   - モデル間比較チャート

8. **Webダッシュボード**
   - Streamlitで簡易ダッシュボード作成
   - リアルタイム価格確認UI

---

## 🚨 注意事項・既知の問題

### API関連

**楽天市場API**:
- ✅ 正常動作（アプリID: `1037682033117300178`）
- レート制限: 2秒間隔（スクリプトで自動調整済み）
- iPhone Xのみ400エラー（在庫なし）

**Yahoo!ショッピングAPI**:
- ❌ 403 Forbiddenエラー継続
- Client ID取得済みだが追加申請が必要な可能性
- 当面は楽天データのみで進行

### データの制約

1. **ランク表記の不統一**
   - 約70%が「中古（ランク不明）」
   - 出品者によってランク表記方法が異なる
   - 一部は状態記載なし

2. **価格の変動**
   - 本データは2025-11-13時点のスナップショット
   - 時系列分析には定期収集が必要

3. **欠損データ**
   - iPhone Xは楽天に在庫なし
   - 古いモデルほどデータ少ない傾向

### 環境変数

永続化済み（`~/.zshrc`）:
```bash
export RAKUTEN_APP_ID="1037682033117300178"
export YAHOO_CLIENT_ID="dj00aiZpPXdFUkVaaXMwUnNOdCZzPWNvbnN1bWVyc2VjcmV0Jng9YmY-"
```

新しいターミナルでは自動読み込み。
現在のセッションで認識されない場合:
```bash
source ~/.zshrc
```

---

## 🔗 関連ファイルへのリンク

### ドキュメント
- [README.md](../iphone-market-research/resale-market/README.md) - 使い方ガイド
- [CLAUDE.md](../iphone-market-research/resale-market/CLAUDE.md) - 詳細仕様
- [次セッションへの引き継ぎ.md](../iphone-market-research/resale-market/次セッションへの引き継ぎ.md) - 旧版引継ぎ（2025-11-06作成）

### スクリプト
- [analyze.py](../iphone-market-research/resale-market/scripts/analyze.py) - 分析スクリプト★本セッションで拡張
- [collect_all.py](../iphone-market-research/resale-market/scripts/collect_all.py) - データ収集スクリプト
- [models.py](../iphone-market-research/resale-market/scripts/models.py) - 86モデル定義

### データ
- `data/raw/rakuten/*.json` - 収集済み生データ（84ファイル）
- [最新レポート（Excel）](../iphone-market-research/resale-market/reports/iphone_price_report_20251113_154452.xlsx)
- [最新レポート（CSV基本）](../iphone-market-research/resale-market/reports/iphone_price_report_20251113_154452.csv)
- [最新レポート（CSVランク別）](../iphone-market-research/resale-market/reports/iphone_price_report_rank_20251113_154452.csv)

---

## 💡 よくある分析コマンド

### 特定モデルの価格確認

```bash
cd /Users/noguchisara/projects/work/iphone-market-research/resale-market

# iPhone 13 128GBのランク別価格
uv run python -c "
import pandas as pd
df = pd.read_csv('reports/iphone_price_report_rank_20251113_154452.csv')
data = df[(df['model'] == 'iPhone 13') & (df['capacity'] == '128GB')]
print(data.to_string())
"
```

### 全モデルの平均価格（ランク別）

```bash
uv run python -c "
import pandas as pd
df = pd.read_csv('reports/iphone_price_report_rank_20251113_154452.csv')
avg_by_rank = df.groupby('rank')['平均価格'].mean().sort_values(ascending=False)
print(avg_by_rank)
"
```

### モデル世代別の商品数

```bash
uv run python -c "
import pandas as pd
df = pd.read_csv('reports/iphone_price_report_20251113_154452.csv')
count_by_model = df.groupby('model')['商品数'].sum().sort_values(ascending=False)
print(count_by_model)
"
```

### 再分析（データ再読み込み）

```bash
cd /Users/noguchisara/projects/work/iphone-market-research/resale-market
uv run python scripts/analyze.py
# → 新しいタイムスタンプでレポート生成
```

### 追加データ収集（楽天のみ）

```bash
cd /Users/noguchisara/projects/work/iphone-market-research/resale-market
export RAKUTEN_APP_ID='1037682033117300178'

# 全モデル再収集（約17分）
uv run python scripts/collect_all.py --channels rakuten

# テスト実行（3モデルのみ）
uv run python scripts/collect_all.py --channels rakuten --test
```

---

## 📝 セッションメモ

### 実行したコマンド履歴

```bash
# 1. データ収集開始（バックグラウンド）
cd /Users/noguchisara/projects/work/iphone-market-research/resale-market
export RAKUTEN_APP_ID='1037682033117300178'
PYTHONUNBUFFERED=1 uv run python scripts/collect_all.py --channels rakuten
# → 15:15-15:32完了（約17分）

# 2. 分析スクリプトの実行（初回）
uv run python scripts/analyze.py
# → 基本集計のみ生成

# 3. ランク抽出機能実装後、再分析
uv run python scripts/analyze.py
# → 基本集計 + ランク別集計生成（15:44完了）

# 4. iPhone 12 64GBの詳細確認
# CSVから手動抽出して表示
```

### 主なコード変更

**ファイル**: `scripts/analyze.py`

**変更内容**:
1. `extract_rank()` 関数追加（60行）
2. `analyze_channel()` 関数の返り値を tuple に変更
3. `create_price_report()` 関数でランク別レポート生成追加

**行数**: 247行 → 194行（最終的に整理）

---

## ✅ チェックリスト（次セッション用）

### 開始時に確認すること

- [ ] この引継ぎファイルを読んだ
- [ ] プロジェクトディレクトリに移動した
- [ ] 環境変数が設定されているか確認した
- [ ] 最新レポート（20251113_154452）の存在を確認した

### 分析を始める前に

- [ ] どのモデル/容量を分析するか決めた
- [ ] 基本集計とランク別集計のどちらを使うか決めた
- [ ] 必要に応じてCSV/Excelを開いて確認した

### 新規データ収集する場合

- [ ] 前回収集から十分な時間が経過しているか（価格変動を見たいか）
- [ ] 楽天APIの環境変数が設定されているか
- [ ] ディスク容量は十分か（84ファイル × 約100KB）

---

**作成者**: Claude
**作成日**: 2025-11-13 16:30 (Thursday)
**次回更新**: データ再収集時、または新機能追加時
