# Claude Code クイックスタート

出典: [Quickstart](https://code.claude.com/docs/en/quickstart)

---

## ステップ1: インストール

**macOS / Linux / WSL:**
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows PowerShell:**
```powershell
irm https://claude.ai/install.ps1 | iex
```

**Homebrew:**
```bash
brew install --cask claude-code
```

**NPM (Node.js 18+):**
```bash
npm install -g @anthropic-ai/claude-code
```

---

## ステップ2: ログイン

```bash
claude
# 初回使用時にログインを求められる
```

**対応アカウント**: Claude Pro, Max, Teams, Enterprise, Console

---

## ステップ3: セッション開始

```bash
cd /path/to/your/project
claude
```

---

## ステップ4: 最初の質問

```bash
> what does this project do?
> what technologies does this project use?
> where is the main entry point?
> explain the folder structure
```

---

## ステップ5: コード変更

```bash
> add a hello world function to the main file
```

Claudeは: ファイル検出 → 変更提案 → 承認確認 → 編集実行

---

## ステップ6: Git操作

```bash
> what files have I changed?
> commit my changes with a descriptive message
> create a new branch called feature/quickstart
> help me resolve merge conflicts
```

---

## ステップ7: バグ修正・機能追加

```bash
> add input validation to the user registration form
> there's a bug where users can submit empty forms - fix it
```

---

## 必須コマンド

| コマンド | 説明 |
|---------|------|
| `claude` | インタラクティブモード開始 |
| `claude "task"` | ワンタイムタスク実行 |
| `claude -p "query"` | クエリ実行後終了 |
| `claude -c` | 最新会話を続行 |
| `claude -r` | 以前の会話を再開 |
| `claude commit` | Gitコミット作成 |
| `/clear` | 会話履歴クリア |
| `/help` | コマンド一覧 |
| `exit` / `Ctrl+C` | 終了 |

---

## プロティップス

### 1. 具体的なリクエスト
- ❌ `fix the bug`
- ✅ `fix the login bug where users see a blank screen after entering wrong credentials`

### 2. 段階的な指示
```bash
> 1. create a new database table for user profiles
> 2. create an API endpoint to get and update user profiles
> 3. build a webpage that allows users to see and edit their information
```

### 3. 先に探索させる
```bash
> analyze the database schema
> build a dashboard showing products that are most frequently returned
```

### 4. ショートカット
- `?`: キーボードショートカット表示
- `Tab`: コマンド補完
- `↑`: コマンド履歴
- `/`: スラッシュコマンド一覧

---

## 重要なポイント

- Claudeは常にファイル変更前に許可を求める
- ファイルは自動で読み込まれる（手動追加不要）
- `/login`でアカウント切り替え可能
