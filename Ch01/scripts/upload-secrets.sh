#!/bin/bash
# Upload secrets to Bitwarden vault using CLI
# This script automates the process of securely storing infrastructure secrets
# in Bitwarden for use by CI/CD pipelines and deployment tools.

set -euo pipefail

# Load environment variables from .env file
# Expected variables: BW_CLIENTID, BW_CLIENTSECRET, BW_PASSWORD
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found. Please create it from .env_example"
    exit 1
fi

# Verify required environment variables are set
if [ -z "${BW_CLIENTID:-}" ] || [ -z "${BW_CLIENTSECRET:-}" ] || [ -z "${BW_PASSWORD:-}" ]; then
    echo "Error: Required Bitwarden credentials not set in .env"
    exit 1
fi

echo "Logging into Bitwarden using API credentials..."
# Authenticate with Bitwarden using client ID and secret
bw login --apikey

echo "Unlocking Bitwarden vault..."
# Unlock the vault using the master password
# This creates a session token for subsequent commands
export BW_SESSION=$(bw unlock --passwordenv BW_PASSWORD --raw)

echo "Creating GitHub Secrets item in Bitwarden..."
# Read the JSON file, base64 encode it, and create a new item in Bitwarden
# This securely stores the secrets for retrieval by CI/CD pipelines
SECRETS_JSON=$(cat secrets-setup/github_secrets.json)
bw create item "$SECRETS_JSON"

echo "Syncing Bitwarden vault..."
# Synchronize local Bitwarden cache with the server
bw sync

echo "Locking Bitwarden vault..."
# Lock the vault to invalidate the session token
bw lock

echo "Successfully uploaded secrets to Bitwarden"
exit 0
