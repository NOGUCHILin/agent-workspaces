# 技術SEO実装ガイド

## 構造化データ

### 必須Schema一覧
| Schema | 用途 | 実装場所 |
|--------|------|----------|
| Article | 記事ページ | 記事詳細 |
| FAQPage | FAQ | 記事末尾、LP |
| HowTo | 手順説明 | ガイド記事 |
| BreadcrumbList | パンくず | 全ページ |
| LocalBusiness | 店舗情報 | レイアウト |
| Product | 商品・買取価格 | 価格ページ |
| Service | サービス | LP |
| AggregateRating | 評価 | 商品・サービス |

### Article Schema
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "タイトル",
  "author": {
    "@type": "Person",
    "name": "著者名"
  },
  "datePublished": "2025-01-01",
  "dateModified": "2025-01-15"
}
```

### FAQPage Schema
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [{
    "@type": "Question",
    "name": "質問",
    "acceptedAnswer": {
      "@type": "Answer",
      "text": "回答"
    }
  }]
}
```

### Product Schema（買取用）
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "iPhone 15 Pro 買取",
  "brand": "Apple",
  "offers": {
    "@type": "Offer",
    "price": "85000",
    "priceCurrency": "JPY",
    "itemCondition": "https://schema.org/UsedCondition"
  }
}
```

## メタタグ

### 必須タグ
```html
<title>60文字以内｜ブランド名</title>
<meta name="description" content="120-160文字の説明" />
<meta name="robots" content="index, follow" />
<link rel="canonical" href="正規URL" />
```

### OGP
```html
<meta property="og:title" content="タイトル" />
<meta property="og:description" content="説明" />
<meta property="og:image" content="画像URL" />
<meta property="og:type" content="article" />
```

## Core Web Vitals

### 目標値
| 指標 | 目標 | 測定 |
|------|------|------|
| LCP | < 2.5秒 | 最大コンテンツ描画 |
| FID/INP | < 100ms | 初回入力遅延 |
| CLS | < 0.1 | レイアウトシフト |

### 最適化手法

#### LCP改善
- 画像: WebP/AVIF変換
- Lazy Loading
- プリロード（ヒーロー画像）
- フォント最適化

#### CLS改善
- 画像サイズ明示（width/height）
- フォントswap設定
- 動的コンテンツの領域確保

## サイトマップ

### XML Sitemap
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/page</loc>
    <lastmod>2025-01-01</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
```

### 画像サイトマップ
Google Image Search対応

## robots.txt

```
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/

Sitemap: https://example.com/sitemap.xml
```

## Canonical URL

### ルール
- 各ページに1つの正規URL
- httpsを優先
- www有無を統一
- トレイリングスラッシュを統一

## 検証ツール

- [Rich Results Test](https://search.google.com/test/rich-results)
- [Schema Validator](https://validator.schema.org/)
- [PageSpeed Insights](https://pagespeed.web.dev/)
- [Search Console](https://search.google.com/search-console)
