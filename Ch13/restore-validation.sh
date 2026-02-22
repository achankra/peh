#!/bin/bash
# Velero Restore Validation Script
#
# This script validates Velero restore operations by:
# - Running a test restore from the latest backup to a temporary namespace
# - Verifying restored resources exist and are healthy
# - Measuring RTO (Recovery Time Objective)
# - Cleaning up the test namespace after validation
# - Outputting a comprehensive validation report
#
# Suitable for weekly automated DR validation runs and CI/CD pipelines
#
# Usage:
#   ./restore-validation.sh [options]
#
# Options:
#   --backup-name      Specific backup name (uses latest if not specified)
#   --target-namespace Temporary namespace for restore (default: restore-test-TIMESTAMP)
#   --namespaces       Comma-separated list of namespaces to validate (default: all)
#   --rto-target       RTO target in seconds (default: 600)
#   --output           Output file for report (default: stdout)
#   --cleanup          Auto cleanup test namespace on success (default: true)
#   --dry-run          Show what would be done without executing
#   --help             Show this help message

set -euo pipefail

# ============================================================================
# Configuration and Defaults
# ============================================================================

VELERO_NAMESPACE="${VELERO_NAMESPACE:-velero}"
BACKUP_NAME=""
TARGET_NAMESPACE=""
VALIDATE_NAMESPACES=""
RTO_TARGET_SECONDS=600
OUTPUT_FILE=""
CLEANUP_ON_SUCCESS=true
DRY_RUN=false

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Tracking variables
VALIDATION_START_TIME=$(date +%s)
RESTORE_START_TIME=""
RESTORE_END_TIME=""
VALIDATION_FAILED=false
VALIDATION_WARNINGS=()
VALIDATION_ERRORS=()

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    local message="$1"
    echo -e "\n${BLUE}=== ${message} ===${NC}\n"
}

print_info() {
    local message="$1"
    echo -e "${BLUE}[INFO]${NC} ${message}"
}

print_success() {
    local message="$1"
    echo -e "${GREEN}[SUCCESS]${NC} ${message}"
}

print_warning() {
    local message="$1"
    echo -e "${YELLOW}[WARNING]${NC} ${message}"
    VALIDATION_WARNINGS+=("$message")
}

print_error() {
    local message="$1"
    echo -e "${RED}[ERROR]${NC} ${message}"
    VALIDATION_ERRORS+=("$message")
    VALIDATION_FAILED=true
}

log_output() {
    if [ -n "$OUTPUT_FILE" ]; then
        echo "$1" >> "$OUTPUT_FILE"
    fi
}

run_command() {
    local description="$1"
    shift
    local cmd=("$@")

    print_info "Running: ${cmd[*]}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would execute: ${cmd[*]}"
        return 0
    fi

    if ! "${cmd[@]}"; then
        print_error "Command failed: ${cmd[*]}"
        return 1
    fi
}

show_help() {
    grep "^#" "$0" | grep -v "^#!/bin/bash" | sed 's/^# *//' | sed 's/^#//'
    exit 0
}

# ============================================================================
# Validation Functions
# ============================================================================

get_latest_backup() {
    local latest=$(velero backup get -n "$VELERO_NAMESPACE" -o json | \
        jq -r '.items | sort_by(.metadata.creationTimestamp) | reverse | .[0].metadata.name')

    if [ -z "$latest" ] || [ "$latest" = "null" ]; then
        print_error "No backups found in Velero"
        return 1
    fi

    echo "$latest"
}

validate_backup_exists() {
    local backup_name="$1"

    print_info "Validating backup exists: $backup_name"

    local phase=$(velero backup get "$backup_name" -n "$VELERO_NAMESPACE" \
        -o jsonpath='{.status.phase}' 2>/dev/null || echo "")

    if [ -z "$phase" ]; then
        print_error "Backup not found: $backup_name"
        return 1
    fi

    if [ "$phase" != "Completed" ]; then
        print_error "Backup is not in Completed state: $phase"
        return 1
    fi

    print_success "Backup validated: $backup_name (Status: $phase)"
    return 0
}

create_test_namespace() {
    local namespace="$1"

    print_info "Creating test namespace: $namespace"

    if kubectl get namespace "$namespace" 2>/dev/null; then
        print_warning "Namespace already exists, deleting and recreating: $namespace"
        kubectl delete namespace "$namespace" --wait=true --timeout=120s 2>/dev/null || true
        sleep 5
    fi

    kubectl create namespace "$namespace"
    kubectl label namespace "$namespace" \
        restore-test="true" \
        created-at="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --overwrite

    print_success "Test namespace created: $namespace"
}

perform_restore() {
    local backup_name="$1"
    local namespace="$2"

    print_header "Performing Restore Operation"

    RESTORE_START_TIME=$(date +%s)

    local restore_name="restore-validation-$(date +%s)"

    print_info "Starting restore from backup: $backup_name"
    print_info "Target namespace: $namespace"
    print_info "Restore name: $restore_name"

    # Create restore resource
    velero restore create "$restore_name" \
        --from-backup "$backup_name" \
        --namespace-mappings "$(echo "${VALIDATE_NAMESPACES:-}" | sed 's/,/:'"$namespace"',/g;s/$/:'$namespace'/')" \
        --wait \
        -n "$VELERO_NAMESPACE" || {
        print_error "Failed to create restore: $restore_name"
        return 1
    }

    print_success "Restore completed: $restore_name"
    RESTORE_END_TIME=$(date +%s)

    return 0
}

validate_resources_restored() {
    local namespace="$1"

    print_header "Validating Restored Resources"

    # Check namespace exists
    if ! kubectl get namespace "$namespace" >/dev/null 2>&1; then
        print_error "Namespace not restored: $namespace"
        return 1
    fi

    print_success "Namespace exists: $namespace"

    # Count resource types
    local pod_count=$(kubectl get pods -n "$namespace" --no-headers 2>/dev/null | wc -l)
    local deployment_count=$(kubectl get deployments -n "$namespace" --no-headers 2>/dev/null | wc -l)
    local service_count=$(kubectl get services -n "$namespace" --no-headers 2>/dev/null | wc -l)
    local pvc_count=$(kubectl get pvc -n "$namespace" --no-headers 2>/dev/null | wc -l)

    print_info "Resource counts in restored namespace:"
    echo "  Pods: $pod_count"
    echo "  Deployments: $deployment_count"
    echo "  Services: $service_count"
    echo "  PersistentVolumeClaims: $pvc_count"

    if [ "$pod_count" -eq 0 ] && [ "$deployment_count" -eq 0 ]; then
        print_warning "No pods or deployments found in restored namespace"
        return 0
    fi

    print_success "Resources detected in restored namespace"
    return 0
}

wait_for_pod_readiness() {
    local namespace="$1"
    local max_wait=300  # 5 minutes

    print_header "Waiting for Pod Readiness"

    print_info "Waiting for deployments to be ready (max ${max_wait}s)..."

    local start_time=$(date +%s)
    local ready=false

    # Wait for deployments if they exist
    if kubectl get deployments -n "$namespace" 2>/dev/null | grep -q .; then
        if timeout $max_wait kubectl rollout status deployment \
            -n "$namespace" \
            --timeout="${max_wait}s" 2>&1; then
            ready=true
            print_success "All deployments are ready"
        else
            print_warning "Deployments did not reach ready state within ${max_wait}s"

            # List deployment status
            print_info "Deployment status:"
            kubectl get deployments -n "$namespace" -o wide
        fi
    else
        print_info "No deployments found in namespace"
        ready=true
    fi

    # Check pod status
    print_info "Pod status in restored namespace:"
    kubectl get pods -n "$namespace" -o wide

    local end_time=$(date +%s)
    local pod_readiness_time=$((end_time - start_time))

    if [ "$ready" = true ]; then
        print_success "Pod readiness check completed in ${pod_readiness_time}s"
    else
        print_warning "Some pods may not be ready, continuing validation..."
    fi

    return 0
}

verify_services_healthy() {
    local namespace="$1"

    print_header "Verifying Service Health"

    local services=$(kubectl get services -n "$namespace" --no-headers 2>/dev/null | awk '{print $1}')

    if [ -z "$services" ]; then
        print_info "No services found in namespace"
        return 0
    fi

    local unhealthy_count=0

    while IFS= read -r service; do
        if [ -z "$service" ]; then
            continue
        fi

        local endpoints=$(kubectl get endpoints "$service" -n "$namespace" \
            -o jsonpath='{.subsets[0].addresses[*].ip}' 2>/dev/null || echo "")

        if [ -z "$endpoints" ] && [ "$service" != "kubernetes" ]; then
            print_warning "Service has no ready endpoints: $service"
            ((unhealthy_count++))
        else
            print_success "Service is healthy: $service"
        fi
    done <<< "$services"

    if [ $unhealthy_count -gt 0 ]; then
        print_warning "Found $unhealthy_count services without ready endpoints"
    else
        print_success "All services are healthy"
    fi

    return 0
}

measure_rto() {
    local rto_target="$1"

    print_header "RTO (Recovery Time Objective) Analysis"

    if [ -z "$RESTORE_START_TIME" ] || [ -z "$RESTORE_END_TIME" ]; then
        print_warning "Restore timing information not available"
        return 0
    fi

    local rto_actual=$((RESTORE_END_TIME - RESTORE_START_TIME))

    print_info "RTO Target: ${rto_target}s"
    print_info "Actual RTO: ${rto_actual}s"

    if [ "$rto_actual" -le "$rto_target" ]; then
        print_success "RTO Target PASSED"
        return 0
    else
        local excess=$((rto_actual - rto_target))
        print_warning "RTO Target FAILED (exceeded by ${excess}s)"
        return 1
    fi
}

cleanup_test_namespace() {
    local namespace="$1"

    print_header "Cleanup"

    if [ "$CLEANUP_ON_SUCCESS" = false ]; then
        print_info "Cleanup disabled, leaving test namespace: $namespace"
        return 0
    fi

    if [ "$VALIDATION_FAILED" = true ]; then
        print_warning "Validation failed, leaving test namespace for investigation: $namespace"
        return 0
    fi

    print_info "Cleaning up test namespace: $namespace"

    if kubectl delete namespace "$namespace" --wait=true --timeout=120s 2>&1; then
        print_success "Test namespace deleted: $namespace"
        return 0
    else
        print_error "Failed to delete test namespace: $namespace"
        return 1
    fi
}

# ============================================================================
# Report Generation
# ============================================================================

generate_report() {
    local backup_name="$1"
    local target_namespace="$2"

    local validation_end_time=$(date +%s)
    local total_duration=$((validation_end_time - VALIDATION_START_TIME))

    local report=""
    report+="===============================================================================\n"
    report+="VELERO RESTORE VALIDATION REPORT\n"
    report+="===============================================================================\n"
    report+="\n"
    report+="Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)\n"
    report+="Validation Duration: ${total_duration}s\n"
    report+="\n"

    report+="Configuration:\n"
    report+="  Backup Name: $backup_name\n"
    report+="  Test Namespace: $target_namespace\n"
    report+="  Velero Namespace: $VELERO_NAMESPACE\n"
    report+="  RTO Target: ${RTO_TARGET_SECONDS}s\n"
    report+="\n"

    if [ -n "$RESTORE_START_TIME" ] && [ -n "$RESTORE_END_TIME" ]; then
        local rto_actual=$((RESTORE_END_TIME - RESTORE_START_TIME))
        report+="Performance Metrics:\n"
        report+="  Restore Duration: ${rto_actual}s\n"
        report+="  RTO Status: "
        if [ "$rto_actual" -le "$RTO_TARGET_SECONDS" ]; then
            report+="PASSED\n"
        else
            report+="FAILED\n"
        fi
        report+="\n"
    fi

    report+="Validation Results:\n"
    report+="  Status: "
    if [ "$VALIDATION_FAILED" = true ]; then
        report+="FAILED\n"
    else
        report+="PASSED\n"
    fi

    if [ ${#VALIDATION_ERRORS[@]} -gt 0 ]; then
        report+="\n  Errors (${#VALIDATION_ERRORS[@]}):\n"
        for error in "${VALIDATION_ERRORS[@]}"; do
            report+="    - $error\n"
        done
    fi

    if [ ${#VALIDATION_WARNINGS[@]} -gt 0 ]; then
        report+="\n  Warnings (${#VALIDATION_WARNINGS[@]}):\n"
        for warning in "${VALIDATION_WARNINGS[@]}"; do
            report+="    - $warning\n"
        done
    fi

    report+="\nRecommendations:\n"
    if [ "$VALIDATION_FAILED" = true ]; then
        report+="  - Review error logs above\n"
        report+="  - Check Velero operator logs: kubectl logs -n velero -l app=velero\n"
        report+="  - Verify backup integrity: velero backup describe $backup_name\n"
    else
        report+="  - Validation passed successfully\n"
        report+="  - Consider running this validation weekly\n"
        report+="  - Monitor RTO trends over time\n"
    fi

    report+="===============================================================================\n"

    if [ -n "$OUTPUT_FILE" ]; then
        echo -ne "$report" > "$OUTPUT_FILE"
        print_success "Report written to: $OUTPUT_FILE"
    else
        echo -ne "$report"
    fi

    return 0
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backup-name)
                BACKUP_NAME="$2"
                shift 2
                ;;
            --target-namespace)
                TARGET_NAMESPACE="$2"
                shift 2
                ;;
            --namespaces)
                VALIDATE_NAMESPACES="$2"
                shift 2
                ;;
            --rto-target)
                RTO_TARGET_SECONDS="$2"
                shift 2
                ;;
            --output)
                OUTPUT_FILE="$2"
                shift 2
                ;;
            --cleanup)
                CLEANUP_ON_SUCCESS="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help|-h)
                show_help
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Initialize output file if specified
    if [ -n "$OUTPUT_FILE" ]; then
        > "$OUTPUT_FILE"
    fi

    # Generate target namespace if not specified
    if [ -z "$TARGET_NAMESPACE" ]; then
        TARGET_NAMESPACE="restore-test-$(date +%s)"
    fi

    print_header "Velero Restore Validation Starting"

    # Get latest backup if not specified
    if [ -z "$BACKUP_NAME" ]; then
        print_info "No backup specified, using latest backup..."
        BACKUP_NAME=$(get_latest_backup) || exit 1
    fi

    print_info "Using backup: $BACKUP_NAME"

    # Execute validation workflow
    validate_backup_exists "$BACKUP_NAME" || exit 1

    create_test_namespace "$TARGET_NAMESPACE" || exit 1

    if ! perform_restore "$BACKUP_NAME" "$TARGET_NAMESPACE"; then
        print_error "Restore operation failed"
        cleanup_test_namespace "$TARGET_NAMESPACE"
        generate_report "$BACKUP_NAME" "$TARGET_NAMESPACE"
        exit 1
    fi

    validate_resources_restored "$TARGET_NAMESPACE" || true

    wait_for_pod_readiness "$TARGET_NAMESPACE" || true

    verify_services_healthy "$TARGET_NAMESPACE" || true

    measure_rto "$RTO_TARGET_SECONDS" || true

    cleanup_test_namespace "$TARGET_NAMESPACE" || true

    print_header "Validation Complete"

    generate_report "$BACKUP_NAME" "$TARGET_NAMESPACE"

    if [ "$VALIDATION_FAILED" = true ]; then
        exit 1
    fi

    exit 0
}

# Run main function
main "$@"
