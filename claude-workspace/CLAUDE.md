# claude-workspace

複数プロジェクト・ブランチを管理するワークスペース + Playwright MCP専用環境

---

## セッション開始時

**ユーザーが「こんにちは」「何ができる?」等と言ったら、まず状態を確認して報告:**

```bash
.claude/skills/check-status/scripts/scan-status.sh
```

### 報告例

```
【ワークスペース: claude-workspace】
複数のプロジェクト・ブランチを並行管理するワークスペースです。

📊 現在の状態:
- プロジェクト: 2個 (applebuyers_application, xlm-trader)
- アクティブworktree: 13個
- セットアップ: 完了

🔧 できること:
1. 新規プロジェクト/worktree作成
2. 各worktreeの作業状況確認
3. テンプレートリポジトリへの同期
4. Playwright MCPでブラウザ操作

💡 次のアクション:
- 特定のworktreeで作業を開始しますか?
- 新しいプロジェクトを追加しますか?
```

---

## Playwright MCP（ブラウザ操作）

このワークスペースはPlaywright MCP専用環境です。

### ブラウザ起動時の認証

**「ブラウザを開いて」と言われたら、以下のGoogleアカウントでログイン状態を確認:**

- アカウント: `eguchinatsu@japanconsulting.co.jp`
- 認証情報: `.claude/credentials/google.json`

認証が切れている場合は https://accounts.google.com でログインしてからユーザーの操作を行う。

### 用途

- Google Ads管理
- ログインが必要なサイトの操作
- 認証状態を永続化したいブラウザ作業

### 利用可能なMCP

| MCP | 用途 |
|-----|------|
| playwright | ブラウザ自動化（認証永続化） |
| context7 | ドキュメント検索 |
| slack | Slack連携 |

### プロファイル保存場所

`~/.playwright-profiles/claude-workspace/`

---

## 発送関連スキル

### 送り状作成 (`create-shipping-label`)

B2クラウドで宅急便コンパクトの送り状を作成しPDFダウンロード。

```
ユーザー: 送り状作って
ユーザー: ラベル作成して
```

**ワークフロー:**
1. B2クラウド発行画面 → 「宅急便コンパクト」選択
2. お届け先情報入力（電話番号、郵便番号、住所、名前）
3. ご依頼主: アップルバイヤーズ秋葉原
4. 品名: SKU番号、荷扱い: 精密機器
5. 登録 → 印刷 → PDFダウンロード

### 発送完了通知 (`notify-shipment`)

送り状PDFから追跡番号を抽出→Notion記入→Slack送信。

```
ユーザー: 発送通知して
ユーザー: 追跡番号をNotionに記入して
```

**ワークフロー:**
1. PyPDF2でPDFから追跡番号抽出（`4694-XXXX-XXXX`形式）
2. Notionの発送予定ページで該当SKUの備考欄に追跡番号を記入
3. SlackのapplebueyrsチャンネルにPDFを添付送信

---

## ワークスペース設計原則

| 概念 | パス | 役割 |
|------|------|------|
| worktreeルート | `projects/{project}/worktrees/{branch}/` | Claude Code起動場所 |
| repo | `projects/{project}/worktrees/{branch}/repo/` | ソースコード（Git管理） |

**重要:**
- Claude Codeは常に **worktreeルート** で開く
- `repo/.claude/` は使用しない（`worktree/.claude/` を使用）

## 設定階層

| 層 | パス | 共有範囲 | 方法 |
|---|------|---------|------|
| ワークスペース共通 | `_shared/` | 全project | → project/.claude/へコピー |
| project共通 | `project/.claude/` | 全worktree | → worktree/.claude/へsymlink |
| worktree個別 | `worktree/.claude/` | 個別 | 直接配置 |

**ディレクトリ構成:**
```
my-claude-code-worktrees/
├── claude-workspace/  ← このワークスペース（Claude Code起動場所）
│   └── .claude/       ← ワークスペース管理用skills/scripts
├── _shared/           ← 全project共通テンプレート(rules, skills)
└── projects/{project}/
    ├── .claude/       ← project共通(_shared/からコピー、カスタマイズ可)
    └── worktrees/{branch}/
        └── .claude/   ← symlink → project/.claude/
```

## 初回セットアップ

```bash
.claude/scripts/setup.sh
```

### 必要な設定

| 設定 | 方法 |
|------|------|
| `.mcp.json` | `.mcp.json.example`をコピーしてトークン設定 |
| Slack Token | https://api.slack.com/apps → OAuth & Permissions |
| Team ID | SlackのURL `app.slack.com/client/Txxxxxxxx/` |

詳細: [../docs/SETUP.md](../docs/SETUP.md)

## projects/内で作業時

- projects/は独自git管理（親の.gitignoreで除外済み）
- 親のCLAUDE.md設定を継承する

## 参照

- セットアップ: @../docs/SETUP.md
- Claude Code参考: @../docs/reference/
