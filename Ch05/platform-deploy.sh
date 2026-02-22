#!/bin/bash
# Chapter 5: Self-Service Platform Deployment Script
# ===================================================
# Developer-friendly deployment tool with pre-configured templates.
# Usage: ./platform-deploy.sh <app-name> <namespace> [environment]

set -euo pipefail

APP_NAME="${1:?Usage: $0 <app-name> <namespace> [environment]}"
NAMESPACE="${2:?Usage: $0 <app-name> <namespace> [environment]}"
ENVIRONMENT="${3:-dev}"

echo "=== Platform Self-Service Deploy ==="
echo "App: $APP_NAME | Namespace: $NAMESPACE | Env: $ENVIRONMENT"

# --- Prerequisites Check ---
for cmd in kubectl kustomize argocd; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: $cmd is required but not installed."
    exit 1
  fi
done

# --- Ensure Namespace Exists ---
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
  echo "Creating namespace: $NAMESPACE"
  kubectl create namespace "$NAMESPACE"
  kubectl label namespace "$NAMESPACE" \
    app.kubernetes.io/managed-by=platform-deploy \
    environment="$ENVIRONMENT"
fi

# --- Apply Kustomize Overlays ---
OVERLAY_DIR="overlays/${ENVIRONMENT}"
if [ -d "$OVERLAY_DIR" ]; then
  echo "Applying Kustomize overlay: $OVERLAY_DIR"
  kustomize build "$OVERLAY_DIR" | kubectl apply -n "$NAMESPACE" -f -
else
  echo "No overlay found at $OVERLAY_DIR, applying base manifests"
  kubectl apply -n "$NAMESPACE" -f base/
fi

# --- Register with ArgoCD ---
echo "Registering $APP_NAME with ArgoCD..."
argocd app create "$APP_NAME" \
  --repo "https://github.com/platform-org/${APP_NAME}.git" \
  --path "overlays/${ENVIRONMENT}" \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace "$NAMESPACE" \
  --sync-policy automated \
  --auto-prune \
  --self-heal \
  --upsert 2>/dev/null || echo "ArgoCD registration skipped (not connected)"

echo "Deployment complete for $APP_NAME in $NAMESPACE ($ENVIRONMENT)"
