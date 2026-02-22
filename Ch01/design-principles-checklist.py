#!/usr/bin/env python3
"""
Design Principles Validation Checklist

This script validates a platform configuration against core design principles.
It reads a platform-config.yaml file and checks if the platform adheres to:

- Self-Service: Can teams self-serve without bottlenecks?
- Guardrails: Are safe boundaries in place?
- Golden Paths: Are recommended patterns clear?
- Extensibility: Can the platform be extended?
- Observability: Can platform health be monitored?
- Security: Are security practices enforced?

Usage:
    python design-principles-checklist.py platform-config.yaml

Output:
    Detailed validation report showing compliance for each principle.
"""

import sys
from typing import Dict, List, Tuple


class DesignPrinciplesValidator:
    """Validate platform configuration against design principles."""

    def __init__(self, config: Dict) -> None:
        """
        Initialize validator with platform configuration.

        Args:
            config: Dictionary containing platform configuration
        """
        self.config = config
        self.results: Dict[str, Dict] = {}

    def validate_self_service(self) -> Tuple[bool, List[str]]:
        """
        Validate self-service principle.

        Checks:
        - Internal developer portal exists
        - Self-service templates available
        - Automation level is high
        - No manual approval gates for common tasks
        """
        checks = []
        passed = True

        # Check for portal
        if "self-service" in self.config:
            if "internal-developer-portal" in self.config["self-service"]:
                checks.append("✓ Internal developer portal defined")
            else:
                checks.append("✗ Internal developer portal not found")
                passed = False

            if "available-templates" in self.config["self-service"]:
                templates = self.config["self-service"]["available-templates"]
                if len(templates) >= 3:
                    checks.append(f"✓ {len(templates)} self-service templates available")
                else:
                    checks.append(
                        f"✗ Only {len(templates)} templates (recommend >= 3)"
                    )
                    passed = False
            else:
                checks.append("✗ No self-service templates defined")
                passed = False

            automation_level = self.config["self-service"].get(
                "automation-level", "Unknown"
            )
            if automation_level == "High":
                checks.append("✓ High automation level")
            else:
                checks.append(f"⚠ Automation level is {automation_level}")
                passed = False
        else:
            checks.append("✗ No self-service configuration found")
            passed = False

        return passed, checks

    def validate_guardrails(self) -> Tuple[bool, List[str]]:
        """
        Validate guardrails principle.

        Checks:
        - Security standards are defined
        - Policies are in place
        - Automated checks enabled
        - Compliance standards defined
        """
        checks = []
        passed = True

        if "security" in self.config:
            if "compliance" in self.config["security"]:
                compliance = self.config["security"]["compliance"]
                standards = compliance.get("standards", [])
                if standards:
                    checks.append(
                        f"✓ Compliance standards defined: {', '.join(standards)}"
                    )
                else:
                    checks.append("✗ No compliance standards defined")
                    passed = False

                if compliance.get("automated-checks"):
                    checks.append("✓ Automated compliance checks enabled")
                else:
                    checks.append("✗ Automated compliance checks not enabled")
                    passed = False
            else:
                checks.append("✗ No compliance configuration found")
                passed = False
        else:
            checks.append("✗ No security configuration found")
            passed = False

        if "policies" in self.config:
            policies = self.config["policies"]
            if "code-quality" in policies:
                if policies["code-quality"].get("linting-required"):
                    checks.append("✓ Linting required in policies")
                else:
                    checks.append("⚠ Linting not required")

            if "deployment" in policies:
                if policies["deployment"].get("security-scanning-required"):
                    checks.append("✓ Security scanning required for deployments")
                else:
                    checks.append("✗ Security scanning not required")
                    passed = False
        else:
            checks.append("✗ No policies defined")
            passed = False

        return passed, checks

    def validate_golden_paths(self) -> Tuple[bool, List[str]]:
        """
        Validate golden paths principle.

        Checks:
        - Golden paths are defined
        - Each path has tech stack
        - Documentation and examples provided
        - At least 2 paths defined
        """
        checks = []
        passed = True

        if "golden-paths" in self.config:
            paths = self.config["golden-paths"]
            if len(paths) >= 2:
                checks.append(f"✓ {len(paths)} golden paths defined")
            else:
                checks.append(f"✗ Only {len(paths)} golden path(s) (recommend >= 2)")
                passed = False

            for path_name, path_config in paths.items():
                if "tech-stack" in path_config:
                    checks.append(f"  ✓ {path_name}: tech stack defined")
                else:
                    checks.append(f"  ✗ {path_name}: no tech stack defined")
                    passed = False

                if "documentation" in path_config or "example-repo" in path_config:
                    checks.append(f"  ✓ {path_name}: documentation provided")
                else:
                    checks.append(f"  ✗ {path_name}: no documentation")
                    passed = False
        else:
            checks.append("✗ No golden paths defined")
            passed = False

        return passed, checks

    def validate_extensibility(self) -> Tuple[bool, List[str]]:
        """
        Validate extensibility principle.

        Checks:
        - API standards defined
        - API versioning required
        - Plugin/integration support mentioned
        - Multiple tech stacks supported
        """
        checks = []
        passed = True

        if "api" in self.config:
            api_config = self.config["api"]
            if api_config.get("format") == "REST + JSON":
                checks.append("✓ REST API format standardized")
            else:
                checks.append(f"⚠ API format: {api_config.get('format')}")

            if api_config.get("default-version"):
                checks.append("✓ API versioning supported")
            else:
                checks.append("✗ API versioning not configured")
                passed = False
        else:
            checks.append("✗ No API standards defined")
            passed = False

        # Check for multiple tech stack support
        if "golden-paths" in self.config:
            languages = set()
            for path_config in self.config["golden-paths"].values():
                if "tech-stack" in path_config:
                    for tech in path_config["tech-stack"]:
                        if isinstance(tech, dict) and "language" in tech:
                            languages.add(tech["language"])

            if len(languages) >= 2:
                checks.append(
                    f"✓ Multiple languages supported: {', '.join(languages)}"
                )
            else:
                checks.append("⚠ Limited language support")
        else:
            checks.append("⚠ Cannot verify language support")

        return passed, checks

    def validate_observability(self) -> Tuple[bool, List[str]]:
        """
        Validate observability principle.

        Checks:
        - Metrics system configured
        - Logging system configured
        - Tracing enabled
        - Dashboards defined
        """
        checks = []
        passed = True

        if "observability" not in self.config:
            checks.append("✗ No observability configuration found")
            return False, checks

        obs_config = self.config["observability"]

        if "metrics" in obs_config and obs_config["metrics"].get("system"):
            checks.append(f"✓ Metrics system: {obs_config['metrics']['system']}")
        else:
            checks.append("✗ No metrics system configured")
            passed = False

        if "logging" in obs_config and obs_config["logging"].get("system"):
            checks.append(f"✓ Logging system: {obs_config['logging']['system']}")
        else:
            checks.append("✗ No logging system configured")
            passed = False

        if "tracing" in obs_config and obs_config["tracing"].get("system"):
            checks.append(f"✓ Distributed tracing: {obs_config['tracing']['system']}")
        else:
            checks.append("⚠ No distributed tracing configured")

        if "dashboards" in obs_config:
            dashboards = obs_config["dashboards"]
            if len(dashboards) >= 3:
                checks.append(f"✓ {len(dashboards)} dashboards defined")
            else:
                checks.append(f"⚠ Only {len(dashboards)} dashboards")

        if "key-metrics" in obs_config.get("metrics", {}):
            metrics = obs_config["metrics"]["key-metrics"]
            checks.append(f"✓ {len(metrics)} key metrics defined")
        else:
            checks.append("✗ No key metrics defined")
            passed = False

        return passed, checks

    def validate_security(self) -> Tuple[bool, List[str]]:
        """
        Validate security principle.

        Checks:
        - Authentication method configured
        - Authorization model defined
        - Secrets management configured
        - MFA required
        - Audit logging enabled
        """
        checks = []
        passed = True

        if "security" not in self.config:
            checks.append("✗ No security configuration found")
            return False, checks

        security_config = self.config["security"]

        if "authentication" in security_config:
            auth = security_config["authentication"]
            checks.append(f"✓ Authentication: {auth.get('method', 'Unknown')}")

            if auth.get("mfa-required"):
                checks.append("✓ MFA required")
            else:
                checks.append("⚠ MFA not required")
                passed = False
        else:
            checks.append("✗ No authentication configured")
            passed = False

        if "authorization" in security_config:
            authz = security_config["authorization"]
            checks.append(f"✓ Authorization model: {authz.get('model', 'Unknown')}")
        else:
            checks.append("✗ No authorization model defined")
            passed = False

        if "secrets-management" in security_config:
            secrets = security_config["secrets-management"]
            checks.append(f"✓ Secrets system: {secrets.get('system', 'Unknown')}")

            if secrets.get("rotation-period"):
                checks.append(f"✓ Secrets rotation: {secrets['rotation-period']}")
            else:
                checks.append("⚠ No secrets rotation period defined")
        else:
            checks.append("✗ No secrets management configured")
            passed = False

        if "compliance" in security_config:
            if security_config["compliance"].get("audit-logging"):
                checks.append("✓ Audit logging enabled")
            else:
                checks.append("⚠ Audit logging not enabled")
                passed = False

        return passed, checks

    def validate_all(self) -> None:
        """Run all validations and store results."""
        validators = [
            ("Self-Service", self.validate_self_service),
            ("Guardrails", self.validate_guardrails),
            ("Golden Paths", self.validate_golden_paths),
            ("Extensibility", self.validate_extensibility),
            ("Observability", self.validate_observability),
            ("Security", self.validate_security),
        ]

        for principle_name, validator_func in validators:
            passed, checks = validator_func()
            self.results[principle_name] = {"passed": passed, "checks": checks}

    def generate_report(self) -> str:
        """
        Generate validation report.

        Returns:
            Formatted report string
        """
        if not self.results:
            return "No validation results. Run validate_all() first."

        report = "\n" + "=" * 70 + "\n"
        report += "DESIGN PRINCIPLES VALIDATION REPORT\n"
        report += "=" * 70 + "\n\n"

        total_principles = len(self.results)
        passed_principles = sum(1 for r in self.results.values() if r["passed"])

        report += f"Compliance Score: {passed_principles}/{total_principles}\n\n"

        for principle, result in self.results.items():
            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            report += f"{principle}: {status}\n"
            for check in result["checks"]:
                report += f"  {check}\n"
            report += "\n"

        # Summary
        report += "-" * 70 + "\n"
        report += "SUMMARY\n\n"

        if passed_principles == total_principles:
            report += "✓ All design principles are satisfied!\n"
        else:
            report += (
                f"⚠ {total_principles - passed_principles} principle(s) need attention.\n"
            )
            report += "\nFailing principles:\n"
            for principle, result in self.results.items():
                if not result["passed"]:
                    report += f"  - {principle}\n"

        report += "\n" + "=" * 70 + "\n"

        return report


def load_yaml_config(filename: str) -> Dict:
    """
    Load YAML configuration file.

    Args:
        filename: Path to YAML file

    Returns:
        Parsed configuration dictionary

    Note:
        This is a simple YAML parser for demo purposes.
        For production, use PyYAML: pip install pyyaml
    """
    try:
        import yaml

        with open(filename) as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        print(
            "PyYAML not installed. Install with: pip install pyyaml"
        )
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File not found: {filename}")
        sys.exit(1)


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) < 2:
        print("Usage: python design-principles-checklist.py <config-file>")
        print("Example: python design-principles-checklist.py platform-config.yaml")
        sys.exit(1)

    config_file = sys.argv[1]

    # Load configuration
    config = load_yaml_config(config_file)

    # Run validation
    validator = DesignPrinciplesValidator(config)
    validator.validate_all()

    # Generate and print report
    report = validator.generate_report()
    print(report)
