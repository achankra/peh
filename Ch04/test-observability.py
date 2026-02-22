#!/usr/bin/env python3
"""
Chapter 4: Observability Stack Tests
======================================
Validates that the observability stack configuration is correct.

Usage:
    python test-observability.py
"""

import json
import os
import unittest


class TestOTELCollector(unittest.TestCase):
    """Validate OTEL Collector configuration."""

    def setUp(self):
        self.code_dir = os.path.dirname(__file__)

    def test_collector_config_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.code_dir, "otel-collector-config.yaml")))

    def test_collector_deployment_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.code_dir, "otel-collector-deployment.yaml")))

    def test_collector_has_all_pipelines(self):
        """OTEL config should have metrics, traces, and logs pipelines."""
        content = open(os.path.join(self.code_dir, "otel-collector-config.yaml")).read()
        for pipeline in ["metrics", "traces", "logs"]:
            self.assertIn(pipeline, content, f"Missing {pipeline} pipeline")


class TestGrafanaDashboard(unittest.TestCase):
    """Validate Grafana dashboard JSON."""

    def test_dashboard_is_valid_json(self):
        path = os.path.join(os.path.dirname(__file__), "grafana-dashboard-platform.json")
        with open(path) as f:
            data = json.load(f)
        self.assertIn("panels", data)
        self.assertIn("title", data)

    def test_dashboard_has_panels(self):
        path = os.path.join(os.path.dirname(__file__), "grafana-dashboard-platform.json")
        with open(path) as f:
            data = json.load(f)
        self.assertGreater(len(data["panels"]), 0, "Dashboard should have at least one panel")


class TestAlertRules(unittest.TestCase):
    """Validate alerting rules."""

    def test_alert_rules_exist(self):
        self.assertTrue(os.path.exists(os.path.join(os.path.dirname(__file__), "alert-rules.yaml")))

    def test_alert_rules_have_severity(self):
        content = open(os.path.join(os.path.dirname(__file__), "alert-rules.yaml")).read()
        self.assertIn("severity", content, "Alert rules should have severity labels")


class TestInstrumentedApp(unittest.TestCase):
    """Validate the instrumented example app."""

    def test_app_is_valid_python(self):
        path = os.path.join(os.path.dirname(__file__), "instrument-app.py")
        with open(path) as f:
            compile(f.read(), path, "exec")


if __name__ == "__main__":
    print("=" * 60)
    print("Chapter 4: Observability Stack Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
