---
name: bm-condition-check
description: BMコンディション不明チェック。販売経路がバックマーケットでBMコンディション未入力のレコードを特定し、Back Market APIでコンディションを取得してKintoneを一括更新する。
---

# BMコンディション不明チェック

## 概要

財務管理表（販売シート）で、販売経路が「バックマーケット」かつBMコンディションが空白のレコードを特定し、Back Market販売者APIでコンディション（グレード）を取得して、KintoneのBMコンディションフィールドを一括更新する。

## 認証情報

認証情報は `.claude/auth/credentials.md` を参照。

- **Google Sheets API**: `.claude/skills/assessment/credentials.json`（サービスアカウント）
- **Back Market販売者サイト**: info@applebuyers.jp / 4126Uprose
- **Kintone**: noguchisara@japanconsulting.co.jp / 4126uprose

---

## ワークフロー

### 1. 対象レコード抽出（Google Sheets API）

**スプレッドシート**: `1Gg4Lvvlx25GGk-LdEnr8apUO2Q4e2ZOYovaAlBfV7os`
**シート**: 販売（GID: 1310950962）

**フィルタ条件**:
- 販売経路（列AU / index 46）= `バックマーケット`
- BMコンディション（列AK / index 36）= 空白
- レコード番号（列A / index 0）= 空でない

```python
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

CREDS_PATH = '.claude/skills/assessment/credentials.json'
SPREADSHEET_ID = '1Gg4Lvvlx25GGk-LdEnr8apUO2Q4e2ZOYovaAlBfV7os'

creds = Credentials.from_service_account_file(CREDS_PATH, scopes=['https://www.googleapis.com/auth/spreadsheets'])
service = build('sheets', 'v4', credentials=creds)

result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range='販売!A1:AV5000'
).execute()
rows = result.get('values', [])

# レコード番号: col 0, BMコンディション: col 36, 販売経路: col 46
records = []
for row in rows[1:]:
    while len(row) <= 46:
        row.append('')
    if row[46].strip() == 'バックマーケット' and row[36].strip() == '' and row[0].strip() != '':
        records.append(row[0].strip())
```

---

### 2. Back MarketでSKU検索→コンディション取得

**前提**: Back Marketの販売者サイトにログイン済みのブラウザセッションが必要。

**セッション準備**:
1. MCP Playwrightブラウザで https://www.backmarket.co.jp/bo-seller/orders/all にアクセス
2. ログイン（2FA必要 → ユーザーにコード確認）
3. ストレージステートを保存:
```javascript
async (page) => {
  const context = page.context();
  await context.storageState({ path: 'auth/backmarket_session.json' });
}
```

**SKU検索パターン**（5パターンすべて試す）:
1. レコード番号そのまま（例: `338613`）
2. レコード番号 + 半角小文字s（例: `338613s`）
3. レコード番号 + 半角大文字S（例: `338613S`）
4. レコード番号 + 全角小文字ｓ（例: `338613ｓ`）
5. レコード番号 + 全角大文字Ｓ（例: `338613Ｓ`）

**API エンドポイント**:
- 注文検索: `GET https://www.backmarket.co.jp/bm/merchants/orders?page=1&pageSize=10&endDate={today}&sku={sku}`
- 注文詳細: `GET https://www.backmarket.co.jp/bm/merchants/orders/{orderId}`

**コンディション取得**: 注文詳細レスポンスの `orderLines[0].grade.label` がコンディション値。

| grade.label | grade.code | 意味 |
|-------------|-----------|------|
| プレミアム | （要確認） | 最高グレード |
| Aグレード | （要確認） | 良品 |
| Bグレード | （要確認） | 使用感あり |
| Cグレード | ECO | 目立つ傷あり |

---

### 3. Kintone更新（REST API）

**アプリ**: 買取販売リスト(iPhone,iPad)（App ID: 11）
**フィールドコード**: `BackMarketコンディション`
**選択肢**: プレミアム / Aグレード / Bグレード / Cグレード

```python
import requests, base64

auth = base64.b64encode(b'noguchisara@japanconsulting.co.jp:4126uprose').decode()
headers = {'X-Cybozu-Authorization': auth, 'Content-Type': 'application/json'}

payload = {
    'app': 11,
    'id': record_number,
    'record': {
        'BackMarketコンディション': {'value': 'Cグレード'}
    }
}
requests.put('https://japanconsulting.cybozu.com/k/v1/record.json', headers=headers, json=payload)
```

---

## 一括処理の実行方法

Playwrightの保存済みセッションを使い、Back Market APIをfetchで呼び出す方式が最速。

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(storage_state='auth/backmarket_session.json')
    page = context.new_page()
    page.goto('https://www.backmarket.co.jp/bo-seller/orders/all', wait_until='domcontentloaded')

    # page.evaluate() でfetchを実行してAPI呼び出し
    resp = page.evaluate(f"""async () => {{
        const r = await fetch('https://www.backmarket.co.jp/bm/merchants/orders?page=1&pageSize=10&endDate=2026-01-29&sku={sku}');
        return await r.json();
    }}""")
```

---

## 注意事項

- Back Marketのセッションは時間経過で切れる。切れた場合はMCPブラウザで再ログイン＆セッション再保存が必要（2FA必要）
- 全パターンのSKUで該当なしのレコードは、Back Market以外の特殊販売やデータ不整合の可能性があるため、一覧を報告してスルーする
- API負荷軽減のため、各リクエスト間に0.3〜0.5秒の待機を入れる
- 販売シートは最大5000行まで取得される。それ以上の場合は範囲を拡張する
