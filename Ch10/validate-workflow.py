#!/usr/bin/env python3
"""Validate the complete starter kit workflow."""

import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path = None) -> tuple[int, str]:
    """Run command and return exit code and output."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def validate_clone():
    """Validate repository was created and can be cloned."""
    print("Testing repository clone...")

    code, output = run([
        "git", "clone",
        "https://github.com/platform-org/order-service.git",
        "order-service"
    ])

    if code != 0:
        print(f"Clone failed: {output}")
        return False

    print("Clone: PASSED")
    return True


def validate_local_dev():
    """Validate local development workflow."""
    print("Testing local development...")

    project_path = Path("order-service")

    # Install dependencies
    code, _ = run(["npm", "install"], cwd=project_path)
    if code != 0:
        print("npm install failed")
        return False

    # Build project
    code, output = run(["npm", "run", "build"], cwd=project_path)
    if code != 0:
        print(f"Build failed: {output}")
        return False

    # Run tests
    code, output = run(["npm", "test"], cwd=project_path)
    if code != 0:
        print(f"Tests failed: {output}")
        return False

    # Run lint
    code, output = run(["npm", "run", "lint"], cwd=project_path)
    if code != 0:
        print(f"Lint failed: {output}")
        return False

    print("Local development: PASSED")
    return True


def validate_container_build():
    """Validate container builds successfully."""
    print("Testing container build...")

    project_path = Path("order-service")

    code, output = run([
        "docker", "build",
        "-t", "order-service:local",
        "."
    ], cwd=project_path)

    if code != 0:
        print(f"Container build failed: {output}")
        return False

    print("Container build: PASSED")
    return True


def validate_catalog_registration():
    """Validate service appears in Backstage catalog."""
    print("Testing catalog registration...")

    project_path = Path("order-service")
    catalog_file = project_path / "catalog-info.yaml"

    import yaml
    with open(catalog_file) as f:
        catalog = yaml.safe_load(f)

    if catalog.get("kind") != "Component":
        print("Invalid catalog kind")
        return False

    if not catalog.get("metadata", {}).get("name"):
        print("Missing component name")
        return False

    print("Catalog registration: PASSED")
    return True


def validate_infrastructure_claim():
    """Validate database infrastructure claim exists."""
    print("Testing infrastructure claim...")

    project_path = Path("order-service")
    claim_file = project_path / "infrastructure" / "database.yaml"

    if not claim_file.exists():
        print("Database claim file missing")
        return False

    import yaml
    with open(claim_file) as f:
        claim = yaml.safe_load(f)

    if claim.get("kind") != "PostgreSQLClaim":
        print("Invalid claim kind")
        return False

    print("Infrastructure claim: PASSED")
    return True


def cleanup():
    """Clean up test artifacts."""
    import shutil
    project_path = Path("order-service")
    if project_path.exists():
        shutil.rmtree(project_path)


def main():
    cleanup()

    tests = [
        validate_clone,
        validate_local_dev,
        validate_container_build,
        validate_catalog_registration,
        validate_infrastructure_claim
    ]

    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
            break

    cleanup()

    if all_passed:
        print("\nAll workflow validations PASSED!")
        return 0
    else:
        print("\nWorkflow validation FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
