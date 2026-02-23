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
if [ -f "$SCRIPT_DIR/../../Ch01/scripts/bw-helper.sh" ]; then
    source "$SCRIPT_DIR/../../Ch01/scripts/bw-helper.sh"
else
    echo "Error: bw-helper.sh not found. Copy it from Ch01/scripts/"
    exit 1
fi

echo "Loading Chapter 7 secrets from Bitwarden..."
echo ""

bw_init

# GitHub credentials for onboarding API and teamService.js
bw_export "GITHUB_TOKEN" "peh-github" "password"
bw_export "GITHUB_ORG"   "peh-github" "org"

echo ""
echo "Chapter 7 secrets loaded. You can now run:"
echo "  python3 onboarding-api.py"
echo "  node services/teamService.js"
