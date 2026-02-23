#!/usr/bin/env python3

"""
Chapter 11: Custom Prometheus Exporter for Gatekeeper Audit Results
====================================================================
Queries OPA Gatekeeper audit results and exposes them as Prometheus metrics.
Enables monitoring of policy violations in real-time dashboards and alerting.

Usage:
    python gatekeeper_exporter.py [--port 8000] [--interval 30]

Arguments:
    --port PORT          Port for metrics HTTP server (default: 8000)
    --interval INTERVAL  Polling interval in seconds (default: 30)
    --namespace NS       Kubernetes namespace for Gatekeeper (default: gatekeeper-system)
    --once               Run once and exit (for testing)

Prerequisites:
    - kubectl configured with cluster access
    - OPA Gatekeeper installed (see gatekeeper-install.yaml)
    - prometheus_client library: pip install prometheus_client
    - Python 3.7+

Metrics Exposed:
    - gatekeeper_violations_total: Total violations by policy and enforcement action
    - gatekeeper_violations_by_namespace: Violations grouped by namespace
    - gatekeeper_violations_by_kind: Violations grouped by resource kind
    - gatekeeper_violations_by_severity: Violations by severity level
    - gatekeeper_audit_timestamp: Timestamp of last audit collection
    - gatekeeper_constraint_count: Number of constraint templates deployed

Example Prometheus scrape_config:
    scrape_configs:
      - job_name: 'gatekeeper'
        static_configs:
          - targets: ['localhost:8000']
        scrape_interval: 30s
        scrape_timeout: 10s

Example Grafana queries:
    - rate(gatekeeper_violations_total[5m])
    - gatekeeper_violations_by_namespace
    - sum(gatekeeper_violations_total) by (enforcement)

Example Alerting Rules:
    - alert: HighViolationRate
      expr: rate(gatekeeper_violations_total[5m]) > 0.1
      for: 5m
    - alert: CriticalViolations
      expr: gatekeeper_violations_by_severity{severity="CRITICAL"} > 0
      for: 1m
"""

import json
import subprocess
import sys
import time
import argparse
import logging
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple

# prometheus_client imports
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    start_http_server,
    CollectorRegistry,
    REGISTRY,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Prometheus Metrics Definitions
# ============================================================================

# Counter: Total violations (incremented, never decreases)
violations_total = Counter(
    "gatekeeper_violations_total",
    "Total Gatekeeper constraint violations",
    ["policy", "enforcement_action", "namespace", "resource_kind"]
)

# Gauge: Current violation count by policy
violations_by_policy = Gauge(
    "gatekeeper_violations_by_policy",
    "Current number of violations by policy",
    ["policy", "enforcement_action"]
)

# Gauge: Current violation count by namespace
violations_by_namespace = Gauge(
    "gatekeeper_violations_by_namespace",
    "Current number of violations by namespace",
    ["namespace"]
)

# Gauge: Current violation count by resource kind
violations_by_kind = Gauge(
    "gatekeeper_violations_by_kind",
    "Current number of violations by resource kind",
    ["kind"]
)

# Gauge: Violations by severity level
violations_by_severity = Gauge(
    "gatekeeper_violations_by_severity",
    "Current number of violations by severity",
    ["severity"]
)

# Gauge: Number of constraint templates
constraint_count = Gauge(
    "gatekeeper_constraint_count",
    "Number of Gatekeeper constraint templates deployed"
)

# Gauge: Last audit timestamp
audit_timestamp = Gauge(
    "gatekeeper_audit_timestamp",
    "Timestamp of last audit collection (seconds since epoch)"
)

# Histogram: Time to collect violations
collection_duration = Histogram(
    "gatekeeper_collection_duration_seconds",
    "Time taken to collect audit results from cluster"
)

# Counter: Collection errors
collection_errors = Counter(
    "gatekeeper_collection_errors_total",
    "Number of errors while collecting metrics",
    ["error_type"]
)


# ============================================================================
# Gatekeeper Data Collection
# ============================================================================

def run_kubectl(args: List[str], timeout: int = 30) -> Dict:
    """Execute a kubectl command and return parsed JSON output."""
    cmd = ["kubectl"] + args + ["-o", "json"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0:
            logger.warning(f"kubectl command failed: {result.stderr.strip()}")
            collection_errors.labels(error_type="kubectl_error").inc()
            return {}
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except subprocess.TimeoutExpired:
        logger.error(f"kubectl command timed out after {timeout}s")
        collection_errors.labels(error_type="timeout").inc()
        return {}
    except FileNotFoundError:
        logger.error("kubectl not found in PATH")
        collection_errors.labels(error_type="kubectl_not_found").inc()
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON output: {e}")
        collection_errors.labels(error_type="json_error").inc()
        return {}


def get_constraint_templates() -> List[Dict]:
    """Retrieve all Gatekeeper ConstraintTemplates from the cluster."""
    data = run_kubectl(["get", "constrainttemplates"])
    return data.get("items", [])


def get_constraints() -> List[Dict]:
    """Retrieve all Gatekeeper constraints and their audit results."""
    templates = get_constraint_templates()
    all_constraints = []

    for template in templates:
        kind = (
            template.get("spec", {})
            .get("crd", {})
            .get("spec", {})
            .get("names", {})
            .get("kind", "")
        )
        if kind:
            data = run_kubectl(["get", kind.lower(), "--all-namespaces"])
            all_constraints.extend(data.get("items", []))

    return all_constraints


def classify_severity(policy_kind: str, enforcement: str) -> str:
    """Classify violation severity based on policy kind and enforcement."""
    critical_keywords = ["privileged", "secret", "registry", "security"]

    if any(kw in policy_kind.lower() for kw in critical_keywords):
        if enforcement == "deny":
            return "CRITICAL"
        if enforcement == "dryrun":
            return "HIGH"

    if enforcement == "deny":
        return "HIGH"
    if enforcement == "dryrun":
        return "MEDIUM"

    return "LOW"


def parse_violations(constraints: List[Dict]) -> List[Dict]:
    """Extract violations from constraint audit results."""
    violations = []

    for constraint in constraints:
        kind = constraint.get("kind", "Unknown")
        name = constraint.get("metadata", {}).get("name", "Unknown")
        enforcement = constraint.get("spec", {}).get("enforcementAction", "deny")

        # Gatekeeper stores audit results in status.violations
        audit_violations = constraint.get("status", {}).get("violations", [])

        for v in audit_violations:
            violation = {
                "policy": f"{kind}/{name}",
                "policy_kind": kind,
                "policy_name": name,
                "enforcement": enforcement,
                "namespace": v.get("namespace", "cluster-scoped"),
                "resource_kind": v.get("kind", "Unknown"),
                "resource_name": v.get("name", "Unknown"),
                "message": v.get("message", "No message"),
                "severity": classify_severity(kind, enforcement),
            }
            violations.append(violation)

    return violations


# ============================================================================
# Metrics Update
# ============================================================================

def update_metrics(gatekeeper_namespace: str = "gatekeeper-system") -> Tuple[int, int]:
    """
    Collect Gatekeeper audit results and update all Prometheus metrics.

    Returns:
        Tuple of (total_violations, constraint_count)
    """
    start_time = time.time()

    try:
        logger.info("Collecting Gatekeeper audit results...")

        # Get constraint templates
        templates = get_constraint_templates()
        constraint_count.set(len(templates))
        logger.info(f"Found {len(templates)} constraint templates")

        # Get constraints and violations
        constraints = get_constraints()
        violations = parse_violations(constraints)
        total_violations = len(violations)

        logger.info(f"Found {total_violations} violations across {len(constraints)} constraints")

        # Reset gauges before updating
        violations_by_policy.clear()
        violations_by_namespace.clear()
        violations_by_kind.clear()
        violations_by_severity.clear()

        # Aggregate violations
        policy_counts: Dict[Tuple[str, str], int] = defaultdict(int)
        namespace_counts: Dict[str, int] = defaultdict(int)
        kind_counts: Dict[str, int] = defaultdict(int)
        severity_counts: Dict[str, int] = defaultdict(int)

        for v in violations:
            # Count by policy and enforcement
            policy_key = (v["policy"], v["enforcement"])
            policy_counts[policy_key] += 1

            # Count by namespace
            namespace_counts[v["namespace"]] += 1

            # Count by resource kind
            kind_counts[v["resource_kind"]] += 1

            # Count by severity
            severity_counts[v["severity"]] += 1

            # Increment counter (permanent record)
            violations_total.labels(
                policy=v["policy"],
                enforcement_action=v["enforcement"],
                namespace=v["namespace"],
                resource_kind=v["resource_kind"]
            ).inc()

        # Update gauges
        for (policy, enforcement), count in policy_counts.items():
            violations_by_policy.labels(
                policy=policy,
                enforcement_action=enforcement
            ).set(count)

        for namespace, count in namespace_counts.items():
            violations_by_namespace.labels(namespace=namespace).set(count)

        for kind, count in kind_counts.items():
            violations_by_kind.labels(kind=kind).set(count)

        for severity, count in severity_counts.items():
            violations_by_severity.labels(severity=severity).set(count)

        # Update timestamp
        audit_timestamp.set(time.time())

        # Record collection duration
        duration = time.time() - start_time
        collection_duration.observe(duration)

        logger.info(
            f"Metrics updated successfully "
            f"({duration:.2f}s, {total_violations} violations)"
        )

        return total_violations, len(templates)

    except Exception as e:
        logger.error(f"Error updating metrics: {e}")
        collection_errors.labels(error_type="processing_error").inc()
        return 0, 0


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Prometheus exporter for OPA Gatekeeper audit results"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for metrics HTTP server (default: 8000)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Polling interval in seconds (default: 30)"
    )
    parser.add_argument(
        "--namespace",
        type=str,
        default="gatekeeper-system",
        help="Kubernetes namespace for Gatekeeper (default: gatekeeper-system)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (for testing)"
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("Gatekeeper Prometheus Exporter")
    logger.info("=" * 70)
    logger.info(f"Metrics port: {args.port}")
    logger.info(f"Polling interval: {args.interval}s")
    logger.info(f"Gatekeeper namespace: {args.namespace}")
    logger.info(f"Once mode: {args.once}")
    logger.info("=" * 70)

    # Start Prometheus metrics HTTP server
    logger.info(f"Starting metrics server on port {args.port}...")
    start_http_server(args.port)
    logger.info(f"Metrics available at http://localhost:{args.port}/metrics")

    # Run once for testing
    if args.once:
        logger.info("Running once mode (exiting after collection)...")
        violations, templates = update_metrics(args.namespace)
        logger.info(f"Collected {violations} violations from {templates} templates")
        sys.exit(0)

    # Continuous polling loop
    logger.info("Starting continuous polling loop...")
    try:
        while True:
            try:
                violations, templates = update_metrics(args.namespace)
                logger.info(
                    f"Next collection in {args.interval}s "
                    f"({violations} violations, {templates} templates)"
                )
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                collection_errors.labels(error_type="loop_error").inc()

            time.sleep(args.interval)

    except KeyboardInterrupt:
        logger.info("Exporter shutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
