# Claude Code メモリ管理

出典: [Memory](https://code.claude.com/docs/en/memory)

---

## メモリタイプと場所

| タイプ | 場所 | 用途 | 共有 |
|--------|------|------|------|
| **Enterprise** | macOS: `/Library/Application Support/ClaudeCode/CLAUDE.md`<br/>Linux: `/etc/claude-code/CLAUDE.md`<br/>Windows: `C:\Program Files\ClaudeCode\CLAUDE.md` | 組織全体の指示 | 全ユーザー |
| **Project** | `./CLAUDE.md` or `./.claude/CLAUDE.md` | チーム共有指示 | チームメンバー |
| **Rules** | `./.claude/rules/*.md` | モジュール化指示 | チームメンバー |
| **User** | `~/.claude/CLAUDE.md` | 個人設定（全PJ） | 自分のみ |
| **Local** | `./CLAUDE.local.md` | 個人設定（現PJ） | 自分のみ |

---

## 初期化

```bash
> /init
```

---

## CLAUDE.md構文

### インポート構文

```markdown
See @README for project overview and @package.json for available npm commands.

# Additional Instructions
- git workflow @docs/git-instructions.md
```

**特徴**:
- 相対/絶対パス対応
- 再帰インポート（最大5階層）
- ホームディレクトリ: `@~/.claude/my-project-instructions.md`
- コードスパン内は評価されない: `` `@anthropic-ai/claude-code` ``

### 読み込み済みファイル確認

```bash
/memory
```

---

## モジュール化: `.claude/rules/`

### 基本構造

```
your-project/
├── .claude/
│   ├── CLAUDE.md
│   └── rules/
│       ├── code-style.md
│       ├── testing.md
│       └── security.md
```

### パス固有ルール

YAMLフロントマターでスコープ指定:

```markdown
---
paths: src/api/**/*.ts
---

# API開発ルール

- 全APIエンドポイントに入力バリデーション必須
- 標準エラーレスポンス形式を使用
- OpenAPIドキュメントコメント含める
```

### サポートされるGlobパターン

```
**/*.ts              # 全TypeScriptファイル
src/**/*             # src配下全ファイル
*.md                 # ルートのMarkdown
src/components/*.tsx # 特定ディレクトリ
src/**/*.{ts,tsx}    # 複数パターン
{src,lib}/**/*.ts, tests/**/*.test.ts  # 結合パターン
```

### サブディレクトリ

```
.claude/rules/
├── frontend/
│   ├── react.md
│   └── styles.md
├── backend/
│   ├── api.md
│   └── database.md
└── general.md
```

### ユーザーレベルルール

```
~/.claude/rules/
├── preferences.md
└── workflows.md
```

---

## ベストプラクティス

| 項目 | 推奨 |
|------|------|
| 具体性 | "Use 2-space indentation" > "Format code properly" |
| 構造化 | 見出し下に箇条書き |
| 定期見直し | プロジェクト進化に合わせて更新 |
| フォーカス | 1ファイル1トピック |
| ファイル名 | 内容を示す名前 |
| シンボリックリンク | 共通ルールを複数PJで共有可能 |
