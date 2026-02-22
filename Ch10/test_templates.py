#!/usr/bin/env python3
"""Test suite for starter kit templates.

Validates that templates:
- Have valid Backstage YAML
- Contain required files
- Generate valid projects that build and pass linting
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import pytest
import yaml

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


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
class TestTemplate:
    """Tests for each template version."""

    def test_backstage_yaml_valid(self, template_name, version):
        """Validate Backstage template YAML."""
        template_path = TEMPLATES_DIR / template_name / version
        backstage_file = template_path / "backstage" / "template.yaml"

        assert backstage_file.exists(), "backstage/template.yaml missing"

        with open(backstage_file) as f:
            template = yaml.safe_load(f)

        assert template.get("apiVersion") == "scaffolder.backstage.io/v1beta3"
        assert template.get("kind") == "Template"
        assert template.get("metadata", {}).get("name")
        assert template.get("spec", {}).get("parameters")
        assert template.get("spec", {}).get("steps")

    def test_required_files_exist(self, template_name, version):
        """Check required template files exist."""
        template_path = TEMPLATES_DIR / template_name / version / "template"

        required_files = [
            "README.md.ejs",
            "Dockerfile.ejs",
        ]

        if "backend" in template_name:
            required_files.extend([
                "package.json.ejs",
                "tsconfig.json",
                ".github/workflows/ci.yml.ejs"
            ])

        for file_name in required_files:
            file_path = template_path / file_name
            assert file_path.exists(), f"Missing required file: {file_name}"

    def test_generator_produces_valid_project(self, template_name, version, temp_dir):
        """Generate a project and validate it."""
        generator_path = TEMPLATES_DIR / template_name / version / "generator"

        if not (generator_path / "index.js").exists():
            pytest.skip("No Yeoman generator found")

        # Run generator
        result = subprocess.run(
            [
                "yo", str(generator_path),
                "--name", "test-service",
                "--team", "test-team",
                "--database", "none",
                "--no-install"
            ],
            cwd=temp_dir,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Generator failed: {result.stderr}"

        project_path = temp_dir / "test-service"
        assert project_path.exists(), "Generated project not found"

        # Check key files exist
        assert (project_path / "package.json").exists()
        assert (project_path / "Dockerfile").exists()
        assert (project_path / "README.md").exists()

    def test_generated_project_builds(self, template_name, version, temp_dir):
        """Verify generated project builds successfully."""
        generator_path = TEMPLATES_DIR / template_name / version / "generator"

        if not (generator_path / "index.js").exists():
            pytest.skip("No Yeoman generator found")

        # Generate project
        subprocess.run(
            [
                "yo", str(generator_path),
                "--name", "build-test",
                "--team", "test-team",
                "--database", "none"
            ],
            cwd=temp_dir,
            capture_output=True
        )

        project_path = temp_dir / "build-test"

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
        generator_path = TEMPLATES_DIR / template_name / version / "generator"

        if not (generator_path / "index.js").exists():
            pytest.skip("No Yeoman generator found")

        # Generate project
        subprocess.run(
            [
                "yo", str(generator_path),
                "--name", "lint-test",
                "--team", "test-team",
                "--database", "none"
            ],
            cwd=temp_dir,
            capture_output=True
        )

        project_path = temp_dir / "lint-test"

        # Run lint
        result = subprocess.run(
            ["npm", "run", "lint"],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Lint failed: {result.stderr}"
