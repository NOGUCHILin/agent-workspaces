# xlm-trader (master branch)

Branch-specific Claude Code settings for master branch.

## CI/CDルール（必須）

コード変更時は以下を遵守:

1. **コミット前**: ローカルでlint/型チェック実行
   - Python: `ruff check trader.py && mypy trader.py --ignore-missing-imports`
   - Dashboard: `npm run lint && npx tsc --noEmit`

2. **プッシュ後**: GitHub Actions通過を確認

3. **デプロイ先**:
   - trader.py → Railway (cron毎時)
   - dashboard/ → Vercel (自動)

## CLIコマンド

### Railway (trader)
```bash
railway status          # 状態確認
railway logs            # ログ表示（ストリーム）
railway logs -d         # デプロイログ
railway logs -b         # ビルドログ
```

### Vercel (dashboard)
```bash
cd repo/dashboard
vercel list             # デプロイ一覧
vercel logs <url>       # ログ確認
```

### Supabase
```bash
supabase db diff        # スキーマ差分
supabase db push        # マイグレーション適用
```

## Auto-backtest

description: 自動バックテストを実行。開始日と終了日を指定してバックテストを自動化します。

```python
start_date: str = "2020-01-01" # バックテスト開始日 (YYYY-MM-DD)
end_date: str = "2026-01-12"   # バックテスト終了日 (YYYY-MM-DD)
```

```bash
cd repo
python backtest.py --start_date {start_date} --end_date {end_date}
```