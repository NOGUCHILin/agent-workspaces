#!/bin/bash
set -e

WORKTREE_PATH=$1
SPEC_NAME=$2
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/../templates"

# 引数チェック
if [ -z "$WORKTREE_PATH" ] || [ -z "$SPEC_NAME" ]; then
    echo "Usage: init-spec.sh <worktree-path> <spec-name>"
    echo ""
    echo "Examples:"
    echo "  init-spec.sh projects/xlm-trader/worktrees/master auth-flow"
    echo "  init-spec.sh projects/my-app/worktrees/feature-x dashboard"
    exit 1
fi

# ワークツリーパスを解決
if [[ "$WORKTREE_PATH" = /* ]]; then
    FULL_WORKTREE_PATH="$WORKTREE_PATH"
else
    FULL_WORKTREE_PATH="$WORKSPACE_ROOT/$WORKTREE_PATH"
fi

# ワークツリー存在確認
if [ ! -d "$FULL_WORKTREE_PATH" ]; then
    echo "Error: Worktree not found: $FULL_WORKTREE_PATH"
    exit 1
fi

# spec ディレクトリ作成
SPEC_DIR="$FULL_WORKTREE_PATH/docs/specs/$SPEC_NAME"

if [ -d "$SPEC_DIR" ]; then
    echo "Error: Spec '$SPEC_NAME' already exists at $SPEC_DIR"
    exit 1
fi

mkdir -p "$SPEC_DIR"

# 日付取得
DATE=$(date +%Y-%m-%d)

# テンプレートをコピーして変数置換
for template in "$TEMPLATE_DIR"/*.md; do
    filename=$(basename "$template")
    sed -e "s/{{SPEC_NAME}}/$SPEC_NAME/g" \
        -e "s/{{DATE}}/$DATE/g" \
        "$template" > "$SPEC_DIR/$filename"
done

echo "Created spec: $SPEC_NAME"
echo ""
echo "Files:"
ls -la "$SPEC_DIR"
echo ""
echo "Next steps:"
echo "1. Open $SPEC_DIR/01-requirements.md"
echo "2. Fill in the requirements"
echo "3. Proceed to 02-design.md, then 03-tasks.md"
