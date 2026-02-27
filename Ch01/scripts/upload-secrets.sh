#!/bin/bash
# =============================================================================
# Upload All Book Secrets to Bitwarden Vault
# =============================================================================
# Creates all the Bitwarden vault items needed across the book's chapters.
# Run this ONCE during Chapter 1 setup. Every subsequent chapter's
# load-secrets.sh will pull from these items automatically.
#
# Usage:
#   export BW_SESSION=$(bw unlock --raw)   # unlock first
#   bash scripts/upload-secrets.sh          # then run this
#
# What gets created:
#   peh-github     -> GitHub PAT (used in Ch6, Ch7, Ch8)
#   peh-keycloak   -> Keycloak admin creds (used in Ch3)
#   peh-db         -> PostgreSQL password (used in Ch9)
#   peh-backstage  -> Backstage API token (used in Ch10)
#   peh-openai     -> OpenAI API key (used in Ch14, optional)
# =============================================================================

set -euo pipefail

# ── Colors ───────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ── Check BW_SESSION ─────────────────────────────────────────────────
if [ -z "${BW_SESSION:-}" ]; then
    echo -e "${RED}Error: BW_SESSION is not set.${NC}"
    echo ""
    echo "Unlock your vault first:"
    echo "  export BW_SESSION=\$(bw unlock --raw)"
    echo ""
    echo "Then re-run this script:"
    echo "  bash scripts/upload-secrets.sh"
    exit 1
fi

# ── Helper: create or update a vault item ────────────────────────────
# Uses type 2 (Secure Note) to avoid the Login type's uris bug.
# Stores values as custom fields, which bw_export() reads via bw_get().
create_item() {
    local name="$1"
    shift
    # remaining args are field_name=field_value pairs

    # Check if item already exists
    if bw get item "$name" --session "$BW_SESSION" &>/dev/null; then
        echo -e "${YELLOW}  ⟳ $name already exists — skipping (delete it first to recreate)${NC}"
        return 0
    fi

    # Build fields JSON array
    local fields="["
    local first=true
    for pair in "$@"; do
        local fname="${pair%%=*}"
        local fvalue="${pair#*=}"
        if [ "$first" = true ]; then
            first=false
        else
            fields+=","
        fi
        fields+="{\"name\":\"$fname\",\"value\":\"$fvalue\",\"type\":0}"
    done
    fields+="]"

    # type 2 = Secure Note (avoids the Login uris bug in bw CLI)
    local json="{\"type\":2,\"secureNote\":{\"type\":0},\"name\":\"$name\",\"notes\":\"\",\"fields\":$fields}"

    local encoded
    encoded=$(echo "$json" | bw encode)
    if bw create item "$encoded" --session "$BW_SESSION" > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ $name created${NC}"
    else
        echo -e "${RED}  ✗ $name failed to create${NC}"
        return 1
    fi
}

# ── Collect values from user ─────────────────────────────────────────
echo ""
echo "=========================================="
echo " Bitwarden Vault Setup for PEH Book"
echo "=========================================="
echo ""
echo "This script creates all the vault items needed across the book."
echo "Press Enter to accept the [default] value shown in brackets."
echo ""

# GitHub PAT
echo -e "${YELLOW}── GitHub (used in Ch6, Ch7, Ch8) ──${NC}"
read -rp "GitHub Personal Access Token (ghp_...): " GITHUB_TOKEN_INPUT
read -rp "GitHub Org or Username [platformetrics]: " GITHUB_ORG_INPUT
GITHUB_ORG_INPUT="${GITHUB_ORG_INPUT:-platformetrics}"

# Keycloak
echo ""
echo -e "${YELLOW}── Keycloak (used in Ch3) ──${NC}"
read -rp "Keycloak admin username [admin]: " KC_USER
KC_USER="${KC_USER:-admin}"
read -rp "Keycloak admin password [admin]: " KC_PASS
KC_PASS="${KC_PASS:-admin}"
read -rp "Keycloak URL [http://localhost:8180]: " KC_URL
KC_URL="${KC_URL:-http://localhost:8180}"

# PostgreSQL
echo ""
echo -e "${YELLOW}── PostgreSQL (used in Ch9) ──${NC}"
read -rp "PostgreSQL password [platformdev123]: " PG_PASS
PG_PASS="${PG_PASS:-platformdev123}"

# Backstage
echo ""
echo -e "${YELLOW}── Backstage (used in Ch10) ──${NC}"
read -rp "Backstage URL [http://localhost:7007]: " BS_URL
BS_URL="${BS_URL:-http://localhost:7007}"
read -rp "Backstage API token (or press Enter to skip): " BS_TOKEN

# OpenAI (optional)
echo ""
echo -e "${YELLOW}── OpenAI (used in Ch14, optional) ──${NC}"
read -rp "OpenAI API key (sk-... or press Enter to skip): " OPENAI_KEY

# ── Create vault items ───────────────────────────────────────────────
echo ""
echo "Creating vault items..."
echo ""

# peh-github
if [ -n "$GITHUB_TOKEN_INPUT" ]; then
    create_item "peh-github" "password=$GITHUB_TOKEN_INPUT" "org=$GITHUB_ORG_INPUT"
else
    echo -e "${YELLOW}  ⏭ peh-github skipped (no token provided)${NC}"
fi

# peh-keycloak
create_item "peh-keycloak" "username=$KC_USER" "password=$KC_PASS" "uri=$KC_URL"

# peh-db
create_item "peh-db" "postgres_password=$PG_PASS"

# peh-backstage
if [ -n "$BS_TOKEN" ]; then
    create_item "peh-backstage" "uri=$BS_URL" "password=$BS_TOKEN"
else
    create_item "peh-backstage" "uri=$BS_URL"
    echo -e "${YELLOW}    (no API token yet — update later when Backstage is running)${NC}"
fi

# peh-openai
if [ -n "$OPENAI_KEY" ]; then
    create_item "peh-openai" "password=$OPENAI_KEY"
else
    echo -e "${YELLOW}  ⏭ peh-openai skipped (no key provided)${NC}"
fi

# ── Sync ─────────────────────────────────────────────────────────────
echo ""
bw sync --session "$BW_SESSION" > /dev/null 2>&1
echo -e "${GREEN}Vault synced.${NC}"

echo ""
echo "=========================================="
echo " Done! Vault items are ready."
echo "=========================================="
echo ""
echo "Each chapter's load-secrets.sh will now pull"
echo "credentials automatically. Usage:"
echo ""
echo "  export BW_SESSION=\$(bw unlock --raw)"
echo "  cd ChXX"
echo "  source load-secrets.sh"
echo ""
