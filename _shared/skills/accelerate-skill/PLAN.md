# accelerate-skill 展開計画書

## 目的

AI駆動開発手法に基づき、各メンバーのGUIスキルをCLI高速版に進化させる。

```
1. ワークフローをGUIスキル化 ← 完了
2. GUIスキルからCLIスキルをつくる ← 今ここ
3. 両スキルをもとにアプリケーションをつくる
```

## 対象メンバーとスキル

### eguchinatsu
| スキル | 内容 | CLI化見込み |
|--------|------|-------------|
| yamato-login | ヤマトB2クラウドログイン | B2クラウドAPI |
| create-shipping-label | 送り状作成 | B2クラウドAPI |
| backmarket-ship | BackMarket出荷処理 | BackMarket API |
| notify-shipment | 出荷通知 | Slack API + 各種API |

### sasoli0502
| スキル | 内容 | CLI化見込み |
|--------|------|-------------|
| assessment | Kintone査定 | Kintone API |
| morning-kpi-input | 朝KPI入力 | Google Sheets API |
| evening-kpi-input | 夕KPI入力 | Google Sheets API |
| cashflow-update | キャッシュフロー更新 | Google Sheets API |
| bm-condition-check | BM状態確認 | BackMarket API |
| setup-tomorrow-tasks | 明日のタスク設定 | Notion API |

### nakamura-misaki
（GUIスキル作成中）

### noguchilin
（テンプレート状態）

## 展開スケジュール

### Phase 1: パイロット
- 対象: sasoli0502の`morning-kpi-input`
- 理由: Google Sheets APIは確立されており、成功確率が高い
- 成果物: cli.md + scripts/

### Phase 2: 横展開（sasoli0502）
- 残りのsasoli0502スキルをCLI化
- 学んだパターンを適用

### Phase 3: 横展開（eguchinatsu）
- ヤマトAPI、BackMarket APIを調査・実装
- 業務特化のため個別対応が必要

### Phase 4: 全メンバー展開
- nakamura-misaki、noguchlinへ
- テンプレート化してスキル作成と同時にCLI化を検討

## 成功指標

| 指標 | 目標 |
|------|------|
| 実行時間短縮 | GUI版の1/10以下 |
| エラー率低下 | ブラウザ依存のエラー削減 |
| 自動化率向上 | 人間の介入なしで実行可能 |

## リスクと対策

| リスク | 対策 |
|--------|------|
| APIが存在しない | スクレイピング最適化、headless高速化 |
| API利用制限 | レート制限を考慮した設計 |
| 認証の複雑さ | OAuth対応スクリプトのテンプレート化 |

## 次のアクション

1. [ ] sasoli0502の`morning-kpi-input`をパイロットとして高速化
2. [ ] 結果を検証し、SKILL.mdを改善
3. [ ] 横展開開始
