---
name: generate-video
description: AI動画生成を支援する。「動画作って」「ビデオ生成」「映像作成」と言われた時に使用。Sora/Runway/Pika/Klingの選択とプロンプト作成をサポート。
---

# ワークフロー（4フェーズ）

| フェーズ | 内容 |
|---------|------|
| 1. Pre-production | 目的ヒアリング、ビートシート/ストーリーボード作成、スタイル統一 |
| 2. Low-res探索 | **720p**で3-5バリエーション生成、アーティファクト記録 |
| 3. Refinement | 1変数ずつ調整（"enhance shadow depth"等）、成功プロンプト保存 |
| 4. Post-processing | アップスケール、色補正、音声ミキシング |

**重要**: 720p生成→アップスケールが**ネイティブ4Kより高品質**（75%が支持）

# ツール選択（2026年1月ランキング）

| 順位 | ツール | 特徴 | 価格 |
|------|--------|------|------|
| 1 | **Google Veo 3** | 4K、2分+、**ネイティブ音声生成**（声・環境音・BGM）、リップシンク◎ | $19.99〜249.99/月 |
| 2 | Sora 2 (OpenAI) | ストーリーテリング最高峰、最長20秒、キャラ一貫性 | $20/月(Plus) |
| 3 | Kling AI | コスパ抜群、人物モーション◎、短尺向け | $5/月 |
| 4 | Runway Gen-4 | プロ編集+VFX一体、モーションコントロール | $12/月〜 |
| 5 | HeyGen | アバター、リップシンク、多言語、5分+対応 | 従量制 |

## 目的別おすすめ

| 目的 | ツール |
|------|--------|
| 音声付き・商用品質 | Google Veo 3 |
| ストーリーテリング | Sora 2 |
| コスパ重視・短尺 | Kling AI |
| 編集・VFX込み | Runway Gen-4 |
| ビジネス動画・アバター | HeyGen |

# 各ツール詳細

## Sora（OpenAI）
- **特徴**: 最大60秒、圧倒的リアリズム、シーン一貫性
- **短所**: 招待制、生成に時間がかかる
- **用途**: 映画、プロ品質作品

## Runway（Gen-3 Alpha）
- **特徴**: 動画生成+編集+VFXが一つで完結
- **アクセス**: runwayml.com
- **用途**: プロモーション、広告、VFX映像

## Pika
- **特徴**: 直感的操作、高速生成
- **アクセス**: pika.art
- **用途**: SNS投稿、マーケティング動画、入門

## Kling（Kuaishou）
- **特徴**: 物理シミュレーション、人間らしい動き
- **アクセス**: klingai.com
- **用途**: 人物動画、物理的動きのシーン

# プロンプトのコツ

## 基本構成
```
[被写体] + [アクション] + [環境/背景] + [カメラワーク] + [スタイル/雰囲気]
```

## 効果的なプロンプト例

```
A Japanese woman in her 30s walking through a sunlit Tokyo street,
cherry blossoms falling gently,
camera follows from behind then circles to front,
cinematic style, soft natural lighting, 4K quality
```

## Tips
- **具体的に**: 曖昧な指示は避ける
- **カメラワーク指定**: pan, zoom, tracking shot, aerial view
- **スタイル指定**: cinematic, documentary, anime style
- **長さ指定**: 5 seconds, 15 seconds

# マルチモデルワークフロー（高品質）

1. **キーフレーム生成**: Midjourney v7でスタイル・構図を固定
2. **モーション合成**: Veo 3/Runway で開始・終了フレーム間を補間
3. **アップスケール**: Topaz Video AI（Proteusモデル）で4K化

# キーワード集

| カテゴリ | キーワード例 |
|----------|-------------|
| Lighting | golden hour, soft diffused, dramatic side, backlit, rim, neon glow |
| Atmosphere | misty, foggy, cinematic, ethereal, dreamlike, crisp |
| Camera | pan, zoom, tracking shot, aerial view, dolly, crane, handheld |
| Movement | slow motion, time-lapse, freeze frame, speed ramp |

# ネガティブプロンプト

```
blurry, low quality, artifacts, watermark, morphing, flickering, jittery motion
```

# 選定の判断基準

| 基準 | 確認ポイント |
|------|-------------|
| 品質レベル | プロ品質 → Veo 3/Sora |
| 予算 | 低コスト → Kling AI |
| 音声必要 | あり → Veo 3 |
| 編集の有無 | 編集も必要 → Runway |
| 商用利用 | 各ツールの規約確認必須 |
