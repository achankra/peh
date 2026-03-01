#!/bin/bash
# Velero Disaster Recovery drill script with timing and RTO measurement
# Creates a test namespace, backs it up, deletes it, restores it, and measures RTO.

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BACKUP_NAME="dr-drill-backup-$(date +%s)"
RESTORE_NAME="dr-drill-restore-$(date +%s)"
DR_NAMESPACE="dr-drill-demo"
RTO_TIMEOUT=600  # 10 minutes RTO target

echo -e "${YELLOW}=== Velero Disaster Recovery Drill ===${NC}"
echo "Start time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Step 0: Create a test namespace with sample workloads
echo -e "${YELLOW}Step 0: Setting up test namespace with sample workloads...${NC}"
kubectl create namespace "$DR_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
kubectl create deployment nginx-demo --image=nginx:alpine -n "$DR_NAMESPACE" --replicas=2
kubectl create configmap demo-config --from-literal=env=production --from-literal=version=1.0 -n "$DR_NAMESPACE"
kubectl wait --for=condition=available deployment/nginx-demo -n "$DR_NAMESPACE" --timeout=60s
echo -e "${GREEN}Test namespace ready with nginx deployment and configmap${NC}"
echo ""

# Record start time
START_TIME=$(date +%s)

# Step 1: Create backup
echo -e "${YELLOW}Step 1: Creating backup of ${DR_NAMESPACE}...${NC}"
velero backup create "$BACKUP_NAME" \
  --include-namespaces "$DR_NAMESPACE" \
  --include-cluster-resources=false \
  --wait

BACKUP_PHASE=$(kubectl get backup "$BACKUP_NAME" -n velero -o jsonpath='{.status.phase}')
BACKUP_CREATION_TIME=$(date +%s)
BACKUP_DURATION=$((BACKUP_CREATION_TIME - START_TIME))

if [ "$BACKUP_PHASE" = "Completed" ]; then
  echo -e "${GREEN}Backup completed successfully in ${BACKUP_DURATION}s${NC}"
elif [ "$BACKUP_PHASE" = "PartiallyFailed" ]; then
  echo -e "${YELLOW}Backup partially completed in ${BACKUP_DURATION}s (some resources may have warnings)${NC}"
else
  echo -e "${RED}Backup failed with phase: ${BACKUP_PHASE}${NC}"
  velero backup describe "$BACKUP_NAME"
  exit 1
fi

# Step 2: Simulate disaster - delete namespace
echo ""
echo -e "${YELLOW}Step 2: Simulating disaster - deleting namespace ${DR_NAMESPACE}...${NC}"
kubectl delete namespace "$DR_NAMESPACE" --wait=true
echo -e "${GREEN}Namespace deleted — disaster simulated${NC}"

DISASTER_TIME=$(date +%s)

# Step 3: Wait before restore (simulate disaster discovery delay)
echo ""
echo -e "${YELLOW}Step 3: Disaster detected, preparing recovery...${NC}"
echo "Waiting 5 seconds before initiating restore..."
sleep 5

# Step 4: Restore from backup
echo ""
echo -e "${YELLOW}Step 4: Restoring from backup — Starting RTO measurement...${NC}"
RESTORE_START=$(date +%s)

velero restore create "$RESTORE_NAME" \
  --from-backup "$BACKUP_NAME" \
  --wait

RESTORE_PHASE=$(kubectl get restore "$RESTORE_NAME" -n velero -o jsonpath='{.status.phase}')
RESTORE_END=$(date +%s)
RESTORE_DURATION=$((RESTORE_END - RESTORE_START))

if [ "$RESTORE_PHASE" = "Completed" ]; then
  echo -e "${GREEN}Restore completed in ${RESTORE_DURATION}s${NC}"
elif [ "$RESTORE_PHASE" = "PartiallyFailed" ]; then
  echo -e "${YELLOW}Restore partially completed in ${RESTORE_DURATION}s${NC}"
else
  echo -e "${RED}Restore failed with phase: ${RESTORE_PHASE}${NC}"
  velero restore describe "$RESTORE_NAME"
  exit 1
fi

# Step 5: Verify recovery
echo ""
echo -e "${YELLOW}Step 5: Verifying recovery...${NC}"

RECOVERY_VERIFIED=true

# Check namespace exists
if kubectl get namespace "$DR_NAMESPACE" &>/dev/null; then
  echo -e "${GREEN}Namespace restored: ${DR_NAMESPACE}${NC}"
else
  echo -e "${RED}Namespace NOT restored: ${DR_NAMESPACE}${NC}"
  RECOVERY_VERIFIED=false
fi

# Check deployment is back
if kubectl get deployment nginx-demo -n "$DR_NAMESPACE" &>/dev/null; then
  echo -e "${GREEN}Deployment restored: nginx-demo${NC}"
  kubectl wait --for=condition=available deployment/nginx-demo -n "$DR_NAMESPACE" --timeout=60s
else
  echo -e "${RED}Deployment NOT restored: nginx-demo${NC}"
  RECOVERY_VERIFIED=false
fi

# Check configmap
if kubectl get configmap demo-config -n "$DR_NAMESPACE" &>/dev/null; then
  echo -e "${GREEN}ConfigMap restored: demo-config${NC}"
  CONFIG_VAL=$(kubectl get configmap demo-config -n "$DR_NAMESPACE" -o jsonpath='{.data.env}')
  echo "  env=${CONFIG_VAL} (should be 'production')"
else
  echo -e "${RED}ConfigMap NOT restored: demo-config${NC}"
  RECOVERY_VERIFIED=false
fi

# Step 6: Generate report
echo ""
echo -e "${YELLOW}=== DR Drill Report ===${NC}"

END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))

echo "Recovery Time Objective (RTO): ${RTO_TIMEOUT}s"
echo "Actual Recovery Time: ${RESTORE_DURATION}s"

if [ $RESTORE_DURATION -le $RTO_TIMEOUT ]; then
  echo -e "${GREEN}RTO Target: PASSED${NC}"
else
  echo -e "${RED}RTO Target: FAILED${NC}"
fi

echo ""
echo "Detailed Timings:"
echo "  Backup duration: ${BACKUP_DURATION}s"
echo "  Disaster simulation: $(($DISASTER_TIME - $BACKUP_CREATION_TIME))s"
echo "  Restore duration: ${RESTORE_DURATION}s"
echo "  Total drill time: ${TOTAL_DURATION}s"
echo ""
echo "Backup name: $BACKUP_NAME"
echo "Restore name: $RESTORE_NAME"
echo ""

if [ "$RECOVERY_VERIFIED" = true ] && [ $RESTORE_DURATION -le $RTO_TIMEOUT ]; then
  echo -e "${GREEN}DR Drill completed successfully!${NC}"
  exit 0
else
  echo -e "${YELLOW}DR Drill completed with warnings — check details above${NC}"
  exit 0
fi
