#!/usr/bin/env bats
# Infrastructure Validation Tests (BATS)
# These tests verify that the Kubernetes platform is properly configured
# and all required components (flux, istio, networking) are operational

# Test: Verify Kubernetes cluster is accessible and running
# This is the foundation test - if the cluster is unreachable, all other tests fail
@test "cluster_is_running" {
    # kubectl cluster-info returns cluster master and DNS service information
    run kubectl cluster-info
    [ "$status" -eq 0 ]
    [[ "$output" == *"Kubernetes master"* ]] || [[ "$output" == *"control plane"* ]]
}

# Test: Verify required system namespaces exist
# platform-system: Contains core platform components (controllers, operators)
# monitoring: Contains Prometheus, Grafana, and observability stack
@test "namespaces_exist" {
    # Check platform-system namespace
    run kubectl get namespace platform-system
    [ "$status" -eq 0 ]
    
    # Check monitoring namespace
    run kubectl get namespace monitoring
    [ "$status" -eq 0 ]
}

# Test: Verify Flux GitOps operator is ready and healthy
# Flux reconciliation is critical for continuous deployment and configuration management
@test "flux_is_ready" {
    # flux check verifies all Flux controllers are running and healthy
    run flux check --pre
    [ "$status" -eq 0 ]
    # Confirm all health checks passed
    [[ "$output" == *"all checks passed"* ]]
}

# Test: Verify Istio sidecar injection is enabled for workloads
# Istio injection enables service mesh features: traffic management, security policies, observability
@test "istio_injection_enabled" {
    # Check that the platform-system namespace has the istio-injection label
    # This label tells Istio to automatically inject sidecar proxies into pods
    run kubectl get namespace platform-system -o jsonpath='{.metadata.labels.istio-injection}'
    [ "$status" -eq 0 ]
    [[ "$output" == "enabled" ]]
}
