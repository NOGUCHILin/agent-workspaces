# description: バックテスト。「バックテストして」「検証」で発動

## 実行コマンド

```bash
cd /Users/noguchilin/claude-code-workspaces/projects/xlm-trader/worktrees/master/repo
python backtester.py         # BTCのデフォルト実行
python backtester.py ETH     # ETHで実行
```

## 結果の確認

バックテスト結果はDBに保存される:

```sql
SELECT pair, win_rate, profit_factor, max_drawdown, sharpe_ratio, created_at
FROM backtest_results
ORDER BY created_at DESC
LIMIT 10;
```

## グリッドサーチ

最適な閾値を探索:

```python
from backtester import Backtester
bt = Backtester(pair="BTC")
df = bt.fetch_historical_data(days=90)
df = bt.compute_features(df)
df = bt.generate_signals(df)
result = bt.optimize_thresholds(df)
print(f"Best: buy={result['parameters']['buy_threshold']}, sell={result['parameters']['sell_threshold']}")
```

## 次のステップ

1. 良い結果が出たら `optimize_strategy.py` で設定更新
2. ダッシュボードで進捗確認
