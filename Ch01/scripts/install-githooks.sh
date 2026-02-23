#!/bin/bash
# Install custom git hooks into the local repository
# This script copies pre-configured hooks from .git-hooks/ to .git/hooks/
# ensuring all developers use the same commit message validation rules.
#
# Can be run from anywhere inside the repository — it will auto-detect
# both the git root and the .git-hooks source directory.

set -euo pipefail

# ── Locate the git repository root ──────────────────────────────────
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
    echo "Error: Not inside a git repository."
    echo "Run 'git init' first, or cd into your repo."
    exit 1
}

# ── Locate the .git-hooks source directory ──────────────────────────
# Look in: (1) current dir, (2) script's own dir/../.git-hooks, (3) Ch1/code/.git-hooks
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODE_DIR="$(dirname "$SCRIPT_DIR")"   # scripts/ -> Ch1/code/

if [ -d ".git-hooks" ]; then
    HOOKS_SRC="$(pwd)/.git-hooks"
elif [ -d "$CODE_DIR/.git-hooks" ]; then
    HOOKS_SRC="$CODE_DIR/.git-hooks"
else
    echo "Error: Could not find .git-hooks directory."
    echo "Expected at: $CODE_DIR/.git-hooks"
    exit 1
fi

GIT_HOOKS_DIR="$GIT_ROOT/.git/hooks"

# ── Install hooks ───────────────────────────────────────────────────
mkdir -p "$GIT_HOOKS_DIR"

if [ -f "$HOOKS_SRC/commit-msg" ]; then
    cp "$HOOKS_SRC/commit-msg" "$GIT_HOOKS_DIR/commit-msg"
    chmod +x "$GIT_HOOKS_DIR/commit-msg"
    echo "Successfully installed commit-msg hook"
else
    echo "Warning: commit-msg hook not found in $HOOKS_SRC"
    exit 1
fi

echo "Git hooks installation complete"
echo "  Source:  $HOOKS_SRC/commit-msg"
echo "  Target:  $GIT_HOOKS_DIR/commit-msg"
echo "Commit messages will now be validated for conventional commits format"
exit 0
