#!/bin/bash
# =============================================================================
# Chapter 7: Load Secrets from Bitwarden
# =============================================================================
# Retrieves GitHub token and onboarding API configuration from the Bitwarden
# vault for the self-service team onboarding exercises.
#
# Usage:
#   source load-secrets.sh    # exports env vars into current shell
#
# Vault items expected (create these in Bitwarden):
#   "peh-github"         -> password: <your-github-pat>
#   "peh-github"         -> custom field "org": <your-org-name>
#
# After running, the following environment variables are set:
#   GITHUB_TOKEN         - GitHub Personal Access Token (Fine-Grained)
#   GITHUB_ORG           - GitHub Organization name
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

echo "Loading Chapter 7 secrets from Bitwarden..."
echo ""

# Skip bw_init if the vault is already unlocked (BW_SESSION set externally)
if [ -n "${BW_SESSION:-}" ]; then
    echo "Bitwarden session already active, skipping unlock."
else
    bw_init
fi

# GitHub credentials for onboarding API and teamService.js
bw_export "GITHUB_TOKEN" "peh-github" "password"
bw_export "GITHUB_ORG"   "peh-github" "org"

echo ""
echo "Chapter 7 secrets loaded. You can now run:"
echo "  python3 onboarding-api.py"
echo "  node services/teamService.js"
