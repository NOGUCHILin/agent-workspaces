# description: バックテスト実行。「バックテストして」「検証して」「過去データで確認」で発動

## 実行手順

```bash
cd /Users/noguchilin/claude-code-workspaces/projects/xlm-trader/worktrees/master/repo
python backtester.py
```

## 出力内容

- 期間: 過去90日
- 初期残高 / 最終残高
- リターン率
- 取引回数 / 勝率
- プロフィットファクター
- 最大ドローダウン
- シャープレシオ

## オプション

グリッドサーチ（閾値最適化）:
```bash
python backtest_grid.py
```

月別分析:
```bash
python backtest_monthly.py
```
