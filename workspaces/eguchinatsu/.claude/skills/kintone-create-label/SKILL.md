---
name: kintone-create-label
description: kintoneの住所情報からB2クラウド送り状作成（返送・ムスビー等）。「返送の送り状作って」「kintone送り状」と言われた時に使用。
---

# kintone 送り状作成スキル

kintone（買取販売リスト）の住所情報を使って、B2クラウドで宅急便コンパクトの送り状を発行する。
Back Market以外の媒体（返送、ムスビー等）で使用。

## 前提条件

- Playwright MCPが有効であること
- B2クラウドにログイン済みであること
- kintoneにログイン済みであること
- Notion発送予定が開いていること

## ワークフロー概要

1. Notionの発送予定からレコード番号を確認
2. kintoneでレコード番号を検索
3. kintoneから住所情報を取得
4. B2クラウドで送り状を作成・発行

## 手順

### 1. Notionの発送予定を確認

発送予定リストから以下を取得：
- 名前
- レコード番号
- 媒体（返送、ムスビー、特殊など）

### 2. kintoneでレコード番号を検索

```
検索URL: https://japanconsulting.cybozu.com/k/11/show#record={レコード番号}
または検索窓にレコード番号を入力
```

### 3. kintoneから住所情報を取得

レコード詳細画面から以下を取得：
- ユーザー氏名
- 電話番号
- 郵便番号
- 都道府県
- 市区町村
- 町・番地
- 建物・部屋番号等

### 4. B2クラウドでフォーム入力

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

  // 品名（レコード番号＋返送）
  await page.getByRole('textbox', { name: '例)衣類' }).fill('339234返送');

  // 荷扱い1を精密機器に設定
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

### 5. 町・番地と建物名を入力

```javascript
// 町・番地
const streetField = page.getByRole('cell', { name: '郵便番号 必須 XXX-XXXX' })
  .getByPlaceholder('例)銀座２－１６－１０');
await streetField.fill('町・番地');

// マンション・ビル名
await page.locator('#consignee_address04').fill('建物名');
```

### 6. ご依頼主を検索・選択

```javascript
await page.getByRole('link', { name: 'ご依頼主を検索' }).click();
await page.waitForTimeout(1500);

const frame = page.frameLocator('iframe').first();
await frame.getByRole('textbox', { name: '2文字以上', exact: true }).fill('アップルバイヤーズ');
await frame.getByRole('link', { name: '検索', exact: true }).click();
await page.waitForTimeout(1500);
await frame.getByRole('link', { name: '選択' }).click();
```

### 7. 送り状を発行

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

## 品名のルール

| 媒体 | 品名フォーマット | 例 |
|------|-----------------|-----|
| 返送 | レコード番号＋返送 | 339234返送 |
| ムスビー | レコード番号 | 339234 |
| 特殊 | レコード番号 | 339234 |
| バックマーケット | SKU番号（別スキル使用） | 339234 |

## kintoneの住所フィールド

| フィールド名 | 説明 |
|-------------|------|
| ユーザー氏名 | お届け先名 |
| 電話番号 | 数字のみ（ハイフンなし） |
| 郵便番号 | 数字のみ（7桁） |
| 都道府県 | 自動入力される |
| 市区町村 | 自動入力される |
| 町・番地 | 手動で確認・入力 |
| 建物・部屋番号等 | マンション・ビル名に入力 |

## エラー処理

| 状況 | 対応 |
|------|------|
| kintoneでレコードが見つからない | レコード番号を再確認 |
| 住所情報が不完全 | ユーザーに確認 |
| 郵便番号で住所検索できない | 手動で都道府県・市区町村を入力 |

## 関連スキル

- `yamato-login`: ヤマトB2クラウドへのログイン
- `kintone-login`: kintoneへのログイン
- `backmarket-create-label`: Back Market注文用（別スキル）
- `open-shipping-schedule`: Notion発送予定を開く
