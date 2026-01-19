#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"
PROJECT_FILTER=$1

ACTIVE_SPECS=0
COMPLETED_SPECS=0
EMPTY_SPECS=0

get_status() {
    local file=$1
    if [ -f "$file" ]; then
        grep -m1 "^> Status:" "$file" 2>/dev/null | sed 's/.*Status: //' || echo "unknown"
    else
        echo "missing"
    fi
}

count_tasks() {
    local file=$1
    if [ -f "$file" ]; then
        local total=$(grep -c "^\- \[ \]" "$file" 2>/dev/null || echo 0)
        local done=$(grep -c "^\- \[x\]" "$file" 2>/dev/null || echo 0)
        echo "$done/$((total + done))"
    else
        echo "0/0"
    fi
}

check_spec() {
    local spec_path=$1
    local spec_name=$(basename "$spec_path")

    local req_status=$(get_status "$spec_path/01-requirements.md")
    local design_status=$(get_status "$spec_path/02-design.md")
    local tasks_status=$(get_status "$spec_path/03-tasks.md")
    local task_count=$(count_tasks "$spec_path/03-tasks.md")

    echo "  specs/$spec_name:"

    # Requirements
    if [ "$req_status" = "completed" ]; then
        echo "    - 01-requirements: completed"
    elif [ "$req_status" = "draft" ]; then
        echo "    - 01-requirements: draft (作業中)"
    else
        echo "    - 01-requirements: $req_status"
    fi

    # Design
    if [ "$design_status" = "completed" ]; then
        echo "    - 02-design: completed"
    elif [ "$design_status" = "draft" ]; then
        echo "    - 02-design: draft"
    else
        echo "    - 02-design: $design_status"
    fi

    # Tasks
    if [ "$tasks_status" = "completed" ]; then
        echo "    - 03-tasks: completed ($task_count)"
        ((COMPLETED_SPECS++))
    elif [ "$tasks_status" = "draft" ]; then
        echo "    - 03-tasks: draft ($task_count)"
        ((ACTIVE_SPECS++))
    else
        echo "    - 03-tasks: $tasks_status"
    fi
}

check_worktree() {
    local worktree_path=$1
    local project_name=$(basename "$(dirname "$(dirname "$worktree_path")")")
    local worktree_name=$(basename "$worktree_path")

    local specs_dir="$worktree_path/docs/specs"

    echo ""
    echo "[$project_name/$worktree_name]"

    if [ ! -d "$specs_dir" ]; then
        echo "  (no specs)"
        return
    fi

    local spec_count=0
    for spec in "$specs_dir"/*/; do
        if [ -d "$spec" ]; then
            check_spec "$spec"
            ((spec_count++))
        fi
    done

    if [ $spec_count -eq 0 ]; then
        echo "  (no specs)"
        ((EMPTY_SPECS++))
    fi
}

check_project() {
    local project_path=$1

    if [ ! -d "$project_path/worktrees" ]; then
        return
    fi

    for worktree in "$project_path/worktrees"/*/; do
        if [ -d "$worktree" ]; then
            check_worktree "$worktree"
        fi
    done
}

echo "=== Workspace Status ==="

if [ -n "$PROJECT_FILTER" ]; then
    if [ -d "$WORKSPACE_ROOT/projects/$PROJECT_FILTER" ]; then
        check_project "$WORKSPACE_ROOT/projects/$PROJECT_FILTER"
    else
        echo "Error: Project '$PROJECT_FILTER' not found"
        exit 1
    fi
else
    if [ ! -d "$WORKSPACE_ROOT/projects" ]; then
        echo "No projects found"
        exit 0
    fi

    for project in "$WORKSPACE_ROOT/projects"/*/; do
        if [ -d "$project" ]; then
            check_project "$project"
        fi
    done
fi

echo ""
echo "=== Summary ==="
echo "Active specs: $ACTIVE_SPECS"
echo "Completed specs: $COMPLETED_SPECS"
echo "Empty worktrees: $EMPTY_SPECS"
