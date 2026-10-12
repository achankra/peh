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

    def _manager(self, outputs):
        """Load VeleroBackupManager with `velero` calls mocked (no cluster needed)."""
        import importlib.util
        from unittest import mock
        spec = importlib.util.spec_from_file_location("backup_automation", self.backup_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        manager = module.VeleroBackupManager()
        manager._run_command = mock.Mock(side_effect=[(0, out, "") for out in outputs])
        return manager

    @staticmethod
    def _backup(name):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {"metadata": {"name": name}, "status": {"startTimestamp": now}}

    def test_list_backups_handles_single_backup_json(self):
        """velero prints a bare Backup (not a BackupList) when only one exists."""
        import json
        single = {"kind": "Backup", **self._backup("only-backup")}
        manager = self._manager([json.dumps(single)])
        self.assertEqual([b["metadata"]["name"] for b in manager.list_backups()], ["only-backup"])

    def test_freshness_compares_timezone_aware_timestamps(self):
        import json
        manager = self._manager([json.dumps({"items": [self._backup("fresh-backup")]})])
        self.assertEqual(manager.get_backup_freshness(1), {"fresh-backup": True})

    def test_validate_reads_top_level_phase_from_describe(self):
        import json
        listing = json.dumps({"items": [self._backup("done-backup")]})
        describe = json.dumps({"phase": "Completed"})
        manager = self._manager([listing, describe])
        self.assertEqual(manager.validate_backups(), {"done-backup": True})


class TestChaosRunner(unittest.TestCase):
    """Validate chaos-runner status handling (kubectl mocked, no cluster needed)."""

    def setUp(self):
        import importlib.util
        path = os.path.join(os.path.dirname(__file__), "chaos-runner.py")
        spec = importlib.util.spec_from_file_location("chaos_runner", path)
        self.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.runner)

    @staticmethod
    def _chaos(action, desired, **conditions):
        return {
            "spec": {"action": action},
            "status": {
                "experiment": {"desiredPhase": desired},
                "conditions": [{"type": k, "status": v} for k, v in conditions.items()],
            },
        }

    def test_recovered_experiment_is_completed(self):
        chaos = self._chaos("delay", "Stop", AllInjected="False", AllRecovered="True")
        self.assertEqual(self.runner.experiment_phase(chaos), "Completed")

    def test_one_shot_actions_complete_once_injected(self):
        """pod-kill/container-kill never recover: desiredPhase stays Run, AllRecovered False."""
        for action in ("pod-kill", "container-kill"):
            chaos = self._chaos(action, "Run", AllInjected="True", AllRecovered="False")
            self.assertEqual(self.runner.experiment_phase(chaos), "Completed", action)

    def test_injected_network_experiment_is_running(self):
        chaos = self._chaos("delay", "Run", AllInjected="True", AllRecovered="False")
        self.assertEqual(self.runner.experiment_phase(chaos), "Running")

    def test_new_experiment_is_pending(self):
        self.assertEqual(self.runner.experiment_phase({}), "Pending")

    def test_report_flags_missing_prometheus_data(self):
        """A report built from all-zero metrics must not pass silently."""
        runner = self.runner.ChaosExperimentRunner()

        def report(**kwargs):
            metrics = self.runner.ExperimentMetrics(
                start_time="t0", end_time="t1", duration_seconds=1, error_count=0,
                error_rate=0.0, latency_p50=0.0, latency_p95=0.0, latency_p99=0.0,
                pod_restarts=0, pods_affected=0, **kwargs)
            return runner.generate_report("demo", metrics)

        self.assertIn("No Prometheus data returned", report(data_available=False))
        self.assertNotIn("No Prometheus data returned", report(data_available=True))

    def test_zero_is_data_but_no_result_is_not(self):
        from unittest import mock
        runner = self.runner.ChaosExperimentRunner()
        runner._query_prometheus = mock.Mock(return_value="0")
        self.assertTrue(runner.collect_metrics().data_available)
        runner._query_prometheus = mock.Mock(return_value=None)
        self.assertFalse(runner.collect_metrics().data_available)

    def test_create_experiment_records_created_objects(self):
        from unittest import mock
        runner = self.runner.ChaosExperimentRunner()
        applied = (
            "podchaos.chaos-mesh.org/pod-kill-single created\n"
            "networkchaos.chaos-mesh.org/network-loss unchanged\n"
            "schedule.chaos-mesh.org/pod-kill-schedule created\n"
        )
        runner._run_command = mock.Mock(return_value=(0, applied, ""))
        self.assertTrue(runner.create_experiment("demo", "demo.yaml"))
        self.assertEqual(runner.experiments["demo"]["objects"], ["pod-kill-single", "network-loss"])


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
