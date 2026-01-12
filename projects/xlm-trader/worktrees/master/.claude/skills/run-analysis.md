# description: モデル分析・比較。「分析して」「モデル比較」「どのモデルがいい」で発動

## 重要

新規分析スクリプトを作成しないこと。以下の既存スクリプトを使用する。

## モデル比較実験

```bash
cd /Users/noguchilin/claude-code-workspaces/projects/xlm-trader/worktrees/master/repo
python analyze_model.py
```

## 比較対象

- XGBoost（標準/深層）
- GradientBoosting
- RandomForest

## 出力

各モデルのCV精度を比較表示

## 戦略最適化

```bash
python optimize_strategy.py
```

閾値・レバレッジ等のパラメータ最適化
