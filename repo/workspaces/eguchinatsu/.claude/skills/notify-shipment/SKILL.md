---
name: notify-shipment
description: 送り状PDFから追跡番号を抽出しNotionに記入、SlackにPDF添付送信。「発送通知して」「追跡番号をNotionに」と言われた時に使用。
---

# 発送完了通知スキル

送り状PDFから追跡番号を抽出し、Notionの備考欄に記入、SlackにPDFを添付送信する。

## 前提条件

- Playwright MCPが有効であること
- 送り状PDFがダウンロード済みであること（`.playwright-mcp/UMINXXXXXXXXX`）
- Notionの発送予定ページが開いていること
- Slackにログイン済みであること

## 入力

| 項目 | 説明 | 例 |
|------|------|-----|
| PDFパス | ダウンロード済みPDFのパス | `.playwright-mcp/UMIN0002042929` |
| SKU | 対象商品のSKU（Notion検索用） | 336363 |
| Slackチャンネル | 送信先チャンネル | applebuyers |

## ワークフロー

### 1. PDFから追跡番号を抽出

PyPDF2を使用してPDFから追跡番号を抽出：

```python
import re
from PyPDF2 import PdfReader

reader = PdfReader(r'PDFパス')
text = ''
for page in reader.pages:
    text += page.extract_text()

# 追跡番号パターン: XXXX-XXXX-XXXX
tracking_numbers = re.findall(r'\d{4}-\d{4}-\d{4}', text)
tracking_number = list(set(tracking_numbers))[0]
print(f'追跡番号: {tracking_number}')
```

追跡番号形式: `4694-XXXX-XXXX`

### 2. Notionの発送予定ページを開く

```
URL: https://www.notion.so/japanconsulting/ebaadbf255204fddb6098081a1715f9f?v=6bbe9978896c44c7a04ad8476491231c
```

### 3. SKUで対象行を検索

1. 発送予定一覧からSKUが一致する行を探す
2. 該当行の「備考」列をクリック

### 4. 追跡番号を備考欄に入力

1. 備考セルをクリックして編集モードに
2. 追跡番号をペースト（例: `4694-4122-6096`）
3. セル外をクリックして確定

### 5. Slackにログイン（未ログインの場合）

```
URL: https://app.slack.com/client/T5CF8BCDP/CTB9H9NLR
```

Google認証でログイン（アカウント: `eguchinatsu@japanconsulting.co.jp`）

### 6. 対象チャンネルを選択

1. 左サイドバーから対象チャンネル（例: applebuyers）をクリック
2. または `Ctrl+K` で検索

### 7. PDFを添付して送信

1. メッセージ入力欄の「添付」ボタン（クリップアイコン）をクリック
2. 「コンピューターからアップロード」を選択
3. ファイル選択ダイアログでPDFを選択
   - 複数ファイルの場合は複数選択可能
4. 「今すぐ送信する」ボタンをクリック

## Slack操作の詳細

### ファイルアップロード手順

```yaml
# 添付ボタン
button "添付" [ref=e2444]

# メニュー項目
menuitem "コンピューターからアップロード" [ref=e3220]

# ファイル選択後
button "今すぐ送信する" [ref=e3277]
```

### 複数ファイル送信

`browser_file_upload` ツールで複数パスを配列で指定：

```json
{
  "paths": [
    "c:\\...\\UMIN0001963388",
    "c:\\...\\UMIN0002042929"
  ]
}
```

## 完了確認

以下を確認して完了：

1. **Notion**: 備考欄に追跡番号が記入されている
2. **Slack**: PDFファイルがチャンネルに投稿されている
   - 投稿者名と時刻が表示
   - ファイル名（UMINXXXXXXXXX）が表示

## エラー処理

| エラー | 対処 |
|--------|------|
| PDF読み取り失敗 | ファイルパスを確認、PyPDF2がインストールされているか確認 |
| 追跡番号が見つからない | PDFのテキスト内容を直接確認 |
| Notion行が見つからない | SKU番号を確認、ページをリロード |
| Slackアップロード失敗 | ファイルパスの存在確認、再試行 |

## 出力

処理完了後、以下を報告：

```
【発送通知完了】
- 追跡番号: 4694-4122-6096
- Notion備考欄: 更新済み
- Slack送信: applebuyers チャンネルに送信済み
- PDF: UMIN0002042929
```

## 関連スキル

- `create-shipping-label`: 送り状作成（このスキルの前に実行）
- `yamato-login`: ヤマトB2クラウドへのログイン
