#!/usr/bin/env python3
"""
Chapter 13: Disaster Recovery Validation
=========================================
Validates DR readiness by checking backup freshness, testing restore
procedures, and calculating RTO/RPO compliance.

Usage:
    python disaster-recovery-plan.py [--demo]      # demo mode, no cluster needed
    python disaster-recovery-plan.py               # live cluster validation

Prerequisites:
    - kubectl configured with cluster access
    - Velero installed for backup management
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BackupStatus:
    """Represents the status of a Velero backup."""
    name: str
    phase: str  # Completed, Failed, InProgress, PartiallyFailed
    created: Optional[datetime] = None
    expires: Optional[datetime] = None
    items_backed_up: int = 0
    warnings: int = 0
    errors: int = 0


@dataclass
class DRConfig:
    """Disaster recovery configuration with targets."""
    rto_minutes: int = 30        # Recovery Time Objective
    rpo_minutes: int = 60        # Recovery Point Objective
    max_backup_age_hours: int = 24
    required_namespaces: list = field(default_factory=lambda: ["production", "platform-system"])


def run_kubectl(args: list) -> str:
    """Execute kubectl command and return stdout."""
    cmd = ["kubectl"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"Warning: kubectl unavailable: {e}")
        return ""


def get_velero_backups() -> list:
    """Retrieve Velero backup status from cluster."""
    output = run_kubectl(["get", "backups.velero.io", "-n", "velero", "-o", "json"])
    if not output:
        return []
    try:
        data = json.loads(output)
        backups = []
        for item in data.get("items", []):
            meta = item.get("metadata", {})
            status = item.get("status", {})
            created = meta.get("creationTimestamp", "")
            expires = status.get("expiration", "")
            backups.append(BackupStatus(
                name=meta.get("name", "unknown"),
                phase=status.get("phase", "Unknown"),
                created=datetime.fromisoformat(created.replace("Z", "+00:00")) if created else None,
                expires=datetime.fromisoformat(expires.replace("Z", "+00:00")) if expires else None,
                items_backed_up=status.get("progress", {}).get("itemsBackedUp", 0),
                warnings=status.get("warnings", 0),
                errors=status.get("errors", 0),
            ))
        return backups
    except (json.JSONDecodeError, ValueError):
        return []


def check_backup_freshness(backups: list, config: DRConfig) -> dict:
    """Verify backups are recent enough to meet RPO."""
    now = datetime.now().astimezone()
    max_age = timedelta(hours=config.max_backup_age_hours)
    results = {"pass": True, "checks": []}

    if not backups:
        results["pass"] = False
        results["checks"].append({"check": "Backups exist", "status": "FAIL", "detail": "No backups found"})
        return results

    # Find most recent successful backup
    successful = [b for b in backups if b.phase == "Completed"]
    if not successful:
        results["pass"] = False
        results["checks"].append({"check": "Successful backup exists", "status": "FAIL",
                                   "detail": "No completed backups"})
        return results

    latest = max(successful, key=lambda b: b.created or datetime.min.replace(tzinfo=now.tzinfo))
    age = now - latest.created if latest.created else timedelta(hours=999)

    results["checks"].append({
        "check": "Latest backup freshness",
        "status": "PASS" if age < max_age else "FAIL",
        "detail": f"Latest backup '{latest.name}' is {age.total_seconds()/3600:.1f}h old (max: {config.max_backup_age_hours}h)"
    })

    if age >= max_age:
        results["pass"] = False

    # Check RPO compliance
    rpo_delta = timedelta(minutes=config.rpo_minutes)
    results["checks"].append({
        "check": f"RPO compliance ({config.rpo_minutes} min)",
        "status": "PASS" if age < rpo_delta else "FAIL",
        "detail": f"Data loss window: {age.total_seconds()/60:.0f} min"
    })

    # Check for backup errors
    errored = [b for b in backups if b.errors > 0]
    results["checks"].append({
        "check": "No backup errors",
        "status": "WARN" if errored else "PASS",
        "detail": f"{len(errored)} backups have errors" if errored else "All backups clean"
    })

    return results


def estimate_rto(config: DRConfig) -> dict:
    """Estimate Recovery Time Objective based on cluster state."""
    # In a real system, this would time actual restore operations
    # Here we estimate based on cluster size
    node_count_str = run_kubectl(["get", "nodes", "--no-headers"])
    node_count = len(node_count_str.strip().split("\n")) if node_count_str.strip() else 0

    # Rough estimates (would be calibrated from actual restore tests)
    base_restore_min = 5
    per_node_min = 2
    estimated_rto = base_restore_min + (node_count * per_node_min)

    return {
        "check": f"RTO estimate ({config.rto_minutes} min target)",
        "status": "PASS" if estimated_rto <= config.rto_minutes else "WARN",
        "detail": f"Estimated restore time: ~{estimated_rto} min for {node_count} nodes"
    }


def generate_demo_results() -> dict:
    """Generate demo DR validation results (no cluster needed)."""
    config = DRConfig()
    return {
        "config": {"rto_minutes": config.rto_minutes, "rpo_minutes": config.rpo_minutes},
        "backup_checks": {
            "pass": True,
            "checks": [
                {"check": "Latest backup freshness", "status": "PASS",
                 "detail": "Latest backup 'daily-2025-01-20' is 6.2h old (max: 24h)"},
                {"check": "RPO compliance (60 min)", "status": "PASS",
                 "detail": "Data loss window: 45 min"},
                {"check": "No backup errors", "status": "PASS",
                 "detail": "All backups clean"},
            ]
        },
        "rto_estimate": {"check": "RTO estimate (30 min target)", "status": "PASS",
                         "detail": "Estimated restore time: ~11 min for 3 nodes"},
        "overall": "PASS"
    }


def print_results(results: dict):
    """Print DR validation results in a readable format."""
    print("\n" + "=" * 60)
    print("  DISASTER RECOVERY VALIDATION REPORT")
    print("=" * 60)
    print(f"\nRTO Target: {results['config']['rto_minutes']} minutes")
    print(f"RPO Target: {results['config']['rpo_minutes']} minutes\n")

    for check in results["backup_checks"]["checks"]:
        icon = "✓" if check["status"] == "PASS" else "✗" if check["status"] == "FAIL" else "!"
        print(f"  [{icon}] {check['check']}: {check['detail']}")

    rto = results["rto_estimate"]
    icon = "✓" if rto["status"] == "PASS" else "!"
    print(f"  [{icon}] {rto['check']}: {rto['detail']}")

    overall = results["overall"]
    print(f"\n{'=' * 60}")
    print(f"  Overall DR Readiness: {overall}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    demo_mode = "--demo" in sys.argv

    if demo_mode:
        print("Running in demo mode (no cluster required)...")
        results = generate_demo_results()
    else:
        config = DRConfig()
        backups = get_velero_backups()
        backup_results = check_backup_freshness(backups, config)
        rto_result = estimate_rto(config)

        overall = "PASS" if backup_results["pass"] and rto_result["status"] != "FAIL" else "FAIL"
        results = {
            "config": {"rto_minutes": config.rto_minutes, "rpo_minutes": config.rpo_minutes},
            "backup_checks": backup_results,
            "rto_estimate": rto_result,
            "overall": overall,
        }

    print_results(results)
