#!/usr/bin/env python3
"""
Platform Configuration Tests

Unit tests for validating platform configuration files.

Tests cover:
- YAML syntax validation
- Required configuration sections
- Configuration completeness
- Data type validation
- Golden path requirements
- Security policy validation

Usage:
    # Run with pytest
    python -m pytest test-platform-config.py -v

    # Or run directly
    python test-platform-config.py

    # Run specific test
    python -m pytest test-platform-config.py::test_config_structure -v
"""

import sys
from typing import Dict, Any


class TestResult:
    """Store test result."""

    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name}: {self.message}"


class PlatformConfigTests:
    """Test suite for platform configuration."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize test suite with configuration.

        Args:
            config: Dictionary containing platform configuration
        """
        self.config = config
        self.results = []

    def test_config_structure(self) -> TestResult:
        """Test that basic config structure is present."""
        try:
            assert "platform" in self.config, "Missing 'platform' section"
            assert "name" in self.config["platform"], "Missing 'platform.name'"
            assert (
                "teams" in self.config
            ), "Missing 'teams' section"
            return TestResult(
                "Config Structure",
                True,
                "Platform and teams sections present",
            )
        except AssertionError as e:
            return TestResult("Config Structure", False, str(e))

    def test_platform_principles(self) -> TestResult:
        """Test that platform principles are defined."""
        try:
            assert (
                "principles" in self.config.get("platform", {})
            ), "Missing 'platform.principles'"
            principles = self.config["platform"]["principles"]
            assert len(principles) >= 4, "Need at least 4 principles"

            required_principles = [
                "Self-Service",
                "Guardrails",
                "Golden Paths",
                "Security",
            ]
            principle_names = [p.get("name") for p in principles]

            for required in required_principles:
                assert (
                    required in principle_names
                ), f"Missing principle: {required}"

            return TestResult(
                "Platform Principles", True, f"All {len(principles)} principles defined"
            )
        except AssertionError as e:
            return TestResult("Platform Principles", False, str(e))

    def test_team_structure(self) -> TestResult:
        """Test team structure is properly defined."""
        try:
            teams = self.config.get("teams", {})
            assert "platform" in teams, "Missing 'teams.platform'"
            assert "stream-aligned" in teams, "Missing 'teams.stream-aligned'"

            platform_team = teams["platform"]
            assert "name" in platform_team, "Platform team missing 'name'"
            assert "responsibilities" in platform_team, "Platform team missing 'responsibilities'"
            assert (
                len(platform_team["responsibilities"]) >= 3
            ), "Platform team should have >= 3 responsibilities"

            return TestResult(
                "Team Structure", True, "Platform and stream-aligned teams defined"
            )
        except AssertionError as e:
            return TestResult("Team Structure", False, str(e))

    def test_golden_paths(self) -> TestResult:
        """Test golden paths are defined and complete."""
        try:
            assert (
                "golden-paths" in self.config
            ), "Missing 'golden-paths' section"
            paths = self.config["golden-paths"]
            assert len(paths) >= 2, "Need at least 2 golden paths"

            for path_name, path_config in paths.items():
                assert (
                    "name" in path_config
                ), f"Path '{path_name}' missing 'name'"
                assert (
                    "tech-stack" in path_config
                ), f"Path '{path_name}' missing 'tech-stack'"
                assert (
                    "description" in path_config
                ), f"Path '{path_name}' missing 'description'"

            return TestResult(
                "Golden Paths",
                True,
                f"{len(paths)} golden paths properly defined",
            )
        except AssertionError as e:
            return TestResult("Golden Paths", False, str(e))

    def test_security_configuration(self) -> TestResult:
        """Test security configuration is complete."""
        try:
            assert "security" in self.config, "Missing 'security' section"
            security = self.config["security"]

            assert (
                "authentication" in security
            ), "Missing 'security.authentication'"
            assert (
                "authorization" in security
            ), "Missing 'security.authorization'"
            assert (
                "secrets-management" in security
            ), "Missing 'security.secrets-management'"
            assert (
                "compliance" in security
            ), "Missing 'security.compliance'"

            auth = security["authentication"]
            assert "method" in auth, "Authentication missing 'method'"
            assert auth.get("mfa-required") is not None, "MFA requirement not specified"

            compliance = security["compliance"]
            assert "standards" in compliance, "Compliance missing 'standards'"
            assert len(compliance["standards"]) > 0, "No compliance standards defined"

            return TestResult("Security Configuration", True, "All security sections present")
        except AssertionError as e:
            return TestResult("Security Configuration", False, str(e))

    def test_observability(self) -> TestResult:
        """Test observability configuration."""
        try:
            assert (
                "observability" in self.config
            ), "Missing 'observability' section"
            obs = self.config["observability"]

            assert "metrics" in obs, "Missing 'observability.metrics'"
            assert "logging" in obs, "Missing 'observability.logging'"

            metrics = obs["metrics"]
            assert "system" in metrics, "Metrics missing 'system'"

            logging = obs["logging"]
            assert "system" in logging, "Logging missing 'system'"

            assert "dashboards" in obs, "Missing 'observability.dashboards'"
            assert len(obs["dashboards"]) >= 2, "Need at least 2 dashboards"

            return TestResult(
                "Observability", True, "Observability fully configured"
            )
        except AssertionError as e:
            return TestResult("Observability", False, str(e))

    def test_self_service_capabilities(self) -> TestResult:
        """Test self-service capabilities are defined."""
        try:
            assert (
                "self-service" in self.config
            ), "Missing 'self-service' section"
            self_service = self.config["self-service"]

            assert (
                "internal-developer-portal" in self_service
            ), "Missing internal developer portal"
            assert (
                "available-templates" in self_service
            ), "Missing 'available-templates'"

            templates = self_service["available-templates"]
            assert len(templates) >= 3, "Need at least 3 self-service templates"

            return TestResult(
                "Self-Service",
                True,
                f"{len(templates)} templates available",
            )
        except AssertionError as e:
            return TestResult("Self-Service", False, str(e))

    def test_infrastructure(self) -> TestResult:
        """Test infrastructure configuration."""
        try:
            assert (
                "infrastructure" in self.config
            ), "Missing 'infrastructure' section"
            infra = self.config["infrastructure"]

            assert "primary-cloud" in infra, "Missing 'primary-cloud'"
            assert "kubernetes" in infra, "Missing 'kubernetes' configuration"
            assert "databases" in infra, "Missing 'databases' configuration"

            k8s = infra["kubernetes"]
            assert "version" in k8s, "Kubernetes missing 'version'"
            assert "distribution" in k8s, "Kubernetes missing 'distribution'"

            return TestResult(
                "Infrastructure", True, "Infrastructure properly configured"
            )
        except AssertionError as e:
            return TestResult("Infrastructure", False, str(e))

    def test_api_standards(self) -> TestResult:
        """Test API standards are defined."""
        try:
            assert "api" in self.config, "Missing 'api' section"
            api = self.config["api"]

            assert "default-version" in api, "API missing 'default-version'"
            assert "format" in api, "API missing 'format'"
            assert "standards" in api, "API missing 'standards'"
            assert len(api["standards"]) > 0, "No API standards defined"

            return TestResult("API Standards", True, "API standards defined")
        except AssertionError as e:
            return TestResult("API Standards", False, str(e))

    def test_policies(self) -> TestResult:
        """Test policies are defined."""
        try:
            assert "policies" in self.config, "Missing 'policies' section"
            policies = self.config["policies"]

            assert "naming-conventions" in policies, "Missing 'naming-conventions'"
            assert "code-quality" in policies, "Missing 'code-quality'"
            assert "deployment" in policies, "Missing 'deployment'"

            code_quality = policies["code-quality"]
            assert (
                "minimum-test-coverage" in code_quality
            ), "Missing 'minimum-test-coverage'"

            deployment = policies["deployment"]
            assert (
                "automated-testing-required" in deployment
            ), "Missing 'automated-testing-required'"
            assert (
                "security-scanning-required" in deployment
            ), "Missing 'security-scanning-required'"

            return TestResult("Policies", True, "All required policies defined")
        except AssertionError as e:
            return TestResult("Policies", False, str(e))

    def test_support_configuration(self) -> TestResult:
        """Test support configuration."""
        try:
            assert "support" in self.config, "Missing 'support' section"
            support = self.config["support"]

            assert "primary-channel" in support, "Missing 'primary-channel'"
            assert "documentation" in support, "Missing 'documentation'"

            return TestResult("Support", True, "Support configuration present")
        except AssertionError as e:
            return TestResult("Support", False, str(e))

    def run_all_tests(self) -> list:
        """
        Run all tests.

        Returns:
            List of TestResult objects
        """
        test_methods = [
            self.test_config_structure,
            self.test_platform_principles,
            self.test_team_structure,
            self.test_golden_paths,
            self.test_security_configuration,
            self.test_observability,
            self.test_self_service_capabilities,
            self.test_infrastructure,
            self.test_api_standards,
            self.test_policies,
            self.test_support_configuration,
        ]

        results = []
        for test_method in test_methods:
            result = test_method()
            results.append(result)

        return results

    def print_report(self) -> None:
        """Print test report."""
        results = self.run_all_tests()
        self.results = results

        print("\n" + "=" * 70)
        print("PLATFORM CONFIGURATION TEST REPORT")
        print("=" * 70 + "\n")

        passed = sum(1 for r in results if r.passed)
        total = len(results)

        print(f"Results: {passed}/{total} tests passed\n")

        for result in results:
            status = "✓" if result.passed else "✗"
            print(f"{status} {result}")

        print("\n" + "=" * 70)

        if passed == total:
            print("✓ All tests passed!")
        else:
            print(f"✗ {total - passed} test(s) failed.")
            print("\nFailed tests:")
            for result in results:
                if not result.passed:
                    print(f"  - {result.name}: {result.message}")

        print("=" * 70 + "\n")

        return passed == total


def load_yaml_config(filename: str) -> Dict:
    """Load YAML configuration."""
    try:
        import yaml

        with open(filename) as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        print("PyYAML not installed. Install with: pip install pyyaml")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Config file not found: {filename}")
        sys.exit(1)


if __name__ == "__main__":
    # Load configuration
    config = load_yaml_config("platform-config.yaml")

    # Run tests
    test_suite = PlatformConfigTests(config)
    success = test_suite.print_report()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
