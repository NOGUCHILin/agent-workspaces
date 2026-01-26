# AI/AEO（Answer Engine Optimization）フレームワーク

## 概要

AEOは、AIが生成する回答に引用・参照されることを目的とした最適化。2025年、Google検索の16%でAI Overviewが表示され、65%以上の検索がクリックなしで終了。

## なぜAEOが重要か

**2025年の検索状況**:
- AI Overviewが16%の検索に表示
- 65%以上の検索がゼロクリック
- Gartner予測: 2026年までに25%の検索がAIチャットボットへ移行
- AI経由のトラフィックはコンバージョン率10%超（最高水準）

## フレームワーク一覧

### 1. 構造化回答フレームワーク

AIが引用しやすいコンテンツ構造。

**原則**:
- 質問に対する明確な回答を50-100文字で冒頭に
- 詳細はその後に展開
- 箇条書き、表、ステップで整理

**構造パターン**:
```markdown
## [質問形式の見出し]

[50-100文字の直接的な回答]

### 詳細

- ポイント1
- ポイント2
- ポイント3

### 関連情報

[補足説明]
```

**ワークフロー**:
```
1. ターゲット質問を特定
2. 冒頭に直接的な回答を配置
3. 構造化データを実装
4. FAQセクションを追加
5. 比較表を活用
6. ステップバイステップで説明
```

### 2. 構造化データ強化フレームワーク

AIが理解しやすいマークアップ。

**AEOに効果的なSchema**:
| Schema | 効果 | 用途 |
|--------|------|------|
| FAQPage | 高 | よくある質問 |
| HowTo | 高 | 手順説明 |
| Article | 中 | 記事コンテンツ |
| Product | 中 | 商品情報 |
| LocalBusiness | 中 | 店舗情報 |

**FAQ Schema例**:
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [{
    "@type": "Question",
    "name": "壊れたiPhoneでも買取できますか？",
    "acceptedAnswer": {
      "@type": "Answer",
      "text": "はい、画面割れ、水没、電源不良などの状態でも買取可能です。状態により20-50%の減額となる場合があります。"
    }
  }]
}
```

### 3. E-E-A-T強化フレームワーク（AEO版）

AIが信頼できる情報源として認識するための要素。

**AIが重視するE-E-A-Tシグナル**:
| 要素 | AIへの効果 | 実装方法 |
|------|-----------|----------|
| 著者情報 | 高 | Author Schema、経歴明記 |
| 出典・引用 | 高 | 信頼できるソースへのリンク |
| 更新日 | 中 | dateModified明記 |
| 専門用語の定義 | 中 | 用語集、括弧内説明 |
| データ・統計 | 高 | 自社データ、調査結果 |

**ワークフロー**:
```
1. 著者情報をページに明記
2. Author Schemaを実装
3. 引用・出典を明確に
4. 更新日を常に最新に
5. 自社の一次データを活用
```

### 4. ゼロクリック対応フレームワーク

クリックなしでも価値を提供しつつ、クリックを促す。

**戦略**:
| 状況 | 対応 |
|------|------|
| Featured Snippet獲得 | 回答後に「詳細はこちら」で誘導 |
| AI Overview引用 | ブランド認知効果を活用 |
| ゼロクリック | リマーケティング、ブランド検索増加を狙う |

**コンテンツ設計**:
- 冒頭で質問に回答（AI引用用）
- 続きで詳細・付加価値を提供（クリック誘因）
- CTAを効果的に配置

### 5. マルチプラットフォームAEOフレームワーク

各AIプラットフォームへの対応。

**主要プラットフォーム**:
| プラットフォーム | 特徴 | 対応 |
|-----------------|------|------|
| Google AI Overview | 検索結果に統合 | 構造化データ、Featured Snippet最適化 |
| ChatGPT | 37.5M検索/日 | 包括的コンテンツ、明確な回答 |
| Perplexity | リアルタイムWeb検索 | 出典明確、最新情報 |
| Claude | 専門的推論 | 詳細な説明、論理的構造 |

**ワークフロー**:
```
1. 各プラットフォームでブランド検索
2. 現在の表示状況を確認
3. 引用されているコンテンツを分析
4. 不足している情報を補完
5. 定期的にモニタリング
```

## AEOチェックリスト

### コンテンツ構造
- [ ] 質問に直接回答（50-100文字）
- [ ] 見出しが質問形式
- [ ] 箇条書き・表・ステップを活用
- [ ] FAQセクションあり

### 構造化データ
- [ ] FAQPage Schema実装
- [ ] HowTo Schema（手順コンテンツ）
- [ ] Author Schema
- [ ] dateModified明記

### E-E-A-T
- [ ] 著者情報明記
- [ ] 出典・引用あり
- [ ] 自社データ・統計あり
- [ ] 更新日が最新

## 参考資料

- [CXL: Answer Engine Optimization Guide](https://cxl.com/blog/answer-engine-optimization-aeo-the-comprehensive-guide-for-2025/)
- [SurferSEO: AEO Strategies](https://surferseo.com/blog/answer-engine-optimization/)
- [Digital Elevator: AEO Framework](https://thedigitalelevator.com/blog/answer-engine-optimization-aeo/)
- [Shopify: What is AEO](https://www.shopify.com/blog/what-is-aeo)
