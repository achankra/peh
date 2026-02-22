#!/usr/bin/env python3
"""
Chapter 6: Portal Health Tests
================================
Validates Backstage portal configuration and catalog setup.

Usage:
    python test-portal-health.py
"""

import os
import unittest


class TestBackstageConfig(unittest.TestCase):
    """Validate Backstage deployment configuration."""

    def setUp(self):
        self.code_dir = os.path.dirname(__file__)

    def test_helm_values_exist(self):
        self.assertTrue(os.path.exists(os.path.join(self.code_dir, "backstage-helm-values.yaml")))

    def test_app_config_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.code_dir, "app-config.production.yaml")))

    def test_catalog_info_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.code_dir, "catalog-info.yaml")))

    def test_app_config_has_auth(self):
        content = open(os.path.join(self.code_dir, "app-config.production.yaml")).read()
        self.assertTrue("auth" in content.lower(), "App config should include auth settings")

    def test_catalog_has_api_version(self):
        content = open(os.path.join(self.code_dir, "catalog-info.yaml")).read()
        self.assertIn("apiVersion", content, "Catalog info should have apiVersion")


class TestPortalScripts(unittest.TestCase):
    """Validate portal-related scripts."""

    def test_evaluation_framework_valid(self):
        path = os.path.join(os.path.dirname(__file__), "portal-evaluation-framework.py")
        with open(path) as f:
            compile(f.read(), path, "exec")

    def test_catalog_registration_valid(self):
        path = os.path.join(os.path.dirname(__file__), "register-catalog-entities.py")
        with open(path) as f:
            compile(f.read(), path, "exec")


if __name__ == "__main__":
    print("=" * 60)
    print("Chapter 6: Portal Health Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
