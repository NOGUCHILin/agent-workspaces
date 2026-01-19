# Claude Code設定体系

## ファイル種別と役割

| 種類 | 読み込み | 用途 | 特徴 |
|------|---------|------|------|
| **CLAUDE.md** | 自動（起動時） | プロジェクト指示 | 単一ファイル、階層継承 |
| **.claude/rules/** | 自動（起動時） | モジュール化ルール | 複数ファイル、パス条件可 |
| **.claude/skills/** | 自動検出 | タスク自動化 | 説明のみ先読み、使用時に全文 |
| **docs/** | 手動参照 | 参考資料 | 必要時のみ読み込み |
| **.claude/settings.json** | 自動（起動時） | hooks・権限 | JSON、動作制御 |
| **.mcp.json** | 自動（起動時） | MCPサーバー | JSON、ツール追加 |

## コンテキスト消費

- CLAUDE.md / rules → 常にコンテキストに入る
- skills → 説明だけ先読み、関連時に全文
- docs → 必要時のみ（コンテキスト節約）

## コマンド

- `/memory` → CLAUDE.md編集
- `/config` → settings.json編集

## 使い分け

- プロジェクト概要 → CLAUDE.md
- トピック別ルール → .claude/rules/
- 自動化タスク → .claude/skills/
- 参考資料 → docs/
