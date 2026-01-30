---
name: seo-master
description: |
  SEO対策の包括的スキル。7つのSEOカテゴリを統合し、記事作成からLP設計、技術SEO、ローカルSEO、AI/AEO対策まで網羅。

  **トリガー**:
  - 汎用: 「SEO対策」「SEO」「検索エンジン最適化」「SEOやりたい」「SEO改善」
  - コンテンツSEO: 「SEO記事作成」「コンテンツ作成」「ブログ記事」「ピラーページ」
  - LP設計: 「SEO LP」「ランディングページ設計」「LP改善」「ファーストビュー」
  - 技術SEO: 「構造化データ」「Schema」「メタタグ」「Core Web Vitals」
  - 内部SEO: 「内部リンク」「サイト構造」「URL設計」
  - 外部SEO: 「被リンク」「ブランドSEO」「評判管理」
  - ローカルSEO: 「GBP」「Googleビジネスプロフィール」「店舗SEO」「口コミ」
  - AI/AEO: 「AI Overview」「AEO」「ChatGPT対策」「Perplexity」
  - 動画SEO: 「YouTube SEO」「動画最適化」
  - E-E-A-T: 「信頼性向上」「権威性」「専門性」
  - 競合分析: 「競合SEO分析」「上位表示分析」
  - SEO監査: 「SEO監査」「サイト診断」「SEO評価」「優先度判定」

  **対応フレームワーク**: Next.js, React, Tailwind CSS
---

# SEO Master

SEO対策の包括的スキル。記事作成からLP設計、技術SEO実装まで対応。

## 開始ワークフロー（SEO対策を始める時）

**推奨順序**: GSC分析 → SEO監査 → 競合分析

| 順序 | 診断 | 目的 | コマンド |
|------|------|------|----------|
| 1 | GSC分析 | 注力すべきページ/キーワード特定 | `gsc:opportunities` |
| 2 | SEO監査 | 特定ページの技術的問題確認 | `score` / `full` |
| 3 | 競合分析 | 上位サイトとの差分特定 | `serp:analyze` |

### GSC設定確認

```bash
cd .claude/skills/seo-master/scripts
ls gsc-service-account.json  # 存在すれば設定済み
```

**未設定の場合**: SEO監査から開始し、並行してGSC設定を行う

## ワークフロー

### 1. SEO記事作成

```
キーワード選定 → 構成設計 → E-E-A-T実装 → 執筆 → 最適化
```

**手順**:
1. ターゲットキーワードと検索意図を確認
2. 競合上位10記事の構成を分析
3. 見出し構造（H1→H2→H3）を設計
4. E-E-A-T要素を計画（体験、専門性、権威性、信頼性）
5. 記事執筆（段落2-3行、1文20-30文字）
6. CTA配置（3-6箇所）、内部リンク設定
7. メタタグ、構造化データ実装

**詳細**: [references/article-creation.md](references/article-creation.md)

### 2. SEO LP設計

```
ファーストビュー設計 → セクション構成 → CTA最適化 → モバイル対応
```

**ファーストビュー必須要素**:
1. h1（メインキーワード）
2. 価値訴求（具体的メリット）
3. 信頼バッジ（実績、評価）
4. CTAボタン（具体的アクション）
5. ヒーロー画像（縮小してビュー内に）

**よくある問題**:
- CTAがファーストビュー外 → 画像縮小、CTA上部配置
- CTA文言が弱い → 「詳しく見る」→「無料査定」
- 価値訴求が小さい → h1直下に大きく配置

**詳細**: [references/lp-design.md](references/lp-design.md)

### 3. 技術SEO実装

**構造化データ**:
| Schema | 用途 |
|--------|------|
| Article | 記事ページ |
| FAQPage | FAQ |
| Product | 商品・買取価格 |
| LocalBusiness | 店舗情報 |
| BreadcrumbList | パンくず |

**Core Web Vitals目標**:
- LCP < 2.5秒
- FID/INP < 100ms
- CLS < 0.1

**詳細**: [references/technical-seo.md](references/technical-seo.md)

### 4. E-E-A-T実装

| 要素 | 実装方法 |
|------|----------|
| Experience | 実際の買取事例（日付、金額、写真） |
| Expertise | 監修者情報、古物商許可番号 |
| Authoritativeness | 自社データ引用、出典明記 |
| Trust | 更新日時、デメリットも記載 |

**詳細**: [references/eeat-checklist.md](references/eeat-checklist.md)

## クイックリファレンス

### 記事構成基準
- ガイド記事: 5,000-8,000文字
- FAQ記事: 3,000-5,000文字
- 比較記事: 6,000-10,000文字

### 見出し構造
```
H1（1つのみ）
├─ H2（3-5個）
│  └─ H3（各2-4個）
```

### 段落・文章
- 1段落 = 2-3行
- 1文 = 20-30文字（最大50文字）

### 表（モバイルファースト）
- 最大3列、最大8行
- 4列以上はカード形式に分割

### CTA配置
- 導入部（H1直後）
- 各セクション末尾
- 記事末尾

### メタタグ
- title: 60文字以内
- description: 120-160文字

## 注意事項

- YMYL（金融情報）として価格変動を明記
- 誇大表現を避ける
- デメリットも正直に記載
- 更新日時を必ず表示

## SEOフレームワーク一覧

7つのSEOカテゴリを網羅したフレームワーク集。

| カテゴリ | 概要 | 詳細 |
|----------|------|------|
| コンテンツSEO | E-E-A-T、ピラーページ、LP設計 | [01-content-seo.md](references/frameworks/01-content-seo.md) |
| 技術SEO | Core Web Vitals、構造化データ | [02-technical-seo.md](references/frameworks/02-technical-seo.md) |
| 内部SEO | 内部リンク、サイト構造、URL設計 | [03-internal-seo.md](references/frameworks/03-internal-seo.md) |
| 外部SEO | 被リンク、ブランドSEO、デジタルPR | [04-external-seo.md](references/frameworks/04-external-seo.md) |
| ローカルSEO | GBP、NAP、レビュー管理 | [05-local-seo.md](references/frameworks/05-local-seo.md) |
| AI/AEO | AI Overview対策、構造化回答 | [06-ai-aeo.md](references/frameworks/06-ai-aeo.md) |
| 動画SEO | YouTube最適化、動画Schema | [07-video-seo.md](references/frameworks/07-video-seo.md) |
| 評価・スコアリング | 優先度マトリクス、監査基準 | [09-evaluation-scoring.md](references/frameworks/09-evaluation-scoring.md) |
| 監査ツール | 自動監査スクリプト実装計画 | [10-audit-tools.md](references/frameworks/10-audit-tools.md) |
| ブランドSEO | 評判管理、指名検索対策 | [11-brand-seo.md](references/frameworks/11-brand-seo.md) |
| LPコピーライティング | PASBECONA、QUEST、AIDCA等13種 | [12-lp-copywriting-frameworks.md](references/frameworks/12-lp-copywriting-frameworks.md) |

**統合ワークフロー**: [08-integrated-workflow.md](references/frameworks/08-integrated-workflow.md)

## SEO監査ツール

スキル内蔵の自動監査スクリプト。Lighthouse、構造化データ、メタタグ、リンク分析を統合。

### クイックスタート

```bash
# スキルディレクトリに移動
cd .claude/skills/seo-master/scripts

# 高速スコア診断（Lighthouseなし、数秒で完了）
pnpm tsx src/index.ts score https://example.com

# フル監査（Lighthouse含む、30秒程度）
pnpm tsx src/index.ts full https://example.com

# Lighthouseスキップで高速フル監査
pnpm tsx src/index.ts full https://example.com --skip-lighthouse
```

### コマンド一覧

| コマンド | 説明 | 所要時間 |
|----------|------|----------|
| `score <url>` | 高速スコア診断（Lighthouseなし） | ~3秒 |
| `full <url>` | 全監査（Lighthouse含む） | ~30秒 |
| `lighthouse <url>` | Core Web Vitals + SEO監査 | ~25秒 |
| `schema <url>` | 構造化データ検証 | ~2秒 |
| `meta <url>` | メタタグ監査 | ~2秒 |
| `links <url>` | リンク分析 | ~2秒 |

### オプション

```bash
# JSON出力
pnpm tsx src/index.ts full https://example.com -f json

# Markdown出力
pnpm tsx src/index.ts full https://example.com -f md

# ファイルに保存
pnpm tsx src/index.ts full https://example.com -f md -o report.md

# Lighthouseスキップ
pnpm tsx src/index.ts full https://example.com --skip-lighthouse
```

### 出力例

```
╔══════════════════════════════════════╗
║       SEO AUDIT SCORE SUMMARY        ║
╚══════════════════════════════════════╝

Overall Score: 39/40 (98%)

Category Scores:
  Technical SEO   ████████░░ 80%
  Internal SEO    ██████████ 100%

Grade: A+ Excellent
```

**詳細**: [10-audit-tools.md](references/frameworks/10-audit-tools.md) を参照

## GSC Analytics（Search Console連携）

Google Search Consoleからパフォーマンスデータを取得・分析。

### セットアップ

```bash
# 1. Google Cloud Consoleでプロジェクト作成
# 2. Search Console API有効化
# 3. サービスアカウント作成、JSONキーダウンロード
# 4. サービスアカウントをGSCプロパティに追加

# 環境変数設定
export GSC_KEY_FILE=/path/to/service-account.json
```

### コマンド一覧

| コマンド | 説明 |
|----------|------|
| `gsc:performance <site-url>` | パフォーマンス概要（クリック、表示、CTR） |
| `gsc:rankings <site-url> [keywords...]` | 順位変動トラッキング |
| `gsc:opportunities <site-url>` | 改善機会の発見 |

### 使用例

```bash
cd .claude/skills/seo-master/scripts

# パフォーマンス概要（過去30日）
pnpm tsx src/index.ts gsc:performance https://example.com

# 過去7日間のデータ
pnpm tsx src/index.ts gsc:performance https://example.com -d 7

# 特定キーワードの順位追跡
pnpm tsx src/index.ts gsc:rankings https://example.com "iphone 買取" "壊れた iphone"

# SEO改善機会の発見
pnpm tsx src/index.ts gsc:opportunities https://example.com
```

### 機会分析カテゴリ

| カテゴリ | 条件 | アクション |
|----------|------|------------|
| Low CTR | 表示100+、CTR<2% | タイトル・meta改善 |
| Striking Distance | 順位5-20、表示50+ | コンテンツ強化 |
| Link Building | CTR5%+、順位10+ | 被リンク獲得 |
| Missing Content | 汎用ページで表示50+ | 専用ページ作成 |

## 競合分析ワークフロー

GSCデータとSERP分析を組み合わせた競合分析フロー。

```
GSC機会発見 → SERP分析 → ギャップ特定 → 改善実行
```

### 環境設定

```bash
cd .claude/skills/seo-master/scripts

# .env.exampleをコピーして設定
cp .env.example .env

# 必要な環境変数:
# - GSC_KEY_FILE: GSCサービスアカウントJSONパス
# - SERPER_API_KEY: Serper APIキー（https://serper.dev で取得、2,500クエリ/月無料）
```

### ステップ1: 改善機会の発見

```bash
pnpm tsx src/index.ts gsc:opportunities https://applebuyers.jp
```

**注目する機会**:
- **Striking Distance**: 順位5-20位で表示多い → コンテンツ強化で上位狙える
- **Low CTR**: 表示多いがCTR低い → タイトル・description改善

### ステップ2: 競合SERP分析

```bash
# 高速分析（SERP順位のみ）
pnpm tsx src/index.ts serp:analyze "ターゲットキーワード" --no-analyze

# 詳細分析（競合ページの構成も取得）
pnpm tsx src/index.ts serp:analyze "ターゲットキーワード"

# JSON出力
pnpm tsx src/index.ts serp:analyze "ターゲットキーワード" -f json -o analysis.json
```

**取得できる情報**:
- 上位10サイトのURL・タイトル・description
- 各ページのH1/H2構成、文字数、Schema有無
- 自サイトの順位（Top10内の場合）

### ステップ3: ギャップ分析

SERP分析結果から以下を比較:

| 比較項目 | 確認ポイント |
|----------|--------------|
| 文字数 | 競合Top3平均より少ない → コンテンツ拡充 |
| H2数 | 競合より少ない → セクション追加 |
| Schema | 競合にあって自サイトにない → 構造化データ追加 |
| H1/タイトル | キーワード含有率、訴求力 |

### ステップ4: 改善アクション

| 状況 | アクション |
|------|------------|
| Top10圏外 | 専用コンテンツ新規作成 |
| 順位4-10位 | コンテンツ拡充、内部リンク強化 |
| 順位1-3位 | CTR改善（タイトル・description最適化） |

### コマンド一覧

| コマンド | 説明 | 所要時間 |
|----------|------|----------|
| `serp:analyze <keyword>` | SERP分析（詳細） | ~30秒 |
| `serp:analyze <keyword> --no-analyze` | SERP分析（高速） | ~2秒 |

### オプション

| オプション | 説明 |
|------------|------|
| `-d, --domain <domain>` | 追跡するドメイン（デフォルト: applebuyers.jp） |
| `-p, --pages <number>` | 詳細分析するページ数（デフォルト: 5） |
| `--no-analyze` | ページ詳細分析をスキップ |
| `-f, --format <type>` | 出力形式（json, console） |
| `-o, --output <file>` | 出力ファイルパス |

## SEOフレームワーク検索（BM25）

ページタイプ、検索意図、LLM対策のデータベースをBM25検索エンジンで検索。

### データベース

| ファイル | 内容 |
|----------|------|
| `data/page-types.csv` | 8種のページタイプ（informational-hub, transactional-cv等） |
| `data/search-intents.csv` | 8種の検索意図（know, do, commercial等） |
| `data/llm-tactics.csv` | 10種のLLM対策（p0-p3優先度付き） |

### コマンド一覧

| コマンド | 説明 |
|----------|------|
| `search <query>` | フレームワーク横断検索 |
| `list <type>` | 全データ一覧表示 |
| `analyze:page <url>` | ページタイプ・検索意図判定 |
| `generate:comment <url>` | SEOメタコメント生成 |
| `check:llm <url>` | LLM対策チェック |

### 使用例

```bash
cd .claude/skills/seo-master/scripts

# フレームワーク検索
pnpm tsx src/index.ts search "買取 価格"
pnpm tsx src/index.ts search "ガイド 解説" --domain page-type
pnpm tsx src/index.ts search "FAQ" --domain llm

# 一覧表示
pnpm tsx src/index.ts list page-types
pnpm tsx src/index.ts list intents
pnpm tsx src/index.ts list llm-tactics

# ページ分析
pnpm tsx src/index.ts analyze:page https://applebuyers.jp/prices/iphone-16

# LLM対策チェック
pnpm tsx src/index.ts check:llm https://applebuyers.jp/articles/sample

# SEOコメント生成
pnpm tsx src/index.ts generate:comment https://applebuyers.jp/prices/iphone-16 -k "iPhone 16 買取"
```

### ページタイプ分類

| タイプ | 検索意図 | CTA強度 | LLM対策 |
|--------|----------|---------|---------|
| informational-hub | Know | soft | high |
| comparison | Commercial | medium | medium |
| transactional-cv | Do | strong | low |
| tutorial-howto | Do (Device) | soft | high |
| brand | Website | navigation | medium |
| product-detail | Commercial | medium | medium |
| local-service | Visit | strong | low |
| news-update | Know | soft | high |

### LLM対策優先度

| 優先度 | 対策 | 説明 |
|--------|------|------|
| p0 | structured-answer | H2を質問形式に、直後に50-100字で直接回答 |
| p0 | faq-schema | FAQPage JSON-LDを5問以上実装 |
| p1 | fact-density | 150-200語ごとに統計・数値を配置 |
| p1 | citation-markup | 引用元にaccessDate、URLを明記 |
| p1 | author-schema | Person Schemaで著者情報 |
| p2 | date-freshness | dateModifiedを30日以内に維持 |
| p2 | brand-mention | ブランド名+属性を自然な文脈で繰り返し言及 |
| p2 | tl-dr | 主要H2の下に1-2文のTL;DR（要約）を配置 |

### 生成されるSEOコメント例

```tsx
/**
 * @seo-meta
 * page-type: transactional-cv
 * search-intent: do
 * target-keywords: ["iPhone 16 買取", "iPhone 16 売る"]
 * llm-strategy: basic
 * schema-required: [Product, Offer, FAQPage]
 * last-audit: 2026-01-11
 */
export default function ModelPricePage() {
```
