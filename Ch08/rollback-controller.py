#!/usr/bin/env python3
"""
Chapter 8: Automated Rollback Controller
==========================================
Monitors deployment health and triggers automatic rollback
when error thresholds are exceeded.

Usage:
    python rollback-controller.py --deployment <name> --namespace <ns> [--demo]
"""

import json
import subprocess
import sys
import time
from dataclasses import dataclass


@dataclass
class RollbackConfig:
    """Configuration for rollback thresholds."""
    deployment: str = "demo-app"
    namespace: str = "default"
    error_rate_threshold: float = 5.0     # Percent error rate to trigger rollback
    check_interval_seconds: int = 10
    max_checks: int = 30
    min_ready_ratio: float = 0.8          # 80% of pods must be ready


def run_kubectl(args: list) -> str:
    try:
        r = subprocess.run(["kubectl"] + args, capture_output=True, text=True, timeout=30)
        return r.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def check_deployment_health(config: RollbackConfig) -> dict:
    """Check deployment health status."""
    output = run_kubectl([
        "get", "deployment", config.deployment,
        "-n", config.namespace, "-o", "json"
    ])
    if not output:
        return {"healthy": False, "reason": "Cannot reach cluster"}

    data = json.loads(output)
    status = data.get("status", {})
    desired = status.get("replicas", 0)
    ready = status.get("readyReplicas", 0)
    available = status.get("availableReplicas", 0)

    ready_ratio = ready / desired if desired > 0 else 0
    healthy = ready_ratio >= config.min_ready_ratio

    return {
        "healthy": healthy,
        "desired": desired,
        "ready": ready,
        "available": available,
        "ready_ratio": ready_ratio,
        "reason": "OK" if healthy else f"Only {ready}/{desired} pods ready",
    }


def rollback_deployment(config: RollbackConfig) -> bool:
    """Execute rollback to previous revision."""
    print(f"  ROLLING BACK {config.deployment} in {config.namespace}...")
    output = run_kubectl([
        "rollout", "undo", "deployment", config.deployment,
        "-n", config.namespace
    ])
    return "rolled back" in output.lower() if output else False


def demo_mode():
    """Simulate rollback monitoring cycle."""
    print("\n--- Demo: Rollback Controller Simulation ---\n")
    states = [
        {"check": 1, "ready": 3, "desired": 3, "status": "Healthy"},
        {"check": 2, "ready": 2, "desired": 3, "status": "Degraded"},
        {"check": 3, "ready": 1, "desired": 3, "status": "CRITICAL - Triggering rollback"},
        {"check": 4, "ready": 3, "desired": 3, "status": "Rollback complete - Healthy"},
    ]
    for s in states:
        print(f"  Check #{s['check']}: {s['ready']}/{s['desired']} ready - {s['status']}")
        time.sleep(1)
    print("\n  Rollback completed successfully.\n")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo_mode()
    else:
        config = RollbackConfig()
        for i, arg in enumerate(sys.argv):
            if arg == "--deployment" and i + 1 < len(sys.argv):
                config.deployment = sys.argv[i + 1]
            elif arg == "--namespace" and i + 1 < len(sys.argv):
                config.namespace = sys.argv[i + 1]

        print(f"Monitoring {config.deployment} in {config.namespace}...")
        for check in range(config.max_checks):
            health = check_deployment_health(config)
            print(f"  Check #{check+1}: {health['reason']}")
            if not health["healthy"]:
                rollback_deployment(config)
                break
            time.sleep(config.check_interval_seconds)
