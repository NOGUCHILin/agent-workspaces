# Claude Code Overview

出典: [Claude Code Docs](https://code.claude.com/docs/en/overview)

---

## インストール方法

### ネイティブ（推奨）

**macOS / Linux / WSL:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows PowerShell:**
```powershell
irm https://claude.ai/install.ps1 | iex
```

### Homebrew
```bash
brew install --cask claude-code
```

### NPM（Node.js 18+必須）
```bash
npm install -g @anthropic-ai/claude-code
```

### 起動
```bash
cd your-project
claude
```

---

## コア機能

| 機能 | 説明 |
|------|------|
| **機能構築** | 自然言語で指示→計画→コード生成→動作確認 |
| **デバッグ** | バグ説明/エラー貼付→分析→修正実装 |
| **コードベース探索** | プロジェクト全体を把握、質問に回答 |
| **外部連携** | MCP経由でGoogle Drive、Figma、Slack等と統合 |
| **自動化** | lint修正、マージコンフリクト解決、リリースノート作成 |

---

## 特徴

### ターミナル統合
- 追加のチャットウィンドウ/IDE不要
- 既存の開発ツールと統合

### アクション実行
- ファイル直接編集
- コマンド実行
- コミット作成
- MCPでカスタムツール統合

### Unix哲学
- 構成可能でスクリプト化可能
- パイプライン例:
```bash
tail -f app.log | claude -p "Slack me if you see anomalies"
```

### CI統合例
```bash
claude -p "If there are new text strings, translate them into French and raise a PR"
```

### エンタープライズ対応
- Claude API使用可能
- AWS/GCPでホスト可能
- セキュリティ・プライバシー・コンプライアンス対応

---

## 関連ドキュメント

| ページ | 内容 |
|--------|------|
| [Quickstart](/en/quickstart) | 5分で実践例 |
| [Common workflows](/en/common-workflows) | ステップバイステップガイド |
| [Troubleshooting](/en/troubleshooting) | 問題解決 |
| [IDE setup](/en/vs-code) | IDE統合 |
| [Settings](/en/settings) | カスタマイズ |
| [Commands](/en/cli-reference) | CLIリファレンス |
| [Security](/en/security) | セキュリティ |
| [Privacy](/en/data-usage) | データ利用 |
