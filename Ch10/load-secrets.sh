#!/bin/bash
# =============================================================================
# Chapter 10: Load Secrets from Bitwarden
# =============================================================================
# Retrieves Backstage API credentials from the Bitwarden vault for
# publishing starter kit templates to the Backstage catalog.
#
# Usage:
#   source load-secrets.sh    # exports env vars into current shell
#
# Vault items expected (create these in Bitwarden):
#   "peh-backstage"      -> uri: http://localhost:7007
#   "peh-backstage"      -> password: <backstage-api-token>
#
# After running, the following environment variables are set:
#   BACKSTAGE_URL        - Backstage instance URL
#   BACKSTAGE_TOKEN      - Backstage API authentication token
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the shared Bitwarden helper
if [ -f "$SCRIPT_DIR/../../Ch01/scripts/bw-helper.sh" ]; then
    source "$SCRIPT_DIR/../../Ch01/scripts/bw-helper.sh"
else
    echo "Error: bw-helper.sh not found. Copy it from Ch01/scripts/"
    exit 1
fi

echo "Loading Chapter 10 secrets from Bitwarden..."
echo ""

bw_init

# Backstage credentials for template publishing
bw_export "BACKSTAGE_URL"   "peh-backstage" "uri"
bw_export "BACKSTAGE_TOKEN" "peh-backstage" "password"

# Default URL if not stored
if [ -z "${BACKSTAGE_URL:-}" ]; then
    export BACKSTAGE_URL="http://localhost:7007"
    echo "  ℹ BACKSTAGE_URL defaulting to http://localhost:7007"
fi

echo ""
echo "Chapter 10 secrets loaded. You can now run:"
echo "  python3 publish.py"
echo "  python3 validate-workflow.py"
