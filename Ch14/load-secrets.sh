#!/bin/bash
# =============================================================================
# Chapter 14: Load Secrets from Bitwarden
# =============================================================================
# Retrieves AI/ML API keys from the Bitwarden vault for the RAG pipeline,
# multi-agent system, and AI governance exercises.
#
# Usage:
#   source load-secrets.sh    # exports env vars into current shell
#
# Vault items expected (create these in Bitwarden):
#   "peh-openai"         -> password: <your-openai-api-key>
#   "peh-pinecone"       -> password: <your-pinecone-api-key> (optional)
#
# After running, the following environment variables are set:
#   OPENAI_API_KEY       - OpenAI API key for LLM components
#   PINECONE_API_KEY     - Pinecone API key (optional, for vector DB)
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the shared Bitwarden helper
if [ -f "$SCRIPT_DIR/../../Ch01/scripts/bw-helper.sh" ]; then
    source "$SCRIPT_DIR/../../Ch01/scripts/bw-helper.sh"
else
    echo "Error: bw-helper.sh not found. Copy it from Ch01/scripts/"
    exit 1
fi

echo "Loading Chapter 14 secrets from Bitwarden..."
echo ""

bw_init

# OpenAI API key for RAG pipeline and chatbot
bw_export "OPENAI_API_KEY"  "peh-openai"  "password"

# Pinecone (optional - for production vector DB)
bw_export "PINECONE_API_KEY" "peh-pinecone" "password" 2>/dev/null || true

echo ""
if [ -n "${OPENAI_API_KEY:-}" ]; then
    echo "Chapter 14 secrets loaded. You can now run:"
    echo "  python3 rag-platform-docs.py"
    echo "  python3 platform_chatbot/incident_triage.py"
else
    echo "⚠ OPENAI_API_KEY not found in vault."
    echo "  Scripts will run in mock mode (no real LLM calls)."
    echo "  To use real LLM, store your key in Bitwarden as 'peh-openai'."
fi
