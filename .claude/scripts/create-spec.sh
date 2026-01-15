#!/bin/bash
set -e

# 仕様を作成するスクリプト（連番付き）
# 使い方: .claude/scripts/create-spec.sh <feature-name>
# 例: .claude/scripts/create-spec.sh auth-integration

FEATURE_NAME=$1
DATE=$(date +%Y-%m-%d)

if [ -z "$FEATURE_NAME" ]; then
    echo "Usage: create-spec.sh <feature-name>"
    echo ""
    echo "Example:"
    echo "  create-spec.sh auth-integration"
    echo "  → docs/specs/001-auth-integration/"
    exit 1
fi

# docs/specs/ディレクトリ確認
SPECS_DIR="docs/specs"
TEMPLATES_DIR="docs/_templates"

if [ ! -d "$TEMPLATES_DIR" ]; then
    echo "Error: Templates not found at $TEMPLATES_DIR"
    echo "Run this from worktree root directory."
    exit 1
fi

mkdir -p "$SPECS_DIR"

# 既存の最大番号を取得
MAX_NUM=0
for dir in "$SPECS_DIR"/[0-9][0-9][0-9]-*/; do
    if [ -d "$dir" ]; then
        num=$(basename "$dir" | grep -o '^[0-9]\+' || echo "0")
        if [ "$num" -gt "$MAX_NUM" ]; then
            MAX_NUM=$num
        fi
    fi
done

# 次の番号
NEXT_NUM=$((MAX_NUM + 1))
NEXT_NUM_PADDED=$(printf "%03d" $NEXT_NUM)

# ディレクトリ作成
SPEC_DIR="$SPECS_DIR/${NEXT_NUM_PADDED}-${FEATURE_NAME}"
mkdir -p "$SPEC_DIR/research"

# テンプレートコピー＆変数置換
for template in 01-requirements.md 02-design.md 03-tasks.md; do
    if [ -f "$TEMPLATES_DIR/$template" ]; then
        sed -e "s/{{FEATURE}}/${NEXT_NUM_PADDED}-${FEATURE_NAME}/g" \
            -e "s/{{DATE}}/$DATE/g" \
            "$TEMPLATES_DIR/$template" > "$SPEC_DIR/$template"
    fi
done

# researchテンプレート
if [ -f "$TEMPLATES_DIR/research/_template.md" ]; then
    cp "$TEMPLATES_DIR/research/_template.md" "$SPEC_DIR/research/"
fi

echo "✅ Created: $SPEC_DIR"
echo ""
echo "Files:"
ls -la "$SPEC_DIR"
echo ""
echo "Next: Edit $SPEC_DIR/01-requirements.md"
