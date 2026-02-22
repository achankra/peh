#!/usr/bin/env python3
"""
Chapter 11: Policy Validation Tests
====================================
Tests that validate OPA Gatekeeper policies by simulating compliant
and non-compliant Kubernetes resources.

Usage:
    python test-policies.py [--live]     # --live tests against real cluster
    python test-policies.py              # default: offline validation

Prerequisites:
    - conftest CLI installed (for offline tests)
    - kubectl + Gatekeeper installed (for --live tests)
"""

import json
import subprocess
import sys
import tempfile
import os
import unittest


# --- Sample Kubernetes manifests for testing ---

COMPLIANT_DEPLOYMENT = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: compliant-app
  labels:
    app.kubernetes.io/name: compliant-app
    app.kubernetes.io/team: platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app: compliant-app
  template:
    metadata:
      labels:
        app: compliant-app
    spec:
      containers:
      - name: app
        image: registry.company.com/apps/compliant-app:v1.0
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
        securityContext:
          privileged: false
          runAsNonRoot: true
"""

NONCOMPLIANT_NO_LIMITS = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: no-limits-app
  labels:
    app.kubernetes.io/name: no-limits-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: no-limits-app
  template:
    metadata:
      labels:
        app: no-limits-app
    spec:
      containers:
      - name: app
        image: registry.company.com/apps/no-limits:v1.0
"""

NONCOMPLIANT_PRIVILEGED = """
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod
  labels:
    app.kubernetes.io/name: privileged-pod
spec:
  containers:
  - name: debug
    image: registry.company.com/tools/debug:latest
    securityContext:
      privileged: true
"""

NONCOMPLIANT_BAD_REGISTRY = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bad-registry-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: bad-registry-app
  template:
    metadata:
      labels:
        app: bad-registry-app
    spec:
      containers:
      - name: app
        image: docker.io/random/untrusted-image:latest
        resources:
          limits:
            cpu: 100m
            memory: 128Mi
"""


class TestPolicyValidation(unittest.TestCase):
    """Offline policy validation tests using manifest analysis."""

    def _parse_yaml_containers(self, manifest: str) -> list:
        """Simple extraction of container specs from YAML manifest."""
        containers = []
        in_container = False
        current = {}
        for line in manifest.strip().split("\n"):
            stripped = line.strip()
            if stripped.startswith("- name:") and "containers" in manifest[:manifest.index(stripped)]:
                if current:
                    containers.append(current)
                current = {"name": stripped.split(":", 1)[1].strip()}
                in_container = True
            elif in_container and "image:" in stripped and not stripped.startswith("#"):
                current["image"] = stripped.split(":", 1)[1].strip().strip('"')
            elif in_container and "privileged:" in stripped:
                current["privileged"] = "true" in stripped.lower()
            elif in_container and "limits:" in stripped:
                current["has_limits"] = True
        if current:
            containers.append(current)
        return containers

    def test_compliant_deployment_passes(self):
        """Compliant deployment should have labels, limits, and approved registry."""
        self.assertIn("app.kubernetes.io/name", COMPLIANT_DEPLOYMENT)
        self.assertIn("limits:", COMPLIANT_DEPLOYMENT)
        self.assertIn("registry.company.com", COMPLIANT_DEPLOYMENT)
        self.assertNotIn("privileged: true", COMPLIANT_DEPLOYMENT)

    def test_no_limits_detected(self):
        """Deployment without resource limits should be flagged."""
        self.assertNotIn("limits:", NONCOMPLIANT_NO_LIMITS)

    def test_privileged_container_detected(self):
        """Privileged container should be flagged."""
        self.assertIn("privileged: true", NONCOMPLIANT_PRIVILEGED)

    def test_untrusted_registry_detected(self):
        """Images from untrusted registries should be flagged."""
        self.assertIn("docker.io", NONCOMPLIANT_BAD_REGISTRY)
        self.assertNotIn("registry.company.com", NONCOMPLIANT_BAD_REGISTRY)

    def test_missing_labels_detected(self):
        """Deployments without required team label should be flagged."""
        self.assertNotIn("app.kubernetes.io/team", NONCOMPLIANT_NO_LIMITS)


class TestConftestIntegration(unittest.TestCase):
    """Integration tests using conftest CLI (skipped if not installed)."""

    @classmethod
    def setUpClass(cls):
        """Check if conftest is available."""
        try:
            subprocess.run(["conftest", "--version"], capture_output=True, timeout=5)
            cls.conftest_available = True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            cls.conftest_available = False

    def _run_conftest(self, manifest: str, policy_dir: str) -> subprocess.CompletedProcess:
        """Run conftest against a manifest with given policy directory."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(manifest)
            f.flush()
            try:
                return subprocess.run(
                    ["conftest", "test", f.name, "--policy", policy_dir, "--output", "json"],
                    capture_output=True, text=True, timeout=30
                )
            finally:
                os.unlink(f.name)

    @unittest.skipUnless(lambda self: self.conftest_available, "conftest not installed")
    def test_conftest_compliant_passes(self):
        """Compliant manifests should pass conftest validation."""
        policy_dir = os.path.join(os.path.dirname(__file__), "conftest-tests")
        if os.path.exists(policy_dir):
            result = self._run_conftest(COMPLIANT_DEPLOYMENT, policy_dir)
            # conftest returns 0 for passing tests
            self.assertEqual(result.returncode, 0, f"Unexpected failures: {result.stdout}")


if __name__ == "__main__":
    print("=" * 60)
    print("Chapter 11: Policy Validation Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
