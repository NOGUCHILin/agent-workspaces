# SEO監査ツール実装計画

## 概要

SEOフレームワーク（01-09）を活用した自動監査ツール。スキル内のscriptsディレクトリに配置し、CLIから実行可能。

## アーキテクチャ

```
.claude/skills/seo-master/
├── SKILL.md
├── references/
│   └── frameworks/
└── scripts/                  # ← 新規追加
    ├── package.json
    ├── tsconfig.json
    ├── src/
    │   ├── index.ts          # CLIエントリ
    │   ├── auditors/
    │   │   ├── lighthouse.ts # CWV + SEO基本
    │   │   ├── schema.ts     # 構造化データ
    │   │   ├── links.ts      # 内部リンク
    │   │   └── meta.ts       # メタタグ
    │   ├── scoring/
    │   │   └── calculator.ts # スコア算出
    │   └── reports/
    │       └── generator.ts  # レポート生成
    └── output/               # レポート出力先
```

## 依存パッケージ

| パッケージ | 用途 | バージョン |
|-----------|------|-----------|
| lighthouse | CWV + SEO監査 | ^12.0.0 |
| puppeteer | ブラウザ自動化 | ^22.0.0 |
| cheerio | HTML解析 | ^1.0.0 |
| commander | CLI | ^12.0.0 |
| chalk | 出力装飾 | ^5.0.0 |
| typescript | 型安全 | ^5.0.0 |
| tsx | 実行 | ^4.0.0 |

## 実装フェーズ

### Phase 1: 基盤構築
**目標**: CLI基盤 + Lighthouse統合

- [x] 1.1 scriptsディレクトリ作成
- [x] 1.2 package.json + tsconfig.json設定
- [x] 1.3 依存パッケージインストール
- [x] 1.4 CLIエントリポイント（commander）
- [x] 1.5 Lighthouse auditor実装
- [x] 1.6 単一URL監査の動作確認

**成果物**: `pnpm audit <url>` でCWV + SEO基本監査が実行可能 ✅

---

### Phase 2: 構造化データ検証
**目標**: JSON-LD Schema検証

- [x] 2.1 schema auditor実装
- [x] 2.2 ページからJSON-LD抽出（cheerio使用）
- [x] 2.3 Schema.org準拠チェック（15+スキーマタイプ対応）
- [x] 2.4 必須プロパティ検証 + 推奨プロパティ警告
- [x] 2.5 テスト実行（apple.com, applebuyers.jp）

**成果物**: 構造化データの有無・品質を評価 ✅

---

### Phase 3: 内部リンク・メタタグ
**目標**: ページ内SEO要素の検証

- [x] 3.1 meta auditor実装（title, description, robots, canonical, OG, viewport, H1）
- [x] 3.2 links auditor実装（内部リンク抽出・分析）
- [x] 3.3 重複リンク検出
- [ ] 3.4 リンク切れチェック（Phase 5で実装予定）
- [x] 3.5 テスト実行（applebuyers.jp）

**成果物**: メタタグ品質 + 内部リンク構造の評価 ✅

---

### Phase 4: スコアリング統合
**目標**: 09-evaluation-scoring.md準拠のスコア算出

- [x] 4.1 scoring calculator実装
- [x] 4.2 カテゴリ別スコア（技術/内部SEO）
- [x] 4.3 総合スコア算出 + グレード表示
- [x] 4.4 優先度マトリクス判定（Quick Wins/Strategic/Fill-in/Low Priority）
- [x] 4.5 テスト実行（applebuyers.jp: A+, example.com: F）

**成果物**: 1-5スケールのスコア + 優先施策リスト ✅

---

### Phase 5: レポート生成
**目標**: 複数形式でのレポート出力

- [x] 5.1 JSON出力
- [x] 5.2 Markdown出力（表形式、構造化）
- [x] 5.3 コンソール出力（整形、色付き）
- [ ] 5.4 サイトマップクロール対応（将来実装）
- [x] 5.5 SKILL.md更新（使い方追記）

**成果物**: 完全なSEO監査レポート ✅

---

## CLIコマンド仕様

```bash
# 単一ページ監査
pnpm --prefix .claude/skills/seo-master/scripts audit https://example.com/page

# サイト全体監査（サイトマップ使用）
pnpm --prefix .claude/skills/seo-master/scripts audit:site https://example.com/sitemap.xml

# 出力形式指定
pnpm --prefix .claude/skills/seo-master/scripts audit https://example.com --format json
pnpm --prefix .claude/skills/seo-master/scripts audit https://example.com --format md

# レポート保存
pnpm --prefix .claude/skills/seo-master/scripts audit https://example.com -o ./output/report.json
```

## 出力形式

### JSON出力例

```json
{
  "url": "https://example.com/page",
  "timestamp": "2025-01-06T12:00:00Z",
  "scores": {
    "overall": 72,
    "content": 18,
    "technical": 20,
    "internal": 16,
    "external": 18
  },
  "audits": {
    "lighthouse": { "performance": 85, "seo": 92, "accessibility": 88 },
    "schema": { "found": true, "types": ["Article", "FAQPage"], "valid": true },
    "meta": { "title": { "length": 55, "hasKeyword": true }, ... },
    "links": { "internal": 12, "external": 3, "broken": 0 }
  },
  "recommendations": [
    { "priority": "quick-win", "issue": "title長すぎ", "action": "60文字以内に" },
    ...
  ]
}
```

## 進捗状況

| Phase | 状態 | 完了日 |
|-------|------|--------|
| Phase 1: 基盤構築 | [x] 完了 | 2025-01-06 |
| Phase 2: 構造化データ | [x] 完了 | 2025-01-06 |
| Phase 3: リンク・メタ | [x] 完了 | 2025-01-06 |
| Phase 4: スコアリング | [x] 完了 | 2025-01-06 |
| Phase 5: レポート | [x] 完了 | 2025-01-06 |

## 参考資料

- [Lighthouse GitHub](https://github.com/GoogleChrome/lighthouse)
- [structured-data-testing-tool](https://github.com/iaincollins/structured-data-testing-tool)
- [09-evaluation-scoring.md](09-evaluation-scoring.md) - スコアリング基準

---

作成日: 2025-01-06
最終更新: 2025-01-06 (Phase 1完了)
