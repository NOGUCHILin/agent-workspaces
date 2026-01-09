#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PROJECT_FILTER=$1

ERRORS=0
WARNINGS=0

check_worktree() {
    local worktree_path=$1
    local worktree_name=$(basename "$worktree_path")
    local project_name=$(basename "$(dirname "$(dirname "$worktree_path")")")

    # 必須ディレクトリ確認
    for dir in .claude docs repo; do
        if [ ! -d "$worktree_path/$dir" ]; then
            echo "  ERROR: Missing directory '$dir' in $worktree_name"
            ((ERRORS++))
        fi
    done

    # CLAUDE.md確認
    if [ ! -f "$worktree_path/CLAUDE.md" ]; then
        echo "  ERROR: Missing CLAUDE.md in $worktree_name"
        ((ERRORS++))
    fi

    # repo内のgit確認
    if [ -d "$worktree_path/repo" ]; then
        if [ ! -d "$worktree_path/repo/.git" ] && [ ! -f "$worktree_path/repo/.git" ]; then
            echo "  WARNING: No git in repo/ of $worktree_name"
            ((WARNINGS++))
        fi
    fi
}

check_project() {
    local project_path=$1
    local project_name=$(basename "$project_path")

    echo "Checking project: $project_name"

    # worktrees ディレクトリ確認
    if [ ! -d "$project_path/worktrees" ]; then
        echo "  ERROR: Missing 'worktrees' directory"
        ((ERRORS++))
        return
    fi

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
