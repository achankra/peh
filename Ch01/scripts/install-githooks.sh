#!/bin/bash
# Install custom git hooks into the local repository
# This script copies pre-configured hooks from .git-hooks/ to .git/hooks/
# ensuring all developers use the same commit message validation rules.

set -euo pipefail

HOOKS_DIR=".git-hooks"
GIT_HOOKS_DIR=".git/hooks"

# Verify .git directory exists (repository must be initialized)
if [ ! -d ".git" ]; then
    echo "Error: Not a git repository. Please run this script from the repository root."
    exit 1
fi

# Verify custom hooks directory exists
if [ ! -d "$HOOKS_DIR" ]; then
    echo "Error: .git-hooks directory not found"
    exit 1
fi

# Create .git/hooks directory if it doesn't exist
mkdir -p "$GIT_HOOKS_DIR"

# Copy commit-msg hook to .git/hooks and make it executable
if [ -f "$HOOKS_DIR/commit-msg" ]; then
    cp "$HOOKS_DIR/commit-msg" "$GIT_HOOKS_DIR/commit-msg"
    chmod +x "$GIT_HOOKS_DIR/commit-msg"
    echo "Successfully installed commit-msg hook"
else
    echo "Warning: commit-msg hook not found in $HOOKS_DIR"
    exit 1
fi

echo "Git hooks installation complete"
echo "Commit messages will now be validated for conventional commits format"
exit 0
