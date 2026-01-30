# 技術SEOフレームワーク

## 概要

技術SEOは、検索エンジンがサイトを効率的にクロール・インデックスできるようにする施策。

## フレームワーク一覧

### 1. Core Web Vitalsフレームワーク

Googleのページ体験指標。

| 指標 | 意味 | 目標値 | 改善方法 |
|------|------|--------|----------|
| LCP | 最大コンテンツ描画 | ≤ 2.5秒 | 画像最適化、サーバー応答改善 |
| INP | 次描画への応答 | ≤ 200ms | JS最適化、メインスレッド軽減 |
| CLS | レイアウトシフト | ≤ 0.1 | サイズ明示、フォント最適化 |

**ワークフロー**:
```
1. PageSpeed Insightsで現状計測
2. 各指標の問題点を特定
3. LCP改善（画像、サーバー）
4. INP改善（JavaScript）
5. CLS改善（レイアウト）
6. 再計測・検証
7. 継続モニタリング設定
```

### 2. 構造化データフレームワーク

Schema.orgによる意味付け。

| Schema | 用途 | 効果 |
|--------|------|------|
| Article | 記事 | リッチスニペット |
| FAQPage | FAQ | FAQ表示 |
| HowTo | 手順 | ステップ表示 |
| Product | 商品 | 価格・評価表示 |
| LocalBusiness | 店舗 | ローカルパック |
| BreadcrumbList | パンくず | ナビゲーション表示 |
| VideoObject | 動画 | 動画リッチスニペット |

**実装形式**: JSON-LD（推奨）

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "タイトル",
  "author": {"@type": "Person", "name": "著者"},
  "datePublished": "2025-01-01",
  "dateModified": "2025-01-15"
}
```

**ワークフロー**:
```
1. ページタイプに適したSchemaを選定
2. 必須プロパティを確認
3. JSON-LDで実装
4. Rich Results Testで検証
5. Search Consoleで監視
```

### 3. クローラビリティフレームワーク

検索エンジンのクロール効率化。

**チェックリスト**:
- [ ] robots.txt設定
- [ ] XMLサイトマップ作成
- [ ] 内部リンク構造最適化
- [ ] クロールバジェット管理
- [ ] 404/リダイレクト処理

**ワークフロー**:
```
1. robots.txtで不要ページをブロック
2. XMLサイトマップを生成・登録
3. 孤立ページを特定・リンク追加
4. クロールエラーを修正
5. 定期的なサイトマップ更新
```

### 4. インデクサビリティフレームワーク

検索インデックスへの登録最適化。

**チェックリスト**:
- [ ] canonical設定
- [ ] meta robots適切に設定
- [ ] 重複コンテンツ解消
- [ ] noindex/nofollow適切に使用
- [ ] hreflang（多言語の場合）

### 5. モバイルファーストフレームワーク

モバイル最適化（Google Mobile-First Indexing対応）。

**チェックリスト**:
- [ ] レスポンシブデザイン
- [ ] タップターゲット 44x44px以上
- [ ] フォントサイズ 16px以上
- [ ] ビューポート設定
- [ ] モバイル表示速度

### 6. セキュリティフレームワーク

サイトセキュリティ。

**チェックリスト**:
- [ ] HTTPS導入
- [ ] 混合コンテンツ解消
- [ ] セキュリティヘッダー設定

## メタタグ最適化

### 必須メタタグ
```html
<title>60文字以内｜ブランド名</title>
<meta name="description" content="120-160文字" />
<meta name="robots" content="index, follow" />
<link rel="canonical" href="正規URL" />
```

### OGPタグ
```html
<meta property="og:title" content="タイトル" />
<meta property="og:description" content="説明" />
<meta property="og:image" content="画像URL" />
<meta property="og:type" content="article" />
```

## 検証ツール

- [PageSpeed Insights](https://pagespeed.web.dev/)
- [Rich Results Test](https://search.google.com/test/rich-results)
- [Schema Validator](https://validator.schema.org/)
- [Mobile-Friendly Test](https://search.google.com/test/mobile-friendly)
- [Search Console](https://search.google.com/search-console)

## 参考資料

- [DashThis: Technical SEO Checklist](https://dashthis.com/blog/technical-seo-checklist/)
- Google Search Central Documentation
