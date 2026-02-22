#!/bin/bash
# =============================================================================
# Chapter 9: Load Secrets from Bitwarden
# =============================================================================
# Retrieves cloud provider credentials from the Bitwarden vault and creates
# the Kubernetes Secret that Crossplane providers need for authentication.
#
# Usage:
#   source load-secrets.sh           # export env vars only
#   ./load-secrets.sh --create-k8s   # also create the K8s secret
#
# Vault items expected (create these in Bitwarden):
#   "peh-aws"            -> custom field "access_key_id": <your-key>
#   "peh-aws"            -> custom field "secret_access_key": <your-secret>
#   "peh-aws"            -> custom field "region": us-east-1
#
# After running, the following environment variables are set:
#   AWS_ACCESS_KEY_ID        - AWS access key
#   AWS_SECRET_ACCESS_KEY    - AWS secret key
#   AWS_DEFAULT_REGION       - AWS region
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the shared Bitwarden helper
if [ -f "$SCRIPT_DIR/../../Ch1/code/scripts/bw-helper.sh" ]; then
    source "$SCRIPT_DIR/../../Ch1/code/scripts/bw-helper.sh"
else
    echo "Error: bw-helper.sh not found. Copy it from Ch1/code/scripts/"
    exit 1
fi

echo "Loading Chapter 9 secrets from Bitwarden..."
echo ""

bw_init

# AWS credentials for Crossplane providers
bw_export "AWS_ACCESS_KEY_ID"     "peh-aws" "access_key_id"
bw_export "AWS_SECRET_ACCESS_KEY" "peh-aws" "secret_access_key"
bw_export "AWS_DEFAULT_REGION"    "peh-aws" "region"

# Default region if not stored
if [ -z "${AWS_DEFAULT_REGION:-}" ]; then
    export AWS_DEFAULT_REGION="us-east-1"
    echo "  ℹ AWS_DEFAULT_REGION defaulting to us-east-1"
fi

# Optionally create the Kubernetes secret for Crossplane
if [ "${1:-}" = "--create-k8s" ]; then
    echo ""
    echo "Creating Kubernetes secret for Crossplane AWS provider..."

    kubectl create secret generic aws-credentials \
        --namespace crossplane-system \
        --from-literal=credentials="[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
region = ${AWS_DEFAULT_REGION}" \
        --dry-run=client -o yaml | kubectl apply -f -

    echo -e "${GREEN}  ✓ aws-credentials secret created in crossplane-system${NC}"
fi

echo ""
echo "Chapter 9 secrets loaded. You can now run:"
echo "  kubectl apply -f crossplane-providers.yaml"
echo "  kubectl apply -f xrd-postgresql.yaml"
echo ""
echo "To also create the Kubernetes secret:"
echo "  ./load-secrets.sh --create-k8s"
