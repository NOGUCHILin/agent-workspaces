# Settings

出典: [Settings](https://code.claude.com/docs/en/settings)

---

## 設定ファイル場所（優先度順）

| 優先度 | 種類 | 場所 |
|-------|------|------|
| 1 | Managed | macOS: `/Library/Application Support/ClaudeCode/managed-settings.json`<br/>Linux: `/etc/claude-code/managed-settings.json` |
| 2 | Local | `.claude/settings.local.json` |
| 3 | Project | `.claude/settings.json` |
| 4 | User | `~/.claude/settings.json` |

---

## 主要設定項目

```json
{
  "permissions": {
    "allow": ["Bash(git:*)", "Read(~/.zshrc)"],
    "deny": ["Bash(curl:*)", "Read(.env*)"]
  },
  "model": "claude-opus-4-5-20251101",
  "env": {"FOO": "bar"},
  "hooks": { ... },
  "sandbox": {"enabled": true}
}
```

---

## Permissions設定

### 許可パターン

```json
{
  "permissions": {
    "allow": [
      "Bash(git:*)",
      "Bash(npm run:*)",
      "Read(~/.zshrc)",
      "Edit(src/**/*.ts)"
    ]
  }
}
```

### 拒否パターン

```json
{
  "permissions": {
    "deny": [
      "Bash(curl:*)",
      "Bash(rm -rf:*)",
      "Read(.env*)",
      "Read(**/secrets/**)"
    ]
  }
}
```

---

## 環境変数

```json
{
  "env": {
    "NODE_ENV": "development",
    "DEBUG": "true"
  }
}
```

---

## Sandbox設定

```json
{
  "sandbox": {
    "enabled": true,
    "allowedPaths": ["/tmp", "./"]
  }
}
```
