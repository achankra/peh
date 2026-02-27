#!/usr/bin/env python3
"""Publish starter kit templates to Backstage catalog."""

import os
import sys
import json
import time
import yaml
import requests
import subprocess
from pathlib import Path
from dataclasses import dataclass


@dataclass
class TemplateMetadata:
    """Metadata for a starter kit template."""
    name: str
    version: str
    path: Path
    backstage_yaml: dict


# ── Configuration ───────────────────────────────────────────────
BACKSTAGE_NS = os.environ.get("BACKSTAGE_NS", "backstage")

# GitHub repository where templates live.
# Format: owner/repo  (e.g. "achankra/peh")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "achankra/peh")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")

# Path prefix from repo root to the chapter's code directory.
# If templates/ is at Ch10/templates/ in the repo, set this to "Ch10".
REPO_PREFIX = os.environ.get("REPO_PREFIX", "Ch10")


def kubectl(*args, **kwargs):
    """Run a kubectl command and return the result."""
    return subprocess.run(
        ["kubectl", *args],
        capture_output=True, text=True,
        **kwargs,
    )


class TemplatePublisher:
    """Publish templates to Backstage."""

    def __init__(self, backstage_url: str, token: str = ""):
        self.backstage_url = backstage_url.rstrip("/")
        self.headers = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def discover_templates(self, base_path: Path) -> list[TemplateMetadata]:
        """Discover all templates in the repository."""
        templates = []
        templates_dir = base_path / "templates"
        if not templates_dir.exists():
            return templates

        for template_dir in templates_dir.iterdir():
            if not template_dir.is_dir():
                continue
            for version_dir in template_dir.iterdir():
                if not version_dir.is_dir():
                    continue
                template_file = version_dir / "template.yaml"
                if not template_file.exists():
                    continue
                with open(template_file) as f:
                    backstage_yaml = yaml.safe_load(f)
                templates.append(TemplateMetadata(
                    name=template_dir.name,
                    version=version_dir.name,
                    path=version_dir,
                    backstage_yaml=backstage_yaml,
                ))
        return templates

    def validate_template(self, template: TemplateMetadata) -> list[str]:
        """Validate a template before publishing."""
        errors = []
        for req in ["template.yaml", "skeleton/Dockerfile",
                     "skeleton/README.md"]:
            if not (template.path / req).exists():
                errors.append(f"Missing required file: {req}")
        spec = template.backstage_yaml.get("spec", {})
        if not spec.get("parameters"):
            errors.append("Template missing parameters")
        if not spec.get("steps"):
            errors.append("Template missing steps")
        return errors

    # ── GitHub integration setup ────────────────────────────────

    @staticmethod
    def setup_github_token(github_token: str):
        """Update Backstage's GitHub integration token.

        Finds the app-config ConfigMap, patches the GitHub token,
        and restarts Backstage.
        """
        # ── find the app-config ConfigMap ───────────────────────
        result = kubectl("get", "cm", "-n", BACKSTAGE_NS, "-o", "json")
        if result.returncode != 0:
            print(f"Cannot list ConfigMaps: {result.stderr.strip()}")
            return False

        cms = json.loads(result.stdout)
        app_config_cm = None
        app_config_key = None

        for cm in cms.get("items", []):
            data = cm.get("data", {})
            for key, value in data.items():
                if isinstance(value, str) and "baseUrl" in value:
                    app_config_cm = cm
                    app_config_key = key
                    break
            if app_config_cm:
                break

        if not app_config_cm:
            print("Could not find Backstage app-config ConfigMap.")
            print("Add this manually to your app-config.yaml:")
            print("  integrations:")
            print("    github:")
            print(f"      - host: github.com")
            print(f"        token: {github_token}")
            return False

        cm_name = app_config_cm["metadata"]["name"]
        config = yaml.safe_load(app_config_cm["data"][app_config_key])

        # ── update or add GitHub integration ────────────────────
        integrations = config.setdefault("integrations", {})
        github_list = integrations.setdefault("github", [])

        # Find existing github.com entry or create one
        gh_entry = None
        for entry in github_list:
            if entry.get("host") == "github.com":
                gh_entry = entry
                break
        if gh_entry:
            gh_entry["token"] = github_token
        else:
            github_list.append({
                "host": "github.com",
                "token": github_token,
            })

        # ── apply the updated ConfigMap ─────────────────────────
        app_config_cm["data"][app_config_key] = yaml.dump(
            config, default_flow_style=False, sort_keys=False
        )
        for field in ["resourceVersion", "uid", "creationTimestamp",
                      "managedFields"]:
            app_config_cm["metadata"].pop(field, None)

        result = kubectl("apply", "-f", "-",
                         input=json.dumps(app_config_cm))
        if result.returncode != 0:
            print(f"Failed to patch ConfigMap: {result.stderr.strip()}")
            return False

        print(f"Updated GitHub token in {cm_name}")

        # ── restart Backstage ───────────────────────────────────
        for workload in ["deployment", "statefulset"]:
            r = kubectl("get", workload, "-n", BACKSTAGE_NS,
                        "-l", "app.kubernetes.io/name=backstage",
                        "-o", "jsonpath={.items[0].metadata.name}")
            if r.returncode == 0 and r.stdout.strip():
                name = r.stdout.strip()
                print(f"Restarting {workload}/{name}...", end="",
                      flush=True)
                kubectl("rollout", "restart",
                        f"{workload}/{name}", "-n", BACKSTAGE_NS)
                kubectl("rollout", "status",
                        f"{workload}/{name}", "-n", BACKSTAGE_NS,
                        "--timeout=120s")
                print(" done")
                return True

        # Fallback: delete pods
        print("Restarting Backstage pods...", end="", flush=True)
        kubectl("delete", "pods", "-n", BACKSTAGE_NS,
                "-l", "app.kubernetes.io/name=backstage")
        time.sleep(15)
        print(" done")
        return True

    # ── publishing ──────────────────────────────────────────────

    def _github_url(self, template: TemplateMetadata) -> str:
        """Build the GitHub URL for a template."""
        return (
            f"https://github.com/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/"
            f"{REPO_PREFIX}/templates/"
            f"{template.name}/{template.version}/template.yaml"
        )

    def publish_template(self, template: TemplateMetadata) -> bool:
        """Publish a single template to Backstage."""
        errors = self.validate_template(template)
        if errors:
            print(f"Validation failed for {template.name}/"
                  f"{template.version}:")
            for error in errors:
                print(f"  - {error}")
            return False

        location_target = self._github_url(template)
        catalog_url = f"{self.backstage_url}/api/catalog/locations"

        response = requests.post(
            catalog_url,
            headers=self.headers,
            json={"type": "url", "target": location_target}
        )

        if response.status_code in (200, 201):
            print(f"Published {template.name}/{template.version}")
            print(f"  -> {location_target}")
            return True
        elif response.status_code == 409:
            print(f"Already registered {template.name}/{template.version}"
                  " (use --refresh to update)")
            return True
        else:
            print(f"Failed to publish {template.name}/{template.version}:"
                  f" {response.text}")
            return False

    def remove_all(self):
        """Remove all previously registered template locations."""
        catalog_url = f"{self.backstage_url}/api/catalog/locations"
        try:
            response = requests.get(catalog_url, headers=self.headers)
            if response.status_code != 200:
                print(f"Could not fetch locations: {response.status_code}")
                return
            for loc in response.json():
                target = loc.get("data", {}).get("target", "")
                loc_id = loc.get("data", {}).get("id", "")
                if loc_id and ("template.yaml" in target):
                    requests.delete(
                        f"{catalog_url}/{loc_id}", headers=self.headers
                    )
                    print(f"  Removed location: {target}")
        except requests.ConnectionError:
            print("  Backstage not reachable, skipping removal")

    def wait_for_template(self, template_name: str,
                          timeout: int = 90) -> bool:
        """Poll Backstage catalog until the template entity appears."""
        entity_url = (
            f"{self.backstage_url}/api/catalog/entities/by-name/"
            f"template/default/{template_name}"
        )
        print("Waiting for Backstage to ingest template...", end="",
              flush=True)
        start = time.time()
        while time.time() - start < timeout:
            try:
                r = requests.get(entity_url, headers=self.headers)
                if r.status_code == 200:
                    print(" ready!")
                    return True
            except requests.ConnectionError:
                pass
            print(".", end="", flush=True)
            time.sleep(3)
        print(" timeout")
        return False

    def publish_all(self, base_path: Path) -> dict:
        """Publish all discovered templates."""
        templates = self.discover_templates(base_path)
        results = {"published": [], "failed": []}
        for template in templates:
            if self.publish_template(template):
                results["published"].append(
                    f"{template.name}/{template.version}")
            else:
                results["failed"].append(
                    f"{template.name}/{template.version}")
        return results


def ensure_port_forward():
    """Check if Backstage port-forward is running, restart if needed."""
    try:
        r = requests.get(
            "http://localhost:7007/.backstage/health/v1/readiness",
            timeout=2)
        if r.status_code == 200:
            return True
    except (requests.ConnectionError, requests.Timeout):
        pass

    print("Port-forward lost, re-establishing...", end="", flush=True)
    subprocess.Popen(
        ["kubectl", "port-forward", "-n", BACKSTAGE_NS,
         "svc/backstage", "7007:7007"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(20):
        time.sleep(1)
        try:
            r = requests.get(
                "http://localhost:7007/.backstage/health/v1/readiness",
                timeout=2)
            if r.status_code == 200:
                print(" ready")
                return True
        except (requests.ConnectionError, requests.Timeout):
            pass
        print(".", end="", flush=True)
    print(" failed")
    return False


def main():
    backstage_url = os.environ.get("BACKSTAGE_URL", "http://localhost:7007")
    backstage_token = os.environ.get("BACKSTAGE_TOKEN", "")
    refresh = "--refresh" in sys.argv
    setup_github = "--setup-github" in sys.argv

    publisher = TemplatePublisher(backstage_url, backstage_token)

    # ── one-time GitHub token setup ─────────────────────────────
    if setup_github:
        github_token = os.environ.get("GITHUB_TOKEN", "")
        if not github_token:
            print("Set GITHUB_TOKEN env var first:")
            print("  export GITHUB_TOKEN=ghp_your_token_here")
            print("  python3 publish.py --setup-github")
            sys.exit(1)

        publisher.setup_github_token(github_token)
        ensure_port_forward()
        print("\nGitHub integration updated. You can now run:")
        print("  python3 publish.py")
        return

    # ── clean up previous registrations ─────────────────────────
    if refresh:
        print("Refreshing: removing existing locations first...")
        publisher.remove_all()
        print()

    # ── register templates using GitHub URLs ────────────────────
    print(f"Publishing templates from {GITHUB_REPO} ({GITHUB_BRANCH})...")
    results = publisher.publish_all(Path("."))

    print(f"\nPublished: {len(results['published'])}")
    print(f"Failed: {len(results['failed'])}")

    # ── wait for ingestion ──────────────────────────────────────
    if results["published"]:
        templates = publisher.discover_templates(Path("."))
        for t in templates:
            name = t.backstage_yaml.get("metadata", {}).get("name",
                                                             t.name)
            if not publisher.wait_for_template(name):
                print("\nTip: check Backstage logs:")
                print(f"  kubectl logs -n {BACKSTAGE_NS}"
                      f" -l app.kubernetes.io/name=backstage"
                      f" --tail=30")
                print("Common issue: GitHub integration token expired."
                      " Fix with:")
                print("  export GITHUB_TOKEN=ghp_...")
                print("  python3 publish.py --setup-github")


if __name__ == "__main__":
    main()
