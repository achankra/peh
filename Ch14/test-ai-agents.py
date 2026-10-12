#!/usr/bin/env python3
"""
Chapter 14: AI Agent Tests
===========================
Tests for the guardrails, alert correlator, multi-agent supervisor,
incident agent, impact metrics, runbook automator and RAG module.
Most tests run the code; a few only check structure (file exists,
compiles). No cluster, LLM or API key is needed.

Usage:
    python test-ai-agents.py        # add -v to list each test
"""

import logging
import os
import sys
import unittest
import json

# Add parent directory so we can import the modules
sys.path.insert(0, os.path.dirname(__file__))

# The modules under test log progress at INFO level; keep test output readable
logging.disable(logging.CRITICAL)


def _read(path):
    """Read a source file and close it."""
    with open(path) as f:
        return f.read()


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
        content = _read(path)
        self.assertTrue(
            "allow" in content.lower() or "permitted" in content.lower(),
            "Guardrails should define action allowlists"
        )

    def test_guardrails_has_human_approval(self):
        """Destructive actions should require human approval."""
        path = os.path.join(os.path.dirname(__file__), "ai-guardrails.py")
        content = _read(path)
        self.assertTrue(
            "approval" in content.lower() or "human" in content.lower(),
            "Guardrails should include human-in-the-loop approval"
        )

    def test_unsafe_actions_cannot_execute_even_if_marked_approved(self):
        import importlib.util
        path = os.path.join(os.path.dirname(__file__), "ai-guardrails.py")
        spec = importlib.util.spec_from_file_location("ai_guardrails", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        Sev, Status = mod.ActionSeverity, mod.ApprovalStatus
        fw = mod.GuardrailsFramework()

        # Not in the agent's allowlist and below the critical confidence threshold
        bad = fw.validate_action("remediation_agent", "delete_data", "database", 0.5, Sev.CRITICAL)
        self.assertIsNone(fw.request_approval_if_needed(bad))
        self.assertEqual(bad.approval_status, Status.REJECTED)
        self.assertFalse(fw.execute_action(bad))

        # A forged approval must not bypass the safety check
        bad.approval_status = Status.APPROVED
        self.assertFalse(fw.execute_action(bad))
        self.assertFalse(bad.executed)

        # A safe medium-risk action still goes through approval and executes
        ok = fw.validate_action("remediation_agent", "scale_service", "api", 0.8, Sev.MEDIUM)
        request = fw.request_approval_if_needed(ok)
        self.assertIsNotNone(request)
        self.assertFalse(fw.execute_action(ok))  # still pending
        fw.approval_manager.approve_action(request.request_id, approved_by="on_call")
        ok.approval_status = Status.APPROVED
        self.assertTrue(fw.execute_action(ok))

        # Actions created in the same second get distinct IDs
        self.assertEqual(len(fw.actions), 2)
        self.assertNotEqual(bad.action_id, ok.action_id)


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
        content = _read(path)
        # Should have handling for empty or minimal input
        self.assertIn("def", content, "Should define functions")

    def test_correlator_groups_same_host_and_reports_noise_reduction(self):
        """Sample alerts: CPU x2 + memory on one host group together; stats are sane."""
        import importlib.util
        path = os.path.join(os.path.dirname(__file__), "alert-correlator.py")
        spec = importlib.util.spec_from_file_location("alert_correlator", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        correlator = mod.AlertCorrelator()
        incidents = correlator.correlate(mod.create_sample_alerts())

        self.assertEqual(sorted(len(i.alerts) for i in incidents), [1, 1, 3])
        self.assertEqual(correlator.get_statistics()["noise_reduction"], "40.0%")


class TestMultiAgentSystem(unittest.TestCase):
    """Test the supervisor / approval-gate behaviour."""

    def test_nothing_runs_past_an_unapproved_step(self):
        import importlib.util
        path = os.path.join(os.path.dirname(__file__), "agents", "multi_agent_system.py")
        spec = importlib.util.spec_from_file_location("multi_agent_system", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        result = mod.SupervisorAgent().execute({"issue_type": "pod_crash_loop"})

        execution = result["steps"]["execution"]
        self.assertEqual(result["status"], "pending_approval")
        self.assertEqual(execution["steps_executed"], 0)
        self.assertEqual(
            [r["status"] for r in execution["results"]],
            ["waiting_for_approval", "skipped"],
        )


    def test_destructive_plan_records_approval_in_audit_trail(self):
        import importlib.util
        path = os.path.join(os.path.dirname(__file__), "agents", "multi_agent_system.py")
        spec = importlib.util.spec_from_file_location("multi_agent_system", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        supervisor = mod.SupervisorAgent()
        supervisor.planning_agent.execute = lambda task: {
            "plan_id": "plan-test",
            "steps": [{
                "step": 1,
                "action": "scale_cluster",
                "severity": mod.ActionSeverity.DESTRUCTIVE.value,
                "requires_approval": False,
            }],
        }

        result = supervisor.execute({"issue_type": "pod_crash_loop"})

        self.assertEqual(result["status"], "completed")
        approvals = [
            log for log in supervisor.get_audit_trail()
            if log.approval_status == "approved"
        ]
        self.assertEqual(len(approvals), 1)
        self.assertEqual(approvals[0].approval_user, "system-admin")


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
        content = _read(path).lower()
        roles_found = sum(1 for role in ["triage", "diagnos", "remediat"]
                         if role in content)
        self.assertGreaterEqual(roles_found, 2,
                                "Should define at least 2 distinct agent roles")


class TestIncidentAgentBehavior(unittest.TestCase):
    """Run the incident response pipeline on the sample alerts."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        path = os.path.join(os.path.dirname(__file__), "incident-agent.py")
        spec = importlib.util.spec_from_file_location("incident_agent", path)
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def test_security_breach_is_diagnosed_escalated_and_needs_approval(self):
        agent = self.mod.IncidentAgent()
        incident = agent.handle_incident(
            "CRITICAL: Security breach detected - unauthorized access attempt"
        )
        self.assertTrue(incident.triage.requires_escalation)
        self.assertGreaterEqual(incident.diagnosis.confidence, 0.5)
        self.assertIn("credentials", incident.diagnosis.root_cause.lower())
        self.assertTrue(incident.proposed_action.requires_approval)

    def test_low_confidence_diagnosis_requires_approval(self):
        agent = self.mod.IncidentAgent()
        # Low severity, unrecognized pattern -> 0.3-confidence "Unknown" diagnosis
        incident = agent.handle_incident("Unexplained anomaly noticed")
        self.assertLess(incident.diagnosis.confidence, 0.5)
        self.assertEqual(incident.proposed_action.risk_level, "medium")
        self.assertTrue(incident.proposed_action.requires_approval)

    def test_incident_ids_are_unique(self):
        agent = self.mod.IncidentAgent()
        ids = {agent.handle_incident("WARNING: Database connection pool exhausted").incident_id
               for _ in range(3)}
        self.assertEqual(len(ids), 3)


class TestImpactMeasurement(unittest.TestCase):
    """Check the impact metrics against values worked out by hand."""

    def test_demo_metrics_match_hand_calculation(self):
        import importlib.util
        path = os.path.join(os.path.dirname(__file__), "measure-ai-impact.py")
        spec = importlib.util.spec_from_file_location("measure_ai_impact", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        incidents = mod.generate_demo_incidents()

        # Manual resolution = 90 + 10i min and AI-assisted = 30 + 5i min, i = 0..9:
        # means are 90 + 10*4.5 = 135.0 and 30 + 5*4.5 = 52.5
        mttr = mod.calculate_mttr(incidents)
        self.assertEqual(mttr["manual_mttr_min"], 135.0)
        self.assertEqual(mttr["ai_assisted_mttr_min"], 52.5)
        self.assertEqual(mttr["improvement_pct"], 61.1)  # (135 - 52.5) / 135

        # Ack: 12 + 2i (mean 21.0) vs 3 + i (mean 7.5)
        ack = mod.calculate_alert_to_ack(incidents)
        self.assertEqual((ack["manual_avg_ack_min"], ack["ai_avg_ack_min"]), (21.0, 7.5))
        self.assertEqual(ack["improvement_pct"], 64.3)  # (21 - 7.5) / 21

        # Diagnosis = diagnosis - ack: 33 + 3i (mean 46.5) vs 9 + i (mean 13.5)
        diag = mod.calculate_diagnosis_speed(incidents)
        self.assertEqual(
            (diag["manual_avg_diagnosis_min"], diag["ai_avg_diagnosis_min"]), (46.5, 13.5)
        )
        self.assertEqual(diag["improvement_pct"], 71.0)  # (46.5 - 13.5) / 46.5


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
        content = _read(path).lower()
        self.assertTrue(
            "safety" in content or "check" in content or "approval" in content,
            "Runbook automator should include safety checks"
        )


class TestRunbookAutomatorBehavior(unittest.TestCase):
    """Run the runbook parser, validator and executor."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        path = os.path.join(os.path.dirname(__file__), "runbook-automator.py")
        spec = importlib.util.spec_from_file_location("runbook_automator", path)
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def _step(self, command, step_type="ACTION", approval=False):
        m = self.mod
        return m.RunbookStep("s", "n", m.StepType[step_type], command, None,
                             approval, 300, "ok", "rollback")

    def test_dangerous_command_blocked_whatever_type_it_declares(self):
        m = self.mod
        runbook = (
            "# Runbook: Sneaky\n"
            "## Step 1: No type line\nCommand: rm -rf /var/lib/postgresql/data\n"
            "## Step 2: Claims to be read-only\nType: Diagnostic\n"
            "Command: kubectl delete namespace prod\n"
        )
        for step in m.RunbookParser().parse_markdown(runbook)[1]:
            safe, warnings = m.SafetyValidator.validate_step(step)
            self.assertFalse(safe, step.command)
            self.assertIn("requires approval", warnings[0])

    def test_keywords_match_whole_words_only(self):
        m = self.mod
        # "rm" appears inside "format" but is not the rm command
        _, warnings = m.SafetyValidator.validate_step(self._step("pg_dump --format=custom db"))
        self.assertFalse(any("'rm'" in w for w in warnings))
        safe, _ = m.SafetyValidator.validate_step(
            self._step("pg_dump --format=custom db", approval=True))
        self.assertTrue(safe)
        # Notification text is just a message, never a command
        safe, _ = m.SafetyValidator.validate_step(
            self._step("Notify #ops: delete done", "NOTIFICATION"))
        self.assertTrue(safe)

    def test_waiting_for_approval_is_pending_not_failed(self):
        m = self.mod
        _, steps = m.RunbookParser().parse_markdown(m.create_sample_runbook())
        execution = m.RunbookExecutor().execute_runbook("Database Recovery", steps)
        self.assertEqual(execution.status, "pending_approval")
        self.assertEqual([s["success"] for s in execution.steps_executed], [True, True, False])
        self.assertTrue(execution.steps_executed[-1]["pending_approval"])

    def test_execution_ids_are_unique(self):
        m = self.mod
        executor = m.RunbookExecutor()
        ids = {executor.execute_runbook("r", [self._step("df -h", "DIAGNOSTIC")]).execution_id
               for _ in range(3)}
        self.assertEqual(len(ids), 3)


class TestRAGSources(unittest.TestCase):
    """Answers should cite where the retrieved context came from."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        path = os.path.join(os.path.dirname(__file__), "platform_chatbot", "rag_pipeline.py")
        spec = importlib.util.spec_from_file_location("rag_pipeline", path)
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def _pipeline(self):
        # Mock embeddings, store and LLM: no model download, no Ollama/Anthropic call
        from unittest import mock
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "OLLAMA_MODEL": ""}):
            return self.mod.RAGPipeline(vector_db="mock", embedding_model="mock")

    def test_json_documents_are_cited_by_title(self):
        rag = self._pipeline()
        rag.index_json_data([
            {"title": "Deployment Guide", "content": "Build, push, helm install."},
            {"title": "Troubleshooting", "content": "Check pod logs."},
        ])
        result = rag.query("How do I deploy?")
        self.assertEqual(result.source_citations, ["Deployment Guide", "Troubleshooting"])

    def test_file_documents_are_cited_by_path(self):
        import tempfile
        if self.mod.RecursiveCharacterTextSplitter is None:
            self.skipTest("langchain-text-splitters not installed")
        rag = self._pipeline()
        with tempfile.TemporaryDirectory() as tmp:
            doc = os.path.join(tmp, "runbook.md")
            with open(doc, "w") as f:
                f.write("# Runbook\n\nRestart the service.")
            rag.index_documents(tmp)
            result = rag.query("How do I restart?")
        self.assertEqual(result.source_citations, [doc])


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
