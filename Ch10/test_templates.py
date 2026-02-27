#!/usr/bin/env python3
"""Test suite for starter kit templates."""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
import pytest
import yaml
import requests

TEMPLATES_DIR = Path(__file__).parent / "templates"


def get_template_versions():
    """Get all template/version combinations."""
    templates = []
    for template_dir in TEMPLATES_DIR.iterdir():
        if not template_dir.is_dir():
            continue
        for version_dir in template_dir.iterdir():
            if version_dir.is_dir() and version_dir.name.startswith("v"):
                templates.append((template_dir.name, version_dir.name))
    return templates


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    dir_path = tempfile.mkdtemp()
    yield Path(dir_path)
    shutil.rmtree(dir_path)


@pytest.mark.parametrize("template_name,version", get_template_versions())
class TestTemplateStructure:
    """Structural tests for each template version."""

    def test_template_yaml_valid(self, template_name, version):
        """Validate Backstage template YAML."""
        template_path = TEMPLATES_DIR / template_name / version
        template_file = template_path / "template.yaml"

        assert template_file.exists(), "template.yaml missing"

        with open(template_file) as f:
            template = yaml.safe_load(f)

        assert template.get("apiVersion") == "scaffolder.backstage.io/v1beta3"
        assert template.get("kind") == "Template"
        assert template.get("metadata", {}).get("name")
        assert template.get("spec", {}).get("parameters")
        assert template.get("spec", {}).get("steps")

    def test_required_files_exist(self, template_name, version):
        """Check required template files exist."""
        template_path = TEMPLATES_DIR / template_name / version / "skeleton"

        required_files = [
            "README.md",
            "Dockerfile",
        ]

        if "backend" in template_name:
            required_files.extend([
                "package.json",
                "tsconfig.json",
                ".github/workflows/ci.yml"
            ])

        for file_name in required_files:
            file_path = template_path / file_name
            assert file_path.exists(), f"Missing required file: {file_name}"


@pytest.mark.parametrize("template_name,version", get_template_versions())
class TestTemplateGeneration:
    """Functional tests that generate and validate projects."""

    def test_generated_project_builds(self, template_name, version, temp_dir):
        """Verify generated project builds successfully."""
        skeleton_path = TEMPLATES_DIR / template_name / version / "skeleton"
        project_path = temp_dir / "test-project"

        # Copy skeleton (simulating generation without variable substitution)
        shutil.copytree(skeleton_path, project_path)

        # Substitute variables manually for testing
        self._substitute_variables(project_path, {
            "serviceName": "test-project",
            "team": "test-team",
            "description": "Test project",
            "port": "8080",
            "templateVersion": "1.0.0",
            "year": "2024"
        })

        # Install dependencies
        result = subprocess.run(
            ["npm", "install"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"npm install failed: {result.stderr}"

        # Run build
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Build failed: {result.stderr}"

    def test_generated_project_passes_lint(self, template_name, version, temp_dir):
        """Verify generated project passes linting."""
        skeleton_path = TEMPLATES_DIR / template_name / version / "skeleton"
        project_path = temp_dir / "lint-test"

        shutil.copytree(skeleton_path, project_path)
        self._substitute_variables(project_path, {
            "serviceName": "lint-test",
            "team": "test-team",
            "description": "Lint test",
            "port": "8080",
            "templateVersion": "1.0.0",
            "year": "2024"
        })

        subprocess.run(["npm", "install"], cwd=project_path, capture_output=True)
        result = subprocess.run(
            ["npm", "run", "lint"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Lint failed: {result.stderr}"

    def test_generated_project_tests_pass(self, template_name, version, temp_dir):
        """Verify generated project's tests pass."""
        skeleton_path = TEMPLATES_DIR / template_name / version / "skeleton"
        project_path = temp_dir / "test-test"

        shutil.copytree(skeleton_path, project_path)
        self._substitute_variables(project_path, {
            "serviceName": "test-test",
            "team": "test-team",
            "description": "Test test",
            "port": "8080",
            "templateVersion": "1.0.0",
            "year": "2024"
        })

        subprocess.run(["npm", "install"], cwd=project_path, capture_output=True)
        result = subprocess.run(
            ["npm", "test"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Tests failed: {result.stderr}"

    def test_health_endpoint_responds(self, template_name, version, temp_dir):
        """Verify the application's health endpoint actually responds."""
        if "backend" not in template_name:
            pytest.skip("Health check only applies to backend services")

        skeleton_path = TEMPLATES_DIR / template_name / version / "skeleton"
        project_path = temp_dir / "health-test"

        shutil.copytree(skeleton_path, project_path)
        self._substitute_variables(project_path, {
            "serviceName": "health-test",
            "team": "test-team",
            "description": "Health test",
            "port": "8080",
            "templateVersion": "1.0.0",
            "year": "2024"
        })

        subprocess.run(["npm", "install"], cwd=project_path, capture_output=True)
        subprocess.run(["npm", "run", "build"], cwd=project_path, capture_output=True)

        # Start the application
        proc = subprocess.Popen(
            ["npm", "start"],
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        try:
            # Wait for startup
            time.sleep(5)

            # Check health endpoint
            response = requests.get("http://localhost:8080/health", timeout=5)
            assert response.status_code == 200, f"Health check failed: {response.status_code}"
        finally:
            proc.terminate()
            proc.wait()

    def _substitute_variables(self, project_path: Path, values: dict):
        """Replace template variables in all files."""
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                try:
                    content = file_path.read_text()
                    for key, value in values.items():
                        content = content.replace(f"${{{{ values.{key} }}}}", value)
                    file_path.write_text(content)
                except UnicodeDecodeError:
                    pass  # Skip binary files
