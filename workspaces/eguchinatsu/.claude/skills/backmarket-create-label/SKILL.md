---
name: backmarket-create-label
description: Back Market注文のB2クラウド送り状作成（PDFダウンロードなし）。「BM送り状作って」「バックマーケット送り状」と言われた時に使用。
---

# Back Market 送り状作成スキル

Back Marketの発送予定注文に対して、B2クラウドで宅急便コンパクトの送り状を発行する（PDFダウンロードなし）。

## 前提条件

- Playwright MCPが有効であること
- B2クラウドにログイン済みであること
- Back Market seller portalにログイン済みであること

## ワークフロー概要

1. Back Marketで発送予定注文を確認
2. B2クラウドで送り状を作成・発行
3. 全ての注文を処理するまで繰り返し

## 手順

### 1. Back Marketで発送予定注文を確認

```
URL: https://www.backmarket.co.jp/bo-seller/orders/all?page=1&pageSize=100&endDate={today}&state=MERCHANT_NEED_TO_SEND
```

「発送予定」ステータスの注文一覧から以下を取得：
- 注文番号
- SKU（末尾の's'などの文字は検索時に除外）
- お客様名

### 2. B2クラウド「1件ずつ発行」画面を開く

```
URL: https://newb2web.kuronekoyamato.co.jp/single_issue_reg.html
```

### 3. 各注文の処理

#### 3.1 Back Marketから住所情報を取得

1. Back Marketタブで該当注文の注文番号ボタンをクリック
2. 右側に表示されるパネルから住所情報を取得：
   - お届け先名
   - 電話番号
   - 郵便番号
   - 住所（市区町村、町・番地）

#### 3.2 B2クラウドでフォーム入力

```javascript
async (page) => {
  // 宅急便コンパクトを選択
  await page.locator('input[value="8"]').click();

  // 電話番号
  await page.locator('#consignee_telephone').fill('電話番号');

  // 郵便番号
  await page.locator('#consignee_zip_code').fill('郵便番号');

  // お届け先名
  await page.getByRole('row', { name: 'お届け先名称' })
    .getByPlaceholder('例)ヤマト運輸株式会社').fill('お届け先名');

  // 品名（SKU番号）
  await page.getByRole('textbox', { name: '例)衣類' }).fill('SKU番号');

  // 荷扱い1を精密機器に設定（必ずclear()してからfill()）
  await page.locator('#shipment_titlehandling_information1').clear();
  await page.locator('#shipment_titlehandling_information1').fill('精密機器');

  // 郵便番号から住所を検索
  await page.locator('#consignee_zip_address').click();
  await page.waitForTimeout(2000);

  // 住所選択ダイアログで「選択」をクリック
  const frame = page.frameLocator('iframe').first();
  await frame.getByRole('link', { name: '選択' }).click();
}
```

#### 3.3 町・番地を入力

郵便番号検索後、町・番地フィールドに残りの住所を入力：

```javascript
const streetField = page.getByRole('cell', { name: '郵便番号 必須 XXX-XXXX' })
  .getByPlaceholder('例)銀座２－１６－１０');
await streetField.fill('町・番地・建物名');
```

#### 3.4 ご依頼主を検索・選択

```javascript
// ご依頼主を検索
await page.getByRole('link', { name: 'ご依頼主を検索' }).click();
await page.waitForTimeout(1500);

const frame = page.frameLocator('iframe').first();
await frame.getByRole('textbox', { name: '2文字以上', exact: true }).fill('アップルバイヤーズ');
await frame.getByRole('link', { name: '検索', exact: true }).click();
await page.waitForTimeout(1500);
await frame.getByRole('link', { name: '選択' }).click();
```

#### 3.5 送り状を発行

```javascript
// 印刷内容の確認へ
await page.getByRole('link', { name: '印刷内容の確認へ' }).click();
await page.waitForTimeout(2000);

// 発行開始
await page.getByRole('link', { name: '発行開始' }).click();
await page.waitForTimeout(3000);

// ポップアップを閉じる
const closeBtn = page.getByRole('link', { name: 'Close' });
if (await closeBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
  await closeBtn.click();
}

// 送り状の登録に戻る
await page.getByRole('link', { name: '１．送り状の登録に戻る' }).click();
```

### 4. 次の注文へ

手順3を全ての「発送予定」注文が処理されるまで繰り返す。

## フォーム要素ID一覧

| 要素 | セレクター |
|------|-----------|
| 宅急便コンパクト | `input[value="8"]` |
| お届け先電話番号 | `#consignee_telephone` |
| お届け先郵便番号 | `#consignee_zip_code` |
| 郵便番号⇒住所入力 | `#consignee_zip_address` |
| 荷扱い1 | `#shipment_titlehandling_information1` |

## SKU番号の注意点

- Back MarketのSKUは末尾に's'などの文字が付く場合がある
- B2クラウドの品名には数字部分のみを入力（例: 335306s → 335306）

## 名前照合ルール

- B2クラウドのお届け先名とBack Marketの顧客名が一致することを確認
- 不一致の場合は処理を停止してユーザーに確認

## エラー処理

| 状況 | 対応 |
|------|------|
| 郵便番号で住所検索できない | 手動で都道府県・市区町村を入力 |
| 荷扱い1に既存値が残る | `.clear()` してから `.fill()` |
| 名前不一致 | ユーザーに報告、確認を求める |

## Todoリスト管理

処理開始時にTodoリストを作成し、各注文の進捗を管理：

```
- 顧客名 (SKU) 送り状作成: pending/in_progress/completed
```

## 関連スキル

- `yamato-login`: ヤマトB2クラウドへのログイン
- `backmarket-ship`: 発送完了連絡（追跡番号をBack Marketに入力）
- `open-backmarket`: バックマーケット販売者管理ページを開く
