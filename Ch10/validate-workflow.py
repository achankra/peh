#!/usr/bin/env python3
"""Validate the complete starter kit workflow.

Tests the entire journey from project generation to deployment readiness:
1. Project generation
2. Local development (build, test, lint)
3. Container build
4. Catalog registration validity
"""

import subprocess
import time
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path = None) -> tuple[int, str]:
    """Run command and return exit code and output."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def validate_generation():
    """Validate project generation."""
    print("Testing project generation...")

    code, output = run([
        "npx", "yo", "@platform/backend-service",
        "--name", "workflow-test",
        "--team", "test-team",
        "--database", "postgresql",
        "--no-install"
    ])

    if code != 0:
        print(f"Generation failed: {output}")
        return False

    project_path = Path("workflow-test")
    required_files = [
        "package.json",
        "Dockerfile",
        "docker-compose.yml",
        ".github/workflows/ci.yml",
        "infrastructure/database.yaml",
        "catalog-info.yaml"
    ]

    for file_name in required_files:
        if not (project_path / file_name).exists():
            print(f"Missing file: {file_name}")
            return False

    print("✓ Generation: PASSED")
    return True


def validate_local_dev():
    """Validate local development workflow."""
    print("Testing local development...")

    project_path = Path("workflow-test")

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

    print("✓ Local development: PASSED")
    return True


def validate_container_build():
    """Validate container builds successfully."""
    print("Testing container build...")

    project_path = Path("workflow-test")

    code, output = run([
        "docker", "build",
        "-t", "workflow-test:local",
        "."
    ], cwd=project_path)

    if code != 0:
        print(f"Container build failed: {output}")
        return False

    print("✓ Container build: PASSED")
    return True


def validate_catalog_registration():
    """Validate catalog-info.yaml is valid."""
    print("Testing catalog registration...")

    project_path = Path("workflow-test")
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

    print("✓ Catalog registration: PASSED")
    return True


def cleanup():
    """Clean up test artifacts."""
    import shutil
    project_path = Path("workflow-test")
    if project_path.exists():
        shutil.rmtree(project_path)


def main():
    cleanup()

    tests = [
        validate_generation,
        validate_local_dev,
        validate_container_build,
        validate_catalog_registration
    ]

    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
            break

    cleanup()

    if all_passed:
        print("\n✓ All workflow validations PASSED!")
        return 0
    else:
        print("\n✗ Workflow validation FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
