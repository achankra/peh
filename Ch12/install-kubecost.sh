#!/bin/bash
# KubeCost installation script with helm and kubectl commands

set -e

echo "Adding KubeCost Helm repository..."
helm repo add kubecost https://kubecost.github.io/cost-analyzer/
helm repo update

echo "Creating kubecost namespace..."
kubectl create namespace kubecost --dry-run=client -o yaml | kubectl apply -f -

echo "Installing KubeCost..."
helm install kubecost kubecost/cost-analyzer \
  --namespace kubecost \
  --set prometheus.server.global.external_labels.cluster_id=my-cluster \
  --set kubecostModel.warmCache=true \
  --set kubecostModel.warmSavingsCache=true

echo "Waiting for KubeCost deployment to be ready..."
kubectl rollout status deployment/kubecost-cost-analyzer -n kubecost --timeout=5m

echo "KubeCost installation completed successfully"
echo "Access KubeCost UI: kubectl port-forward -n kubecost svc/kubecost-cost-analyzer 9090:9090"
