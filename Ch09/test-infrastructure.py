#!/usr/bin/env python3
"""Test infrastructure provisioning and connectivity.

This script validates the complete infrastructure workflow:
1. Apply PostgreSQL claim
2. Wait for claim to become ready
3. Verify connection secret was created
4. Verify application can connect to database
"""

import subprocess
import time
import sys
from typing import Optional


def run_kubectl(args: list[str]) -> tuple[int, str, str]:
    """Run kubectl command and return exit code, stdout, stderr."""
    result = subprocess.run(
        ["kubectl"] + args,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def wait_for_claim_ready(
    name: str,
    namespace: str,
    timeout: int = 300
) -> bool:
    """Wait for PostgreSQL claim to become ready."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        code, stdout, _ = run_kubectl([
            "get", "postgresqlclaim", name,
            "-n", namespace,
            "-o", "jsonpath={.status.conditions[?(@.type=='Ready')].status}"
        ])

        if code == 0 and stdout.strip() == "True":
            return True

        print(f"Waiting for claim {name} to be ready...")
        time.sleep(10)

    return False


def verify_secret_exists(name: str, namespace: str) -> bool:
    """Verify connection secret was created."""
    code, _, _ = run_kubectl([
        "get", "secret", name, "-n", namespace
    ])
    return code == 0


def verify_app_connectivity(namespace: str) -> bool:
    """Verify application can connect to database."""
    code, stdout, _ = run_kubectl([
        "exec", "-n", namespace,
        "deployment/demo-app", "--",
        "curl", "-s", "localhost:8080/health"
    ])

    if code != 0:
        return False

    return "database" in stdout.lower() and "connected" in stdout.lower()


def main():
    namespace = "team-alpha"
    claim_name = "demo-app-db"
    secret_name = "demo-app-db-connection"

    print("Testing infrastructure provisioning...")

    # Apply the claim
    code, _, stderr = run_kubectl([
        "apply", "-f", "demo-app/infrastructure/database.yaml"
    ])
    if code != 0:
        print(f"Failed to apply claim: {stderr}")
        sys.exit(1)

    # Wait for claim to be ready
    if not wait_for_claim_ready(claim_name, namespace):
        print("Claim did not become ready in time")
        sys.exit(1)
    print("✓ Claim is ready")

    # Verify secret exists
    if not verify_secret_exists(secret_name, namespace):
        print("Connection secret was not created")
        sys.exit(1)
    print("✓ Connection secret exists")

    # Verify application connectivity
    if not verify_app_connectivity(namespace):
        print("Application cannot connect to database")
        sys.exit(1)
    print("✓ Application connected to database successfully")

    print("\n✓ All infrastructure tests passed!")


if __name__ == "__main__":
    main()
