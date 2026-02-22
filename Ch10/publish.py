#!/usr/bin/env python3
"""Publish starter kit templates to Backstage catalog.

This script discovers, validates, and publishes starter kit templates
to the Backstage developer portal.
"""

import os
import yaml
import requests
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class TemplateMetadata:
    """Metadata for a starter kit template."""
    name: str
    version: str
    path: Path
    backstage_yaml: dict


class TemplatePublisher:
    """Publish templates to Backstage."""

    def __init__(self, backstage_url: str, token: str):
        self.backstage_url = backstage_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def discover_templates(self, base_path: Path) -> list[TemplateMetadata]:
        """Discover all templates in the repository."""
        templates = []

        for template_dir in (base_path / "templates").iterdir():
            if not template_dir.is_dir():
                continue

            for version_dir in template_dir.iterdir():
                if not version_dir.is_dir():
                    continue

                backstage_file = version_dir / "backstage" / "template.yaml"
                if not backstage_file.exists():
                    continue

                with open(backstage_file) as f:
                    backstage_yaml = yaml.safe_load(f)

                templates.append(TemplateMetadata(
                    name=template_dir.name,
                    version=version_dir.name,
                    path=version_dir,
                    backstage_yaml=backstage_yaml
                ))

        return templates

    def validate_template(self, template: TemplateMetadata) -> list[str]:
        """Validate a template before publishing."""
        errors = []

        required_files = [
            "backstage/template.yaml",
            "template/package.json.ejs" if "backend" in template.name else None,
            "template/Dockerfile.ejs",
            "template/README.md.ejs"
        ]

        for file_path in filter(None, required_files):
            if not (template.path / file_path).exists():
                errors.append(f"Missing required file: {file_path}")

        # Validate YAML structure
        spec = template.backstage_yaml.get("spec", {})
        if not spec.get("parameters"):
            errors.append("Template missing parameters")
        if not spec.get("steps"):
            errors.append("Template missing steps")

        return errors

    def publish_template(self, template: TemplateMetadata) -> bool:
        """Publish a single template to Backstage."""
        # Validate first
        errors = self.validate_template(template)
        if errors:
            print(f"Validation failed for {template.name}/{template.version}:")
            for error in errors:
                print(f"  - {error}")
            return False

        # Register in catalog
        catalog_url = f"{self.backstage_url}/api/catalog/locations"

        # For this example, we assume templates are in a git repo
        # Backstage will fetch from there
        location_target = (
            f"https://github.com/platform-org/starter-kits/blob/main/"
            f"templates/{template.name}/{template.version}/backstage/template.yaml"
        )

        response = requests.post(
            catalog_url,
            headers=self.headers,
            json={
                "type": "url",
                "target": location_target
            }
        )

        if response.status_code in (200, 201):
            print(f"✓ Published {template.name}/{template.version}")
            return True
        else:
            print(f"✗ Failed to publish {template.name}/{template.version}: {response.text}")
            return False

    def publish_all(self, base_path: Path) -> dict:
        """Publish all discovered templates."""
        templates = self.discover_templates(base_path)

        results = {
            "published": [],
            "failed": []
        }

        for template in templates:
            if self.publish_template(template):
                results["published"].append(f"{template.name}/{template.version}")
            else:
                results["failed"].append(f"{template.name}/{template.version}")

        return results


if __name__ == "__main__":
    backstage_url = os.environ.get("BACKSTAGE_URL", "http://localhost:7007")
    backstage_token = os.environ.get("BACKSTAGE_TOKEN", "")

    publisher = TemplatePublisher(backstage_url, backstage_token)
    results = publisher.publish_all(Path("."))

    print(f"\nPublished: {len(results['published'])}")
    print(f"Failed: {len(results['failed'])}")
