# MCP (Model Context Protocol)

出典: [MCP](https://code.claude.com/docs/en/mcp)

---

## 概要

MCPはClaude Codeを外部サービス（GitHub、Slack、Figma等）と連携させるプロトコル。

---

## 設定ファイル場所

| スコープ | 場所 |
|---------|------|
| ユーザー/ローカル | `~/.claude.json` |
| プロジェクト | `.mcp.json`（git管理） |

---

## 基本設定例

### HTTP server（推奨）

```bash
claude mcp add --transport http github https://api.githubcopilot.com/mcp/
```

### 認証付き

```bash
claude mcp add --transport http stripe https://mcp.stripe.com \
  --header "Authorization: Bearer YOUR_TOKEN"
```

### ローカルstdio server

```bash
claude mcp add --transport stdio db \
  --env DB_URL=postgresql://... \
  -- npx -y @server/db-server
```

---

## スコープ指定

```bash
claude mcp add --scope local|project|user ...
```

| スコープ | 説明 |
|---------|------|
| `local` | 現在のマシンのみ |
| `project` | プロジェクト全体（git管理） |
| `user` | ユーザー全体 |
