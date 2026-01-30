---
name: check-recent-activity
description: LINE Chatでトークを開き、昨日から1週間以内にやりとりがあるか確認する。「やりとり確認して」「最近のやりとりチェック」と言われた時に使用。
---

# 概要

Playwright MCPを使用して、LINE Chat（chat.line.biz）で指定されたユーザーのトークを開き、昨日のメッセージより前の1週間以内にやりとりがあったかどうかを判定する。

# 前提条件

- LINE Chatが既にブラウザで開かれていること（open-lineスキルで事前にログイン済み）
- チャットリストが表示されていること

# 実行フロー

```
1. 指定されたユーザーのトークを開く
     ↓
2. チャット内の日付セパレーターを取得
     ↓
3. 昨日から1週間以内のやりとりがあるか判定
     ↓
4. 結果を報告
```

# Step 1: ユーザーのトークを開く

```javascript
mcp__playwright__browser_evaluate:
() => {
  var el = document.querySelector('div.flex-fill.overflow-y-auto');
  if (!el) return 'chat list not found';
  var links = el.querySelectorAll('a');
  for (var i = 0; i < links.length; i++) {
    var h6 = links[i].querySelector('h6');
    if (h6 && h6.textContent.trim() === 'ユーザー名') {
      links[i].click();
      return 'clicked';
    }
  }
  return 'user not found';
}
```

- `'ユーザー名'` を実際のユーザー名に置き換える
- クリック後、2秒待機

# Step 2: チャット内の日付セパレーターを取得

まずチャットメッセージペインを一番上までスクロールして全メッセージを読み込む:

```javascript
mcp__playwright__browser_evaluate:
() => {
  var divs = document.querySelectorAll('div.overflow-y-auto');
  for (var i = 0; i < divs.length; i++) {
    var rect = divs[i].getBoundingClientRect();
    if (rect.left > 230 && rect.width > 400) {
      divs[i].scrollTop = 0;
      return 'scrolled to top';
    }
  }
  return 'not found';
}
```

2秒待機後、日付セパレーターを全て取得:

```javascript
mcp__playwright__browser_evaluate:
() => {
  var dates = document.querySelectorAll('.chatsys-date');
  var results = [];
  for (var i = 0; i < dates.length; i++) {
    var text = dates[i].textContent.trim();
    if (text) results.push(text);
  }
  return JSON.stringify(results);
}
```

# Step 3: 判定ロジック

## 日付セパレーターの表示形式

| 期間 | 表示形式 | 例 |
|------|---------|-----|
| 今日 | 「今日」 | `今日` |
| 昨日 | 「昨日」 | `昨日` |
| 2〜6日前 | 曜日 | `月曜日` |
| 7日以上前 | 日付 | `2025/11/29` |

## 判定方法

日付セパレーター一覧から、「昨日」の直前にある日付を確認する:

- **曜日表示がある場合** → 1週間以内にやりとりあり
- **日付表示（YYYY/MM/DD）のみの場合** → その日付が昨日から1週間以内かを計算

```javascript
mcp__playwright__browser_evaluate:
() => {
  var dates = document.querySelectorAll('.chatsys-date');
  var texts = [];
  for (var i = 0; i < dates.length; i++) {
    var t = dates[i].textContent.trim();
    if (t) texts.push(t);
  }

  // 「昨日」のインデックスを探す
  var yesterdayIdx = -1;
  for (var i = 0; i < texts.length; i++) {
    if (texts[i] === '昨日') { yesterdayIdx = i; break; }
  }
  if (yesterdayIdx < 0) return JSON.stringify({error: '昨日のメッセージが見つかりません'});
  if (yesterdayIdx === 0) return JSON.stringify({result: 'no_prior', message: '昨日より前のやりとりなし'});

  // 昨日の直前の日付を確認
  var prev = texts[yesterdayIdx - 1];
  var days = ['日曜日','月曜日','火曜日','水曜日','木曜日','金曜日','土曜日'];

  // 曜日表示なら1週間以内
  for (var d = 0; d < days.length; d++) {
    if (prev === days[d]) {
      return JSON.stringify({result: 'within_week', message: prev + 'にやりとりあり（1週間以内）'});
    }
  }

  // 日付表示（YYYY/MM/DD）なら計算
  var match = prev.match(/(\d{4})\/(\d{1,2})\/(\d{1,2})/);
  if (match) {
    var prevDate = new Date(parseInt(match[1]), parseInt(match[2]) - 1, parseInt(match[3]));
    var today = new Date();
    var yesterday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 1);
    var oneWeekBefore = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate() - 7);
    var withinWeek = prevDate >= oneWeekBefore;
    return JSON.stringify({
      result: withinWeek ? 'within_week' : 'over_week',
      prevDate: prev,
      message: withinWeek
        ? prev + 'にやりとりあり（1週間以内）'
        : prev + 'が最後のやりとり（1週間以上前）'
    });
  }

  return JSON.stringify({result: 'unknown', prev: prev});
}
```

# Step 4: 結果の報告

判定結果に応じて報告:

| result | 意味 | 次のアクション |
|--------|------|--------------|
| `within_week` | 昨日から1週間以内にやりとりあり | 仮査定催促の対象外の可能性あり（要確認） |
| `over_week` | 1週間以上やりとりなし | 仮査定催促の対象 |
| `no_prior` | 昨日が初回やりとり | 仮査定催促の対象 |

# 注意事項

- チャットメッセージが多い場合、スクロールで全て読み込むまで複数回スクロールが必要な場合がある
- 日付セパレーターは仮想スクロールで動的に表示されるため、一番上までスクロールしてから取得すること
- 「昨日」の表示は今日の日付に基づいて自動的に決まる
