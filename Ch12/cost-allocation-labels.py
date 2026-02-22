#!/usr/bin/env python3
"""
Cost Allocation Labels Validator and Reporter

Validates that all Kubernetes workloads have proper cost allocation labels.
Reports on cost distribution by team/project/cost-center.

Required labels:
- team: Organization team or business unit
- cost-center: Billing cost center code
- cost-allocation: Project or service name
- environment: prod/staging/dev

Usage:
    python3 cost-allocation-labels.py
    python3 cost-allocation-labels.py --namespace production
    python3 cost-allocation-labels.py --report-by team
    python3 cost-allocation-labels.py --report-by team --output json
    python3 cost-allocation-labels.py --enforce-labels
"""

import json
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Dict, List, Set, Optional, Tuple


REQUIRED_LABELS = {
    "team": "Organization team/business unit",
    "cost-center": "Billing cost center code",
    "cost-allocation": "Project or service name",
    "environment": "Environment: prod/staging/dev",
}

VALID_ENVIRONMENTS = {"prod", "staging", "dev", "test"}


@dataclass
class LabelCompliance:
    """Resource label compliance information"""
    resource_type: str
    namespace: str
    resource_name: str
    missing_labels: List[str]
    is_compliant: bool
    labels: Dict[str, str]


@dataclass
class TeamCostAllocation:
    """Cost allocation summary by team"""
    team: str
    cost_center: str
    resources: int
    namespaces: Set[str]
    workload_types: Dict[str, int]
    environments: Dict[str, int]


class KubectlWrapper:
    """Wrapper for kubectl queries"""
    
    @staticmethod
    def get_resources(resource_type: str, namespace: str = None) -> List[Dict]:
        """Get all resources of a type"""
        cmd = ["kubectl", "get", resource_type, "-o", "json"]
        if namespace:
            cmd.extend(["-n", namespace])
        else:
            cmd.append("-A")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            return data.get("items", [])
        except subprocess.CalledProcessError as e:
            print(f"Error querying {resource_type}: {e.stderr}", file=sys.stderr)
            return []
    
    @staticmethod
    def get_namespaces() -> List[str]:
        """Get all namespaces"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "namespaces", "-o", "json"],
                capture_output=True,
                text=True,
                check=True
            )
            data = json.loads(result.stdout)
            return [ns["metadata"]["name"] for ns in data.get("items", [])]
        except subprocess.CalledProcessError:
            return []


class LabelValidator:
    """Validates cost allocation labels on Kubernetes resources"""
    
    def __init__(self, enforce: bool = False):
        self.enforce = enforce
        self.compliance_results: List[LabelCompliance] = []
        self.kubectl = KubectlWrapper()
    
    def validate_namespace(self, namespace: str) -> List[LabelCompliance]:
        """Validate labels in a specific namespace"""
        self.compliance_results = []
        
        # Resource types to check for labels
        resource_types = [
            "deployments",
            "statefulsets",
            "daemonsets",
            "jobs",
            "cronjobs",
            "pods",
        ]
        
        for resource_type in resource_types:
            resources = self.kubectl.get_resources(resource_type, namespace)
            
            for resource in resources:
                compliance = self._check_resource_compliance(resource, resource_type, namespace)
                self.compliance_results.append(compliance)
        
        return self.compliance_results
    
    def validate_all_namespaces(self) -> List[LabelCompliance]:
        """Validate labels across all namespaces"""
        self.compliance_results = []
        namespaces = self.kubectl.get_namespaces()
        
        for ns in namespaces:
            self.validate_namespace(ns)
        
        return self.compliance_results
    
    def _check_resource_compliance(
        self,
        resource: Dict,
        resource_type: str,
        namespace: str
    ) -> LabelCompliance:
        """Check compliance of a single resource"""
        metadata = resource.get("metadata", {})
        resource_name = metadata.get("name", "unknown")
        labels = metadata.get("labels", {})
        
        missing_labels = []
        for required_label in REQUIRED_LABELS:
            if required_label not in labels:
                missing_labels.append(required_label)
        
        # Additional validations
        if "environment" in labels:
            if labels["environment"] not in VALID_ENVIRONMENTS:
                missing_labels.append(f"environment (invalid value: {labels['environment']})")
        
        is_compliant = len(missing_labels) == 0
        
        return LabelCompliance(
            resource_type=resource_type,
            namespace=namespace,
            resource_name=resource_name,
            missing_labels=missing_labels,
            is_compliant=is_compliant,
            labels=labels,
        )
    
    def print_compliance_report(self):
        """Print human-readable compliance report"""
        if not self.compliance_results:
            print("No resources found")
            return
        
        compliant = [r for r in self.compliance_results if r.is_compliant]
        non_compliant = [r for r in self.compliance_results if not r.is_compliant]
        
        print("\n=== Cost Allocation Label Compliance Report ===\n")
        print(f"Total resources: {len(self.compliance_results)}")
        print(f"Compliant: {len(compliant)} ({100*len(compliant)//len(self.compliance_results)}%)")
        print(f"Non-compliant: {len(non_compliant)} ({100*len(non_compliant)//len(self.compliance_results)}%)\n")
        
        if non_compliant:
            print("=== Non-Compliant Resources ===\n")
            for result in sorted(non_compliant, key=lambda x: (x.namespace, x.resource_type, x.resource_name)):
                print(f"{result.namespace}/{result.resource_type}/{result.resource_name}")
                print(f"  Missing labels: {', '.join(result.missing_labels)}")
                if result.labels:
                    print(f"  Current labels: {json.dumps(result.labels, indent=4)}")
                print()
        
        print("\n=== Required Labels ===")
        for label, description in REQUIRED_LABELS.items():
            print(f"  {label}: {description}")
    
    def to_json(self) -> str:
        """Export compliance results as JSON"""
        summary = {
            "total": len(self.compliance_results),
            "compliant": len([r for r in self.compliance_results if r.is_compliant]),
            "non_compliant": len([r for r in self.compliance_results if not r.is_compliant]),
        }
        
        results = [asdict(r) for r in self.compliance_results]
        
        return json.dumps({
            "summary": summary,
            "results": results
        }, indent=2)


class CostAllocationReporter:
    """Reports cost allocation by team, cost center, etc."""
    
    def __init__(self):
        self.kubectl = KubectlWrapper()
        self.allocations: Dict[str, TeamCostAllocation] = {}
    
    def generate_team_report(self, namespace: str = None) -> Dict[str, TeamCostAllocation]:
        """Generate cost allocation report by team"""
        self.allocations = {}
        
        resource_types = ["deployments", "statefulsets", "daemonsets", "jobs"]
        
        for resource_type in resource_types:
            resources = self.kubectl.get_resources(resource_type, namespace)
            
            for resource in resources:
                self._process_resource(resource, resource_type)
        
        return self.allocations
    
    def _process_resource(self, resource: Dict, resource_type: str):
        """Process a resource and add to allocations"""
        metadata = resource.get("metadata", {})
        labels = metadata.get("labels", {})
        namespace = metadata.get("namespace", "unknown")
        
        team = labels.get("team", "unassigned")
        cost_center = labels.get("cost-center", "unknown")
        environment = labels.get("environment", "unknown")
        
        key = f"{team}:{cost_center}"
        
        if key not in self.allocations:
            self.allocations[key] = TeamCostAllocation(
                team=team,
                cost_center=cost_center,
                resources=0,
                namespaces=set(),
                workload_types={},
                environments={},
            )
        
        allocation = self.allocations[key]
        allocation.resources += 1
        allocation.namespaces.add(namespace)
        allocation.workload_types[resource_type] = allocation.workload_types.get(resource_type, 0) + 1
        allocation.environments[environment] = allocation.environments.get(environment, 0) + 1
    
    def print_team_report(self):
        """Print team cost allocation report"""
        if not self.allocations:
            print("No resources found")
            return
        
        print("\n=== Cost Allocation Report by Team ===\n")
        
        for key in sorted(self.allocations.keys()):
            allocation = self.allocations[key]
            
            print(f"Team: {allocation.team}")
            print(f"Cost Center: {allocation.cost_center}")
            print(f"Total Resources: {allocation.resources}")
            print(f"Namespaces: {', '.join(sorted(allocation.namespaces))}")
            print(f"Workload Types: {dict(allocation.workload_types)}")
            print(f"Environments: {dict(allocation.environments)}")
            print()
    
    def to_json(self) -> str:
        """Export report as JSON"""
        data = {
            allocation.team: {
                "cost_center": allocation.cost_center,
                "total_resources": allocation.resources,
                "namespaces": list(allocation.namespaces),
                "workload_types": allocation.workload_types,
                "environments": allocation.environments,
            }
            for allocation in self.allocations.values()
        }
        return json.dumps(data, indent=2)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate and report on cost allocation labels"
    )
    parser.add_argument(
        "--namespace",
        help="Specific namespace to check"
    )
    parser.add_argument(
        "--report-by",
        choices=["team", "cost-center", "compliance"],
        default="compliance",
        help="Generate report by team or cost-center"
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    parser.add_argument(
        "--enforce-labels",
        action="store_true",
        help="Check enforcement (dry-run)"
    )
    
    args = parser.parse_args()
    
    if args.report_by == "compliance":
        validator = LabelValidator(enforce=args.enforce_labels)
        
        if args.namespace:
            validator.validate_namespace(args.namespace)
        else:
            validator.validate_all_namespaces()
        
        if args.output == "json":
            print(validator.to_json())
        else:
            validator.print_compliance_report()
    
    elif args.report_by in ["team", "cost-center"]:
        reporter = CostAllocationReporter()
        reporter.generate_team_report(args.namespace)
        
        if args.output == "json":
            print(reporter.to_json())
        else:
            reporter.print_team_report()


if __name__ == "__main__":
    main()
