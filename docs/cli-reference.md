# CLI Reference

出典: [CLI Reference](https://code.claude.com/docs/en/cli-reference)

---

## 基本コマンド

| コマンド | 説明 |
|---------|------|
| `claude` | 対話REPL起動 |
| `claude "query"` | 初期プロンプト付き起動 |
| `claude -p "query"` | 実行後終了（headless） |
| `claude -c` | 前回の会話再開 |
| `claude -r "session-id"` | 特定セッション再開 |

---

## 重要オプション

| オプション | 説明 |
|-----------|------|
| `--agent <name>` | サブエージェント指定 |
| `--model claude-opus-4-5` | モデル指定 |
| `--append-system-prompt "..."` | システムプロンプト追加 |
| `--tools "Bash,Edit,Read"` | ツール制限 |
| `--permission-mode plan` | パーミッションモード指定 |

---

## パーミッションモード

| モード | 説明 |
|--------|------|
| `default` | 通常（都度確認） |
| `plan` | 計画モード（読み取りのみ許可） |
| `bypass` | 確認スキップ |

---

## 使用例

### Headlessモードでタスク実行
```bash
claude -p "fix all lint errors in src/"
```

### 特定ツールのみ許可
```bash
claude --tools "Read,Grep,Glob"
```

### モデル指定
```bash
claude --model claude-sonnet-4-20250514
```
