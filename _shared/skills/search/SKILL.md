---
name: search
description: 情報を検索する。「調べて」「検索して」「最新情報」と言われた時に使用。2軸（鮮度×深さ）でツールを自動選択。
---

# 検索の原則

- 情報を「与える」のではなく「アクセスさせる」
- grepや検索ツールで動的に引き出す（トークン47%削減）
- 2軸（鮮度×深さ）でツール選択
- **具体的なクエリ**で精度向上

# クエリ改善パターン

| ❌ 曖昧 | ✅ 具体的 |
|---------|----------|
| "AIについて" | "2025年教育分野のAIトレンドTop5" |
| "React" | "React 19 Server Components使い方" |
| "エラー" | "TypeError: Cannot read property of undefined React useEffect" |

# 2軸分類システム

## 軸1: 情報の鮮度

| 鮮度 | 説明 | ツール |
|------|------|--------|
| リアルタイム | 数時間以内の速報 | Grok |
| 最新 | 数日〜数週間 | Gemini CLI / WebSearch |
| 安定 | 公式ドキュメント | Context7 |

## 軸2: 探索の深さ

| 深さ | 説明 | ツール |
|------|------|--------|
| ピンポイント | API名、エラー文、特定の答え | Context7 / grep |
| 広範囲 | 比較、選定、概要把握 | Gemini CLI |
| 発見的 | トレンド、意見、未知の情報 | Grok / Reddit |

## 統合マトリクス

| | ピンポイント | 広範囲 | 発見的 |
|---|-------------|--------|--------|
| **リアルタイム** | Grok | Grok | Grok |
| **最新** | Gemini CLI | Gemini CLI | Gemini (`site:reddit.com`) |
| **安定** | Context7 | Context7 → Gemini | - |

# クエリ判定ガイド

| キーワード | 鮮度 | 深さ | ツール |
|-----------|------|------|--------|
| 「〜の使い方」「〜メソッド」 | 安定 | ピンポイント | Context7 |
| エラーメッセージ | 最新 | ピンポイント | Gemini CLI |
| 「〜 vs 〜」「比較」 | 最新 | 広範囲 | Gemini CLI |
| 「最新」「今」「トレンド」 | リアルタイム | 発見的 | Grok |
| 「使ってみた」「感想」 | 最新 | 発見的 | Gemini (`site:reddit.com`) |
| 「インストール」「設定」 | 安定 | ピンポイント | Context7 |

# 高度な検索演算子

| 演算子 | 用途 | 例 |
|--------|------|-----|
| `site:` | ドメイン限定 | `site:github.com React hooks` |
| `filetype:` | ファイル形式 | `filetype:pdf AI research 2025` |
| `before:/after:` | 日付範囲 | `AI after:2025-01-01` |
| `"..."` | 完全一致 | `"useEffect cleanup"` |
| `-` | 除外 | `Python tutorial -beginner` |
| `OR` | どちらか | `React OR Vue state management` |

**組み合わせ例**: `site:*.edu "machine learning" filetype:pdf after:2024`

# AIプロンプト技法

| 技法 | 説明 | 例 |
|------|------|-----|
| Zero-shot | 例なしで直接質問 | 「〜とは何ですか」 |
| Few-shot | 例を示して質問 | 「例: A→B, C→D, ではE→?」 |
| Chain-of-thought | 段階的推論を要求 | 「ステップバイステップで説明して」 |

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

## Perplexity（オプション）

| Focusモード | 用途 |
|-------------|------|
| Web | 一般検索（デフォルト） |
| Academic | 学術論文、査読済みソース |
| Writing | 文法チェック、リライト |
| Video | チュートリアル検索 |

**Tips**:
- 「summarize sources」で要約取得
- Collectionsでトピック別に整理
- Pro Searchで深掘り質問

# フォールバック

| 1st | 失敗時 |
|-----|--------|
| Context7 | Gemini CLI |
| Gemini CLI | WebSearch |
| Grok | - (代替なし) |

# 検索がうまくいかない時

| 問題 | 対処 |
|------|------|
| 結果が多すぎる | `site:`, `filetype:`, `"完全一致"`で絞る |
| 結果が少なすぎる | 同義語追加（`OR`）、除外条件削除 |
| 古い情報ばかり | `after:2024`で日付制限 |
| 関係ない結果 | `-除外ワード`で不要な結果を除去 |
| 専門的すぎる | `beginner`, `tutorial`, `入門`を追加 |

# 注意事項

- Gemini CLIはX直接アクセス不可（`site:x.com`で公開投稿のみ）
- GrokはX内検索+ウェブ検索を自動実行
- ログイン必要時はユーザーに協力依頼
- **スペースなし**: `site:example.com`（✅）、`site: example.com`（❌）
