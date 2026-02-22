#!/usr/bin/env python3
"""
Chapter 11: Compliance Dashboard Generator
==========================================
Queries OPA Gatekeeper audit results and generates a compliance report
showing violations by policy, namespace, and severity.

Usage:
    python compliance-dashboard.py [--output report.md] [--format markdown|json]

Prerequisites:
    - kubectl configured with cluster access
    - OPA Gatekeeper installed (see gatekeeper-install.yaml)
"""

import json
import subprocess
import sys
import os
from datetime import datetime
from collections import defaultdict


def run_kubectl(args: list) -> dict:
    """Execute a kubectl command and return parsed JSON output."""
    cmd = ["kubectl"] + args + ["-o", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"Warning: kubectl command failed: {result.stderr.strip()}")
            return {}
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: {e}")
        return {}


def get_constraint_templates() -> list:
    """Retrieve all Gatekeeper ConstraintTemplates from the cluster."""
    data = run_kubectl(["get", "constrainttemplates"])
    return data.get("items", [])


def get_constraints() -> list:
    """Retrieve all Gatekeeper constraints and their audit results."""
    # First, get all constraint kinds from templates
    templates = get_constraint_templates()
    all_constraints = []

    for template in templates:
        kind = template.get("spec", {}).get("crd", {}).get("spec", {}).get("names", {}).get("kind", "")
        if kind:
            data = run_kubectl(["get", kind.lower(), "--all-namespaces"])
            all_constraints.extend(data.get("items", []))

    return all_constraints


def parse_violations(constraints: list) -> list:
    """Extract violations from constraint audit results."""
    violations = []
    for constraint in constraints:
        kind = constraint.get("kind", "Unknown")
        name = constraint.get("metadata", {}).get("name", "Unknown")
        enforcement = constraint.get("spec", {}).get("enforcementAction", "deny")

        # Gatekeeper stores audit results in status.violations
        audit_violations = constraint.get("status", {}).get("violations", [])
        for v in audit_violations:
            violations.append({
                "policy": f"{kind}/{name}",
                "enforcement": enforcement,
                "namespace": v.get("namespace", "cluster-scoped"),
                "resource": f"{v.get('kind', '?')}/{v.get('name', '?')}",
                "message": v.get("message", "No message"),
                "severity": _classify_severity(kind, enforcement),
            })
    return violations


def _classify_severity(kind: str, enforcement: str) -> str:
    """Classify violation severity based on policy kind and enforcement."""
    # Critical: security-related policies in deny mode
    critical_keywords = ["privileged", "secret", "registry", "security"]
    if any(kw in kind.lower() for kw in critical_keywords) and enforcement == "deny":
        return "CRITICAL"
    if enforcement == "deny":
        return "HIGH"
    if enforcement == "dryrun":
        return "MEDIUM"
    return "LOW"


def generate_markdown_report(violations: list) -> str:
    """Generate a Markdown compliance report from violations."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    total = len(violations)

    # Aggregate by policy
    by_policy = defaultdict(int)
    by_namespace = defaultdict(int)
    by_severity = defaultdict(int)
    for v in violations:
        by_policy[v["policy"]] += 1
        by_namespace[v["namespace"]] += 1
        by_severity[v["severity"]] += 1

    lines = [
        f"# Platform Compliance Report",
        f"",
        f"**Generated:** {now}",
        f"**Total Violations:** {total}",
        f"",
        f"## Summary by Severity",
        f"",
        f"| Severity | Count |",
        f"|----------|-------|",
    ]
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        lines.append(f"| {sev} | {by_severity.get(sev, 0)} |")

    lines += [
        f"",
        f"## Violations by Policy",
        f"",
        f"| Policy | Count |",
        f"|--------|-------|",
    ]
    for policy, count in sorted(by_policy.items(), key=lambda x: -x[1]):
        lines.append(f"| {policy} | {count} |")

    lines += [
        f"",
        f"## Violations by Namespace",
        f"",
        f"| Namespace | Count |",
        f"|-----------|-------|",
    ]
    for ns, count in sorted(by_namespace.items(), key=lambda x: -x[1]):
        lines.append(f"| {ns} | {count} |")

    lines += [
        f"",
        f"## Detailed Violations",
        f"",
        f"| Severity | Policy | Namespace | Resource | Message |",
        f"|----------|--------|-----------|----------|---------|",
    ]
    for v in sorted(violations, key=lambda x: ["CRITICAL","HIGH","MEDIUM","LOW"].index(x["severity"])):
        msg = v["message"][:80] + "..." if len(v["message"]) > 80 else v["message"]
        lines.append(f"| {v['severity']} | {v['policy']} | {v['namespace']} | {v['resource']} | {msg} |")

    return "\n".join(lines)


def generate_demo_report() -> str:
    """Generate a demo report with sample data (no cluster required)."""
    sample_violations = [
        {"policy": "K8sRequiredLabels/require-app-label", "enforcement": "deny",
         "namespace": "team-alpha", "resource": "Deployment/web-api",
         "message": "Missing required label: app.kubernetes.io/name", "severity": "HIGH"},
        {"policy": "K8sContainerLimits/require-limits", "enforcement": "deny",
         "namespace": "team-beta", "resource": "Deployment/worker",
         "message": "Container 'worker' has no resource limits", "severity": "HIGH"},
        {"policy": "K8sDenyPrivileged/no-privileged", "enforcement": "deny",
         "namespace": "team-alpha", "resource": "Pod/debug-pod",
         "message": "Privileged containers are not allowed", "severity": "CRITICAL"},
        {"policy": "K8sAllowedRegistries/trusted-registries", "enforcement": "dryrun",
         "namespace": "team-gamma", "resource": "Deployment/legacy-app",
         "message": "Image from untrusted registry: docker.io/random/image", "severity": "MEDIUM"},
    ]
    return generate_markdown_report(sample_violations)


if __name__ == "__main__":
    output_file = None
    demo_mode = "--demo" in sys.argv

    for i, arg in enumerate(sys.argv):
        if arg == "--output" and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]

    if demo_mode:
        print("Running in demo mode (no cluster required)...")
        report = generate_demo_report()
    else:
        print("Querying Gatekeeper audit results...")
        constraints = get_constraints()
        violations = parse_violations(constraints)
        report = generate_markdown_report(violations)

    if output_file:
        with open(output_file, "w") as f:
            f.write(report)
        print(f"Report written to {output_file}")
    else:
        print(report)
