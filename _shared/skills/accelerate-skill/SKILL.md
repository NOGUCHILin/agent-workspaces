---
name: accelerate-skill
description: GUIスキルにCLI高速版を追加する。「スキルを高速化して」「CLI版を追加して」「このスキルをAPI化して」と言われた時に使用。
---

# GUIスキル高速化スキル

既存のGUIスキル（Playwright MCP）にCLI高速版を追加し、実行時に選択できるようにする。

## ワークフロー

### 1. 対象スキルの特定

ユーザーに確認：
- 高速化したいスキルのパス
- または現在のワークスペースのスキル一覧から選択

### 2. GUIスキルの分析

対象スキルの`SKILL.md`を読み、以下を抽出：
- 対象サービス（ヤマト、Kintone、Googleスプレッドシート等）
- 実行ステップ（ログイン→操作→結果取得）
- 入出力データ

### 3. CLI化の調査

対象サービスについてWeb検索で調査：

| 優先度 | 方法 | 例 |
|--------|------|-----|
| 1 | 公式API | ヤマトAPI、Kintone API、Google Sheets API |
| 2 | 公式CLI | gh, gcloud, aws cli |
| 3 | 非公式ライブラリ | npm/pip パッケージ |
| 4 | スクレイピング最適化 | headless高速化、並列化 |

### 4. CLI版の生成

`cli.md`を作成：
```markdown
# CLI版（高速）

## 前提条件
- APIキー設定: `.env`に`SERVICE_API_KEY`
- 依存: `pip install xxx` または `npm install xxx`

## 実行手順
1. 認証
2. API呼び出し
3. 結果処理
```

### 5. スキル構造の再編成

**Before:**
```
skills/example-skill/
└── SKILL.md          # GUI版のみ
```

**After:**
```
skills/example-skill/
├── SKILL.md          # 選択肢を提示
├── gui.md            # GUI版（元のSKILL.mdの内容）
└── cli.md            # CLI版（新規作成）
```

### 6. SKILL.mdの書き換え

```markdown
---
name: example-skill
description: ...
---

# スキル名

## 実行モード

| モード | 特徴 | 推奨場面 |
|--------|------|----------|
| GUI版 | ブラウザ操作、視覚確認可能 | 初回実行、デバッグ、手順確認 |
| 高速版 | API/スクリプト | 日常運用、自動化、大量処理 |

**どちらのモードで実行しますか？**

## GUI版
→ [gui.md](gui.md) を参照

## 高速版（CLI）
→ [cli.md](cli.md) を参照
```

## 調査のポイント

### API検索キーワード
- `{サービス名} API`
- `{サービス名} REST API`
- `{サービス名} developer`
- `{サービス名} automation`

### 確認事項
- 認証方式（APIキー、OAuth、Basic認証）
- レート制限
- 利用規約（自動化の可否）

## 出力

1. `cli.md` - CLI版の手順書
2. `gui.md` - GUI版（元の内容を移動）
3. `SKILL.md` - 選択肢を提示する形に更新
4. `scripts/` - 必要に応じてスクリプトファイル

## 使用例

```
ユーザー: yamato-loginスキルを高速化して
Claude: [このスキルを実行]
        1. yamato-loginのSKILL.mdを分析
        2. ヤマトAPIを調査 → B2クラウドAPIあり
        3. cli.mdを生成（API利用版）
        4. 元のSKILL.mdをgui.mdに移動
        5. 新SKILL.mdで選択肢を提示
```
