---
name: generate-image
description: AI画像生成を支援する。「画像作って」「バナー作って」「イラスト生成」と言われた時に使用。Nano Banana Pro（Gemini 3 Pro Image）のプロンプト作成をサポート。
---

# ワークフロー

1. 目的・用途をヒアリング
2. 適切なツール選択
3. プロンプト作成支援（4層構造）
4. 参考画像の要否を確認
5. **イテレーション**（1変数ずつ変更して改善）

# ツール選択（2026年1月ランキング）

| 順位 | ツール | 特徴 |
|------|--------|------|
| 1 | Qwen Image 2.5 | オープンソース最高性能、ローカル実行可、テキスト描写◎ |
| 2 | Midjourney v7 | アーティスティック、クリエイター定番 |
| 3 | Nano Banana Pro | テキスト精度、Gemini統合、日本語◎ |
| 4 | Ideogram | グラフィックス、カスタム画像 |
| 5 | FLUX.1 / Stable Diffusion | オープンソース、柔軟性高 |

# Nano Banana Pro アクセス方法

1. Geminiアプリ/ウェブで「Create images」
2. モデルを「Thinking」に切り替え（Pro版必要）
3. プロンプト入力 → 生成

# プロンプト4層構造（汎用）

| 層 | 内容 | 例 |
|---|------|-----|
| 1. Subject | 主題（何を描くか） | "Golden retriever puppy" |
| 2. Description | 文脈・詳細 | "running in a park, cherry blossoms" |
| 3. Style | 美的方向性 | "photorealistic, golden hour, soft lighting" |
| 4. Constraints | 除外・技術指定 | "no blur, 4K, --ar 16:9" |

## イテレーション戦略
- **1回1変数**: 色、距離、ポーズ、背景のうち1つだけ変更
- **成功パターン記録**: 良かったプロンプトは保存して再利用

# 日本風バナー広告のプロンプト構成

```
[スタイル指定] + [背景] + [メイン要素] + [テキスト指定] + [雰囲気] + [技術指定]
```

## プロンプト例（日本風バナー広告）

```
Create a clean, minimalist Japanese-style web banner advertisement for [商品].
Aspect ratio [1200x628/1080x1080/728x90].
Background is [soft white/beige] with [subtle pattern].
Center a photorealistic image of [被写体の詳細].
Text in Japanese: [位置] "[日本語テキスト]" in [フォント色・種類].
Overall [natural/refreshing/trustworthy] feel like Japanese e-commerce sites.
High resolution, professional design.
```

# 日本的デザインの特徴

| 要素 | 内容 |
|------|------|
| デザイン | ミニマル、余白多め |
| 色使い | パステル調、緑・青・ベージュ |
| フォント | ゴシック/丸ゴシック、短く簡潔 |
| 写真 | ライフスタイル、笑顔の人物 |

# 参考画像の使い方

| ケース | 参考画像 |
|--------|----------|
| 単発バナー | 不要（プロンプトのみでOK） |
| ブランド統一 | 製品画像を参照 |
| キャラクター連作 | 最大9枚（アイデンティティロック14枚） |

## 参照画像使用時のプロンプト

```
Use image A for background style, image B for character pose, image C for color palette.
```

# ネガティブプロンプト（除外指定）

```
blurry, low quality, distorted proportions, watermark, text artifacts, extra limbs
```

# ツール別Tips

| ツール | Tips |
|--------|------|
| Midjourney | `--ar 16:9`（比率）、`--v 7`（バージョン）、`--s 250`（スタイライズ） |
| Stable Diffusion | 重み付け `(keyword:1.5)`、ネガティブプロンプト必須 |
| Nano Banana | 日本語プロンプトOK、テキスト指定が得意 |

# 一般Tips

- 解像度: 「high resolution, 4K」追加
- スタイル: 「minimalist Japanese web banner style」
- 避けたい要素: 「no clutter, no bold flashing text」
