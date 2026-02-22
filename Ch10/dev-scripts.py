#!/usr/bin/env python3
"""Development helper scripts for starter kit projects.

Provides a consistent interface for common development operations
regardless of the underlying tooling.
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import Optional


def run_command(cmd: list[str], cwd: Optional[Path] = None) -> int:
    """Run a command and return exit code."""
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def dev_start():
    """Start local development environment."""
    print("Starting development environment...")

    # Check if docker-compose exists
    compose_file = Path("docker-compose.yml")
    if compose_file.exists():
        return run_command(["docker", "compose", "up", "--build"])
    else:
        return run_command(["npm", "run", "dev"])


def dev_test(watch: bool = False):
    """Run tests."""
    cmd = ["npm", "run", "test:watch"] if watch else ["npm", "test"]
    return run_command(cmd)


def dev_lint(fix: bool = False):
    """Run linting."""
    cmd = ["npm", "run", "lint:fix"] if fix else ["npm", "run", "lint"]
    return run_command(cmd)


def dev_db_migrate():
    """Run database migrations."""
    return run_command(["npm", "run", "db:migrate"])


def dev_db_seed():
    """Seed database with test data."""
    return run_command(["npm", "run", "db:seed"])


def dev_clean():
    """Clean build artifacts and dependencies."""
    print("Cleaning project...")

    dirs_to_remove = ["node_modules", "dist", ".turbo", "coverage"]
    for dir_name in dirs_to_remove:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"  Removing {dir_name}/")
            import shutil
            shutil.rmtree(dir_path)

    # Stop docker containers
    if Path("docker-compose.yml").exists():
        run_command(["docker", "compose", "down", "-v"])

    print("Clean complete!")
    return 0


def dev_validate():
    """Validate project configuration."""
    print("Validating project configuration...")

    checks = [
        ("package.json exists", Path("package.json").exists()),
        ("Dockerfile exists", Path("Dockerfile").exists()),
        ("CI workflow exists", Path(".github/workflows/ci.yml").exists()),
        ("README exists", Path("README.md").exists()),
    ]

    all_passed = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  [{status}] {name}")
        if not passed:
            all_passed = False

    return 0 if all_passed else 1


if __name__ == "__main__":
    commands = {
        "start": dev_start,
        "test": lambda: dev_test(watch="--watch" in sys.argv),
        "lint": lambda: dev_lint(fix="--fix" in sys.argv),
        "db:migrate": dev_db_migrate,
        "db:seed": dev_db_seed,
        "clean": dev_clean,
        "validate": dev_validate,
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Usage: dev.py <command>")
        print("Commands:", ", ".join(commands.keys()))
        sys.exit(1)

    sys.exit(commands[sys.argv[1]]())
