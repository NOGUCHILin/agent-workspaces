#!/bin/bash

# 仕様の状態を一覧表示するスクリプト
# 使い方: .claude/scripts/scan-specs.sh

SPECS_DIR="docs/specs"

if [ ! -d "$SPECS_DIR" ]; then
    echo "No specs directory found."
    echo "Create a spec: .claude/scripts/create-spec.sh <feature-name>"
    exit 0
fi

# ヘッダー
echo "=== 仕様一覧 ==="
echo ""
printf "%-30s | %-12s | %-12s | %-12s\n" "Feature" "Requirements" "Design" "Tasks"
printf "%-30s-+-%-12s-+-%-12s-+-%-12s\n" "------------------------------" "------------" "------------" "------------"

# 各仕様ディレクトリを処理
for spec_dir in "$SPECS_DIR"/*/; do
    if [ ! -d "$spec_dir" ]; then
        continue
    fi

    feature=$(basename "$spec_dir")

    # 各ファイルのステータスを取得
    get_status() {
        local file=$1
        if [ -f "$file" ]; then
            status=$(grep -m1 '^status:' "$file" 2>/dev/null | sed 's/status:[[:space:]]*//')
            if [ -n "$status" ]; then
                echo "$status"
            else
                echo "no-status"
            fi
        else
            echo "-"
        fi
    }

    req_status=$(get_status "${spec_dir}01-requirements.md")
    design_status=$(get_status "${spec_dir}02-design.md")
    tasks_status=$(get_status "${spec_dir}03-tasks.md")

    printf "%-30s | %-12s | %-12s | %-12s\n" "$feature" "$req_status" "$design_status" "$tasks_status"
done

echo ""
echo "Status: draft → in_progress → completed"
