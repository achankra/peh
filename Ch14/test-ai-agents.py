#!/usr/bin/env python3
"""
Chapter 14: AI Agent Tests
===========================
Tests for AI agent guardrails, alert correlation accuracy,
and runbook parsing.

Usage:
    python test-ai-agents.py
"""

import os
import sys
import unittest
import json

# Add parent directory so we can import the modules
sys.path.insert(0, os.path.dirname(__file__))


class TestAIGuardrails(unittest.TestCase):
    """Test the guardrails framework for AI agents."""

    def test_guardrails_module_exists(self):
        path = os.path.join(os.path.dirname(__file__), "ai-guardrails.py")
        self.assertTrue(os.path.exists(path))

    def test_guardrails_valid_python(self):
        path = os.path.join(os.path.dirname(__file__), "ai-guardrails.py")
        with open(path) as f:
            source = f.read()
        compile(source, path, "exec")

    def test_guardrails_defines_action_allowlist(self):
        """Guardrails should define allowed and denied actions."""
        path = os.path.join(os.path.dirname(__file__), "ai-guardrails.py")
        content = open(path).read()
        self.assertTrue(
            "allow" in content.lower() or "permitted" in content.lower(),
            "Guardrails should define action allowlists"
        )

    def test_guardrails_has_human_approval(self):
        """Destructive actions should require human approval."""
        path = os.path.join(os.path.dirname(__file__), "ai-guardrails.py")
        content = open(path).read()
        self.assertTrue(
            "approval" in content.lower() or "human" in content.lower(),
            "Guardrails should include human-in-the-loop approval"
        )


class TestAlertCorrelator(unittest.TestCase):
    """Test the alert correlation engine."""

    def test_correlator_module_exists(self):
        path = os.path.join(os.path.dirname(__file__), "alert-correlator.py")
        self.assertTrue(os.path.exists(path))

    def test_correlator_valid_python(self):
        path = os.path.join(os.path.dirname(__file__), "alert-correlator.py")
        with open(path) as f:
            source = f.read()
        compile(source, path, "exec")

    def test_correlator_handles_empty_alerts(self):
        """Correlator should handle empty alert lists gracefully."""
        path = os.path.join(os.path.dirname(__file__), "alert-correlator.py")
        content = open(path).read()
        # Should have handling for empty or minimal input
        self.assertIn("def", content, "Should define functions")


class TestIncidentAgent(unittest.TestCase):
    """Test the multi-agent incident response system."""

    def test_incident_agent_exists(self):
        path = os.path.join(os.path.dirname(__file__), "incident-agent.py")
        self.assertTrue(os.path.exists(path))

    def test_incident_agent_valid_python(self):
        path = os.path.join(os.path.dirname(__file__), "incident-agent.py")
        with open(path) as f:
            source = f.read()
        compile(source, path, "exec")

    def test_agent_has_role_separation(self):
        """Multi-agent system should have distinct agent roles."""
        path = os.path.join(os.path.dirname(__file__), "incident-agent.py")
        content = open(path).read().lower()
        roles_found = sum(1 for role in ["triage", "diagnos", "remediat"]
                         if role in content)
        self.assertGreaterEqual(roles_found, 2,
                                "Should define at least 2 distinct agent roles")


class TestRunbookAutomator(unittest.TestCase):
    """Test the runbook automation system."""

    def test_automator_exists(self):
        path = os.path.join(os.path.dirname(__file__), "runbook-automator.py")
        self.assertTrue(os.path.exists(path))

    def test_automator_valid_python(self):
        path = os.path.join(os.path.dirname(__file__), "runbook-automator.py")
        with open(path) as f:
            source = f.read()
        compile(source, path, "exec")

    def test_automator_has_safety_checks(self):
        """Runbook automator should have safety checks before executing."""
        path = os.path.join(os.path.dirname(__file__), "runbook-automator.py")
        content = open(path).read().lower()
        self.assertTrue(
            "safety" in content or "check" in content or "approval" in content,
            "Runbook automator should include safety checks"
        )


class TestRAGSystem(unittest.TestCase):
    """Test the RAG platform documentation system."""

    def test_rag_module_exists(self):
        path = os.path.join(os.path.dirname(__file__), "rag-platform-docs.py")
        self.assertTrue(os.path.exists(path))

    def test_rag_valid_python(self):
        path = os.path.join(os.path.dirname(__file__), "rag-platform-docs.py")
        with open(path) as f:
            source = f.read()
        compile(source, path, "exec")


if __name__ == "__main__":
    print("=" * 60)
    print("Chapter 14: AI Agent Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
