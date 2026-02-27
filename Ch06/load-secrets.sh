#!/bin/bash
# =============================================================================
# Chapter 6: Load Secrets from Bitwarden
# =============================================================================
# Retrieves GitHub token for Backstage Developer Portal exercises.
#
# Usage:
#   source load-secrets.sh    # exports env vars into current shell
#
# Vault items expected (create these in Bitwarden):
#   "peh-github"         -> password: <your-github-pat>
#
# After running, the following environment variables are set:
#   GITHUB_TOKEN         - GitHub Personal Access Token (for Backstage GitHub integration)
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the shared Bitwarden helper
# Try runtime layout first (peh repo: ChXX/scripts/), then Manuscript layout (ChX/code/scripts/)
BW_HELPER=""
for candidate in \
    "$SCRIPT_DIR/../Ch01/scripts/bw-helper.sh" \
    "$SCRIPT_DIR/../../Ch1/code/scripts/bw-helper.sh"; do
    if [ -f "$candidate" ]; then
        BW_HELPER="$candidate"
        break
    fi
done

if [ -n "$BW_HELPER" ]; then
    source "$BW_HELPER"
else
    echo "Error: bw-helper.sh not found."
    echo "Looked in:"
    echo "  $SCRIPT_DIR/../Ch01/scripts/bw-helper.sh"
    echo "  $SCRIPT_DIR/../../Ch1/code/scripts/bw-helper.sh"
    return 1 2>/dev/null || exit 1
fi

echo "Loading Chapter 6 secrets from Bitwarden..."
echo ""

# Skip bw_init if the vault is already unlocked (BW_SESSION set externally)
if [ -n "${BW_SESSION:-}" ]; then
    echo "Bitwarden session already active, skipping unlock."
else
    bw_init
fi

# GitHub credentials for Backstage GitHub integration
bw_export "GITHUB_TOKEN" "peh-github" "password"

echo ""
echo "Chapter 6 secrets loaded. You can now run:"
echo "  kubectl create secret generic backstage-secrets --from-literal=GITHUB_TOKEN=\$GITHUB_TOKEN -n backstage"
