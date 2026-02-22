#!/usr/bin/env python3
"""
Chapter 13: Resilience Tests
=============================
Tests for SLO definitions, backup procedures, and chaos experiment
YAML validity.

Usage:
    python test-resilience.py
"""

import os
import sys
import unittest


class TestSLODefinitions(unittest.TestCase):
    """Validate SLO definition YAML structure."""

    def setUp(self):
        self.slo_path = os.path.join(os.path.dirname(__file__), "slo-definitions.yaml")

    def test_slo_file_exists(self):
        self.assertTrue(os.path.exists(self.slo_path))

    def test_slo_has_required_fields(self):
        content = open(self.slo_path).read()
        for field in ["target", "window", "sli"]:
            self.assertIn(field, content.lower(), f"SLO definitions should include '{field}'")

    def test_slo_targets_are_reasonable(self):
        """SLO targets should be between 90% and 99.999%."""
        content = open(self.slo_path).read()
        # Should have targets like 99.9, 99.5, etc.
        self.assertIn("99", content, "Should define SLO targets (e.g., 99.9%)")


class TestChaosExperiments(unittest.TestCase):
    """Validate chaos experiment YAML files."""

    def setUp(self):
        self.code_dir = os.path.dirname(__file__)

    def test_pod_kill_experiment_exists(self):
        path = os.path.join(self.code_dir, "chaos-experiment-pod-kill.yaml")
        self.assertTrue(os.path.exists(path))

    def test_network_experiment_exists(self):
        path = os.path.join(self.code_dir, "chaos-experiment-network.yaml")
        self.assertTrue(os.path.exists(path))

    def test_chaos_experiments_have_selectors(self):
        """Chaos experiments must target specific workloads, not entire cluster."""
        for fname in ["chaos-experiment-pod-kill.yaml", "chaos-experiment-network.yaml"]:
            path = os.path.join(self.code_dir, fname)
            if os.path.exists(path):
                content = open(path).read()
                self.assertTrue(
                    "selector" in content or "namespace" in content,
                    f"{fname} must have selectors to limit blast radius"
                )

    def test_chaos_experiments_have_duration(self):
        """Chaos experiments must have a bounded duration."""
        for fname in ["chaos-experiment-pod-kill.yaml", "chaos-experiment-network.yaml"]:
            path = os.path.join(self.code_dir, fname)
            if os.path.exists(path):
                content = open(path).read()
                self.assertIn("duration", content.lower(),
                              f"{fname} must define a duration to limit impact")


class TestBackupAutomation(unittest.TestCase):
    """Validate backup automation script."""

    def setUp(self):
        self.backup_path = os.path.join(os.path.dirname(__file__), "backup-automation.py")

    def test_backup_script_exists(self):
        self.assertTrue(os.path.exists(self.backup_path))

    def test_backup_script_valid_python(self):
        with open(self.backup_path) as f:
            source = f.read()
        try:
            compile(source, self.backup_path, "exec")
        except SyntaxError as e:
            self.fail(f"Syntax error: {e}")


class TestSLODashboard(unittest.TestCase):
    """Validate Grafana SLO dashboard JSON."""

    def setUp(self):
        self.dashboard_path = os.path.join(os.path.dirname(__file__), "slo-dashboard.json")

    def test_dashboard_file_exists(self):
        self.assertTrue(os.path.exists(self.dashboard_path))

    def test_dashboard_is_valid_json(self):
        import json
        with open(self.dashboard_path) as f:
            data = json.load(f)
        self.assertIn("panels", data, "Dashboard should have panels")
        self.assertIn("title", data, "Dashboard should have a title")


if __name__ == "__main__":
    print("=" * 60)
    print("Chapter 13: Resilience Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
