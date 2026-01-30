---
name: open-kintone
description: ブラウザを開いてkintoneの買取販売リストを開く。「kintone開いて」「キントン開いて」と言われた時に使用。
---

# kintone起動スキル

ブラウザを起動してkintoneの買取販売リストを開くスキル。

## 前提条件

- Playwright MCPが有効であること
- kintoneへのログイン情報がブラウザに保存されていること

## 手順

### 1. ブラウザを開く

```
about:blank
```

### 2. kintoneを開く

```
URL: https://japanconsulting.cybozu.com/k/11/
```

買取販売リスト(iPhone,iPad)が開く。ログイン画面が表示されたら、ユーザーにログインを依頼。

## 最終状態

- kintone買取販売リスト(iPhone,iPad)が表示されている
