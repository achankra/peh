#!/usr/bin/env python3
"""
Chapter 5: Demo App and DevEx Tests
=====================================
Validates the demo app configuration and DevEx measurement tools.

Usage:
    python test-demo-app.py
"""

import os
import unittest


class TestDemoApp(unittest.TestCase):
    """Validate demo app structure."""

    def setUp(self):
        self.demo_dir = os.path.join(os.path.dirname(__file__), "demo-app")

    def test_dockerfile_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.demo_dir, "Dockerfile")))

    def test_app_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.demo_dir, "app.py")))

    def test_k8s_manifests_exist(self):
        self.assertTrue(os.path.exists(os.path.join(self.demo_dir, "k8s-manifests.yaml")))

    def test_app_is_valid_python(self):
        path = os.path.join(self.demo_dir, "app.py")
        with open(path) as f:
            compile(f.read(), path, "exec")


class TestDevExTools(unittest.TestCase):
    """Validate DevEx measurement scripts."""

    def test_survey_script_valid(self):
        path = os.path.join(os.path.dirname(__file__), "devex-survey.py")
        with open(path) as f:
            compile(f.read(), path, "exec")

    def test_friction_analyzer_valid(self):
        path = os.path.join(os.path.dirname(__file__), "friction-analyzer.py")
        with open(path) as f:
            compile(f.read(), path, "exec")

    def test_kpi_collector_valid(self):
        path = os.path.join(os.path.dirname(__file__), "platform-kpi-collector.py")
        with open(path) as f:
            compile(f.read(), path, "exec")


if __name__ == "__main__":
    print("=" * 60)
    print("Chapter 5: Demo App and DevEx Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
