#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"
PROJECT_FILTER=$1

ERRORS=0
WARNINGS=0

check_worktree() {
    local worktree_path=$1
    local worktree_name=$(basename "$worktree_path")
    local project_name=$(basename "$(dirname "$(dirname "$worktree_path")")")

    # 必須ディレクトリ確認
    for dir in .claude docs repo; do
        if [ ! -d "$worktree_path/$dir" ] && [ ! -L "$worktree_path/$dir" ]; then
            echo "  ERROR: Missing directory '$dir' in $worktree_name"
            ((ERRORS++))
        fi
    done

    # CLAUDE.md確認
    if [ ! -f "$worktree_path/CLAUDE.md" ] && [ ! -L "$worktree_path/CLAUDE.md" ]; then
        echo "  ERROR: Missing CLAUDE.md in $worktree_name"
        ((ERRORS++))
    fi

    # repo内のgit確認（.gitはファイルであるべき、ディレクトリではない）
    if [ -d "$worktree_path/repo" ]; then
        if [ -f "$worktree_path/repo/.git" ]; then
            # 正常: worktreeの.gitはファイル
            if ! grep -q "^gitdir:" "$worktree_path/repo/.git" 2>/dev/null; then
                echo "  ERROR: repo/.git is not a valid gitdir file in $worktree_name"
                ((ERRORS++))
            fi
        elif [ -d "$worktree_path/repo/.git" ]; then
            echo "  WARNING: repo/.git is a directory (should be gitdir file) in $worktree_name"
            ((WARNINGS++))
        else
            echo "  WARNING: No git in repo/ of $worktree_name"
            ((WARNINGS++))
        fi
    fi

    # .mcp.json確認
    if [ -f "$worktree_path/.mcp.json" ]; then
        if ! python3 -c "import json; json.load(open('$worktree_path/.mcp.json'))" 2>/dev/null; then
            echo "  ERROR: Invalid JSON in .mcp.json of $worktree_name"
            ((ERRORS++))
        fi
    else
        echo "  WARNING: Missing .mcp.json in $worktree_name"
        ((WARNINGS++))
    fi

    # .claude/rules/ 確認
    if [ ! -d "$worktree_path/.claude/rules" ]; then
        echo "  WARNING: Missing .claude/rules/ in $worktree_name"
        ((WARNINGS++))
    elif [ -z "$(ls -A "$worktree_path/.claude/rules" 2>/dev/null)" ]; then
        echo "  WARNING: .claude/rules/ is empty in $worktree_name"
        ((WARNINGS++))
    fi

    # 余計なファイル/ディレクトリ確認（worktree直下）
    local allowed_items="repo .claude docs CLAUDE.md .mcp.json .DS_Store"
    for item in "$worktree_path"/*; do
        [ -e "$item" ] || continue
        local item_name=$(basename "$item")
        if ! echo "$allowed_items" | grep -qw "$item_name"; then
            echo "  WARNING: Unexpected item '$item_name' in $worktree_name"
            ((WARNINGS++))
        fi
    done
    for item in "$worktree_path"/.*; do
        [ -e "$item" ] || continue
        local item_name=$(basename "$item")
        [[ "$item_name" == "." || "$item_name" == ".." ]] && continue
        if ! echo "$allowed_items" | grep -qw "$item_name"; then
            echo "  WARNING: Unexpected item '$item_name' in $worktree_name"
            ((WARNINGS++))
        fi
    done
}

check_project() {
    local project_path=$1
    local project_name=$(basename "$project_path")

    echo "Checking project: $project_name"

    # .bare ディレクトリ確認
    if [ ! -d "$project_path/.bare" ]; then
        echo "  ERROR: Missing '.bare' directory (not using bare repo structure)"
        ((ERRORS++))
    fi

    # worktrees ディレクトリ確認
    if [ ! -d "$project_path/worktrees" ]; then
        echo "  ERROR: Missing 'worktrees' directory"
        ((ERRORS++))
        return
    fi

    # 余計なファイル/ディレクトリ確認（プロジェクト直下）
    local allowed_project_items=".bare worktrees .DS_Store .claude"
    for item in "$project_path"/*; do
        [ -e "$item" ] || continue
        local item_name=$(basename "$item")
        if ! echo "$allowed_project_items" | grep -qw "$item_name"; then
            echo "  WARNING: Unexpected item '$item_name' in project root"
            ((WARNINGS++))
        fi
    done
    for item in "$project_path"/.*; do
        [ -e "$item" ] || continue
        local item_name=$(basename "$item")
        [[ "$item_name" == "." || "$item_name" == ".." ]] && continue
        if ! echo "$allowed_project_items" | grep -qw "$item_name"; then
            echo "  WARNING: Unexpected item '$item_name' in project root"
            ((WARNINGS++))
        fi
    done

    # 各ワークツリーを確認
    local worktree_count=0
    for worktree in "$project_path/worktrees"/*/; do
        if [ -d "$worktree" ]; then
            check_worktree "$worktree"
            ((worktree_count++))
        fi
    done

    if [ $worktree_count -eq 0 ]; then
        echo "  WARNING: No worktrees found"
        ((WARNINGS++))
    else
        echo "  Found $worktree_count worktree(s)"
    fi
}

echo "=== Workspace Structure Validation ==="
echo ""

# プロジェクト確認
if [ -n "$PROJECT_FILTER" ]; then
    # 特定プロジェクトのみ
    if [ -d "$WORKSPACE_ROOT/projects/$PROJECT_FILTER" ]; then
        check_project "$WORKSPACE_ROOT/projects/$PROJECT_FILTER"
    else
        echo "ERROR: Project '$PROJECT_FILTER' not found"
        exit 1
    fi
else
    # 全プロジェクト
    if [ ! -d "$WORKSPACE_ROOT/projects" ]; then
        echo "No projects directory found"
        exit 0
    fi

    for project in "$WORKSPACE_ROOT/projects"/*/; do
        if [ -d "$project" ]; then
            check_project "$project"
            echo ""
        fi
    done
fi

echo "=== Summary ==="
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"

if [ $ERRORS -gt 0 ]; then
    exit 1
fi
exit 0
