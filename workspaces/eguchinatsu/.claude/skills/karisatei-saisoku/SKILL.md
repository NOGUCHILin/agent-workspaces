---
name: karisatei-saisoku
description: 仮査定後催促を行う。「仮査定催促して」「催促して」「仮査定後催促」と言われた時に使用。LINE Chatで仮査定をした翌日に本査定を申し込んでいない人へ催促メッセージを送り、タグを付ける。
---

# 概要

LINE Chat（chat.line.biz）で、昨日「本査定のご案内」を送ったユーザーに対して、仮査定後催促メッセージを送信し、「仮査定後催促済YYYY/MM」タグを付与する。

# 効率化のポイント

1. **ウィンドウサイズ**: 最初に幅2200pxに設定（右パネル表示のため）
2. **一括JavaScript実行**: メッセージ送信・タグ付与を1回のevaluateで実行
3. **連続処理モード**: 確認なしで次々と処理（エラー時のみ停止）
4. **待機時間最適化**: 必要最小限の待機（1秒ベース）

# Step 0: LINE Chatを開く

## 0-1. LINE Official Account Managerにアクセス

```
mcp__playwright__browser_navigate で https://chat.line.biz/ にアクセス
```

## 0-2. ログイン（必要な場合）

ログイン画面が表示された場合:
1. 「LINEアカウント」ボタンをクリック
2. 「えぐち なつ」のセッションがあれば「ログイン」をクリック
3. セッションがなければユーザーにログイン操作を依頼

## 0-3. ウィンドウサイズを大きくする

```
mcp__playwright__browser_resize: width=2200, height=900
```

これにより右側パネル（タグ編集）が常に表示される。

# Step 1: 今日と昨日の境目までスクロール

## 1-1. チャットリストを「昨日」までスクロール

```javascript
mcp__playwright__browser_evaluate:
() => {
  var el = document.querySelector('div.flex-fill.overflow-y-auto');
  if (!el) return 'not found';
  var count = 0;
  var interval = setInterval(function() {
    el.scrollTop = el.scrollHeight;
    count++;
    if (count >= 30) clearInterval(interval);
  }, 200);
  return 'scrolling';
}
```

8秒待機後、境目を検出。

## 1-2. 今日と昨日の境目を画面中央に表示

```javascript
mcp__playwright__browser_evaluate:
() => {
  var el = document.querySelector('div.flex-fill.overflow-y-auto');
  if (!el) return 'not found';
  var links = el.querySelectorAll('a');
  var firstYesterday = -1;
  for (var i = 0; i < links.length; i++) {
    if (links[i].textContent.indexOf('昨日') > -1) {
      firstYesterday = i;
      break;
    }
  }
  if (firstYesterday > 2) {
    links[firstYesterday - 2].scrollIntoView({block: 'center'});
    return 'scrolled to boundary at index ' + firstYesterday;
  }
  return 'boundary not found or too early: ' + firstYesterday;
}
```

# Step 2: 対象ユーザーの取得

```javascript
mcp__playwright__browser_evaluate:
() => {
  var el = document.querySelector('div.flex-fill.overflow-y-auto');
  if (!el) return JSON.stringify({error: 'chat list not found'});
  var links = el.querySelectorAll('a');
  var targets = [];
  for (var i = 0; i < links.length; i++) {
    var h6 = links[i].querySelector('h6');
    if (!h6) continue;
    var name = h6.textContent.trim();
    var text = links[i].textContent || '';
    if (text.indexOf('本査定のご案内') > -1 &&
        text.indexOf('昨日') > -1 &&
        name.indexOf('Unknown') === -1 &&
        name.length > 0) {
      targets.push(name);
    }
  }
  return JSON.stringify({count: targets.length, targets: targets});
}
```

このリストを保持して連続処理する。

# Step 3: 連続処理（1人あたり約30秒）

## 処理済みリストの管理

```javascript
var done = []; // 処理済みユーザー名を追加していく
```

## 3-1. 次の対象をクリック＆資格確認＆メッセージ送信＆タグ付与（一括）

**重要**: 以下の一括処理関数を使用する

```javascript
mcp__playwright__browser_evaluate:
() => {
  return new Promise(async (resolve) => {
    const sleep = ms => new Promise(r => setTimeout(r, ms));
    const done = [/* 処理済みリストをここに入れる */];

    // 1. 対象ユーザーをクリック
    var el = document.querySelector('div.flex-fill.overflow-y-auto');
    if (!el) return resolve({error: 'chat list not found'});
    var links = el.querySelectorAll('a');
    var clicked = null;
    for (var i = 0; i < links.length; i++) {
      var h6 = links[i].querySelector('h6');
      if (!h6) continue;
      var name = h6.textContent.trim();
      var text = links[i].textContent || '';
      if (text.indexOf('本査定のご案内') > -1 &&
          text.indexOf('昨日') > -1 &&
          name.indexOf('Unknown') === -1 &&
          name.length > 0 &&
          done.indexOf(name) === -1) {
        links[i].click();
        clicked = name;
        break;
      }
    }
    if (!clicked) return resolve({done: true, message: '対象なし'});

    await sleep(1500);

    // 2. 資格確認（日付セパレーター）
    var dates = document.querySelectorAll('.chatsys-date');
    var texts = [];
    for (var i = 0; i < dates.length; i++) {
      var t = dates[i].textContent.trim();
      if (t) texts.push(t);
    }
    var yesterdayIdx = -1;
    for (var i = 0; i < texts.length; i++) {
      if (texts[i] === '昨日') { yesterdayIdx = i; break; }
    }

    var eligible = false;
    var skipReason = '';
    if (yesterdayIdx < 0) {
      skipReason = 'no_yesterday';
    } else if (yesterdayIdx === 0) {
      eligible = true; // 昨日より前のやりとりなし
    } else {
      var prev = texts[yesterdayIdx - 1];
      var days = ['日曜日','月曜日','火曜日','水曜日','木曜日','金曜日','土曜日'];
      var isWeekday = days.some(d => prev === d);
      if (isWeekday) {
        skipReason = 'within_week: ' + prev;
      } else {
        eligible = true; // 1週間以上前
      }
    }

    if (!eligible) {
      return resolve({user: clicked, skipped: true, reason: skipReason});
    }

    // 3. メッセージ送信
    var chatIcon = document.querySelector('i.lar.la-chat-plus');
    if (!chatIcon) return resolve({user: clicked, error: 'chat icon not found'});
    chatIcon.click();
    await sleep(1500);

    var h5s = document.querySelectorAll('h5');
    for (var i = 0; i < h5s.length; i++) {
      if (h5s[i].textContent.trim() === '仮査定中の方へ') {
        h5s[i].click();
        break;
      }
    }
    await sleep(800);

    var buttons = document.querySelectorAll('button');
    for (var i = 0; i < buttons.length; i++) {
      if (buttons[i].textContent.trim() === '選択') {
        buttons[i].click();
        break;
      }
    }
    await sleep(1500);

    var sendBtn = document.querySelector('input.btn.btn-sm.btn-primary');
    if (sendBtn) sendBtn.click();
    await sleep(2000);

    // 4. タグ付与
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

    var now = new Date();
    var targetTag = '仮査定後催促済' + now.getFullYear() + '/' + (now.getMonth() + 1);
    var tagElements = document.querySelectorAll('a, span, div, label');
    for (var i = 0; i < tagElements.length; i++) {
      if (tagElements[i].textContent.trim() === targetTag) {
        tagElements[i].click();
        break;
      }
    }
    await sleep(800);

    buttons = document.querySelectorAll('button');
    for (var i = 0; i < buttons.length; i++) {
      if (buttons[i].textContent.trim() === '保存') {
        buttons[i].click();
        break;
      }
    }
    await sleep(1000);

    resolve({user: clicked, success: true});
  });
}
```

## 3-2. 結果確認と次へ

結果が `{success: true}` なら処理済みリストに追加して次へ。
`{skipped: true}` ならスキップリストに追加して次へ。
`{done: true}` なら終了。
`{error: ...}` ならエラー報告して停止。

# 注意事項

- **ウィンドウサイズ2200px**を最初に設定すること（右パネル表示のため）
- Unknownユーザーは自動スキップ
- タグの年月は処理実行時の年月を使用（例: 2026/1）
- 曜日表示（日曜日〜土曜日）は1週間以内と判定してスキップ
- 一括処理でエラーが出たら簡易版に切り替える
- 定型文のテンプレート名は「仮査定中の方へ」
- タグ編集の鉛筆マークは右側パネルの3つの鉛筆の**真ん中**（left > 1300px）
