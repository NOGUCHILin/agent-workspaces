# Claude Code Sandboxing

出典: [Anthropic Engineering](https://www.anthropic.com/engineering/claude-code-sandboxing)

---

## 課題

Claude Codeがコードベースへのアクセス権を持つため、プロンプトインジェクション攻撃が潜在的リスク。

---

## 2つの柱

### 1. ファイルシステム分離

- ワーキングディレクトリ内の読み書きのみ許可
- システムファイルへのアクセスをブロック

### 2. ネットワーク分離

- 許可されたサーバーへの接続のみ許可
- プロキシサーバーが出発トラフィックを制御

> 「どちらか一方では不十分。両者の組み合わせが有効。」

---

## 実装

### Sandboxed bash tool（ベータ版）

- Linux: bubblewrap
- macOS: seatbelt

スクリプトとサブプロセスを含めて制限を実装。

### Claude Code on the web

- クラウド内でセッション実行
- Git認証情報を外部プロキシで管理
- サンドボックス内の認証情報を保護

---

## 使用方法

```bash
/sandbox
```

ファイルパスとドメインを明示的に設定可能。

---

## 効果

許可プロンプトを**84%削減**
