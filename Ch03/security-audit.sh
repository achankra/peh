#!/bin/bash

################################################################################
# Security Audit Script for Kubernetes Platform
#
# Purpose: Audit Kubernetes cluster for common security misconfigurations
# Checks for:
#   - Overly permissive RBAC roles
#   - Service accounts with excessive permissions
#   - Containers running as root
#   - Missing resource limits
#   - Pods with privileged mode enabled
#
# Usage: bash security-audit.sh [--namespace <ns>] [--verbose]
################################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables
NAMESPACE="${1:-}"
VERBOSE=false
ISSUES_FOUND=0

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    ((ISSUES_FOUND++))
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ((ISSUES_FOUND++))
}

usage() {
    cat << USAGE
Usage: $0 [OPTIONS]

OPTIONS:
    --namespace <ns>    Audit specific namespace (default: all)
    --verbose           Print detailed output
    --help              Show this help message

EXAMPLES:
    # Audit all namespaces
    $0

    # Audit specific namespace
    $0 --namespace kube-system

    # Verbose output
    $0 --verbose
USAGE
    exit 0
}

################################################################################
# Parse Command Line Arguments
################################################################################

while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

################################################################################
# Audit Functions
################################################################################

check_cluster_access() {
    print_header "Cluster Access Check"
    
    if ! kubectl cluster-info &>/dev/null; then
        print_error "Cannot access Kubernetes cluster"
        exit 1
    fi
    
    CLUSTER_VERSION=$(kubectl version --short 2>/dev/null | grep Server | cut -d: -f2 | xargs)
    print_success "Cluster is accessible - Version: $CLUSTER_VERSION"
}

audit_rbac_permissions() {
    print_header "RBAC Permissions Audit"
    
    # Check for wildcard permissions
    while IFS= read -r line; do
        role_name=$(echo "$line" | awk '{print $1}')
        namespace=$(echo "$line" | awk '{print $2}')
        
        if [[ "$line" == *"*"* ]]; then
            print_warning "Role '$role_name' in namespace '$namespace' has wildcard permissions"
        fi
    done < <(kubectl get role -A -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.namespace}{"\t"}{.rules[*].verbs[*]}{"\n"}{end}' 2>/dev/null | grep "\*")
    
    # Check for admin roles
    local admin_count=$(kubectl get clusterrolebindings -o json 2>/dev/null | \
        jq '[.items[] | select(.roleRef.name == "cluster-admin")] | length')
    
    if [[ $admin_count -gt 0 ]]; then
        print_warning "Found $admin_count cluster-admin role bindings"
        kubectl get clusterrolebindings -o jsonpath='{.items[?(@.roleRef.name=="cluster-admin")].metadata.name}' | tr ' ' '\n' | while read -r binding; do
            print_info "  - $binding"
        done
    else
        print_success "No excessive cluster-admin bindings found"
    fi
}

audit_service_accounts() {
    print_header "Service Account Audit"
    
    local sa_with_secrets=0
    
    # Get target namespaces
    local namespaces
    if [[ -n "$NAMESPACE" ]]; then
        namespaces="$NAMESPACE"
    else
        namespaces=$(kubectl get ns -o jsonpath='{.items[*].metadata.name}')
    fi
    
    for ns in $namespaces; do
        local sas=$(kubectl get sa -n "$ns" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null)
        
        for sa in $sas; do
            # Check if service account has token secret
            local token_secrets=$(kubectl get sa "$sa" -n "$ns" -o jsonpath='{.secrets[*].name}' 2>/dev/null)
            
            if [[ -n "$token_secrets" ]]; then
                ((sa_with_secrets++))
                [[ "$VERBOSE" == true ]] && print_info "Service account '$sa' in namespace '$ns' has token secret"
            fi
        done
    done
    
    print_success "Found $sa_with_secrets service accounts with token secrets"
}

audit_pod_security() {
    print_header "Pod Security Audit"
    
    local namespaces
    if [[ -n "$NAMESPACE" ]]; then
        namespaces="$NAMESPACE"
    else
        namespaces=$(kubectl get ns -o jsonpath='{.items[*].metadata.name}')
    fi
    
    local pods_privileged=0
    local pods_root_user=0
    local pods_no_limits=0
    
    for ns in $namespaces; do
        # Check for privileged pods
        while IFS= read -r pod; do
            if [[ -n "$pod" ]]; then
                ((pods_privileged++))
                print_warning "Pod '$pod' in namespace '$ns' running in privileged mode"
            fi
        done < <(kubectl get pods -n "$ns" -o jsonpath='{.items[?(@.spec.containers[*].securityContext.privileged==true)].metadata.name}' 2>/dev/null)
        
        # Check for pods running as root
        while IFS= read -r pod; do
            if [[ -n "$pod" ]]; then
                ((pods_root_user++))
                print_warning "Pod '$pod' in namespace '$ns' running as root user"
            fi
        done < <(kubectl get pods -n "$ns" -o jsonpath='{.items[?(@.spec.containers[*].securityContext.runAsUser==0)].metadata.name}' 2>/dev/null)
        
        # Check for pods without resource limits
        while IFS= read -r pod; do
            if [[ -n "$pod" ]]; then
                ((pods_no_limits++))
                print_warning "Pod '$pod' in namespace '$ns' has no resource limits"
            fi
        done < <(kubectl get pods -n "$ns" -o jsonpath='{.items[?(!@.spec.containers[0].resources.limits)].metadata.name}' 2>/dev/null)
    done
    
    [[ $pods_privileged -eq 0 ]] && print_success "No privileged pods found"
    [[ $pods_root_user -eq 0 ]] && print_success "No pods running as root found"
    [[ $pods_no_limits -eq 0 ]] && print_success "All pods have resource limits"
}

audit_network_policies() {
    print_header "Network Policy Audit"
    
    local namespaces
    if [[ -n "$NAMESPACE" ]]; then
        namespaces="$NAMESPACE"
    else
        namespaces=$(kubectl get ns -o jsonpath='{.items[*].metadata.name}')
    fi
    
    local policy_count=0
    for ns in $namespaces; do
        local ns_policies=$(kubectl get networkpolicies -n "$ns" --no-headers 2>/dev/null | wc -l)
        policy_count=$((policy_count + ns_policies))
    done
    
    if [[ $policy_count -eq 0 ]]; then
        print_warning "No network policies found - consider implementing network segmentation"
    else
        print_success "Found $policy_count network policies"
    fi
}

audit_secrets() {
    print_header "Secrets Audit"
    
    local namespaces
    if [[ -n "$NAMESPACE" ]]; then
        namespaces="$NAMESPACE"
    else
        namespaces=$(kubectl get ns -o jsonpath='{.items[*].metadata.name}')
    fi
    
    local secret_count=0
    for ns in $namespaces; do
        local ns_secrets=$(kubectl get secrets -n "$ns" --no-headers 2>/dev/null | wc -l)
        secret_count=$((secret_count + ns_secrets))
    done
    
    print_info "Found $secret_count secrets across namespaces"
    print_warning "Ensure secrets are encrypted at rest and rotation policy is in place"
}

audit_rbac_bindings() {
    print_header "RBAC Binding Audit"
    
    local namespaces
    if [[ -n "$NAMESPACE" ]]; then
        namespaces="$NAMESPACE"
    else
        namespaces=$(kubectl get ns -o jsonpath='{.items[*].metadata.name}')
    fi
    
    local binding_count=0
    for ns in $namespaces; do
        binding_count=$((binding_count + $(kubectl get rolebindings -n "$ns" --no-headers 2>/dev/null | wc -l)))
    done
    
    print_success "Found $binding_count role bindings"
    
    # Check for bindings to system:authenticated group
    local auth_bindings=$(kubectl get clusterrolebindings -o json 2>/dev/null | \
        jq '[.items[] | select(.subjects[]?.name == "system:authenticated")] | length')
    
    if [[ $auth_bindings -gt 0 ]]; then
        print_warning "Found $auth_bindings bindings to system:authenticated group"
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    echo ""
    print_header "Kubernetes Security Audit"
    echo "Timestamp: $(date)"
    [[ -n "$NAMESPACE" ]] && print_info "Auditing namespace: $NAMESPACE" || print_info "Auditing all namespaces"
    echo ""
    
    # Run all audit checks
    check_cluster_access
    audit_rbac_permissions
    audit_service_accounts
    audit_pod_security
    audit_network_policies
    audit_secrets
    audit_rbac_bindings
    
    # Summary
    echo ""
    print_header "Audit Summary"
    if [[ $ISSUES_FOUND -eq 0 ]]; then
        print_success "No security issues found!"
    else
        print_warning "Found $ISSUES_FOUND potential security issues"
        echo ""
        print_info "Review the findings above and address critical issues"
    fi
    echo ""
}

main "$@"
