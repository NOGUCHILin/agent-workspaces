---
name: search
description: 情報を検索する。「調べて」「検索して」「最新情報」と言われた時に使用。目的に応じてContext7/Gemini CLI/Playwright MCPを自動選択。
---

# 検索の原則

- 情報を「与える」のではなく「アクセスさせる」アプローチ
- grepや検索ツールで必要なものを動的に引き出す（トークン47%削減）
- サブエージェント並行化で効率化
- プロンプトは明確・構造化（XML/ステップバイステップ）

# ツール選択テーブル

| 目的 | 1st選択 | フォールバック |
|------|---------|----------------|
| ライブラリAPI・使い方 | Context7 MCP | Gemini CLI |
| 速報・トレンド（数時間以内） | Playwright MCP → Grok | - |
| 技術比較・選定 | Gemini CLI | WebSearch |
| エラー解決 | Gemini CLI | WebSearch |
| 意見・体験談 | Gemini CLI (`site:reddit.com`) | Playwright → Reddit/X |
| コード実例 | Context7 MCP | Gemini CLI → GitHub |

# 目的別の検索戦略

## 1. ライブラリドキュメント

**戦略**: ハイブリッド検索（grep → semantic search）
- まずgrepでキーワードフィルタリング
- semantic searchで関連ドキュメント絞り込み
- MCPでドキュメントをインデックス化

**プロンプト例**:
```
ライブラリXのAPIを検索し、関連ファイルをgrepでフィルタリング。
例: 'grep -r "function_name" docs/'を実行後、semantic searchで確認。
```

**ツール**: Context7 MCP → grep/semantic search → LlamaParse（複雑なドキュメント）

## 2. エラー解決

**戦略**: ReActループ（Reason + Act）
- エラーログを入力として分析
- 複数ツール並行（grep + ブラウザ検索）
- 失敗モードを分類してルート原因特定

**プロンプト例**:
```
エラーXを分析。
1. ログをgrepで検索
2. 関連コードを読み込み
3. 修正案を提案し、テスト実行
失敗したら再試行。前回の失敗: Y。
```

**ツール**: CLIツール（grep, cat） + ブラウザ（browserbasehq） + Haikuで高速検証

## 3. 最新トレンド

**戦略**: セマンティック検索 + 時間フィルタ
- `since:YYYY-MM-DD`でフィルタ
- サブエージェントで並行検索（ArXiv + Wikipedia + X）
- 多角的ソース収集でバイアス回避

**プロンプト例**:
```
最新トレンドZを検索。since:2025-01-01でフィルタ。
複数ソースから要約し、バイアスを指摘。
```

**ツール**: Playwright → Grok（リアルタイム）、perplexity、ExaAI

## 4. 体験談・意見

**戦略**: キーワード + 感情フィルタ
- `min_faves:10`, `filter:replies`で品質フィルタ
- マルチエージェントでレビュー分類
- exclude_usernamesでバイアス回避

**プロンプト例**:
```
体験談を検索し、肯定的/否定的意見を分類。
例: 'topic OR alternative filter:replies min_faves:10'
```

**ツール**: Gemini CLI (`site:reddit.com`) → Playwright → X/Reddit

## 5. コード実例

**戦略**: ファイルツリー探索 + grep + テスト駆動
- テストを先に書いてコード検証
- サブエージェントで並行実行
- `@file`でスコープ指定

**プロンプト例**:
```
コード例を生成。
1. テストを書け
2. コードを実行しパスするまでイテレート
@file でスコープ指定
```

**ツール**: Context7 MCP → code_execution → Sonnet 4.5（高精度）

# 各ツールの使い方

## Context7 MCP
ライブラリ名でresolve → get-library-docs

## Gemini CLI
```bash
gemini "検索クエリ 情報源のURLも教えて"
gemini "site:reddit.com 検索クエリ 情報源のURLも教えて"
```
**重要**: `-p`フラグは非推奨。位置引数を使用。

## Playwright MCP → Grok
1. x.com/i/grok にアクセス
2. プロンプト: `{トピック}についてX上を検索して最新情報を教えて`
3. ログイン必要時はユーザーに依頼

## WebSearch
Gemini CLIレート制限時のフォールバック

# 注意事項

- Gemini CLIはX直接アクセス不可（`site:x.com`で公開投稿のみ）
- GrokはX内検索+ウェブ検索を自動実行
- ログイン必要時はユーザーに協力依頼
