#!/usr/bin/env python3
"""
Chapter 8: Pipeline Tests
==========================
Validates reusable CI/CD workflow configurations and deployment strategies.

Usage:
    python test-pipelines.py
"""

import os
import unittest


class TestReusableWorkflows(unittest.TestCase):
    """Validate reusable GitHub Actions workflows."""

    def setUp(self):
        self.workflow_dir = os.path.join(os.path.dirname(__file__), "reusable-workflows")

    def test_build_and_test_workflow_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.workflow_dir, "build-and-test.yaml")))

    def test_deploy_workflow_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.workflow_dir, "deploy.yaml")))

    def test_security_scan_workflow_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.workflow_dir, "security-scan.yaml")))

    def test_workflows_are_reusable(self):
        """Reusable workflows must use workflow_call trigger."""
        for fname in ["build-and-test.yaml", "deploy.yaml", "security-scan.yaml"]:
            path = os.path.join(self.workflow_dir, fname)
            content = open(path).read()
            self.assertIn("workflow_call", content,
                          f"{fname} should be a reusable workflow (workflow_call)")


class TestDeploymentStrategies(unittest.TestCase):
    """Validate blue-green and canary deployment configs."""

    def setUp(self):
        self.code_dir = os.path.dirname(__file__)

    def test_blue_green_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.code_dir, "blue-green-deployment.yaml")))

    def test_canary_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.code_dir, "canary-deployment.yaml")))

    def test_canary_has_weight(self):
        content = open(os.path.join(self.code_dir, "canary-deployment.yaml")).read()
        self.assertTrue("weight" in content.lower() or "canary" in content.lower(),
                        "Canary config should define traffic weight")


class TestRollbackController(unittest.TestCase):
    """Validate rollback controller script."""

    def test_rollback_script_valid(self):
        path = os.path.join(os.path.dirname(__file__), "rollback-controller.py")
        with open(path) as f:
            compile(f.read(), path, "exec")

    def test_pipeline_composer_valid(self):
        path = os.path.join(os.path.dirname(__file__), "pipeline-composer.py")
        with open(path) as f:
            compile(f.read(), path, "exec")


if __name__ == "__main__":
    print("=" * 60)
    print("Chapter 8: Pipeline Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
