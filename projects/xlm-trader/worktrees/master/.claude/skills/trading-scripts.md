# description: トレードBot関連スクリプト管理。新規作成前に必ず確認。「スクリプト一覧」「バックテスト」「訓練」「分析」で発動

## 重要: 新規スクリプト作成禁止

既存スクリプトで対応可能な機能の新規作成は禁止。
ユーザーが「〇〇して」と言った場合、まず以下の一覧から該当スクリプトを探し、実行すること。

## 本番スクリプト（変更注意）

| ファイル | 役割 | 実行方法 |
|----------|------|----------|
| trader.py | 本番Bot（Railway自動実行） | `python trader.py` |
| config.py | 設定（単一真実源） | importして使用 |
| train_model.py | RandomForest訓練 | `python train_model.py` |
| backtester.py | バックテスト | `python backtester.py` |

## 実験スクリプト

| ファイル | 役割 | 実行方法 |
|----------|------|----------|
| train_xgboost.py | XGBoost訓練実験 | `python train_xgboost.py` |
| analyze_model.py | モデル比較実験 | `python analyze_model.py` |
| backtest_grid.py | 閾値グリッドサーチ | `python backtest_grid.py` |
| backtest_monthly.py | 月別分析 | `python backtest_monthly.py` |
| optimize_strategy.py | 戦略最適化 | `python optimize_strategy.py` |
| weekly_report.py | 週次レポート | `python weekly_report.py` |

## 廃止予定（使用禁止）

| ファイル | 理由 |
|----------|------|
| backtest.py | 旧版（XLM/SVC用）→ backtester.py使用 |
| backtest_multi.py | 旧版 → backtest_grid.py使用 |
| liquidate_xlm.py | 1回限りの清算用 |
| analyzer.py | 旧版 → analyze_model.py使用 |
| strategy_config.py | 旧版 → config.py使用 |

## ルール

1. **新規スクリプト作成前**: この一覧を確認し、既存で対応可能か検討
2. **本番スクリプト変更時**: config.pyの単一真実源原則を遵守
3. **実験スクリプト追加時**: この一覧を更新
4. **廃止時**: `_deprecated/`に移動、この一覧を更新
