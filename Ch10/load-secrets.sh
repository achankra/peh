#!/bin/bash
# =============================================================================
# Chapter 10: Load Secrets
# =============================================================================
# Sets environment variables needed for template publishing.
#
# Usage:
#   source load-secrets.sh    # exports env vars into current shell
#
# Our Backstage instance uses guest auth (dangerouslyDisableDefaultAuthPolicy)
# from Ch6, so no API token is needed. In production Backstage with real auth,
# you'd add BACKSTAGE_TOKEN here.
# =============================================================================

export BACKSTAGE_URL="${BACKSTAGE_URL:-http://localhost:7007}"
echo "BACKSTAGE_URL=$BACKSTAGE_URL"

# Optional: If your Backstage has auth enabled, set the token via Bitwarden
if [ -n "${BACKSTAGE_TOKEN:-}" ]; then
    echo "BACKSTAGE_TOKEN is set (will use Bearer auth)"
else
    echo "BACKSTAGE_TOKEN not set (using guest auth — no token needed for local Backstage)"
fi

echo ""
echo "Chapter 10 environment ready. You can now run:"
echo "  python3 publish.py"
echo "  pytest test_templates.py -v -k Structure"
