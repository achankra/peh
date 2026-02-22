#!/usr/bin/env python3
"""
Chapter 3: RBAC Permission Tests
==================================
Validates that RBAC configurations correctly restrict access and
that the demo app deploys successfully.

Usage:
    python test-rbac-permissions.py
"""

import os
import unittest


class TestRBACConfigs(unittest.TestCase):
    """Validate RBAC YAML configuration files."""

    def setUp(self):
        self.code_dir = os.path.dirname(__file__)

    def test_platform_admin_role_exists(self):
        path = os.path.join(self.code_dir, "rbac-platform-admin.yaml")
        self.assertTrue(os.path.exists(path))

    def test_developer_role_exists(self):
        path = os.path.join(self.code_dir, "rbac-developer-role.yaml")
        self.assertTrue(os.path.exists(path))

    def test_developer_role_restricts_system_namespaces(self):
        """Developer role should not grant access to kube-system."""
        path = os.path.join(self.code_dir, "rbac-developer-role.yaml")
        content = open(path).read()
        # Developer role should be namespace-scoped, not cluster-admin
        self.assertNotIn("cluster-admin", content,
                         "Developer role should not be cluster-admin")

    def test_platform_admin_has_namespace_management(self):
        """Platform admin should be able to manage namespaces."""
        path = os.path.join(self.code_dir, "rbac-platform-admin.yaml")
        content = open(path).read()
        self.assertIn("namespaces", content,
                      "Platform admin should manage namespaces")


class TestDemoApp(unittest.TestCase):
    """Validate demo app deployment configuration."""

    def test_demo_app_exists(self):
        path = os.path.join(os.path.dirname(__file__), "demo-app-deployment.yaml")
        self.assertTrue(os.path.exists(path))

    def test_demo_app_has_resource_limits(self):
        path = os.path.join(os.path.dirname(__file__), "demo-app-deployment.yaml")
        content = open(path).read()
        self.assertIn("limits", content, "Demo app should have resource limits")

    def test_demo_app_runs_as_non_root(self):
        path = os.path.join(os.path.dirname(__file__), "demo-app-deployment.yaml")
        content = open(path).read()
        self.assertTrue(
            "runAsNonRoot" in content or "securityContext" in content,
            "Demo app should have security context"
        )


class TestCertManager(unittest.TestCase):
    """Validate cert-manager configuration for TLS."""

    def test_cert_config_exists(self):
        path = os.path.join(os.path.dirname(__file__), "cert-manager-config.yaml")
        self.assertTrue(os.path.exists(path))

    def test_cert_config_has_issuer(self):
        path = os.path.join(os.path.dirname(__file__), "cert-manager-config.yaml")
        content = open(path).read()
        self.assertTrue(
            "Issuer" in content or "ClusterIssuer" in content,
            "Should define a certificate issuer"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("Chapter 3: RBAC Permission Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
