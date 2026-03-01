#!/bin/bash

# Chapter 11: Conftest Runner Script
# ==================================
# Validates Kubernetes manifests against OPA policies using conftest
# Enables shift-left policy validation before deployment
#
# Usage:
#   ./run-conftest.sh [manifest_dir] [--strict]
#
# Examples:
#   ./run-conftest.sh .                    # Test current directory
#   ./run-conftest.sh manifests/           # Test manifests directory
#   ./run-conftest.sh . --strict           # Exit with error on any violation
#   ./run-conftest.sh test-pod-violation.yaml  # Test single file
#
# Prerequisites:
#   - conftest installed (https://www.conftest.dev/)
#   - OPA Rego policies in ./policies/ or ./conftest-tests/

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
MANIFEST_PATH="${1:-.}"
STRICT_MODE="${2:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Policy directories (only conftest-tests/ — policies/ contains Gatekeeper YAML, not standalone Rego)
CONFTEST_POLICY_DIR="${SCRIPT_DIR}/conftest-tests"

# Check if conftest is installed
if ! command -v conftest &> /dev/null; then
    echo -e "${RED}ERROR: conftest is not installed${NC}"
    echo "Install from: https://www.conftest.dev/install/"
    exit 1
fi

# Check if policy directory exists
if [ ! -d "$CONFTEST_POLICY_DIR" ]; then
    echo -e "${RED}ERROR: Policy directory not found${NC}"
    echo "Expected: $CONFTEST_POLICY_DIR"
    exit 1
fi

# Function to print header
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Find manifests to test
find_manifests() {
    if [ -f "$MANIFEST_PATH" ]; then
        # Single file provided
        echo "$MANIFEST_PATH"
    elif [ -d "$MANIFEST_PATH" ]; then
        # Directory provided - find YAML files
        find "$MANIFEST_PATH" -type f \( -name "*.yaml" -o -name "*.yml" \) \
            ! -path '*/.*' \
            ! -path '*/__pycache__/*' \
            2>/dev/null || true
    else
        echo ""
    fi
}

# Main validation function
run_validation() {
    local manifest="$1"
    local policy_opts=""

    # Build policy options
    policy_opts="-p $CONFTEST_POLICY_DIR"

    # Run conftest
    echo "Testing: $manifest"

    if conftest test $policy_opts "$manifest" 2>&1; then
        print_success "PASSED: $manifest"
        return 0
    else
        print_error "FAILED: $manifest"
        return 1
    fi
}

# Main execution
main() {
    print_header "Conftest Policy Validation"

    echo "Script directory: $SCRIPT_DIR"
    echo "Manifest path: $MANIFEST_PATH"
    echo "Policy directory: $CONFTEST_POLICY_DIR"
    echo ""

    # Find all manifests
    manifests=$(find_manifests)

    if [ -z "$manifests" ]; then
        print_error "No YAML manifests found in $MANIFEST_PATH"
        exit 1
    fi

    # Count manifests
    manifest_count=$(echo "$manifests" | wc -l)
    echo "Found $manifest_count manifest(s) to validate"
    echo ""

    # Track results
    passed=0
    failed=0
    failed_manifests=()

    # Test each manifest
    while IFS= read -r manifest; do
        [ -z "$manifest" ] && continue

        if run_validation "$manifest"; then
            ((passed++))
        else
            ((failed++))
            failed_manifests+=("$manifest")
        fi
        echo ""
    done <<< "$manifests"

    # Print summary
    print_header "Validation Summary"

    echo "Total:  $manifest_count"
    echo "Passed: $((passed))"
    echo "Failed: $((failed))"
    echo ""

    if [ $failed -gt 0 ]; then
        print_error "Failed manifests:"
        printf '%s\n' "${failed_manifests[@]}" | sed 's/^/  - /'
        echo ""

        if [ "$STRICT_MODE" = "--strict" ]; then
            print_error "STRICT MODE: Exiting with failure due to policy violations"
            exit 1
        else
            print_warning "Run with --strict flag to exit with error on violations"
            exit 0
        fi
    else
        print_success "All manifests passed validation!"
        exit 0
    fi
}

# Run main function
main "$@"
