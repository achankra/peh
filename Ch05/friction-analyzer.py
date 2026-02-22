#!/usr/bin/env python3
"""
Friction Analyzer

Analyzes developer workflows to identify friction points and calculate
a friction score. This tool helps quantify the impact of UX improvements.

The analyzer processes workflow definitions (in YAML format) and identifies:
- Manual vs automated steps
- Serial vs parallel bottlenecks
- Steps with high cognitive load
- Missing feedback loops
- Dependency chains that could be optimized

Friction Score: 0-100 (lower is better)
- 0-20: Minimal friction (highly optimized)
- 21-40: Low friction (good experience)
- 41-60: Moderate friction (some optimization needed)
- 61-80: High friction (significant issues)
- 81-100: Severe friction (critical improvements needed)
"""

import json
import sys
import argparse
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    name: str
    manual: bool = False
    automated: bool = False
    semi_automated: bool = False
    time_minutes: float = 0
    dependencies: List[str] = None
    cognitive_load: int = 1  # 1-5 scale
    has_feedback: bool = True
    error_prone: bool = False

    def __post_init__(self):
        """Validate step configuration."""
        if self.dependencies is None:
            self.dependencies = []

        # Ensure exactly one type is selected
        type_count = sum([self.manual, self.automated, self.semi_automated])
        if type_count != 1:
            raise ValueError(f"Step '{self.name}' must be exactly one type (manual/automated/semi_automated)")


class FrictionAnalyzer:
    """Analyzes workflow friction and provides optimization suggestions."""

    FRICTION_WEIGHTS = {
        "manual_step": 15,  # Manual steps add friction
        "no_feedback": 20,  # Missing feedback loops add major friction
        "high_cognitive_load": 10,  # Complex steps add friction
        "error_prone": 15,  # Unreliable steps add friction
        "time_overhead": 0.5,  # Each minute of overhead adds 0.5 friction points
        "dependency_chain": 5,  # Deep dependency chains add friction
    }

    def __init__(self):
        """Initialize the friction analyzer."""
        self.steps: Dict[str, WorkflowStep] = {}
        self.total_time: float = 0
        self.critical_path_time: float = 0

    def parse_workflow_yaml(self, yaml_content: str) -> None:
        """
        Parse workflow definition from YAML.

        Args:
            yaml_content: YAML content as string

        Raises:
            ValueError: If YAML is invalid
        """
        try:
            import yaml
            data = yaml.safe_load(yaml_content)
        except ImportError:
            # Fallback: simple YAML parser for basic structures
            data = self._parse_simple_yaml(yaml_content)
        except Exception as e:
            raise ValueError(f"Failed to parse YAML: {e}")

        if not data or "workflow" not in data:
            raise ValueError("YAML must contain 'workflow' key")

        workflow = data["workflow"]
        if "steps" not in workflow:
            raise ValueError("Workflow must contain 'steps' list")

        for step_data in workflow["steps"]:
            step = self._create_step(step_data)
            self.steps[step.name] = step

    def _parse_simple_yaml(self, content: str) -> Dict[str, Any]:
        """
        Simple YAML parser for basic workflow structures.

        Args:
            content: YAML content as string

        Returns:
            Parsed dictionary
        """
        # This is a very basic implementation for demo purposes
        result = {"workflow": {"steps": []}}
        lines = content.strip().split('\n')

        current_step = {}
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if ':' not in line:
                continue

            key, value = line.split(':', 1)
            key = key.strip().lstrip('- ')
            value = value.strip()

            if key == "name":
                if current_step:
                    result["workflow"]["steps"].append(current_step)
                current_step = {"name": value}
            else:
                # Parse boolean values
                if value.lower() == 'true':
                    current_step[key] = True
                elif value.lower() == 'false':
                    current_step[key] = False
                # Parse numeric values
                elif value.isdigit():
                    current_step[key] = int(value)
                # Parse lists
                elif key == "dependencies":
                    # Remove brackets and split
                    items = value.replace('[', '').replace(']', '').split(',')
                    current_step[key] = [item.strip().strip('"\'') for item in items]
                else:
                    current_step[key] = value

        if current_step:
            result["workflow"]["steps"].append(current_step)

        return result

    def _create_step(self, step_data: Dict[str, Any]) -> WorkflowStep:
        """
        Create a WorkflowStep from parsed data.

        Args:
            step_data: Step configuration dictionary

        Returns:
            WorkflowStep instance
        """
        return WorkflowStep(
            name=step_data.get("name", "Unnamed"),
            manual=step_data.get("manual", False),
            automated=step_data.get("automated", False),
            semi_automated=step_data.get("semi_automated", False),
            time_minutes=float(step_data.get("time_minutes", 0)),
            dependencies=step_data.get("dependencies", []),
            cognitive_load=int(step_data.get("cognitive_load", 1)),
            has_feedback=step_data.get("has_feedback", True),
            error_prone=step_data.get("error_prone", False),
        )

    def calculate_critical_path(self) -> float:
        """
        Calculate the critical path (longest dependency chain).

        Returns:
            Time in minutes for critical path
        """
        def get_path_time(step_name: str, visited=None) -> float:
            if visited is None:
                visited = set()

            if step_name in visited:
                return 0  # Avoid cycles

            if step_name not in self.steps:
                return 0

            visited.add(step_name)
            step = self.steps[step_name]

            if not step.dependencies:
                return step.time_minutes

            max_dependency_time = 0
            for dep in step.dependencies:
                dep_time = get_path_time(dep, visited.copy())
                max_dependency_time = max(max_dependency_time, dep_time)

            return step.time_minutes + max_dependency_time

        # Find step with longest path
        max_time = 0
        for step_name in self.steps:
            path_time = get_path_time(step_name)
            max_time = max(max_time, path_time)

        self.critical_path_time = max_time
        return max_time

    def calculate_total_time(self) -> float:
        """
        Calculate total workflow time (if all steps were serial).

        Returns:
            Total time in minutes
        """
        self.total_time = sum(step.time_minutes for step in self.steps.values())
        return self.total_time

    def calculate_friction_score(self) -> int:
        """
        Calculate overall friction score (0-100, lower is better).

        Returns:
            Friction score
        """
        friction_points = 0

        for step in self.steps.values():
            # Manual steps add friction
            if step.manual:
                friction_points += self.FRICTION_WEIGHTS["manual_step"]

            # Missing feedback loops add significant friction
            if not step.has_feedback:
                friction_points += self.FRICTION_WEIGHTS["no_feedback"]

            # High cognitive load adds friction
            friction_points += (step.cognitive_load - 1) * self.FRICTION_WEIGHTS["high_cognitive_load"]

            # Error-prone steps add friction
            if step.error_prone:
                friction_points += self.FRICTION_WEIGHTS["error_prone"]

            # Time overhead
            friction_points += step.time_minutes * self.FRICTION_WEIGHTS["time_overhead"]

        # Dependency chains add friction
        for step in self.steps.values():
            friction_points += len(step.dependencies) * self.FRICTION_WEIGHTS["dependency_chain"]

        # Normalize to 0-100 scale
        max_possible_friction = 100
        friction_score = min(int(friction_points), max_possible_friction)

        return friction_score

    def get_friction_level(self, score: int) -> str:
        """
        Get human-readable friction level.

        Args:
            score: Friction score

        Returns:
            Friction level description
        """
        if score <= 20:
            return "Minimal"
        elif score <= 40:
            return "Low"
        elif score <= 60:
            return "Moderate"
        elif score <= 80:
            return "High"
        else:
            return "Severe"

    def identify_friction_points(self) -> List[Dict[str, Any]]:
        """
        Identify specific friction points and optimization opportunities.

        Returns:
            List of friction point descriptions
        """
        friction_points = []

        for step in self.steps.values():
            if step.manual:
                friction_points.append({
                    "step": step.name,
                    "issue": "Manual execution",
                    "impact": "Could be automated",
                    "priority": "High"
                })

            if not step.has_feedback:
                friction_points.append({
                    "step": step.name,
                    "issue": "No feedback loop",
                    "impact": "Developer must wait for external confirmation",
                    "priority": "High"
                })

            if step.cognitive_load >= 4:
                friction_points.append({
                    "step": step.name,
                    "issue": "High cognitive load",
                    "impact": "Complex, error-prone step",
                    "priority": "Medium"
                })

            if step.error_prone:
                friction_points.append({
                    "step": step.name,
                    "issue": "Error-prone",
                    "impact": "Frequently fails, requires rework",
                    "priority": "High"
                })

            if step.time_minutes > 30:
                friction_points.append({
                    "step": step.name,
                    "issue": "Long execution time",
                    "impact": "Blocks developer workflow",
                    "priority": "Medium"
                })

        return friction_points

    def print_report(self):
        """Print friction analysis report."""
        if not self.steps:
            print("No workflow steps to analyze.")
            return

        friction_score = self.calculate_friction_score()
        friction_level = self.get_friction_level(friction_score)

        print("\n" + "=" * 70)
        print("WORKFLOW FRICTION ANALYSIS REPORT")
        print("=" * 70 + "\n")

        print(f"Total Steps: {len(self.steps)}")
        self.calculate_total_time()
        self.calculate_critical_path()
        print(f"Total Time (Serial): {self.total_time:.1f} minutes")
        print(f"Critical Path: {self.critical_path_time:.1f} minutes")
        print(f"Parallelization Potential: {((self.total_time - self.critical_path_time) / self.total_time * 100):.1f}%")

        print("\n" + "-" * 70)
        print(f"Friction Score: {friction_score}/100 ({friction_level})")
        print("-" * 70 + "\n")

        # Step breakdown
        print("Step Breakdown:")
        print(f"{'Step Name':<25} {'Type':<15} {'Time (min)':<12} {'Cognitive':<10}")
        print("-" * 70)

        for step in self.steps.values():
            step_type = "Manual" if step.manual else ("Auto" if step.automated else "Semi-Auto")
            print(f"{step.name:<25} {step_type:<15} {step.time_minutes:<12.1f} {step.cognitive_load:<10}")

        # Friction points
        friction_points = self.identify_friction_points()
        if friction_points:
            print("\n" + "-" * 70)
            print("Friction Points:")
            print("-" * 70)
            for point in friction_points:
                print(f"\n  Step: {point['step']}")
                print(f"  Issue: {point['issue']}")
                print(f"  Impact: {point['impact']}")
                print(f"  Priority: {point['priority']}")

        print("\n" + "=" * 70)

    def export_report(self, filename: str):
        """
        Export analysis to JSON file.

        Args:
            filename: Output file path
        """
        friction_score = self.calculate_friction_score()
        friction_level = self.get_friction_level(friction_score)

        report = {
            "friction_score": friction_score,
            "friction_level": friction_level,
            "total_steps": len(self.steps),
            "total_time_minutes": self.total_time,
            "critical_path_minutes": self.critical_path_time,
            "steps": {
                name: {
                    "type": "manual" if step.manual else ("automated" if step.automated else "semi_automated"),
                    "time_minutes": step.time_minutes,
                    "cognitive_load": step.cognitive_load,
                    "has_feedback": step.has_feedback,
                    "error_prone": step.error_prone,
                    "dependencies": step.dependencies,
                }
                for name, step in self.steps.items()
            },
            "friction_points": self.identify_friction_points(),
        }

        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report exported to {filename}")
        except IOError as e:
            print(f"Error exporting report: {e}", file=sys.stderr)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze workflow friction and identify optimization opportunities"
    )
    parser.add_argument(
        "--workflow",
        "-w",
        required=True,
        help="Path to workflow YAML file"
    )
    parser.add_argument(
        "--export",
        "-e",
        help="Export report to JSON file"
    )

    args = parser.parse_args()

    try:
        with open(args.workflow, 'r') as f:
            workflow_content = f.read()
    except FileNotFoundError:
        print(f"Workflow file not found: {args.workflow}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading workflow file: {e}", file=sys.stderr)
        sys.exit(1)

    analyzer = FrictionAnalyzer()

    try:
        analyzer.parse_workflow_yaml(workflow_content)
    except ValueError as e:
        print(f"Error parsing workflow: {e}", file=sys.stderr)
        sys.exit(1)

    analyzer.print_report()

    if args.export:
        analyzer.export_report(args.export)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
