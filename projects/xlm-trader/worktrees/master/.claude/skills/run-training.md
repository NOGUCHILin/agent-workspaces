# description: モデル訓練。「訓練して」「学習して」「モデル更新」で発動

## 重要

新規訓練スクリプトを作成しないこと。以下の既存スクリプトを使用する。

## 本番訓練（RandomForest）

```bash
cd /Users/noguchilin/claude-code-workspaces/projects/xlm-trader/worktrees/master/repo
python train_model.py
```

## 実験訓練（XGBoost）

```bash
python train_xgboost.py
```

## 出力

- models/high_30_*.pickle（上昇予測モデル）
- models/low_30_*.pickle（下落予測モデル）
- models/*.scaler（スケーラー）
- models/metadata.json（メタデータ）

## 品質ゲート

- MIN_CV_ACCURACY = 0.55（55%以上で合格）
- 不合格時は自動でエラー終了

## 訓練後

1. バックテストで性能確認: `python backtester.py`
2. 問題なければデプロイ（git push → Railway自動デプロイ）
