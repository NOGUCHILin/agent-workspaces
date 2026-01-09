---
name: generate-video
description: AI動画生成を支援する。「動画作って」「ビデオ生成」「映像作成」と言われた時に使用。Sora/Runway/Pika/Klingの選択とプロンプト作成をサポート。
---

# ワークフロー

1. 目的・用途をヒアリング
2. 適切なツール選択（下記テーブル参照）
3. プロンプト作成支援
4. 生成 → 必要に応じて編集

# ツール選択

| 目的 | おすすめツール | 理由 |
|------|---------------|------|
| 映画品質・ストーリー性 | Sora | 最高品質、最大60秒、物理法則理解 |
| 多機能・編集込み | Runway | 生成+編集+VFX一貫、Gen-3 Alpha高品質 |
| SNS・短尺・高速 | Pika | 簡単操作、高速生成、コスパ◎ |
| リアルな人物の動き | Kling | 自然な動作、最大2分1080p |
| Google連携 | Veo | Googleの動画生成（新興） |

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

# 選定の判断基準

| 基準 | 確認ポイント |
|------|-------------|
| 品質レベル | プロ品質 → Sora/Runway |
| 予算 | 無料/低コスト → Pika |
| 納期 | 即日 → Pika、時間あり → Sora |
| 編集の有無 | 編集も必要 → Runway |
| 商用利用 | 各ツールの規約確認必須 |
