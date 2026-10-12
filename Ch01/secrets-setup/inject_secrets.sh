#!/bin/bash
# =============================================================================
# inject_secrets.sh — Load JSON secrets into Bitwarden Vault
# =============================================================================
# Loops through all *.json files in the secrets-setup/ directory and creates
# or updates matching items in your Bitwarden vault. Run this once during
# Chapter 1 setup to populate the vault with all secrets needed by the book.
#
# Usage:
#   cd Ch1/code/secrets-setup
#   chmod +x inject_secrets.sh
#   ./inject_secrets.sh
#
# Prerequisites:
#   - Bitwarden CLI installed: npm install -g @bitwarden/cli
#   - .env file present one level up (Ch1/code/.env) with:
#       BW_CLIENTID=your_client_id
#       BW_CLIENTSECRET=your_client_secret
#       BW_PASSWORD=your_master_password
#   - jq installed: brew install jq  /  apt install jq
#
# What it does:
#   1. Loads credentials from ../.env
#   2. Authenticates and unlocks the Bitwarden vault
#   3. For each *.json file in this directory:
#      - If the item already exists: update it
#      - If it does not exist: create it
#   4. Syncs the vault to the cloud and locks it
# =============================================================================

set -euo pipefail

# ── Colors ───────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ── Load environment variables ────────────────────────────────────────
ENV_FILE="../.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: .env file not found at $ENV_FILE${NC}"
    echo "Copy .env_example to .env and fill in your Bitwarden credentials:"
    echo "  cp ../env_example ../.env"
    exit 1
fi

set -o allexport
# shellcheck source=/dev/null
source "$ENV_FILE"
set +o allexport

# ── Verify required variables ─────────────────────────────────────────
for var in BW_CLIENTID BW_CLIENTSECRET BW_PASSWORD; do
    if [ -z "${!var:-}" ]; then
        echo -e "${RED}Error: $var is not set in $ENV_FILE${NC}"
        exit 1
    fi
done

# ── Authenticate and unlock vault ─────────────────────────────────────
echo -e "${YELLOW}Authenticating with Bitwarden...${NC}"

# Login with API key if not already logged in
if ! bw login --check &>/dev/null; then
    bw login --apikey
fi

echo -e "${YELLOW}Unlocking vault...${NC}"
BW_SESSION=$(bw unlock --passwordenv BW_PASSWORD --raw)
export BW_SESSION

if [ -z "$BW_SESSION" ]; then
    echo -e "${RED}Error: Failed to unlock Bitwarden vault. Check your BW_PASSWORD.${NC}"
    exit 1
fi

echo -e "${GREEN}Vault unlocked successfully.${NC}"
echo ""

# ── Process each JSON file ────────────────────────────────────────────
JSON_FILES=(*.json)
if [ ${#JSON_FILES[@]} -eq 0 ] || [ ! -f "${JSON_FILES[0]}" ]; then
    echo -e "${YELLOW}No JSON files found in $(pwd). Nothing to upload.${NC}"
    bw lock
    exit 0
fi

echo "Processing secret files..."
echo ""

for json_file in *.json; do
    echo "  Processing: $json_file"

    # Extract the item name from the JSON (the "name" field)
    item_name=$(jq -r '.name' "$json_file")

    if [ "$item_name" = "null" ] || [ -z "$item_name" ]; then
        echo -e "  ${YELLOW}  ⚠ Skipping $json_file: missing 'name' field${NC}"
        continue
    fi

    # Check whether the item already exists in the vault
    existing_item=$(bw get item "$item_name" \
        --session "$BW_SESSION" 2>/dev/null || true)

    if [ -n "$existing_item" ]; then
        echo -e "  ${YELLOW}  ⟳ '$item_name' exists — updating...${NC}"
        item_id=$(echo "$existing_item" | jq -r '.id')
        if jq '.' "$json_file" | bw encode | \
           bw edit item "$item_id" --session "$BW_SESSION" > /dev/null 2>&1; then
            echo -e "  ${GREEN}  ✓ '$item_name' updated${NC}"
        else
            echo -e "  ${RED}  ✗ '$item_name' update failed${NC}"
        fi
    else
        echo -e "  ${YELLOW}  + '$item_name' not found — creating...${NC}"
        if jq '.' "$json_file" | bw encode | \
           bw create item --session "$BW_SESSION" > /dev/null 2>&1; then
            echo -e "  ${GREEN}  ✓ '$item_name' created${NC}"
        else
            echo -e "  ${RED}  ✗ '$item_name' creation failed${NC}"
        fi
    fi
done

# ── Sync and lock ─────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Syncing vault to cloud...${NC}"
bw sync --session "$BW_SESSION"
echo -e "${YELLOW}Locking vault...${NC}"
bw lock
echo ""
echo -e "${GREEN}Done. Log in to bitwarden.com to verify your secrets are populated.${NC}"
