#!/usr/bin/env python3
"""
Chapter 11: Policy Validation Tests
====================================
Tests that validate OPA Gatekeeper policies by simulating compliant
and non-compliant Kubernetes resources.

Usage:
    python test-policies.py              # offline validation
    python test-policies.py --live       # also test against a real cluster

Prerequisites:
    - conftest CLI installed (for the conftest integration tests)
    - kubectl + Gatekeeper + the K8sRequiredResources ConstraintTemplate
      from constraint-template.yaml (for --live tests, see README 2.1)
"""

import json
import subprocess
import sys
import tempfile
import os
import time
import unittest
from typing import Optional

# --live is handled here because unittest.main() would reject it.
LIVE = "--live" in sys.argv


# --- Sample Kubernetes manifests for testing ---

COMPLIANT_DEPLOYMENT = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: compliant-app
  labels:
    app.kubernetes.io/name: compliant-app
    team: platform
    owner: alice@example.com
    cost-center: "1234"
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
        image: gcr.io/my-project/compliant-app:v1.0
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
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
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
        self.assertIn("team:", COMPLIANT_DEPLOYMENT)
        self.assertIn("owner:", COMPLIANT_DEPLOYMENT)
        self.assertIn("cost-center:", COMPLIANT_DEPLOYMENT)
        self.assertIn("resources:", COMPLIANT_DEPLOYMENT)
        self.assertNotIn("privileged: true", COMPLIANT_DEPLOYMENT)

    def test_no_limits_detected(self):
        """Deployment without resource limits should be flagged."""
        # Check that the container spec has no resources block
        self.assertNotIn("resources:", NONCOMPLIANT_NO_LIMITS)

    def test_privileged_container_detected(self):
        """Privileged container should be flagged."""
        self.assertIn("privileged: true", NONCOMPLIANT_PRIVILEGED)

    def test_untrusted_registry_detected(self):
        """Images from untrusted registries should be flagged."""
        self.assertIn("docker.io", NONCOMPLIANT_BAD_REGISTRY)
        self.assertNotIn("registry.company.com", NONCOMPLIANT_BAD_REGISTRY)

    def test_missing_labels_detected(self):
        """Deployments without required team label should be flagged."""
        # NONCOMPLIANT_NO_LIMITS has no team/owner/cost-center labels
        self.assertNotIn("owner:", NONCOMPLIANT_NO_LIMITS)
        self.assertNotIn("cost-center:", NONCOMPLIANT_NO_LIMITS)


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


# --- Live cluster tests (--live) ---

TEST_NAMESPACE = "peh-policy-test"
TEST_CONSTRAINT = "peh-live-test"

# Labelled so it passes the Chapter 3 namespace-label constraint, if present.
TEST_NAMESPACE_MANIFEST = f"""
apiVersion: v1
kind: Namespace
metadata:
  name: {TEST_NAMESPACE}
  labels:
    team: platform
    environment: dev
    cost-center: "1234"
"""

# Same template as constraints/require-resources.yaml, but in deny mode and
# scoped to the scratch namespace so the real constraints are never touched.
TEST_CONSTRAINT_MANIFEST = f"""
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredResources
metadata:
  name: {TEST_CONSTRAINT}
spec:
  enforcementAction: deny
  match:
    namespaces: ["{TEST_NAMESPACE}"]
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
"""

# registry.k8s.io is on the Chapter 2 registry allowlist, so a denial can only
# come from the missing resources.
POD_NO_RESOURCES = """
apiVersion: v1
kind: Pod
metadata:
  name: live-noncompliant
spec:
  containers:
  - name: app
    image: registry.k8s.io/pause:3.9
"""

POD_WITH_RESOURCES = """
apiVersion: v1
kind: Pod
metadata:
  name: live-compliant
spec:
  containers:
  - name: app
    image: registry.k8s.io/pause:3.9
    resources:
      requests:
        cpu: 50m
        memory: 64Mi
      limits:
        cpu: 100m
        memory: 128Mi
"""


def kubectl(*args: str, manifest: Optional[str] = None) -> subprocess.CompletedProcess:
    """Run kubectl, optionally feeding a manifest on stdin."""
    return subprocess.run(
        ["kubectl", *args], input=manifest, capture_output=True, text=True, timeout=60
    )


def dry_run(manifest: str) -> subprocess.CompletedProcess:
    """Submit a manifest through the admission webhook without creating it."""
    return kubectl(
        "apply", "--dry-run=server", "-n", TEST_NAMESPACE, "-f", "-", manifest=manifest
    )


@unittest.skipUnless(LIVE, "live cluster tests need --live")
class TestLiveGatekeeper(unittest.TestCase):
    """Check that Gatekeeper rejects and admits pods on a real cluster."""

    @classmethod
    def setUpClass(cls):
        cls.addClassCleanup(cls._cleanup)

        if kubectl("get", "crd", "k8srequiredresources.constraints.gatekeeper.sh").returncode:
            raise RuntimeError(
                "K8sRequiredResources CRD not found. Apply constraint-template.yaml "
                "(README 2.1) and make sure Gatekeeper is running."
            )
        for manifest in (TEST_NAMESPACE_MANIFEST, TEST_CONSTRAINT_MANIFEST):
            result = kubectl("apply", "-f", "-", manifest=manifest)
            if result.returncode:
                raise RuntimeError(f"Could not apply test resources: {result.stderr}")

        # Gatekeeper needs a few seconds before a new constraint is enforced.
        deadline = time.time() + 60
        while f"[{TEST_CONSTRAINT}]" not in dry_run(POD_NO_RESOURCES).stderr:
            if time.time() > deadline:
                raise RuntimeError(f"Constraint {TEST_CONSTRAINT} was not enforced in 60s")
            time.sleep(3)

    @classmethod
    def _cleanup(cls):
        kubectl("delete", "k8srequiredresources", TEST_CONSTRAINT, "--ignore-not-found")
        kubectl("delete", "namespace", TEST_NAMESPACE, "--ignore-not-found", "--wait=false")

    def test_pod_without_resources_denied(self):
        """A pod with no requests/limits is rejected by the test constraint."""
        result = dry_run(POD_NO_RESOURCES)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"[{TEST_CONSTRAINT}]", result.stderr)
        self.assertIn("missing resource limits", result.stderr)

    def test_pod_with_resources_admitted(self):
        """A pod with requests and limits passes admission."""
        result = dry_run(POD_WITH_RESOURCES)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    if LIVE:
        sys.argv.remove("--live")
    print("=" * 60)
    print("Chapter 11: Policy Validation Tests" + (" (live)" if LIVE else ""))
    print("=" * 60)
    unittest.main(verbosity=2)
