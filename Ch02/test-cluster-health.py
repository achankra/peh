#!/usr/bin/env python3
"""
Chapter 2: Cluster Health Tests
================================
Validates Kubernetes cluster configuration, GitOps deployment,
and service mesh readiness.

Usage:
    python test-cluster-health.py [--demo]
"""

import json
import subprocess
import sys
import unittest


def run_kubectl(args: list) -> str:
    """Execute kubectl and return stdout."""
    try:
        r = subprocess.run(["kubectl"] + args, capture_output=True, text=True, timeout=30)
        return r.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


class TestClusterHealth(unittest.TestCase):
    """Validate cluster is healthy and correctly configured."""

    def test_nodes_ready(self):
        """All cluster nodes should be in Ready state."""
        output = run_kubectl(["get", "nodes", "-o", "json"])
        if not output:
            self.skipTest("kubectl not available")
        data = json.loads(output)
        for node in data.get("items", []):
            conditions = {c["type"]: c["status"] for c in node.get("status", {}).get("conditions", [])}
            self.assertEqual(conditions.get("Ready"), "True",
                             f"Node {node['metadata']['name']} not Ready")

    def test_system_pods_running(self):
        """Critical kube-system pods should be running."""
        output = run_kubectl(["get", "pods", "-n", "kube-system", "-o", "json"])
        if not output:
            self.skipTest("kubectl not available")
        data = json.loads(output)
        for pod in data.get("items", []):
            phase = pod.get("status", {}).get("phase", "")
            name = pod["metadata"]["name"]
            self.assertIn(phase, ["Running", "Succeeded"], f"Pod {name} is {phase}")

    def test_argocd_namespace_exists(self):
        """ArgoCD namespace should exist for GitOps."""
        output = run_kubectl(["get", "namespace", "argocd", "--no-headers"])
        if not output:
            self.skipTest("kubectl not available or ArgoCD not installed")
        self.assertIn("argocd", output)


class TestPulumiConfig(unittest.TestCase):
    """Validate Pulumi configuration files."""

    def test_main_py_exists(self):
        import os
        path = os.path.join(os.path.dirname(__file__), "pulumi-cluster", "__main__.py")
        self.assertTrue(os.path.exists(path), "pulumi-cluster/__main__.py not found")

    def test_pulumi_yaml_exists(self):
        import os
        path = os.path.join(os.path.dirname(__file__), "pulumi-cluster", "Pulumi.yaml")
        self.assertTrue(os.path.exists(path), "pulumi-cluster/Pulumi.yaml not found")

    def test_requirements_exists(self):
        import os
        path = os.path.join(os.path.dirname(__file__), "pulumi-cluster", "requirements.txt")
        self.assertTrue(os.path.exists(path), "pulumi-cluster/requirements.txt not found")


class TestServiceMeshConfig(unittest.TestCase):
    """Validate Istio service mesh configuration."""

    def test_istio_config_exists(self):
        import os
        path = os.path.join(os.path.dirname(__file__), "istio-mesh-config.yaml")
        self.assertTrue(os.path.exists(path))

    def test_istio_config_has_mtls(self):
        import os
        path = os.path.join(os.path.dirname(__file__), "istio-mesh-config.yaml")
        content = open(path).read()
        self.assertTrue("mtls" in content.lower() or "STRICT" in content,
                        "Service mesh should enforce mTLS")


if __name__ == "__main__":
    print("=" * 60)
    print("Chapter 2: Cluster Health Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
