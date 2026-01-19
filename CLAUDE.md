# claude-code-worktrees

複数プロジェクト・ブランチを管理するワークスペーステンプレート

**Claude Codeを起動する場所は `claude-workspace/` です。**

```bash
cd claude-workspace
claude
```

## セットアップ

1. このリポジトリをclone
2. `claude-workspace/`に移動
3. Claude Codeを起動（Context7・Playwrightは設定済み）

### Slack連携が必要な場合

`.mcp.json`にSlack設定を追加:
```json
"slack": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-slack"],
  "env": {
    "SLACK_BOT_TOKEN": "<YOUR_SLACK_TOKEN>",
    "SLACK_TEAM_ID": "<YOUR_TEAM_ID>"
  }
}
```

詳細は [docs/SETUP.md](docs/SETUP.md) を参照。
