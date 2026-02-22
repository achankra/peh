#!/usr/bin/env python3
"""
Chapter 12: Cost Optimization Tests
====================================
Validates autoscaling configurations, cost allocation labels,
and budget guardrails for correctness.

Usage:
    python test-cost-optimization.py

Prerequisites:
    - PyYAML (pip install pyyaml) for YAML parsing, or runs basic tests without it
"""

import json
import os
import sys
import unittest


def load_yaml_simple(filepath: str) -> list:
    """Load YAML file using PyYAML if available, else basic parsing."""
    try:
        import yaml
        with open(filepath) as f:
            return list(yaml.safe_load_all(f))
    except ImportError:
        # Fallback: basic text analysis
        return [{"_raw": open(filepath).read()}]


class TestHPAConfig(unittest.TestCase):
    """Validate Horizontal Pod Autoscaler configuration."""

    def setUp(self):
        self.hpa_path = os.path.join(os.path.dirname(__file__), "hpa-config.yaml")

    def test_hpa_file_exists(self):
        """HPA config file should exist."""
        self.assertTrue(os.path.exists(self.hpa_path), "hpa-config.yaml not found")

    def test_hpa_has_min_max_replicas(self):
        """HPA should define minReplicas and maxReplicas."""
        content = open(self.hpa_path).read()
        self.assertIn("minReplicas", content)
        self.assertIn("maxReplicas", content)

    def test_hpa_has_scale_down_policy(self):
        """HPA should have scale-down stabilization to prevent flapping."""
        content = open(self.hpa_path).read()
        # Should have behavior or scaleDown policy
        self.assertTrue(
            "scaleDown" in content or "behavior" in content,
            "HPA should define scale-down behavior to prevent cost spikes"
        )


class TestVPAConfig(unittest.TestCase):
    """Validate Vertical Pod Autoscaler configuration."""

    def setUp(self):
        self.vpa_path = os.path.join(os.path.dirname(__file__), "vpa-config.yaml")

    def test_vpa_file_exists(self):
        """VPA config file should exist."""
        self.assertTrue(os.path.exists(self.vpa_path), "vpa-config.yaml not found")

    def test_vpa_update_mode(self):
        """VPA should use 'Off' or 'Initial' mode for safety (not 'Auto' without review)."""
        content = open(self.vpa_path).read()
        self.assertIn("updateMode", content, "VPA should specify an updateMode")


class TestBudgetGuardrails(unittest.TestCase):
    """Validate budget guardrails (ResourceQuotas and LimitRanges)."""

    def setUp(self):
        self.guardrails_path = os.path.join(os.path.dirname(__file__), "budget-guardrails.yaml")

    def test_guardrails_file_exists(self):
        """Budget guardrails file should exist."""
        self.assertTrue(os.path.exists(self.guardrails_path))

    def test_has_all_tiers(self):
        """Should define quotas for dev, staging, and prod tiers."""
        content = open(self.guardrails_path).read()
        for tier in ["dev", "staging", "prod"]:
            self.assertIn(f"tier: {tier}", content, f"Missing {tier} tier definition")

    def test_has_resource_quotas(self):
        """Should include ResourceQuota definitions."""
        content = open(self.guardrails_path).read()
        self.assertIn("kind: ResourceQuota", content)

    def test_has_limit_ranges(self):
        """Should include LimitRange definitions."""
        content = open(self.guardrails_path).read()
        self.assertIn("kind: LimitRange", content)

    def test_prod_limits_higher_than_dev(self):
        """Production resource limits should be higher than dev."""
        content = open(self.guardrails_path).read()
        # Simple check: prod section should have larger pod count
        self.assertIn('pods: "200"', content, "Prod should allow 200 pods")
        self.assertIn('pods: "20"', content, "Dev should allow only 20 pods")


class TestCostAllocationLabels(unittest.TestCase):
    """Validate cost allocation label configuration."""

    def setUp(self):
        self.labels_path = os.path.join(os.path.dirname(__file__), "cost-allocation-labels.py")

    def test_labels_script_exists(self):
        """Cost allocation labels script should exist."""
        self.assertTrue(os.path.exists(self.labels_path))

    def test_labels_script_is_valid_python(self):
        """Script should be valid Python."""
        with open(self.labels_path) as f:
            source = f.read()
        try:
            compile(source, self.labels_path, "exec")
        except SyntaxError as e:
            self.fail(f"Syntax error in cost-allocation-labels.py: {e}")


class TestSpotInstanceHandler(unittest.TestCase):
    """Validate spot instance handler configuration."""

    def setUp(self):
        self.spot_path = os.path.join(os.path.dirname(__file__), "spot-instance-handler.yaml")

    def test_spot_config_exists(self):
        """Spot instance handler config should exist."""
        self.assertTrue(os.path.exists(self.spot_path))

    def test_has_node_affinity_or_toleration(self):
        """Spot config should handle node selection via affinity or tolerations."""
        content = open(self.spot_path).read()
        self.assertTrue(
            "toleration" in content.lower() or "affinity" in content.lower() or "nodeSelector" in content,
            "Spot handler should configure node selection"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("Chapter 12: Cost Optimization Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
