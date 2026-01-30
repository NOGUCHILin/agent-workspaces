---
name: honsatei-saisoku
description: 本査定後催促を行う。「本査定催促して」「本査定後催促」「本査定後の催促」と言われた時に使用。LINE Chatで本査定結果を送った翌日に返答がない人へ催促メッセージを送り、タグを付ける。
---

# 概要

LINE Chat（chat.line.biz）とkintone（japanconsulting.cybozu.com）を使用して、昨日「本査定結果」を送ったユーザーに対して、本査定後催促メッセージを送信し、「本査定後催促済YYYY/MM」タグを付与する。

# 前提条件

- LINE ChatとkintoneのURLが開いていること
- kintoneで「本査定完了」かつ「昨日完了」のフィルタが設定されていること

# Step 0: 準備

## 0-1. LINE Chatを開く

```
mcp__playwright__browser_navigate で https://chat.line.biz/ にアクセス
```

ログイン画面が表示された場合:
1. 「LINEアカウント」ボタンをクリック
2. 「えぐち なつ」のセッションがあれば「ログイン」をクリック
3. セッションがなければユーザーにログイン操作を依頼

## 0-2. kintoneを新しいタブで開く

```
mcp__playwright__browser_tabs: action=new
mcp__playwright__browser_navigate で kintone URL にアクセス
```

kintone URL: ユーザーから提供されるか、昨日本査定完了した絞り込みビュー

## 0-3. ウィンドウサイズを大きくする（右パネル表示のため）

```
mcp__playwright__browser_resize: width=2200, height=900
```

# Step 1: kintoneで対象者リストを取得

kintoneの一覧から以下の情報を取得:
- レコード番号（6桁）
- ユーザー氏名
- 最終買取価格（高額買取価格）

**重要**: レコード番号と価格をメモしておく

# Step 2: 各対象者の処理

## 2-1. LINE Chatでレコード番号検索

```javascript
// 検索ボックスにレコード番号を入力
mcp__playwright__browser_run_code:
async (page) => {
  const searchBox = page.getByRole('textbox', { name: '検索', exact: true });
  await searchBox.clear();
  await searchBox.fill('【レコード番号】');
  await searchBox.press('Enter');
  return 'searched';
}
```

2秒待機後、「メッセージを検索」リンクをクリックして検索結果を表示

## 2-2. チャットを開いて返答確認

検索結果から該当ユーザーをクリックしてチャットを開く

**スキップ条件**: 顧客から本査定結果送信後に何かメッセージが来ている場合はスキップ
- 例：「○○円でお願いします」「返送希望」など

## 2-3. 催促メッセージ送信

**重要**: 価格による処理分岐

| 価格 | 処理 |
|------|------|
| 100円〜数百円（低価格） | テンプレートそのまま送信 |
| それ以上（高価格） | 「引き取り」の文を削除して送信 |

### テンプレート選択

```javascript
mcp__playwright__browser_evaluate:
() => {
  var chatIcon = document.querySelector('i.lar.la-chat-plus');
  if (chatIcon) chatIcon.click();
  return 'clicked';
}
```

1.5秒待機後、「本査定後の催促」を選択:

```javascript
mcp__playwright__browser_evaluate:
() => {
  return new Promise(async (resolve) => {
    const sleep = ms => new Promise(r => setTimeout(r, ms));
    var h5s = document.querySelectorAll('h5');
    for (var i = 0; i < h5s.length; i++) {
      if (h5s[i].textContent.trim() === '本査定後の催促') {
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

### 高価格の場合: 「引き取り」の文を削除

```javascript
mcp__playwright__browser_run_code:
async (page) => {
  const textbox = page.getByRole('textbox', { name: 'Ctrl + Enterで送信 / Enterで改行' });
  const currentText = await textbox.inputValue();
  const newText = currentText.replace(/また、ご不要な場合は弊社にて【引き取り】をすることも可能でございます。\s*/g, '');
  await textbox.clear();
  await textbox.fill(newText);
  return 'edited';
}
```

### 送信

```javascript
mcp__playwright__browser_run_code:
async (page) => {
  const sendBtn = page.getByRole('button', { name: '送信' });
  await sendBtn.click();
  return 'sent';
}
```

## 2-4. タグ付与

```javascript
mcp__playwright__browser_evaluate:
() => {
  return new Promise(async (resolve) => {
    const sleep = ms => new Promise(r => setTimeout(r, ms));

    // タグ編集を開く
    var pens = document.querySelectorAll('i[class*="la-pen"]');
    var rightPens = [];
    for (var i = 0; i < pens.length; i++) {
      var rect = pens[i].getBoundingClientRect();
      if (rect.left > 1300 && rect.width > 0) rightPens.push(i);
    }
    if (rightPens.length >= 3) {
      pens[rightPens[1]].parentElement.click();
    } else {
      var tagLinks = document.querySelectorAll('a');
      for (var i = 0; i < tagLinks.length; i++) {
        if (tagLinks[i].textContent.trim() === 'タグを追加') {
          tagLinks[i].click();
          break;
        }
      }
    }
    await sleep(1500);

    // 本査定後催促済YYYY/MMタグを選択
    var now = new Date();
    var targetTag = '本査定後催促済' + now.getFullYear() + '/' + (now.getMonth() + 1);
    var tagElements = document.querySelectorAll('a, span, div, label');
    for (var i = 0; i < tagElements.length; i++) {
      if (tagElements[i].textContent.trim() === targetTag) {
        tagElements[i].click();
        break;
      }
    }
    await sleep(800);

    // 保存
    var buttons = document.querySelectorAll('button');
    for (var i = 0; i < buttons.length; i++) {
      if (buttons[i].textContent.trim() === '保存') {
        buttons[i].click();
        break;
      }
    }
    resolve('tagged');
  });
}
```

# Step 3: 次の対象者へ

処理済みリストに追加して、Step 2を繰り返す

# 処理フロー図

```
kintoneで対象リスト取得
    ↓
┌─────────────────────────────┐
│ 各対象者について繰り返し    │
│                             │
│  レコード番号でLINE検索     │
│         ↓                   │
│  チャットを開く             │
│         ↓                   │
│  顧客から返答あり？         │
│    ├─ Yes → スキップ        │
│    └─ No  ↓                 │
│  テンプレート選択           │
│  「本査定後の催促」         │
│         ↓                   │
│  価格チェック               │
│    ├─ 低価格 → そのまま     │
│    └─ 高価格 → 引き取り削除 │
│         ↓                   │
│  メッセージ送信             │
│         ↓                   │
│  タグ追加                   │
│  「本査定後催促済YYYY/MM」  │
└─────────────────────────────┘
    ↓
完了報告
```

# 注意事項

- **レコード番号検索**: 名前ではなく6桁のレコード番号で検索すること（名前だと複数ヒットする）
- **スキップ条件**: 顧客から何かメッセージが来ていたら催促不要（既に対応済みの可能性）
- **価格判定**:
  - 100円〜数百円 = 低価格 → 引き取り文はそのまま
  - 1,000円以上 = 高価格 → 引き取り文を削除
- **タグの年月**: 処理実行時の年月を使用（例: 2026/1）
- **ウィンドウサイズ**: 2200px以上で右パネル（タグ編集）が表示される
- **定型文名**: 「本査定後の催促」

# 認証情報

| 項目 | 値 |
|------|-----|
| LINE Chat URL | https://chat.line.biz/ |
| kintone URL | https://japanconsulting.cybozu.com/k/11/ |
| ログインアカウント | えぐち なつ |
| 公式アカウント名 | アップルバイヤーズ（Pro） |
