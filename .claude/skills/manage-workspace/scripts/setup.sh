#!/bin/bash
set -e

PROJECT=$1
BRANCH=$2
REPO_URL=$3
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

# 引数チェック
if [ -z "$PROJECT" ] || [ -z "$BRANCH" ]; then
    echo "Usage: setup.sh <project-name> <branch-name> [repo-url]"
    echo ""
    echo "Examples:"
    echo "  # 新規プロジェクト（.bare構造で作成）"
    echo "  setup.sh myproject master https://github.com/user/myproject.git"
    echo ""
    echo "  # 既存プロジェクトに worktree 追加"
    echo "  setup.sh myproject feature-x"
    exit 1
fi

PROJECT_DIR="$WORKSPACE_ROOT/projects/$PROJECT"
BARE_DIR="$PROJECT_DIR/.bare"
WORKTREE_DIR="$PROJECT_DIR/worktrees/$BRANCH"

# 既存ワークツリー確認
if [ -d "$WORKTREE_DIR" ]; then
    echo "Error: Worktree '$BRANCH' already exists in project '$PROJECT'"
    exit 1
fi

# テンプレートディレクトリ
TEMPLATE_DIR="$SCRIPT_DIR/../templates"
SHARED_DIR="$WORKSPACE_ROOT/_shared"

# ディレクトリ作成
echo "Creating worktree structure..."
mkdir -p "$WORKTREE_DIR"/{.claude,docs/specs,docs/_templates}

# プロジェクト共通設定ディレクトリ作成（初回のみ）
PROJECT_CLAUDE_DIR="$PROJECT_DIR/.claude"
if [ ! -d "$PROJECT_CLAUDE_DIR/rules" ]; then
    echo "Creating shared settings from _shared/..."
    mkdir -p "$PROJECT_CLAUDE_DIR"
    # _shared/からコピー（project単位でカスタマイズ可能）
    cp -r "$SHARED_DIR/rules" "$PROJECT_CLAUDE_DIR/" 2>/dev/null || true
    cp -r "$SHARED_DIR/skills" "$PROJECT_CLAUDE_DIR/" 2>/dev/null || true
fi

# worktree → project へのシンボリックリンク作成
# worktree/.claude/ から project/.claude/ へ: ../../.claude/
ln -sf "../../.claude/rules" "$WORKTREE_DIR/.claude/rules"
ln -sf "../../.claude/skills" "$WORKTREE_DIR/.claude/skills"

# CLAUDE.md作成
sed -e "s/{{PROJECT}}/$PROJECT/g" -e "s/{{BRANCH}}/$BRANCH/g" \
    "$TEMPLATE_DIR/CLAUDE.md" > "$WORKTREE_DIR/CLAUDE.md"

# settings.jsonコピー
cp "$TEMPLATE_DIR/settings.json" "$WORKTREE_DIR/.claude/settings.json"

# .mcp.json作成（変数置換）
sed -e "s|{{HOME}}|$HOME|g" -e "s/{{BRANCH}}/$BRANCH/g" \
    "$TEMPLATE_DIR/.mcp.json" > "$WORKTREE_DIR/.mcp.json"

# テンプレートコピー（specs用）
cp "$TEMPLATE_DIR/01-requirements.md" "$WORKTREE_DIR/docs/_templates/"
cp "$TEMPLATE_DIR/02-design.md" "$WORKTREE_DIR/docs/_templates/"
cp "$TEMPLATE_DIR/03-tasks.md" "$WORKTREE_DIR/docs/_templates/"
mkdir -p "$WORKTREE_DIR/docs/_templates/research"
cp "$TEMPLATE_DIR/research/_template.md" "$WORKTREE_DIR/docs/_templates/research/"

echo "Created templates and rules"

# Git操作
if [ ! -d "$BARE_DIR" ]; then
    # .bareがない → 新規プロジェクト
    if [ -z "$REPO_URL" ]; then
        echo ""
        echo "Error: This is a new project '$PROJECT'."
        echo "Please provide the repository URL:"
        echo ""
        echo "  setup.sh $PROJECT $BRANCH <repo-url>"
        echo ""
        # 作成したディレクトリを削除
        rm -rf "$WORKTREE_DIR"
        exit 1
    fi

    echo "Creating .bare repository..."
    mkdir -p "$PROJECT_DIR"
    git clone --bare "$REPO_URL" "$BARE_DIR"

    # bare repoの設定を調整
    cd "$BARE_DIR"
    git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
    git fetch origin

    echo "Creating first worktree..."
    mkdir -p "$WORKTREE_DIR/repo"

    # worktree追加
    if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
        git worktree add "$WORKTREE_DIR/repo" "$BRANCH"
    elif git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
        git worktree add "$WORKTREE_DIR/repo" "$BRANCH"
    else
        # デフォルトブランチを取得
        DEFAULT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "main")
        git worktree add "$WORKTREE_DIR/repo" "$DEFAULT_BRANCH"
        echo "Note: Branch '$BRANCH' not found, using '$DEFAULT_BRANCH'"
    fi
else
    # .bareがある → worktree追加
    echo "Adding worktree from .bare..."
    cd "$BARE_DIR"

    # リモートから最新情報取得
    git fetch --all 2>/dev/null || true

    mkdir -p "$WORKTREE_DIR/repo"

    # worktree追加
    if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
        git worktree add "$WORKTREE_DIR/repo" "$BRANCH"
        echo "Attached to existing local branch: $BRANCH"
    elif git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
        git worktree add "$WORKTREE_DIR/repo" "$BRANCH"
        echo "Attached to remote branch: origin/$BRANCH"
    else
        git worktree add -b "$BRANCH" "$WORKTREE_DIR/repo"
        echo "Created new branch: $BRANCH"
    fi
fi

# 構造検証
echo ""
echo "Validating structure..."
"$SCRIPT_DIR/validate.sh" "$PROJECT"

echo ""
echo "Done! Created: $WORKTREE_DIR"
echo ""
echo "Next: cd $WORKTREE_DIR"
