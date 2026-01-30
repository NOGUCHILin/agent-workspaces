# Work専用ルール

このファイルは`work/`ディレクトリ配下での作業時のみ適用されます。

<important-links>
## 重要リンク
- **財務管理表**: https://docs.google.com/spreadsheets/d/1Gg4Lvvlx25GGk-LdEnr8apUO2Q4e2ZOYovaAlBfV7os/edit?pli=1&gid=1310950962#gid=1310950962
</important-links>

<business-hours>
## 営業時間
- 営業時間: 10:00 - 19:00
- 休憩時間: 13:00 - 14:00
</business-hours>

<task-reminder>
## タスクリマインダールール

### 🔴 重要: 自動表示ルール
- **workディレクトリ内での作業時は、必ず最初の応答で野口器個人のタスクを表示する**
- workディレクトリに関する質問・指示・作業が出現したら即座にタスクを表示
- 「タスク確認して」と明示的に言われなくても、work関連の会話では常にタスクを表示
- このルールは絶対に忘れない

### タスク確認時の動作
- **デフォルト（「タスク確認」「タスク見せて」など）**: 野口器個人のタスク（`<pending-tasks>`セクション）を表示
- **「スタッフのタスク確認」**: `task-management/tasks/`内の最新日付のスタッフ割り当てを表示

### 表示フォーマット
- work関連の作業時は、応答の最後に未完了タスクを担当者ごとにグループ化して縦並びで表示する
- フォーマット:
  ```
  📋 未完了タスク:
  【野口器単独】
  - タスク名1
  - タスク名2

  【野口器・野口凜共同】
  - タスク名3

  【野口器・本間久隆共同】
  - タスク名4

  【野口器・本間久隆協力】
  - タスク名5

  【野口創・本間久隆一任】
  - タスク名6
  ```
- タスクがない場合は表示しない
- **完了タスクが発生したら、必ず`<pending-tasks>`セクションから削除する**
</task-reminder>

<pending-tasks>
## 未完了タスク

### 野口器単独（ルーティン）
- クレカ残高の記載
- 買取価格変更
- 資金繰り表の更新

### 野口器単独（返事待ち）
（なし）

### 野口器単独
1. **【完了】既存プロジェクトをスキル化**
2. **【完了】朝の金額KPI入力のスキル化** → `/morning-kpi`
3. **【完了】夜の金額KPI入力のスキル化** → `/evening-kpi`
4. **【完了】資金繰り表入力のスキル化** → `/cashflow-update`
5. **【完了】タスク設定のスキル化** → `/task-setup`
6. **【完了】請求書作成**（エクスチェンジャー向け）→本間さんにLINE送付
7. **【完了】クレジットカード作成**（一枚目到着、二枚目審査待ち）
8. **【バグ修正のみ】査定のスキル化** → `/assessment`（データ整理部分完了、連絡・結果連絡は今後追加）
9. **【新規】価格調整のスキル化**
10. **【バグ修正のみ】財務管理系スキル化**（残り確認のみ）
11. **【完了】消費税還付金の徹底調査**（約56万円還付見込み）
14. **【完了】Kintoneの不具合や修理の内容を全て適切なものに変更**
15. **【新規】ジャンク品の買取価格を全て確認し、変更**

### 野口器・佐々木悠斗共同
- **【新規】店舗端末の全検品、ムスビー・直売振り分け**
- **【新規】仕分け時の判別システム**

### 野口器・江口那都共同
- **【新規】連絡系スキル化**（メール・Slack確認の自動化）
- **【新規】労務・税務・経理のスキル化**

### 野口器・野口凜共同
（タスクなし）

### 野口器・野口凜・本間久隆共同
- 未払い金の整理

### 野口器・本間久隆共同
（タスクなし）

### 野口器・本間久隆協力
（タスクなし）

### 本間久隆一任
（タスクなし）
</pending-tasks>

<staff-skills>
## スタッフスキルマトリックス

### 江口 那都（えぐちなつ）
返信, 振込メッセ, 催促, 査定結果, 返送交渉, 梱包キット作成, 開封, アクティベート, 査定, 成約仕分, 検品, 出品, KPI入力, 実残高入力, 座席決定, タスク設定, 発送準備, 送り状作成, 進捗変更, 発送完了連絡, 品質管理, 電話対応, ムスビー撮影, ムスビー出品, 店舗準備, 店舗査定

### 雜賀 晴士（さいがはるし）
返信, 振込メッセ, 催促, 梱包キット作成, 開封, 査定, 成約仕分, 出品, 修理, パーツ注文, KPI入力, タスク設定, BM在庫確認, 発送準備, 送り状作成, 進捗変更, 電話対応, ムスビー撮影, ムスビー出品, 店舗準備, 店舗査定

### 野口 器（のぐちさら）
返信, 振込メッセ, 査定結果, 返送交渉, 梱包キット作成, 開封, アクティベート, 査定, 成約仕分, 出品, KPI入力, 実残高入力, 座席決定, タスク設定, BM在庫確認, 発送準備, 送り状作成, 進捗変更, 発送完了連絡, 新品価格変更, 電話対応, ムスビー撮影, ムスビー出品, 店舗準備, 店舗査定, 店舗修理受付, 経理業務, データ分析

### 野口 創（のぐちそう）
返信, 振込メッセ, 催促, 梱包キット作成, 開封, 査定, 成約仕分, 修理, パーツ注文, タスク設定, BM在庫確認, 進捗変更, 電話対応, ムスビー出品, 店舗準備, 店舗査定, 店舗修理受付, 法人販売

### 佐々木 悠斗（ささきゆうと）
返信, 振込メッセ, 査定結果, 返送交渉, 梱包キット作成, 開封, アクティベート, 査定, 成約仕分, 検品, 出品, KPI入力, 座席決定, タスク設定, BM在庫確認, 発送準備, 送り状作成, 進捗変更, 発送完了連絡, 新品価格変更, 品質管理, 電話対応, ムスビー撮影, ムスビー出品, 店舗準備, 店舗査定, 店舗修理受付, 法人販売

### 須加尾 蓮（すがおれん）
梱包キット作成, 開封, アクティベート, 査定, タスク設定, BM在庫確認, ムスビー撮影, ムスビー出品

### 高橋 諒（たかはしりょう）
梱包キット作成, 開封, 査定, 成約仕分, 修理, パーツ注文, タスク設定, BM在庫確認

### 島田 博文（しまだひろふみ）
返信, 振込メッセ, 催促, 梱包キット作成, 開封, アクティベート, 査定, 成約仕分, 修理, タスク設定, BM在庫確認, 発送準備, 送り状作成, 進捗変更, 電話対応, ムスビー撮影, ムスビー出品, 店舗準備, 店舗査定, 店舗修理受付

### 平山 優大（ひらやまゆうだい）
返信, 振込メッセ, 催促, 梱包キット作成, 開封, 査定, タスク設定, BM在庫確認, 発送準備, 送り状作成, 進捗変更, 電話対応, ムスビー出品, 店舗準備, 店舗査定

### 細谷 尚央（ほそやたかひろ）
梱包キット作成, 開封, アクティベート, 査定, 検品, 出品, タスク設定, BM在庫確認, ムスビー撮影, ムスビー出品

### NANT YOON THIRI ZAW OO（シャシャ）
梱包キット作成, 開封, アクティベート, 査定, 成約仕分, 検品, 出品, タスク設定, BM在庫確認, ムスビー撮影, ムスビー出品

### 原 紅映（はらくれは）
返信, 振込メッセ, 催促, 開封, アクティベート, 査定, 成約仕分, 検品, 発送準備, 送り状作成, 品質管理

### 野口 博史（のぐちひろし）
（スキルなし）

### 野口 凜（のぐちりん）
返信, 修理

### 本間 久隆（ほんまひさたか）
（スキルなし）

## スタッフ名表記ルール
- スタッフ名を記載する際は、上記スタッフスキルマトリックスに記載されている正しい漢字を使用すること
- このプロジェクトで作業しているユーザーは「野口 器（のぐちさら）」である
</staff-skills>

<buyback-flow>
## iPhone買取フロー（LINE経由）

### フロー概要
1. 顧客がLINEから買取申込
2. 無料梱包キット送付
3. ヤマト運輸の集荷システムで顧客のiPhoneを受取
4. 査定・買取実施

### 計測可能データ
- **梱包キット数**: 日次で取得可能（CSV形式）
- **集荷要請数**: 日次で取得可能（CSV形式）
- **粒度**: 機種・容量・ランクごとに分類されたデータが取得可能

### データ構造
CSVファイルには以下の項目が含まれる：
- 機体型番（例: iPhone 15 Pro）
- 記憶容量（例: 256GB）
- 等級/ランク（例: 新品・未開封、美品、使用感あり等）
- 梱包キット数（日次）
- 集荷要請数（日次）

### 買取価格データ
- 買取価格表: `iphone-market-research/買取価格YYYYMMDD.csv`
- 販売価格表: `iphone-market-research/販売価格YYYYMMDD.csv`
- 価格変更履歴: 記録済み
- 粗利基準: `iphone-market-research/generate_optimizer.py`内のCRITERIA変数に定義

### 価格変更効果の計測目的
現在設定されている最低粗利・粗利率の基準値が、以下の観点で適切かを検証：
1. 買取数の増加に寄与しているか
2. 粗利の最適化ができているか
3. 機種・容量・ランク別の最適な価格設定の発見

### 効果計測システム
**プロジェクト**: `iphone-market-research/price-impact-analysis/`

**主要スクリプト**:
- `scripts/collect_data.py`: データ収集・整形（不良なし端末限定）
- `scripts/analyze_impact.py`: 効果分析（変更前1週間 vs 変更後1週間）
- `scripts/generate_report.py`: Excelレポート生成

**出力ファイル**:
- `data/results/collected_data_YYYYMMDD.csv`: 収集済みデータ
- `data/results/impact_analysis_YYYYMMDD.csv`: 分析結果
- `data/results/impact_report_YYYYMMDD.xlsx`: レポート

**詳細**: `iphone-market-research/price-impact-analysis/README.md` を参照
</buyback-flow>

<playwright-rules>
## Playwright高速化ルール

Playwrightを使用するスクリプトを書く際は、以下のルールを**必ず**適用すること。

### 🚨 禁止事項

1. **`slow_mo`は絶対に使わない**
   ```python
   # NG
   browser = playwright.chromium.launch(slow_mo=100)

   # OK
   browser = playwright.chromium.launch(headless=True)
   ```

2. **`time.sleep()`は絶対に使わない**
   ```python
   # NG
   time.sleep(5)
   page.wait_for_timeout(5000)

   # OK: 要素待機
   page.wait_for_selector('#result')
   page.locator('#loading').wait_for(state='hidden')
   ```

3. **`networkidle`は使わない**（SPAでハングする）
   ```python
   # NG
   page.wait_for_load_state('networkidle')

   # OK
   page.wait_for_load_state('domcontentloaded')
   ```

### ✅ 必須事項

1. **不要リソースのブロック**
   ```python
   def block_unnecessary_resources(page):
       BLOCKED = ['image', 'stylesheet', 'font', 'media']
       def handler(route):
           if route.request.resource_type in BLOCKED:
               route.abort()
           else:
               route.continue_()
       page.route('**/*', handler)
   ```

2. **storage_stateでセッション再利用**
   ```python
   # 保存
   context.storage_state(path='auth/session.json')

   # 再利用
   context = browser.new_context(
       storage_state='auth/session.json' if Path('auth/session.json').exists() else None
   )
   ```

3. **動的待機を使う**
   ```python
   # 要素の出現を待つ
   page.wait_for_selector('#content')

   # 要素が消えるのを待つ
   page.locator('#spinner').wait_for(state='hidden')

   # APIレスポンスを待つ
   with page.expect_response('**/api/data*') as response_info:
       page.click('#fetch-button')
   ```

4. **ブラウザ起動オプション**
   ```python
   browser = playwright.chromium.launch(
       headless=True,
       args=['--disable-dev-shm-usage']
   )
   ```

### 待機方法の選択基準

| 状況 | 使う待機 |
|------|----------|
| 要素の表示待ち | `page.wait_for_selector('#id')` |
| 要素の非表示待ち | `page.locator('#id').wait_for(state='hidden')` |
| ページ読み込み | `page.wait_for_load_state('domcontentloaded')` |
| API応答待ち | `page.expect_response('**/api/*')` |
| URL変更待ち | `page.wait_for_url('**/dashboard')` |

### 最適化テンプレート

```python
from playwright.sync_api import sync_playwright
from pathlib import Path

AUTH_DIR = Path(__file__).parent / "auth"
BLOCKED_RESOURCES = ['image', 'stylesheet', 'font', 'media']

def block_resources(page):
    def handler(route):
        if route.request.resource_type in BLOCKED_RESOURCES:
            route.abort()
        else:
            route.continue_()
    page.route('**/*', handler)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # セッション再利用
        state_file = AUTH_DIR / "state.json"
        context = browser.new_context(
            storage_state=str(state_file) if state_file.exists() else None
        )
        page = context.new_page()

        # リソースブロック
        block_resources(page)

        # 処理...
        page.goto('https://example.com')
        page.wait_for_selector('#content')

        # セッション保存
        context.storage_state(path=str(state_file))
        browser.close()
```
</playwright-rules>
