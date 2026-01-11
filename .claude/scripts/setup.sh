#!/bin/bash
# ============================================================
# Claude Code Workspace セットアップスクリプト
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Claude Code Workspace Setup ==="
echo ""

# 1. OS検出
detect_os() {
    case "$(uname -s)" in
        Darwin*) echo "macos" ;;
        Linux*)  echo "linux" ;;
        *)       echo "unknown" ;;
    esac
}

OS=$(detect_os)
echo "[1/4] OS検出: $OS"

# 2. Playwright MCP確認
echo "[2/4] Playwright MCP確認..."
if [ "$OS" = "macos" ]; then
    PLAYWRIGHT_PATH="/opt/homebrew/bin/mcp-server-playwright"
    if [ ! -f "$PLAYWRIGHT_PATH" ]; then
        PLAYWRIGHT_PATH="/usr/local/bin/mcp-server-playwright"
    fi
else
    PLAYWRIGHT_PATH="$(which mcp-server-playwright 2>/dev/null || echo "")"
fi

if [ -z "$PLAYWRIGHT_PATH" ] || [ ! -f "$PLAYWRIGHT_PATH" ]; then
    echo "  ⚠ mcp-server-playwright が見つかりません"
    echo "  インストール: npm install -g @anthropic-ai/mcp-server-playwright"
else
    echo "  ✓ $PLAYWRIGHT_PATH"
    # playwright-mcp.shを更新
    sed -i.bak "s|/opt/homebrew/bin/mcp-server-playwright|$PLAYWRIGHT_PATH|g" \
        "$SCRIPT_DIR/playwright-mcp.sh" 2>/dev/null || true
fi

# 3. .mcp.json設定
echo "[3/4] MCP設定..."
if [ -f "$WORKSPACE_ROOT/.mcp.json" ]; then
    echo "  ✓ .mcp.json 既存"
else
    if [ -f "$WORKSPACE_ROOT/.mcp.json.example" ]; then
        cp "$WORKSPACE_ROOT/.mcp.json.example" "$WORKSPACE_ROOT/.mcp.json"
        echo "  ✓ .mcp.json 作成（.exampleからコピー）"
        echo ""
        echo "  ⚠ 以下を設定してください:"
        echo "    - SLACK_BOT_TOKEN: Slack App の User/Bot Token"
        echo "    - SLACK_TEAM_ID: ワークスペースID（URLのTxxxxxxxx）"
    else
        echo "  ⚠ .mcp.json.example が見つかりません"
    fi
fi

# 4. 必要なディレクトリ作成
echo "[4/4] ディレクトリ確認..."
mkdir -p "$WORKSPACE_ROOT/projects"
mkdir -p "$HOME/.playwright-profiles"
echo "  ✓ projects/, ~/.playwright-profiles/"

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "次のステップ:"
echo "  1. .mcp.json を編集してトークンを設定"
echo "  2. Claude Code を再起動"
echo ""
