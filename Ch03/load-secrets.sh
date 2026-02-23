#!/bin/bash
# =============================================================================
# Chapter 3: Load Secrets from Bitwarden
# =============================================================================
# Retrieves Keycloak admin credentials and other security-related secrets
# from the Bitwarden vault so they don't need to be hardcoded or manually
# exported as environment variables.
#
# Usage:
#   source load-secrets.sh    # exports env vars into current shell
#   ./load-secrets.sh         # prints export commands (for eval)
#
# Vault items expected (create these in Bitwarden):
#   "peh-keycloak"       -> username: admin, password: <your-password>
#   "peh-keycloak"       -> uri: http://localhost:8080 (optional)
#
# After running, the following environment variables are set:
#   KEYCLOAK_ADMIN       - Keycloak admin username
#   KEYCLOAK_PASSWORD    - Keycloak admin password
#   KEYCLOAK_URL         - Keycloak server URL
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the shared Bitwarden helper
# Try local copy first, then fall back to Ch1
if [ -f "$SCRIPT_DIR/scripts/bw-helper.sh" ]; then
    source "$SCRIPT_DIR/scripts/bw-helper.sh"
elif [ -f "$SCRIPT_DIR/../../Ch01/scripts/bw-helper.sh" ]; then
    source "$SCRIPT_DIR/../../Ch01/scripts/bw-helper.sh"
else
    echo "Error: bw-helper.sh not found. Copy it from Ch01/scripts/"
    exit 1
fi

echo "Loading Chapter 3 secrets from Bitwarden..."
echo ""

bw_init

# Keycloak credentials
bw_export "KEYCLOAK_ADMIN"    "peh-keycloak" "username"
bw_export "KEYCLOAK_PASSWORD" "peh-keycloak" "password"
bw_export "KEYCLOAK_URL"      "peh-keycloak" "uri"

# Default URL if not stored in vault
if [ -z "${KEYCLOAK_URL:-}" ]; then
    export KEYCLOAK_URL="http://localhost:8080"
    echo "  ℹ KEYCLOAK_URL defaulting to http://localhost:8080"
fi

echo ""
echo "Chapter 3 secrets loaded. You can now run:"
echo "  python3 keycloak-realm-config.py"
echo "  kubectl apply -f gatekeeper-policies.yaml"
