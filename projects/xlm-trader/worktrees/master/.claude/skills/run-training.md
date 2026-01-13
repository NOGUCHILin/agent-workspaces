# description: モデル訓練。「訓練して」「学習」で発動

## 実行コマンド

```bash
cd /Users/noguchilin/claude-code-workspaces/projects/xlm-trader/worktrees/master/repo
python train_model.py        # BTCのみ
python train_model.py ETH    # ETHのみ
python train_model.py ALL    # 全ペア
```

## 訓練後の確認

訓練完了後、DBに登録されたモデル情報を確認:

```sql
SELECT pair, cv_accuracy_high, cv_accuracy_low, trained_at, is_active
FROM models
ORDER BY trained_at DESC
LIMIT 5;
```

## 次のステップ

1. バックテストで検証（`python backtester.py`）
2. ダッシュボードでモデル情報を確認
