# Claude Code GitHub README

出典: [GitHub](https://github.com/anthropics/claude-code)

---

## 概要

- ターミナル統合のエージェント型コーディングツール
- 自然言語コマンドでタスク実行
- ターミナル、IDE、GitHub（@claudeタグ）で使用可能

**統計**: Stars 53.5k | Forks 3.8k | Contributors 48名

---

## インストール

| 方法 | コマンド |
|------|---------|
| macOS/Linux | `curl -fsSL https://claude.ai/install.sh \| bash` |
| Homebrew | `brew install --cask claude-code` |
| Windows | `irm https://claude.ai/install.ps1 \| iex` |
| NPM | `npm install -g @anthropic-ai/claude-code` |

**要件**: Node.js 18+（NPM使用時）

---

## 基本使用

```bash
cd your-project
claude
```

---

## プラグインシステム

- 場所: `/plugins`ディレクトリ
- 機能: カスタムコマンドとエージェント拡張
- 詳細: [plugins/README.md](https://github.com/anthropics/claude-code/blob/main/plugins/README.md)

---

## リポジトリ構成

```
claude-code/
├── .claude-plugin/      # プラグイン関連
├── .claude/commands/    # カスタムコマンド
├── .devcontainer/       # 開発環境設定
├── plugins/             # プラグインディレクトリ
├── scripts/             # スクリプト
├── examples/hooks/      # フック例
├── CHANGELOG.md         # 変更履歴
└── SECURITY.md          # セキュリティ
```

---

## バグ報告

| 方法 | 説明 |
|------|------|
| `/bug` | Claude Code内コマンド |
| GitHub Issues | [Issues](https://github.com/anthropics/claude-code/issues) |

---

## コミュニティ

**Discord**: [Claude Developers](https://anthropic.com/discord)

---

## データ収集

### 収集データ
- 使用データ（コード受理/拒否）
- 会話データ
- ユーザーフィードバック（`/bug`経由）

### プライバシー保護
- 機密情報の限定保持期間
- セッションデータへのアクセス制限
- フィードバックをモデルトレーニングに使用しない

詳細: [データ使用ポリシー](https://code.claude.com/docs/en/data-usage)

---

## 技術構成

| 言語 | 割合 |
|------|------|
| Shell | 48.2% |
| Python | 32.7% |
| TypeScript | 12.5% |
| PowerShell | 4.5% |
| Dockerfile | 2.1% |
