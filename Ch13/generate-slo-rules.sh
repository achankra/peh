#!/bin/bash
# Generate Prometheus SLO rules from Sloth specifications

set -e

SLOTH_SPEC_FILE="${1:-sloth-slo-spec.yaml}"
OUTPUT_FILE="${2:-prometheus-slo-rules.yaml}"

echo "Validating Sloth SLO specification..."
if [ ! -f "$SLOTH_SPEC_FILE" ]; then
  echo "Error: Sloth specification file not found: $SLOTH_SPEC_FILE"
  exit 1
fi

echo "Generating Prometheus recording and alert rules from Sloth spec..."
sloth generate \
  --input "$SLOTH_SPEC_FILE" \
  --output "$OUTPUT_FILE"

if [ $? -ne 0 ]; then
  echo "Error: Failed to generate SLO rules"
  exit 1
fi

echo "SLO rules generated successfully: $OUTPUT_FILE"

echo "Validating generated PrometheusRule..."
kubectl apply -f "$OUTPUT_FILE" --dry-run=client -o yaml > /dev/null
if [ $? -ne 0 ]; then
  echo "Warning: Generated rules validation failed, but file was created"
fi

echo "Applying SLO rules to Kubernetes cluster..."
kubectl apply -f "$OUTPUT_FILE"

if [ $? -ne 0 ]; then
  echo "Error: Failed to apply SLO rules to cluster"
  exit 1
fi

echo "SLO rules applied successfully to cluster"
echo "Recording rules and alert rules are now active in Prometheus"

# Display summary
echo ""
echo "=== SLO Rules Summary ==="
kubectl get prometheusrule -A | grep -i slo || echo "No SLO PrometheusRules found"
