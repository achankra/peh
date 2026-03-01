#!/bin/bash
# =============================================================================
# Bitwarden Helper Functions
# =============================================================================
# Shared utility for securely retrieving secrets from Bitwarden vault.
# Sourced by chapter-specific load-secrets.sh scripts throughout the book.
#
# Usage:
#   source scripts/bw-helper.sh   # from Ch1, or copy to other chapters
#   bw_init                       # authenticate and unlock
#   MY_SECRET=$(bw_get "item-name" "field-name")
#   bw_cleanup                    # lock the vault
#
# Prerequisites:
#   - Bitwarden CLI installed (npm install -g @bitwarden/cli)
#   - .env file with BW_CLIENTID, BW_CLIENTSECRET, BW_PASSWORD
#   - Secrets already stored in Bitwarden (via upload-secrets.sh)
# =============================================================================

# Only set strict mode when run directly, not when sourced
# (set -e in a sourced script kills the parent shell on any failure)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    set -euo pipefail
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load .env if present
_bw_load_env() {
    local env_file="${1:-.env}"
    if [ -f "$env_file" ]; then
        # shellcheck source=/dev/null
        source "$env_file"
    elif [ -f "../Ch01/.env" ]; then
        # Fall back to Ch01 .env when running from other chapters (peh/Ch03 -> peh/Ch01)
        # shellcheck source=/dev/null
        source "../Ch01/.env"
    elif [ -f "../Ch1/.env" ]; then
        # Also check non-zero-padded Ch1 directory
        # shellcheck source=/dev/null
        source "../Ch1/.env"
    elif [ -f "../Ch1/code/.env" ]; then
        # Manuscript layout: running from ChXX/code/ -> Ch1/code/.env
        # shellcheck source=/dev/null
        source "../Ch1/code/.env"
    else
        echo -e "${RED}Error: No .env file found.${NC}"
        echo "Create .env from .env_example with your Bitwarden credentials."
        echo "Looked in: .env, ../Ch01/.env, ../Ch1/.env, ../Ch1/code/.env"
        return 1
    fi
}

# Authenticate and unlock Bitwarden vault
# Sets BW_SESSION for subsequent bw commands
bw_init() {
    _bw_load_env "$@"

    if [ -z "${BW_CLIENTID:-}" ] || [ -z "${BW_CLIENTSECRET:-}" ] || [ -z "${BW_PASSWORD:-}" ]; then
        echo -e "${RED}Error: BW_CLIENTID, BW_CLIENTSECRET, and BW_PASSWORD must be set.${NC}"
        return 1
    fi

    echo -e "${YELLOW}Authenticating with Bitwarden...${NC}"

    # Check if already logged in
    if ! bw login --check &>/dev/null; then
        bw login --apikey 2>/dev/null
    fi

    echo -e "${YELLOW}Unlocking vault...${NC}"
    export BW_SESSION
    BW_SESSION=$(bw unlock --passwordenv BW_PASSWORD --raw 2>/dev/null)

    if [ -z "$BW_SESSION" ]; then
        echo -e "${RED}Error: Failed to unlock Bitwarden vault.${NC}"
        return 1
    fi

    # Sync to get latest items
    bw sync --session "$BW_SESSION" &>/dev/null
    echo -e "${GREEN}Bitwarden vault unlocked successfully.${NC}"
}

# Retrieve a secret value from Bitwarden
# Usage: bw_get "item-name" ["field-name"]
#   - If field-name is omitted, returns the password field
#   - If field-name is "notes", returns the secure note
#   - Otherwise returns the named custom field
bw_get() {
    local item_name="$1"
    local field_name="${2:-password}"

    if [ -z "${BW_SESSION:-}" ]; then
        echo -e "${RED}Error: Vault not unlocked. Run bw_init first.${NC}" >&2
        return 1
    fi

    if [ "$field_name" = "notes" ]; then
        bw get notes "$item_name" --session "$BW_SESSION" 2>/dev/null
        return
    fi

    # Try the built-in shortcut first (works for Login items)
    local value=""
    if [ "$field_name" = "password" ]; then
        value=$(bw get password "$item_name" --session "$BW_SESSION" 2>/dev/null || true)
    elif [ "$field_name" = "username" ]; then
        value=$(bw get username "$item_name" --session "$BW_SESSION" 2>/dev/null || true)
    elif [ "$field_name" = "uri" ]; then
        value=$(bw get uri "$item_name" --session "$BW_SESSION" 2>/dev/null || true)
    fi

    # If shortcut returned a value, use it
    if [ -n "$value" ]; then
        echo "$value"
        return
    fi

    # Fall back to custom field lookup (works for both Login and Secure Note items)
    bw get item "$item_name" --session "$BW_SESSION" 2>/dev/null \
        | python3 -c "
import sys, json
item = json.load(sys.stdin)
for f in item.get('fields', []):
    if f['name'] == '$field_name':
        print(f['value'])
        sys.exit(0)
print('')
" 2>/dev/null
}

# Export a secret as an environment variable
# Usage: bw_export "ENV_VAR_NAME" "item-name" ["field-name"]
bw_export() {
    local var_name="$1"
    local item_name="$2"
    local field_name="${3:-}"
    local value

    value=$(bw_get "$item_name" "$field_name")
    if [ -n "$value" ]; then
        export "$var_name=$value"
        echo -e "${GREEN}  ✓ $var_name loaded from vault${NC}"
    else
        echo -e "${YELLOW}  ⚠ $var_name not found in vault (item: $item_name)${NC}"
    fi
}

# Lock the vault and clear the session
bw_cleanup() {
    if [ -n "${BW_SESSION:-}" ]; then
        bw lock --session "$BW_SESSION" &>/dev/null || true
        unset BW_SESSION
        echo -e "${GREEN}Bitwarden vault locked.${NC}"
    fi
}

# Trap to ensure vault is locked on script exit (only when run directly, not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    trap bw_cleanup EXIT
fi
