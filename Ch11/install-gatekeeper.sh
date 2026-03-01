#!/bin/bash
set -euo pipefail

# Install OPA Gatekeeper
# Adds the Gatekeeper Helm repo and installs Gatekeeper in the gatekeeper-system namespace

GATEKEEPER_VERSION=${GATEKEEPER_VERSION:-"3.14.0"}
GATEKEEPER_NAMESPACE="gatekeeper-system"

echo "Installing OPA Gatekeeper v${GATEKEEPER_VERSION}..."

# Add Gatekeeper Helm repository
echo "Adding Gatekeeper Helm repository..."
helm repo add gatekeeper https://open-policy-agent.github.io/gatekeeper/charts
helm repo update

# Create namespace
echo "Creating namespace: ${GATEKEEPER_NAMESPACE}"
kubectl create namespace "${GATEKEEPER_NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Install Gatekeeper
echo "Installing Gatekeeper..."
helm install gatekeeper gatekeeper/gatekeeper \
  --namespace "${GATEKEEPER_NAMESPACE}" \
  --create-namespace \
  --set enableExternalData=true \
  --set enableGeneratorResourceExpansion=true \
  --set logLevel=INFO \
  --wait

# Wait for Gatekeeper to be ready
echo "Waiting for Gatekeeper to be ready..."
kubectl rollout status deployment/gatekeeper-audit \
  -n "${GATEKEEPER_NAMESPACE}" \
  --timeout=5m

kubectl rollout status deployment/gatekeeper \
  -n "${GATEKEEPER_NAMESPACE}" \
  --timeout=5m

echo "OPA Gatekeeper installed successfully!"

# Verify installation
echo ""
echo "Gatekeeper pods:"
kubectl get pods -n "${GATEKEEPER_NAMESPACE}"

echo ""
echo "Gatekeeper is ready to accept ConstraintTemplates and Constraints."
