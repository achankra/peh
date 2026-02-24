#!/bin/bash
# =============================================================================
# Chapter 3: Load Secrets for Keycloak
# =============================================================================
# Loads Keycloak credentials either from Bitwarden vault (if configured)
# or falls back to sensible defaults for local development.
#
# Usage:
#   source load-secrets.sh    # exports env vars into current shell
#
# Vault items expected (if using Bitwarden):
#   "peh-keycloak"       -> username: admin, password: <your-password>
#   "peh-keycloak"       -> uri: http://localhost:8180 (optional)
#
# After running, the following environment variables are set:
#   KEYCLOAK_ADMIN       - Keycloak admin username
#   KEYCLOAK_PASSWORD    - Keycloak admin password
#   KEYCLOAK_URL         - Keycloak server URL (port 8180, since Kind uses 8080)
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

_USE_BW=false

# Try to load Bitwarden helper if available
if [ -f "$SCRIPT_DIR/scripts/bw-helper.sh" ]; then
    source "$SCRIPT_DIR/scripts/bw-helper.sh"
    _USE_BW=true
elif [ -f "$SCRIPT_DIR/../Ch01/scripts/bw-helper.sh" ]; then
    source "$SCRIPT_DIR/../Ch01/scripts/bw-helper.sh"
    _USE_BW=true
fi

if [ "$_USE_BW" = true ] && command -v bw &>/dev/null; then
    echo "Loading Chapter 3 secrets from Bitwarden..."
    echo ""

    if bw_init 2>/dev/null; then
        bw_export "KEYCLOAK_ADMIN"    "peh-keycloak" "username"
        bw_export "KEYCLOAK_PASSWORD" "peh-keycloak" "password"
        bw_export "KEYCLOAK_URL"      "peh-keycloak" "uri"
    else
        echo "  ⚠ Bitwarden vault not available, using defaults"
    fi
else
    echo "Bitwarden CLI not configured — using default credentials for local development."
    echo ""
fi

# Apply defaults for anything not set by Bitwarden
if [ -z "${KEYCLOAK_ADMIN:-}" ]; then
    export KEYCLOAK_ADMIN="admin"
    echo "  ✓ KEYCLOAK_ADMIN=admin (default)"
fi

if [ -z "${KEYCLOAK_PASSWORD:-}" ]; then
    export KEYCLOAK_PASSWORD="admin"
    echo "  ✓ KEYCLOAK_PASSWORD=admin (default)"
fi

if [ -z "${KEYCLOAK_URL:-}" ]; then
    export KEYCLOAK_URL="http://localhost:8180"
    echo "  ✓ KEYCLOAK_URL=http://localhost:8180 (port 8080 is used by Kind)"
fi

echo ""
echo "Chapter 3 secrets loaded. You can now run:"
echo "  python3 keycloak-realm-config.py"
echo "  kubectl apply -f gatekeeper-policies.yaml"
