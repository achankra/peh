#!/usr/bin/env python3
"""
Chapter 7: Onboarding API Tests
=================================
Tests for the onboarding API and bootstrapping workflow.

Usage:
    python test-onboarding.py
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

CODE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CODE_DIR)

from audit_logger import AuditLogger  # noqa: E402


def read_file(name):
    with open(os.path.join(CODE_DIR, name)) as f:
        return f.read()


def assert_compiles(name):
    path = os.path.join(CODE_DIR, name)
    with open(path) as f:
        compile(f.read(), path, "exec")


class TestOnboardingAPI(unittest.TestCase):
    """Validate onboarding API configuration."""

    def test_openapi_spec_exists(self):
        self.assertTrue(os.path.exists(os.path.join(CODE_DIR, "openapi-spec.yaml")))

    def test_api_script_valid(self):
        assert_compiles("onboarding_api.py")

    def test_openapi_has_team_endpoints(self):
        self.assertIn("/teams", read_file("openapi-spec.yaml"), "Should define /teams endpoint")

    def test_bootstrap_yaml_exists(self):
        self.assertTrue(os.path.exists(os.path.join(CODE_DIR, "namespace-bootstrap.yaml")))

    def test_bootstrap_has_resource_quota(self):
        self.assertIn(
            "ResourceQuota", read_file("namespace-bootstrap.yaml"),
            "Bootstrap should include ResourceQuota"
        )


class TestSupportScripts(unittest.TestCase):
    """Validate supporting onboarding scripts."""

    def test_permission_delegation_valid(self):
        assert_compiles("permission_delegation.py")

    def test_project_bootstrapper_valid(self):
        assert_compiles("project_bootstrapper.py")

    def test_audit_logger_valid(self):
        assert_compiles("audit_logger.py")


class TestTeamHistory(unittest.TestCase):
    """get_team_history returns the team's events, including sub-resources."""

    def test_includes_members_and_projects_but_not_other_teams(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger = AuditLogger(os.path.join(tmp, "audit.log"))
            for resource_id in [
                "platform",                  # team itself
                "platform/bob@example.com",  # member
                "platform/my-api",           # project
                "platformer",                # different team, same prefix
                "other/platform",            # different team, team name later
            ]:
                logger.log_event("test", "system", "x", resource_id, "success")

            history = logger.get_team_history("platform")

        self.assertEqual(
            sorted(e["resource_id"] for e in history),
            ["platform", "platform/bob@example.com", "platform/my-api"],
        )


class TestPermissionDelegationCLI(unittest.TestCase):
    """The grant/revoke CLI honours the acting user passed as the last argument."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.env = {
            **os.environ,
            "PERMISSIONS_DB_PATH": os.path.join(tmp.name, "permissions.json"),
            "ONBOARDING_AUDIT_LOG_PATH": os.path.join(tmp.name, "audit.log"),
        }

    def cli(self, *args):
        result = subprocess.run(
            [sys.executable, os.path.join(CODE_DIR, "permission_delegation.py"), *args],
            capture_output=True, text=True, env=self.env, check=True,
        )
        return result.stdout.strip()

    def test_lead_can_revoke_but_default_actor_and_developer_cannot(self):
        self.cli("grant-role", "platform", "alice@example.com", "lead")
        self.cli("grant-role", "platform", "bob@example.com", "developer")

        # Default actor (admin@example.com) has no permissions in the team
        self.assertIn(
            "cannot revoke",
            self.cli("revoke", "platform", "bob@example.com", "manage-ci-cd"),
        )
        # A developer cannot delegate a permission they do not hold
        self.assertIn(
            "cannot revoke",
            self.cli("revoke", "platform", "alice@example.com", "manage-team", "bob@example.com"),
        )
        self.assertIn("True", self.cli("check", "platform", "bob@example.com", "manage-ci-cd"))

        # The lead named on the command line can revoke
        self.assertEqual(
            self.cli("revoke", "platform", "bob@example.com", "manage-ci-cd", "alice@example.com"),
            "Revoked manage-ci-cd from bob@example.com",
        )
        self.assertIn("False", self.cli("check", "platform", "bob@example.com", "manage-ci-cd"))


class ApiTestCase(unittest.TestCase):
    """Base class: Flask test client with kubectl, the audit log and the environment isolated."""

    def setUp(self):
        try:
            import onboarding_api
        except ImportError as e:  # Flask not installed
            self.skipTest(f"onboarding_api needs its dependencies: {e}")
        self.api = onboarding_api

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        patches = [
            mock.patch.object(
                onboarding_api, "audit_logger", AuditLogger(os.path.join(tmp.name, "audit.log"))
            ),
            mock.patch.object(onboarding_api, "teams_db", {}),
            mock.patch.object(onboarding_api, "members_db", {}),
            mock.patch.dict(os.environ),  # restored on cleanup
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        os.environ.pop("KEYCLOAK_ADMIN_CLIENT_SECRET", None)  # Keycloak is opt-in

    def create_team(self, **extra):
        """POST /teams with kubectl mocked; return the Namespace labels it applied."""
        body = {"display_name": "Test", "lead": "alice@example.com", **extra}
        ok = mock.Mock(returncode=0, stderr=b"")
        with mock.patch.object(self.api.subprocess, "run", return_value=ok) as run:
            response = self.api.app.test_client().post("/teams", json=body)
        self.assertEqual(response.status_code, 201, response.get_data(as_text=True))
        namespace = json.loads(run.call_args_list[0].kwargs["input"])
        return namespace["metadata"]["labels"]


class TestNamespaceLabels(ApiTestCase):
    """POST /teams puts the labels required by the Gatekeeper policy on the namespace."""

    def test_defaults(self):
        labels = self.create_team(name="platform")
        self.assertEqual(labels["team"], "platform")
        self.assertEqual(labels["environment"], "dev")
        self.assertEqual(labels["cost-center"], "1000")

    def test_request_overrides(self):
        # cost_center sent as a number must still become a string label value
        labels = self.create_team(name="billing", environment="prod", cost_center=4242)
        self.assertEqual(labels["environment"], "prod")
        self.assertEqual(labels["cost-center"], "4242")


class TestKeycloakOptIn(ApiTestCase):
    """POST /teams creates Keycloak groups only when Keycloak is configured."""

    def create_team_with_keycloak(self, fake_keycloak, secret):
        """Create team 'platform'; `fake_keycloak` stands in for the keycloak_groups module."""
        if secret:
            os.environ["KEYCLOAK_ADMIN_CLIENT_SECRET"] = secret
        with mock.patch.dict(sys.modules, {"keycloak_groups": fake_keycloak}):
            self.create_team(name="platform")

    def test_skipped_without_secret(self):
        fake = mock.Mock()
        self.create_team_with_keycloak(fake, secret=None)
        fake.provision_team_groups.assert_not_called()

    def test_groups_provisioned_for_the_lead_when_configured(self):
        fake = mock.Mock()
        self.create_team_with_keycloak(fake, secret="s3cret")
        fake.provision_team_groups.assert_called_once_with("platform", [], "alice@example.com")

    def test_keycloak_failure_does_not_fail_team_creation(self):
        fake = mock.Mock()
        fake.provision_team_groups.side_effect = RuntimeError("keycloak down")
        self.create_team_with_keycloak(fake, secret="s3cret")  # create_team asserts HTTP 201
        self.assertIn("platform", self.api.teams_db)


if __name__ == "__main__":
    print("=" * 60)
    print("Chapter 7: Onboarding API Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
