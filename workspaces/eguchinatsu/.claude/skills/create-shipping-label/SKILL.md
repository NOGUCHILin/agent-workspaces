---
name: create-shipping-label
description: B2クラウドで宅急便コンパクトの送り状を作成しPDFダウンロード。「送り状作って」「ラベル作成」と言われた時に使用。
---

# B2クラウド 送り状作成スキル

ヤマトB2クラウドで宅急便コンパクトの送り状を作成し、PDFをダウンロードする。

## 前提条件

- Playwright MCPが有効であること
- B2クラウドにログイン済みであること（未ログインの場合は `yamato-login` スキルを先に実行）
- お届け先情報（名前、電話番号、郵便番号、住所）が分かっていること

## 必要な情報

| 項目 | 説明 | 例 |
|------|------|-----|
| お届け先名 | フルネーム（カタカナ自動変換） | 佐藤拓也 |
| 電話番号 | ハイフンあり/なし両対応 | 080-6333-5678 |
| 郵便番号 | 7桁 | 718-0003 |
| 住所 | 都道府県から | 岡山県新見市高尾706-1 |
| SKU | 品名として入力 | 336363 |

## ワークフロー

### 1. B2クラウド発行画面に移動

```
URL: https://newb2web.kuronekoyamato.co.jp/create
```

### 2. 発送方法を選択

**重要: 「宅急便コンパクト」を選択（「発払い」ではない）**

1. 「発払い」の横にある「宅急便コンパクト」ボタンをクリック
2. 発行条件設定が表示される

### 3. お届け先情報を入力

1. 「お届け先」欄の「直接入力」タブをクリック
2. 以下を入力：
   - **電話番号**: 最初のフィールドに入力
   - **郵便番号**: 郵便番号フィールドに入力 → 「住所検索」クリック
   - **番地・号以降**: 残りの住所（番地など）を入力
   - **お届け先名**: 漢字で入力（カタカナは自動生成）

### 4. ご依頼主を選択

1. 「ご依頼主」欄の「アドレス帳」タブをクリック
2. 検索ボタンを押す（検索窓は空のまま）
3. 表示された候補をクリックして選択

### 5. 品名・荷扱いを入力

1. **品名1**: SKU番号を入力（例: 336363）
2. **取扱注意**: 「精密機器」を選択
   - 「特に指定なし」をクリック
   - ドロップダウンから「精密機器」を選択

### 6. 送り状を発行

1. 画面下部の「登録」ボタンをクリック
2. 確認ダイアログで「登録」をクリック
3. 発行完了画面で「印刷」ボタンをクリック

### 7. PDFをダウンロード

印刷プレビューはiframe内に表示され、通常のスナップショットでは読み取れない。
`browser_run_code` を使用してPDFを直接ダウンロードする。

#### 方法1: iframeのsrcからダウンロード（推奨）

```javascript
async (page) => {
  // iframeのsrc属性からPDF URLを取得
  const iframeSrc = await page.locator('iframe').getAttribute('src');
  // 例: /b2/p/B2_OKURIJYO?issue_no=UMIN0002382100&fileonly=1

  const pdfUrl = 'https://newb2web.kuronekoyamato.co.jp' + iframeSrc;

  // ダウンロードイベントを待機
  const downloadPromise = page.waitForEvent('download');

  // ダウンロードリンクを作成してクリック
  await page.evaluate((url) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = 'shipping-label.pdf';
    link.click();
  }, pdfUrl);

  const download = await downloadPromise;
  return {
    path: await download.path(),
    filename: download.suggestedFilename()
  };
}
```

#### 方法2: 再発行画面からダウンロード

発行済みの送り状をダウンロードする場合：

1. メインメニュー → 「再発行」
2. 送り状番号で検索
3. 選択 → 「印刷内容の確認へ」
4. 「発行開始」→ 上記の方法でダウンロード

#### ダウンロード結果

- 保存先: `.playwright-mcp/UMINXXXXXXXXX.pdf`
- ファイル名形式: `UMIN` + 10桁の番号 + `.pdf`
- 例: `UMIN0002382100.pdf`

### 8. 送り状番号を取得

ダウンロードしたPDFを読み取り、送り状番号（追跡番号）を抽出する。

```javascript
// PDFを読み取って送り状番号を抽出
const pdfPath = '.playwright-mcp/UMIN0002042929.pdf';
// Readツールでpdfを読み取り、正規表現で抽出
const trackingNumber = content.match(/\d{4}-\d{4}-\d{4}/)?.[0];
// 例: 4694-4122-6096
```

- 形式: `XXXX-XXXX-XXXX`（ハイフン区切り12桁）
- 例: `4694-4122-6096`

この送り状番号は `notify-shipment` スキルで使用する。

## フォーム要素のref（参考）

| 要素 | 説明 |
|------|------|
| 宅急便コンパクト | button "宅急便コンパクト" |
| 電話番号 | textbox（お届け先セクション内） |
| 郵便番号 | textbox + 「住所検索」ボタン |
| お届け先名 | textbox "お届け先名" |
| 品名1 | textbox "品名1" |
| 取扱注意 | combobox "取扱注意" |
| 登録 | button "登録" |
| 印刷 | button "印刷" |

## 複数送り状の作成

複数の送り状を作成する場合：
1. 最初の送り状を作成・PDF保存
2. 「発行」画面に戻る
3. 次の送り状を作成

## エラー処理

| エラー | 対処 |
|--------|------|
| 住所検索で該当なし | 手動で都道府県・市区町村を選択 |
| 電話番号形式エラー | ハイフンを除去して再入力 |

## 出力

- ダウンロードされたPDFファイルパス（例: `.playwright-mcp/UMIN0002042929`）
- このパスは次のスキル（`notify-shipment`）で使用

## 関連スキル

- `yamato-login`: B2クラウドへのログイン
- `notify-shipment`: 追跡番号抽出→Notion記入→Slack通知
