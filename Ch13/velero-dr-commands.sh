#!/bin/bash
# Velero Disaster Recovery drill script with timing and RTO measurement

set -e

# Configuration
NAMESPACES_TO_BACKUP=("team-alpha" "team-beta")
BACKUP_NAME="dr-drill-backup-$(date +%s)"
RESTORE_NAME="dr-drill-restore-$(date +%s)"
RTO_TIMEOUT=600  # 10 minutes RTO target

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Velero Disaster Recovery Drill ===${NC}"
echo "Start time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Record start time
START_TIME=$(date +%s)

# Step 1: Create backup
echo -e "${YELLOW}Step 1: Creating backup...${NC}"
velero backup create "$BACKUP_NAME" \
  --wait \
  --include-namespaces "$(IFS=,; echo "${NAMESPACES_TO_BACKUP[*]}")" \
  --include-cluster-resources=true

if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Backup creation failed${NC}"
  exit 1
fi

BACKUP_CREATION_TIME=$(date +%s)
BACKUP_DURATION=$((BACKUP_CREATION_TIME - START_TIME))
echo -e "${GREEN}Backup created successfully in ${BACKUP_DURATION}s${NC}"

# Verify backup completion
echo "Waiting for backup to complete..."
until [ "$(velero backup get $BACKUP_NAME -o jsonpath='{.status.phase}')" = "Completed" ]; do
  sleep 5
  PHASE=$(velero backup get $BACKUP_NAME -o jsonpath='{.status.phase}')
  echo "Backup phase: $PHASE"
done

echo -e "${GREEN}Backup phase: Completed${NC}"

# Step 2: Simulate disaster - delete namespaces
echo ""
echo -e "${YELLOW}Step 2: Simulating disaster - deleting namespaces...${NC}"
echo "Deleting namespaces: ${NAMESPACES_TO_BACKUP[*]}"

for ns in "${NAMESPACES_TO_BACKUP[@]}"; do
  echo "Deleting namespace: $ns"
  kubectl delete namespace "$ns" --ignore-not-found=true
done

echo "Waiting for namespace deletion..."
sleep 5

# Verify namespaces are deleted
for ns in "${NAMESPACES_TO_BACKUP[@]}"; do
  if kubectl get namespace "$ns" 2>/dev/null; then
    echo -e "${RED}Error: Namespace $ns still exists${NC}"
    exit 1
  fi
done

echo -e "${GREEN}Namespaces deleted successfully${NC}"
DISASTER_TIME=$(date +%s)

# Step 3: Wait before restore (simulate disaster discovery delay)
echo ""
echo -e "${YELLOW}Step 3: Disaster detected, preparing recovery...${NC}"
echo "Waiting 10 seconds before initiating restore..."
sleep 10

# Step 4: Restore from backup
echo ""
echo -e "${YELLOW}Step 4: Restoring from backup - Starting RTO measurement...${NC}"
RESTORE_START=$(date +%s)

velero restore create "$RESTORE_NAME" \
  --from-backup "$BACKUP_NAME" \
  --wait

if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Restore creation failed${NC}"
  exit 1
fi

# Wait for restore to complete
echo "Waiting for restore to complete..."
until [ "$(velero restore get $RESTORE_NAME -o jsonpath='{.status.phase}')" = "Completed" ]; do
  sleep 5
  PHASE=$(velero restore get $RESTORE_NAME -o jsonpath='{.status.phase}')
  echo "Restore phase: $PHASE"
done

RESTORE_END=$(date +%s)
RESTORE_DURATION=$((RESTORE_END - RESTORE_START))

echo -e "${GREEN}Restore completed in ${RESTORE_DURATION}s${NC}"

# Step 5: Verify recovery
echo ""
echo -e "${YELLOW}Step 5: Verifying recovery...${NC}"

# Check if namespaces are restored
RECOVERY_VERIFIED=true
for ns in "${NAMESPACES_TO_BACKUP[@]}"; do
  if kubectl get namespace "$ns" 2>/dev/null; then
    echo -e "${GREEN}Namespace restored: $ns${NC}"
  else
    echo -e "${RED}Error: Namespace not restored: $ns${NC}"
    RECOVERY_VERIFIED=false
  fi
done

# Wait for pods to be ready
echo "Waiting for workloads to be ready..."
for ns in "${NAMESPACES_TO_BACKUP[@]}"; do
  echo "Checking pods in namespace: $ns"
  kubectl rollout status deployment -n "$ns" --timeout=300s || {
    echo -e "${YELLOW}Warning: Some deployments not ready${NC}"
  }
done

# Verify data integrity (optional)
echo ""
echo -e "${YELLOW}Step 6: Verifying data integrity...${NC}"
for ns in "${NAMESPACES_TO_BACKUP[@]}"; do
  POD_COUNT=$(kubectl get pods -n "$ns" --no-headers 2>/dev/null | wc -l)
  echo "Pods restored in $ns: $POD_COUNT"
done

# Step 7: Generate report
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
echo "  Disaster time: $(($DISASTER_TIME - $BACKUP_CREATION_TIME))s"
echo "  Restore duration: ${RESTORE_DURATION}s"
echo "  Total drill time: ${TOTAL_DURATION}s"
echo ""

echo "Backup name: $BACKUP_NAME"
echo "Restore name: $RESTORE_NAME"
echo ""

# Display backup info
echo "Backup details:"
velero backup describe "$BACKUP_NAME"

echo ""
echo "Restore details:"
velero restore describe "$RESTORE_NAME"

# Cleanup option
echo ""
echo -e "${YELLOW}Cleanup options:${NC}"
echo "To delete this backup: velero backup delete $BACKUP_NAME"
echo "To delete this restore: velero restore delete $RESTORE_NAME"
echo ""

if [ $RECOVERY_VERIFIED = true ] && [ $RESTORE_DURATION -le $RTO_TIMEOUT ]; then
  echo -e "${GREEN}DR Drill completed successfully!${NC}"
  exit 0
else
  echo -e "${RED}DR Drill completed with warnings${NC}"
  exit 1
fi
