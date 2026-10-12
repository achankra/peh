#!/bin/bash
# OpenCost Installation Script
# Chapter 12 - Optimizing Cost, Performance, and Scalability
#
# OpenCost is the CNCF sandbox project for Kubernetes cost allocation.
# It scrapes Prometheus and the Kubernetes API to attribute costs to
# namespaces, teams, and workloads.
#
# Prerequisites:
#   - Kubernetes cluster with kubectl configured
#   - Helm 3 installed
#   - Prometheus running in the cluster (from Chapter 4)
#
# Usage:
#   chmod +x install-opencost.sh
#   ./install-opencost.sh

set -e

NAMESPACE="opencost"
PROMETHEUS_SERVER="kube-prometheus-stack-prometheus"
PROMETHEUS_NAMESPACE="monitoring"

echo "Adding OpenCost Helm repository..."
helm repo add opencost https://opencost.github.io/opencost-helm-chart
helm repo update

# The Gatekeeper policy namespace-must-have-team (Chapters 3/11) checks labels at
# creation time, so they must be on the namespace from the start.
echo "Creating ${NAMESPACE} namespace..."
# istio-injection=enabled gives OpenCost an mTLS identity so the Chapter 4 policy
# (allow-monitoring-internal) lets it query Prometheus.
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml \
  | kubectl label --local -f - team=platform environment=dev cost-center=10001 \
      istio-injection=enabled -o yaml \
  | kubectl apply -f -

# The Gatekeeper policy require-limits denies pods without BOTH cpu and memory
# limits; the chart only sets a memory limit, so add cpu limits for both containers.
echo "Installing OpenCost..."
helm upgrade --install opencost opencost/opencost \
  --namespace ${NAMESPACE} \
  --set opencost.exporter.resources.limits.cpu=500m \
  --set opencost.ui.resources.limits.cpu=200m \
  --set opencost.prometheus.internal.serviceName="${PROMETHEUS_SERVER}" \
  --set opencost.prometheus.internal.namespaceName="${PROMETHEUS_NAMESPACE}" \
  --set opencost.prometheus.internal.port=9090 \
  --set opencost.ui.enabled=true \
  --set opencost.exporter.defaultClusterId="platform-cluster"

echo "Waiting for OpenCost deployment to be ready..."
kubectl rollout status deployment/opencost -n ${NAMESPACE} --timeout=5m

echo "OpenCost installation completed successfully"
echo ""
echo "Access OpenCost UI:"
echo "  kubectl port-forward -n ${NAMESPACE} svc/opencost 9090:9090"
echo "  Then open http://localhost:9090 in your browser"
echo ""
echo "Query cost allocation API:"
echo "  kubectl port-forward -n ${NAMESPACE} svc/opencost 9003:9003"
echo "  curl http://localhost:9003/allocation/compute?window=24h&aggregate=namespace"
