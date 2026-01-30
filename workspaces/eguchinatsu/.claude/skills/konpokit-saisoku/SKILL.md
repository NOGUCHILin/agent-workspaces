---
name: konpokit-saisoku
description: 梱包キット催促を行う。「梱包キット催促して」「キット催促」と言われた時に使用。LINE Chatで梱包キット発送から5日経っても端末を送っていない人へ催促メッセージを送り、タグを付ける。
---

# 概要

kintone（japanconsulting.cybozu.com）とLINE Chat（chat.line.biz）を使用して、5日前に「梱包キット発送完了」となったユーザーに対して、梱包キット催促メッセージを送信し、「梱包キット催促完了YYYY/MM」タグを付与する。

# 前提条件

- LINE Chatが開いていること（open-lineスキルで事前にログイン済み）
- kintoneにログイン済みであること

# フィルタ条件

kintoneの絞り込み条件：
- **更新日時**: 5日前の00:00〜23:30
- **進捗**: 梱包キット発送完了
- **更新者**: Administrators

**重要**: 実行日から5日前の日付になっているか確認すること

# 実行フロー

```
1. kintoneで対象リストを確認
     ↓
2. LINE Chatでレコード番号を検索
     ↓
3. チャットを開いて履歴を確認
     ↓
4. スキップ条件に該当しなければ催促メッセージ送信
     ↓
5. タグ「梱包キット催促完了YYYY/MM」を追加
     ↓
6. 次の対象者へ
```

# Step 0: 準備

## 0-1. kintoneを開く

kintoneのフィルタURLを開く（ユーザーから提供されるか、以下の形式）:
```
https://japanconsulting.cybozu.com/k/11/?view=5520280&q=...
```

フィルタ条件を確認：
- 「絞り込む」ボタンをクリックして条件を表示
- 更新日時が5日前になっているか確認

## 0-2. LINE Chatを別タブで開く

```
mcp__playwright__browser_tabs: action=new
mcp__playwright__browser_navigate で https://chat.line.biz/ にアクセス
```

## 0-3. ウィンドウサイズを大きくする

```
mcp__playwright__browser_resize: width=2200, height=900
```

# Step 1: kintoneで対象者リストを取得

kintoneの一覧から以下の情報を取得：
- レコード番号（6桁）
- ユーザー氏名

# Step 2: 各対象者の処理

## 2-1. LINE Chatでレコード番号検索

```javascript
mcp__playwright__browser_run_code:
async (page) => {
  const searchBox = page.getByRole('textbox', { name: '検索', exact: true });
  await searchBox.clear();
  await searchBox.fill('【レコード番号】');
  await searchBox.press('Enter');
  return 'searched';
}
```

2秒待機後、「メッセージを検索」リンクをクリックして検索結果を表示。

## 2-2. チャットを開いて履歴確認

検索結果から該当ユーザーをクリックしてチャットを開く。

**スキップ条件**（以下のいずれかがある場合はスキップ）:
- 「端末を送りました」などのメッセージ
- 身分証の写真を送っている
- 査定結果を送っている

**無視してよいメッセージ**:
- 「査定をお願いします」→「見積もり完了」のやり取り（別レコードの仮査定）

## 2-3. 催促メッセージ送信

### 定型文アイコンをクリック

```javascript
mcp__playwright__browser_evaluate:
() => {
  var chatIcon = document.querySelector('i.lar.la-chat-plus');
  if (chatIcon) chatIcon.click();
  return 'clicked';
}
```

1.5秒待機後、「梱包キット催促」を選択して送信：

```javascript
mcp__playwright__browser_evaluate:
() => {
  return new Promise(async (resolve) => {
    const sleep = ms => new Promise(r => setTimeout(r, ms));

    var h5s = document.querySelectorAll('h5');
    for (var i = 0; i < h5s.length; i++) {
      if (h5s[i].textContent.trim() === '梱包キット催促') {
        h5s[i].click();
        await sleep(800);

        var buttons = document.querySelectorAll('button');
        for (var j = 0; j < buttons.length; j++) {
          if (buttons[j].textContent.trim() === '選択') {
            buttons[j].click();
            resolve('selected');
            return;
          }
        }
      }
    }
    resolve('not found');
  });
}
```

### 送信ボタンをクリック

```javascript
mcp__playwright__browser_run_code:
async (page) => {
  const sendBtn = page.getByRole('button', { name: '送信' });
  await sendBtn.click();
  return 'sent';
}
```

## 2-4. タグ付与

### タグ編集を開く

右側パネルの「タグを追加」リンクをクリック、または鉛筆マークの真ん中をクリック：

```javascript
mcp__playwright__browser_evaluate:
() => {
  return new Promise(async (resolve) => {
    const sleep = ms => new Promise(r => setTimeout(r, ms));

    var tagLinks = document.querySelectorAll('a');
    for (var i = 0; i < tagLinks.length; i++) {
      var text = tagLinks[i].textContent.trim();
      if (text === 'タグを追加' || text.indexOf('タグを追加') > -1) {
        tagLinks[i].click();
        break;
      }
    }
    await sleep(1500);
    resolve('opened');
  });
}
```

### タグを選択して保存

```javascript
mcp__playwright__browser_evaluate:
() => {
  return new Promise(async (resolve) => {
    const sleep = ms => new Promise(r => setTimeout(r, ms));

    // 「梱包キット催促完了YYYY/MM」タグを選択
    var now = new Date();
    var targetTag = '梱包キット催促完了' + now.getFullYear() + '/' + (now.getMonth() + 1);
    var tagElements = document.querySelectorAll('a');
    for (var i = 0; i < tagElements.length; i++) {
      if (tagElements[i].textContent.trim() === targetTag) {
        tagElements[i].click();
        break;
      }
    }
    await sleep(800);

    // 保存ボタンをクリック
    var buttons = document.querySelectorAll('button');
    for (var i = 0; i < buttons.length; i++) {
      if (buttons[i].textContent.trim() === '保存') {
        buttons[i].click();
        break;
      }
    }
    await sleep(1000);

    resolve('tagged');
  });
}
```

# Step 3: 次の対象者へ

処理済みリストに追加して、Step 2を繰り返す。

# 処理フロー図

```
kintoneで対象リスト取得（5日前のキット発送完了）
    ↓
┌─────────────────────────────┐
│ 各対象者について繰り返し    │
│                             │
│  レコード番号でLINE検索     │
│         ↓                   │
│  チャットを開く             │
│         ↓                   │
│  履歴確認                   │
│    ├─ 端末送った → スキップ │
│    ├─ 身分証送った → スキップ│
│    ├─ 査定結果あり → スキップ│
│    └─ なし ↓                │
│  定型文選択                 │
│  「梱包キット催促」         │
│         ↓                   │
│  メッセージ送信             │
│         ↓                   │
│  タグ追加                   │
│  「梱包キット催促完了YYYY/MM」│
└─────────────────────────────┘
    ↓
完了報告
```

# 注意事項

- **5日前の日付確認**: kintoneのフィルタ日付が実行日から5日前になっているか必ず確認
- **レコード番号検索**: 名前ではなく6桁のレコード番号で検索すること
- **スキップ条件**:
  - 端末を送りましたメッセージがある
  - 身分証の写真を送っている
  - 査定結果を受け取っている
- **無視してよいメッセージ**:
  - 「査定をお願いします」→「見積もり完了」のやり取り（別レコードの仮査定）
- **タグの年月**: 処理実行時の年月を使用（例: 2026/1）
- **ウィンドウサイズ**: 2200px以上で右パネル（タグ編集）が表示される
- **定型文名**: 「梱包キット催促」
- **タグ名**: 「梱包キット催促完了YYYY/MM」

# 認証情報

| 項目 | 値 |
|------|-----|
| LINE Chat URL | https://chat.line.biz/ |
| kintone URL | https://japanconsulting.cybozu.com/k/11/ |
| ログインアカウント | えぐち なつ |
| 公式アカウント名 | アップルバイヤーズ（Pro） |
