#!/bin/bash
# ============================================================
# Playwright MCP Wrapper Script (Workspace専用)
# ============================================================
# 目的: claude-code-workspaces内のworktree間でブラウザプロファイルを分離
#
# プロファイル名生成ロジック:
#   projects/{project}/worktrees/{branch}/* → {project}-{branch}
#   例: projects/xlm-trader/worktrees/master/repo → xlm-trader-master
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# PWDからプロジェクト名とブランチ名を抽出
if [[ "$PWD" =~ ${WORKSPACE_ROOT}/projects/([^/]+)/worktrees/([^/]+) ]]; then
  PROFILE_NAME="${BASH_REMATCH[1]}-${BASH_REMATCH[2]}"
else
  # フォールバック: ディレクトリ名を使用
  PROFILE_NAME=$(basename "$PWD")
fi

USER_DATA_DIR="$HOME/.playwright-profiles/$PROFILE_NAME"
PREFS_DIR="$USER_DATA_DIR/Default"
PREFS_FILE="$PREFS_DIR/Preferences"

# プロファイルディレクトリ作成
mkdir -p "$PREFS_DIR"

# タブ復元設定を適用
if [ ! -f "$PREFS_FILE" ]; then
  cat > "$PREFS_FILE" << 'PREFS_EOF'
{
  "session": {
    "restore_on_startup": 1
  }
}
PREFS_EOF
else
  if ! grep -q '"restore_on_startup"' "$PREFS_FILE" 2>/dev/null; then
    python3 -c "
import json
with open('$PREFS_FILE', 'r') as f:
    prefs = json.load(f)
prefs.setdefault('session', {})['restore_on_startup'] = 1
with open('$PREFS_FILE', 'w') as f:
    json.dump(prefs, f, indent=2)
" 2>/dev/null
  fi
fi

# Playwright MCPパスを自動検出
if [ -x "/opt/homebrew/bin/mcp-server-playwright" ]; then
  PLAYWRIGHT_MCP="/opt/homebrew/bin/mcp-server-playwright"
elif [ -x "/usr/local/bin/mcp-server-playwright" ]; then
  PLAYWRIGHT_MCP="/usr/local/bin/mcp-server-playwright"
else
  PLAYWRIGHT_MCP="$(which mcp-server-playwright 2>/dev/null || echo "")"
fi

if [ -z "$PLAYWRIGHT_MCP" ]; then
  echo "Error: mcp-server-playwright not found" >&2
  echo "Install: npm install -g @anthropic-ai/mcp-server-playwright" >&2
  exit 1
fi

exec "$PLAYWRIGHT_MCP" --user-data-dir "$USER_DATA_DIR" "$@"
