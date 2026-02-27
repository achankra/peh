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


# ── Kubernetes namespace where Backstage runs ───────────────────
BACKSTAGE_NS = os.environ.get("BACKSTAGE_NS", "backstage")
TEMPLATE_SERVER_PORT = 8080


def kubectl(*args, **kwargs):
    """Run a kubectl command and return the result."""
    result = subprocess.run(
        ["kubectl", *args],
        capture_output=True, text=True,
        **kwargs,
    )
    return result


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

        for template_dir in (base_path / "templates").iterdir():
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
                    backstage_yaml=backstage_yaml
                ))

        return templates

    def validate_template(self, template: TemplateMetadata) -> list[str]:
        """Validate a template before publishing."""
        errors = []

        required_files = [
            "template.yaml",
            "skeleton/Dockerfile",
            "skeleton/README.md"
        ]

        for file_path in required_files:
            if not (template.path / file_path).exists():
                errors.append(f"Missing required file: {file_path}")

        spec = template.backstage_yaml.get("spec", {})
        if not spec.get("parameters"):
            errors.append("Template missing parameters")
        if not spec.get("steps"):
            errors.append("Template missing steps")

        return errors

    # ── in-cluster template server ──────────────────────────────

    def deploy_template_server(self, base_path: Path):
        """Deploy a busybox pod inside the cluster to serve templates."""
        templates = self.discover_templates(base_path)
        if not templates:
            print("No templates found")
            return None

        # ── ConfigMap with template YAML content ────────────────
        cm_data = {}
        for t in templates:
            key = f"{t.name}--{t.version}"
            cm_data[key] = (t.path / "template.yaml").read_text()

        cm_manifest = {
            "apiVersion": "v1", "kind": "ConfigMap",
            "metadata": {"name": "starter-kit-templates",
                         "namespace": BACKSTAGE_NS},
            "data": cm_data,
        }

        # ── Pod serving files via busybox httpd ─────────────────
        volume_mounts = []
        for t in templates:
            key = f"{t.name}--{t.version}"
            volume_mounts.append({
                "name": "templates",
                "mountPath": (f"/data/templates/{t.name}/{t.version}"
                              f"/template.yaml"),
                "subPath": key,
            })

        pod_manifest = {
            "apiVersion": "v1", "kind": "Pod",
            "metadata": {"name": "template-server",
                         "namespace": BACKSTAGE_NS,
                         "labels": {"app": "template-server"}},
            "spec": {
                "containers": [{
                    "name": "httpd",
                    "image": "busybox:1.36",
                    "command": ["httpd", "-f", "-p",
                                str(TEMPLATE_SERVER_PORT), "-h", "/data"],
                    "ports": [{"containerPort": TEMPLATE_SERVER_PORT}],
                    "volumeMounts": volume_mounts,
                }],
                "volumes": [{
                    "name": "templates",
                    "configMap": {"name": "starter-kit-templates"},
                }],
            },
        }

        svc_manifest = {
            "apiVersion": "v1", "kind": "Service",
            "metadata": {"name": "template-server",
                         "namespace": BACKSTAGE_NS},
            "spec": {
                "selector": {"app": "template-server"},
                "ports": [{"port": TEMPLATE_SERVER_PORT,
                           "targetPort": TEMPLATE_SERVER_PORT}],
            },
        }

        # ── apply manifests (delete pod first for idempotency) ──
        kubectl("delete", "pod", "template-server",
                "-n", BACKSTAGE_NS, "--ignore-not-found")

        for manifest in [cm_manifest, pod_manifest, svc_manifest]:
            result = kubectl("apply", "-f", "-",
                             input=json.dumps(manifest))
            if result.returncode != 0:
                kind = manifest["kind"]
                print(f"  Failed to apply {kind}: {result.stderr.strip()}")
                return None

        # ── wait for pod readiness ──────────────────────────────
        print("Deploying template server in cluster...", end="", flush=True)
        result = kubectl("wait", "--for=condition=ready",
                         "pod/template-server", "-n", BACKSTAGE_NS,
                         "--timeout=60s")
        if result.returncode != 0:
            print(f" failed: {result.stderr.strip()}")
            return None
        print(" ready")

        svc_host = f"template-server.{BACKSTAGE_NS}.svc"
        return f"http://{svc_host}:{TEMPLATE_SERVER_PORT}"

    @staticmethod
    def cleanup_template_server():
        """Remove the in-cluster template server resources."""
        for kind, name in [("pod", "template-server"),
                           ("service", "template-server"),
                           ("configmap", "starter-kit-templates")]:
            kubectl("delete", kind, name,
                    "-n", BACKSTAGE_NS, "--ignore-not-found")

    # ── Backstage reading allow configuration ───────────────────

    def ensure_reading_allow(self):
        """Ensure Backstage allows reading from in-cluster URLs.

        Backstage only fetches from hosts listed in backend.reading.allow
        or that have configured integrations (GitHub, GitLab, etc.).
        This patches the app-config ConfigMap to allow *.svc hosts.
        Returns True if Backstage was restarted (caller must wait).
        """
        svc_host = f"template-server.{BACKSTAGE_NS}.svc"
        allow_entry = f"{svc_host}:{TEMPLATE_SERVER_PORT}"

        # ── find the app-config ConfigMap ───────────────────────
        result = kubectl("get", "cm", "-n", BACKSTAGE_NS, "-o", "json")
        if result.returncode != 0:
            print(f"Cannot list ConfigMaps: {result.stderr.strip()}")
            return False

        cms = json.loads(result.stdout)
        app_config_cm = None
        app_config_key = None

        for cm in cms.get("items", []):
            name = cm["metadata"]["name"]
            data = cm.get("data", {})
            for key, value in data.items():
                if not isinstance(value, str):
                    continue
                # Look for Backstage app-config markers
                if ("app:" in value and "baseUrl" in value) or \
                   ("backend:" in value and "baseUrl" in value):
                    app_config_cm = cm
                    app_config_key = key
                    break
            if app_config_cm:
                break

        if not app_config_cm:
            print(f"\n  Could not find Backstage app-config ConfigMap.")
            print(f"  Add this to your Backstage app-config.yaml:")
            print(f"    backend:")
            print(f"      reading:")
            print(f"        allow:")
            print(f"          - host: '{allow_entry}'")
            print(f"  Then restart Backstage.\n")
            return False

        cm_name = app_config_cm["metadata"]["name"]
        config_yaml = app_config_cm["data"][app_config_key]

        # ── check if already configured ─────────────────────────
        if allow_entry in config_yaml:
            return False  # Already configured, no restart needed

        # ── parse and patch the config ──────────────────────────
        config = yaml.safe_load(config_yaml)
        backend = config.setdefault("backend", {})
        reading = backend.setdefault("reading", {})
        allow_list = reading.setdefault("allow", [])

        # Add our host
        allow_list.append({"host": allow_entry})

        # ── update the ConfigMap ────────────────────────────────
        app_config_cm["data"][app_config_key] = yaml.dump(
            config, default_flow_style=False, sort_keys=False
        )
        # Remove resourceVersion to avoid conflicts
        app_config_cm["metadata"].pop("resourceVersion", None)
        app_config_cm["metadata"].pop("uid", None)
        app_config_cm["metadata"].pop("creationTimestamp", None)
        managed = app_config_cm["metadata"].pop("managedFields", None)

        result = kubectl("apply", "-f", "-",
                         input=json.dumps(app_config_cm))
        if result.returncode != 0:
            print(f"Failed to patch ConfigMap {cm_name}: "
                  f"{result.stderr.strip()}")
            return False

        print(f"Patched {cm_name}: added backend.reading.allow "
              f"for {allow_entry}")

        # ── restart Backstage to pick up the config change ──────
        # Try deployment first, then statefulset
        for workload in ["deployment", "statefulset"]:
            r = kubectl("get", workload, "-n", BACKSTAGE_NS,
                        "-l", "app.kubernetes.io/name=backstage",
                        "-o", "jsonpath={.items[0].metadata.name}")
            if r.returncode == 0 and r.stdout.strip():
                workload_name = r.stdout.strip()
                print(f"Restarting {workload}/{workload_name}...",
                      end="", flush=True)
                kubectl("rollout", "restart",
                        f"{workload}/{workload_name}",
                        "-n", BACKSTAGE_NS)
                kubectl("rollout", "status",
                        f"{workload}/{workload_name}",
                        "-n", BACKSTAGE_NS,
                        "--timeout=120s")
                print(" done")
                return True  # Restarted

        # Fallback: delete pods to trigger restart
        print("Restarting Backstage pods...", end="", flush=True)
        kubectl("delete", "pods", "-n", BACKSTAGE_NS,
                "-l", "app.kubernetes.io/name=backstage")
        time.sleep(10)
        print(" done")
        return True

    # ── publishing ──────────────────────────────────────────────

    def publish_template(self, template: TemplateMetadata,
                         base_url: str = None) -> bool:
        """Publish a single template to Backstage."""
        errors = self.validate_template(template)
        if errors:
            print(f"Validation failed for {template.name}/"
                  f"{template.version}:")
            for error in errors:
                print(f"  - {error}")
            return False

        catalog_url = f"{self.backstage_url}/api/catalog/locations"

        if base_url:
            location_target = (
                f"{base_url}/templates/"
                f"{template.name}/{template.version}/template.yaml"
            )
        else:
            location_target = (
                "https://github.com/platform-org/starter-kits/blob/main/"
                f"templates/{template.name}/{template.version}/template.yaml"
            )

        response = requests.post(
            catalog_url,
            headers=self.headers,
            json={"type": "url", "target": location_target}
        )

        if response.status_code in (200, 201):
            print(f"Published {template.name}/{template.version}")
            return True
        elif response.status_code == 409:
            print(f"Already registered {template.name}/{template.version}"
                  " (use --refresh to update)")
            return True
        else:
            print(f"Failed to publish {template.name}/{template.version}:"
                  f" {response.text}")
            return False

    def remove_all(self, base_path: Path):
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
                if loc_id and ("starter-kits" in target
                               or "template.yaml" in target):
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

    def publish_all(self, base_path: Path,
                    base_url: str = None) -> dict:
        """Publish all discovered templates."""
        templates = self.discover_templates(base_path)
        results = {"published": [], "failed": []}

        for template in templates:
            if self.publish_template(template, base_url):
                results["published"].append(
                    f"{template.name}/{template.version}")
            else:
                results["failed"].append(
                    f"{template.name}/{template.version}")

        return results


def wait_for_backstage(url: str, timeout: int = 120):
    """Wait for Backstage to become reachable after restart."""
    print("Waiting for Backstage to come back up...", end="", flush=True)
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(
                f"{url}/.backstage/health/v1/readiness", timeout=3
            )
            if r.status_code == 200:
                print(" ready")
                return True
        except (requests.ConnectionError, requests.Timeout):
            pass
        print(".", end="", flush=True)
        time.sleep(3)
    print(" timeout")
    return False


def ensure_port_forward():
    """Check if Backstage port-forward is running, restart if needed."""
    try:
        r = requests.get("http://localhost:7007/.backstage/health/v1/readiness",
                         timeout=2)
        if r.status_code == 200:
            return True
    except (requests.ConnectionError, requests.Timeout):
        pass

    print("Port-forward lost, re-establishing...", end="", flush=True)
    # Start port-forward in background
    proc = subprocess.Popen(
        ["kubectl", "port-forward", "-n", BACKSTAGE_NS,
         "svc/backstage", "7007:7007"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    # Wait for it to be ready
    for _ in range(20):
        time.sleep(1)
        try:
            r = requests.get(
                "http://localhost:7007/.backstage/health/v1/readiness",
                timeout=2,
            )
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
    local = "--local" in sys.argv
    cleanup = "--cleanup" in sys.argv

    publisher = TemplatePublisher(backstage_url, backstage_token)

    # ── cleanup mode ────────────────────────────────────────────
    if cleanup:
        print("Removing in-cluster template server...")
        publisher.cleanup_template_server()
        return

    # ── clean up previous registrations if --refresh ────────────
    if refresh:
        print("Refreshing: removing existing locations first...")
        publisher.remove_all(Path("."))
        publisher.cleanup_template_server()
        print()

    # ── local mode: deploy in-cluster + configure Backstage ─────
    base_url = None
    if local:
        # Step 1: deploy template server pod
        base_url = publisher.deploy_template_server(Path("."))
        if not base_url:
            print("Failed to deploy template server")
            sys.exit(1)

        # Step 2: ensure Backstage can read from in-cluster URLs
        restarted = publisher.ensure_reading_allow()
        if restarted:
            # Backstage restarted — port-forward may have died
            ensure_port_forward()

    # ── register templates ──────────────────────────────────────
    results = publisher.publish_all(Path("."), base_url)

    print(f"\nPublished: {len(results['published'])}")
    print(f"Failed: {len(results['failed'])}")

    # ── wait for ingestion ──────────────────────────────────────
    if local and results["published"]:
        templates = publisher.discover_templates(Path("."))
        for t in templates:
            name = t.backstage_yaml.get("metadata", {}).get("name",
                                                             t.name)
            if not publisher.wait_for_template(name):
                print("\nTip: check Backstage logs:")
                print(f"  kubectl logs -n {BACKSTAGE_NS}"
                      f" -l app.kubernetes.io/name=backstage"
                      f" --tail=30")


if __name__ == "__main__":
    main()
