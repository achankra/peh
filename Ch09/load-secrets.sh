#!/bin/bash
# =============================================================================
# Chapter 9: Load Secrets from Bitwarden
# =============================================================================
# Retrieves credentials from the Bitwarden vault and creates
# the Kubernetes Secrets that Crossplane providers need for authentication.
#
# Usage:
#   source load-secrets.sh           # export env vars only
#   ./load-secrets.sh --create-k8s   # also create the K8s secret
#
# Vault items expected (create these in Bitwarden):
#   "peh-db"             -> custom field "postgres_password": <your-db-pass>
#
# After running, the following environment variables are set:
#   POSTGRES_PASSWORD        - PostgreSQL admin password for Crossplane-managed DBs
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

echo "Loading Chapter 9 secrets from Bitwarden..."
echo ""

# Skip bw_init if the vault is already unlocked (BW_SESSION set externally)
if [ -n "${BW_SESSION:-}" ]; then
    echo "Bitwarden session already active, skipping unlock."
else
    bw_init
fi

# PostgreSQL password for Crossplane-managed databases
bw_export "POSTGRES_PASSWORD" "peh-db" "postgres_password"

# Default password if not stored (for local Kind development only)
if [ -z "${POSTGRES_PASSWORD:-}" ]; then
    export POSTGRES_PASSWORD="platformdev123"
    echo "  ℹ POSTGRES_PASSWORD defaulting to local dev password"
fi

# Optionally create the Kubernetes secret for Crossplane
if [ "${1:-}" = "--create-k8s" ]; then
    echo ""
    echo "Creating Kubernetes secret for Crossplane provider..."

    kubectl create namespace crossplane-system --dry-run=client -o yaml | kubectl apply -f -

    kubectl create secret generic db-credentials \
        --namespace crossplane-system \
        --from-literal=password="${POSTGRES_PASSWORD}" \
        --dry-run=client -o yaml | kubectl apply -f -

    echo -e "${GREEN}  ✓ db-credentials secret created in crossplane-system${NC}"
fi

echo ""
echo "Chapter 9 secrets loaded. You can now run:"
echo "  kubectl apply -f crossplane-providers.yaml"
echo "  kubectl apply -f xrd-postgresql.yaml"
echo ""
echo "To also create the Kubernetes secret:"
echo "  ./load-secrets.sh --create-k8s"
