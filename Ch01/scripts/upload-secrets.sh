#!/bin/bash
# Upload secrets to Bitwarden vault using CLI
# This script automates the process of securely storing infrastructure secrets
# in Bitwarden for use by CI/CD pipelines and deployment tools.

set -euo pipefail

# ── Load environment variables from .env file ───────────────────────
# Expected variables: BW_CLIENTID, BW_CLIENTSECRET, BW_PASSWORD
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

if [ -f "$ENV_FILE" ]; then
    set -a          # auto-export every variable that gets set
    source "$ENV_FILE"
    set +a
elif [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "Error: .env file not found."
    echo "Create it from .env_example:  cp .env_example .env"
    exit 1
fi

# ── Verify required environment variables ────────────────────────────
if [ -z "${BW_CLIENTID:-}" ] || [ -z "${BW_CLIENTSECRET:-}" ] || [ -z "${BW_PASSWORD:-}" ]; then
    echo "Error: Required Bitwarden credentials not set in .env"
    echo "Need: BW_CLIENTID, BW_CLIENTSECRET, BW_PASSWORD"
    exit 1
fi

# ── Authenticate ─────────────────────────────────────────────────────
echo "Logging into Bitwarden using API credentials..."
bw login --apikey 2>/dev/null || echo "(Already logged in)"

echo "Unlocking Bitwarden vault..."
export BW_SESSION=$(bw unlock --passwordenv BW_PASSWORD --raw)

if [ -z "$BW_SESSION" ]; then
    echo "Error: Failed to unlock vault. Check your BW_PASSWORD."
    exit 1
fi

# ── Create the GitHub Secrets item ───────────────────────────────────
echo "Creating GitHub Secrets item in Bitwarden..."

# Locate the JSON template
if [ -f "$SCRIPT_DIR/../secrets-setup/github_secrets.json" ]; then
    JSON_FILE="$SCRIPT_DIR/../secrets-setup/github_secrets.json"
elif [ -f "secrets-setup/github_secrets.json" ]; then
    JSON_FILE="secrets-setup/github_secrets.json"
else
    echo "Error: secrets-setup/github_secrets.json not found"
    exit 1
fi

# bw create item expects base64-encoded JSON
ENCODED=$(cat "$JSON_FILE" | bw encode)
bw create item "$ENCODED"

# ── Sync and lock ────────────────────────────────────────────────────
echo "Syncing Bitwarden vault..."
bw sync

echo "Locking Bitwarden vault..."
bw lock

echo ""
echo "Successfully uploaded secrets to Bitwarden"
exit 0
