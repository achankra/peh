#!/usr/bin/env python3
"""
Chapter 7: Onboarding API Tests
=================================
Tests for the onboarding API and bootstrapping workflow.

Usage:
    python test-onboarding.py
"""

import os
import unittest


class TestOnboardingAPI(unittest.TestCase):
    """Validate onboarding API configuration."""

    def setUp(self):
        self.code_dir = os.path.dirname(__file__)

    def test_openapi_spec_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.code_dir, "openapi-spec.yaml")))

    def test_api_script_valid(self):
        path = os.path.join(self.code_dir, "onboarding-api.py")
        with open(path) as f:
            compile(f.read(), path, "exec")

    def test_openapi_has_team_endpoints(self):
        content = open(os.path.join(self.code_dir, "openapi-spec.yaml")).read()
        self.assertIn("/teams", content, "Should define /teams endpoint")

    def test_bootstrap_yaml_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.code_dir, "namespace-bootstrap.yaml")))

    def test_bootstrap_has_resource_quota(self):
        content = open(os.path.join(self.code_dir, "namespace-bootstrap.yaml")).read()
        self.assertIn("ResourceQuota", content, "Bootstrap should include ResourceQuota")


class TestSupportScripts(unittest.TestCase):
    """Validate supporting onboarding scripts."""

    def test_permission_delegation_valid(self):
        path = os.path.join(os.path.dirname(__file__), "permission-delegation.py")
        with open(path) as f:
            compile(f.read(), path, "exec")

    def test_project_bootstrapper_valid(self):
        path = os.path.join(os.path.dirname(__file__), "project-bootstrapper.py")
        with open(path) as f:
            compile(f.read(), path, "exec")

    def test_audit_logger_valid(self):
        path = os.path.join(os.path.dirname(__file__), "audit-logger.py")
        with open(path) as f:
            compile(f.read(), path, "exec")


if __name__ == "__main__":
    print("=" * 60)
    print("Chapter 7: Onboarding API Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
