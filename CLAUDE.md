# claude-code-workspaces

複数プロジェクト・ブランチを管理するワークスペース

## 初回セットアップ

```bash
.claude/scripts/setup.sh
```

### 必要な設定

| 設定 | 方法 |
|------|------|
| `.mcp.json` | `.mcp.json.example`をコピーしてトークン設定 |
| Slack Token | https://api.slack.com/apps → OAuth & Permissions |
| Team ID | SlackのURL `app.slack.com/client/Txxxxxxxx/` |

詳細: [docs/SETUP.md](docs/SETUP.md)

## projects/内で作業時

- projects/は独自git管理（親の.gitignoreで除外済み）
- 親のCLAUDE.md設定を継承する

## 参照

- セットアップ: @docs/SETUP.md
- Claude Code参考: @docs/reference/
