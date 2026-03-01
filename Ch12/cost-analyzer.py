#!/usr/bin/env python3
"""
Cost Analyzer: Kubernetes Resource Usage Analysis Tool

Analyzes pod resource requests/limits vs actual usage to identify:
- Over-provisioned resources (high requests, low usage)
- Under-provisioned resources (low requests, high usage)
- Right-sizing opportunities
- Cost optimization recommendations

Uses kubectl to query resource metrics and pod specifications.
Requires Metrics Server installed for usage data.

Usage:
    python3 cost-analyzer.py --namespace production
    python3 cost-analyzer.py --namespace production --output-format json
    python3 cost-analyzer.py --all-namespaces --show-waste
"""

import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from decimal import Decimal


@dataclass
class ResourceMetrics:
    """Resource request, limit, and usage metrics"""
    requested_cpu: str = "0m"
    requested_memory: str = "0Mi"
    limited_cpu: str = "0m"
    limited_memory: str = "0Mi"
    used_cpu: str = "0m"
    used_memory: str = "0Mi"


@dataclass
class PodAnalysis:
    """Analysis of a single pod's resource efficiency"""
    pod_name: str
    namespace: str
    container_name: str
    metrics: ResourceMetrics
    cpu_utilization_percent: float
    memory_utilization_percent: float
    is_over_provisioned: bool
    recommendation: str


class ResourceConverter:
    """Convert Kubernetes resource units to comparable values"""
    
    @staticmethod
    def cpu_to_millicores(value: str) -> int:
        """Convert CPU value to millicores (m)"""
        if not value or value == "0":
            return 0
        value = str(value).strip()
        if value.endswith("m"):
            return int(value[:-1])
        elif value.endswith("n"):
            return int(int(value[:-1]) / 1_000_000)
        else:
            return int(float(value) * 1000)
    
    @staticmethod
    def memory_to_bytes(value: str) -> int:
        """Convert memory value to bytes"""
        if not value or value == "0":
            return 0
        value = str(value).strip()
        multipliers = {
            "Ki": 1024,
            "Mi": 1024 ** 2,
            "Gi": 1024 ** 3,
            "Ti": 1024 ** 4,
            "K": 1000,
            "M": 1000 ** 2,
            "G": 1000 ** 3,
        }
        for unit, multiplier in multipliers.items():
            if value.endswith(unit):
                return int(value[:-len(unit)]) * multiplier
        return int(value)


class KubectlClient:
    """Interface to kubectl for resource queries"""
    
    @staticmethod
    def run_command(cmd: List[str]) -> Dict[str, Any]:
        """Execute kubectl command and return JSON output"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout) if result.stdout else {}
        except subprocess.CalledProcessError as e:
            print(f"Error executing {' '.join(cmd)}: {e.stderr}", file=sys.stderr)
            return {}
    
    @staticmethod
    def get_pod_metrics(namespace: str = None) -> Dict[str, Any]:
        """Get pod resource usage from metrics-server"""
        cmd = ["kubectl", "top", "pods", "-o", "json"]
        if namespace:
            cmd.extend(["-n", namespace])
        else:
            cmd.append("-A")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout) if result.stdout else {"items": []}
        except subprocess.CalledProcessError:
            print("Warning: Could not retrieve metrics. Metrics Server may not be installed.", file=sys.stderr)
            return {"items": []}
    
    @staticmethod
    def get_pods(namespace: str = None) -> Dict[str, Any]:
        """Get all pods with resource requests/limits"""
        cmd = ["kubectl", "get", "pods", "-o", "json"]
        if namespace:
            cmd.extend(["-n", namespace])
        else:
            cmd.append("-A")
        return KubectlClient.run_command(cmd)
    
    @staticmethod
    def get_namespaces() -> List[str]:
        """Get all namespaces"""
        cmd = ["kubectl", "get", "namespaces", "-o", "json"]
        result = KubectlClient.run_command(cmd)
        return [ns["metadata"]["name"] for ns in result.get("items", [])]


class CostAnalyzer:
    """Analyze Kubernetes resource costs and efficiency"""
    
    def __init__(self):
        self.converter = ResourceConverter()
        self.client = KubectlClient()
        self.analyses: List[PodAnalysis] = []
    
    def analyze_namespace(self, namespace: str) -> List[PodAnalysis]:
        """Analyze all pods in a namespace"""
        self.analyses = []
        
        pods = self.client.get_pods(namespace)
        metrics = self.client.get_pod_metrics(namespace)
        
        # Create metrics lookup by pod
        metrics_by_pod = {}
        for pod in metrics.get("items", []):
            key = (pod["metadata"]["namespace"], pod["metadata"]["name"])
            metrics_by_pod[key] = pod
        
        # Analyze each pod
        for pod in pods.get("items", []):
            pod_ns = pod["metadata"]["namespace"]
            pod_name = pod["metadata"]["name"]
            
            for container in pod["spec"]["containers"]:
                analysis = self._analyze_container(
                    pod_name, pod_ns, container, metrics_by_pod.get((pod_ns, pod_name))
                )
                self.analyses.append(analysis)
        
        return self.analyses
    
    def _analyze_container(
        self,
        pod_name: str,
        namespace: str,
        container: Dict,
        pod_metrics: Optional[Dict]
    ) -> PodAnalysis:
        """Analyze a single container"""
        container_name = container["name"]
        resources = container.get("resources", {})
        
        # Parse requested resources
        requests = resources.get("requests", {})
        requested_cpu = requests.get("cpu", "0")
        requested_memory = requests.get("memory", "0")
        
        # Parse limited resources
        limits = resources.get("limits", {})
        limited_cpu = limits.get("cpu", "0")
        limited_memory = limits.get("memory", "0")
        
        # Get actual usage from metrics
        used_cpu = "0m"
        used_memory = "0Mi"
        
        if pod_metrics:
            for container_metric in pod_metrics.get("containers", []):
                if container_metric["name"] == container_name:
                    used_cpu = container_metric.get("cpu", "0m")
                    used_memory = container_metric.get("memory", "0Mi")
        
        metrics = ResourceMetrics(
            requested_cpu=requested_cpu,
            requested_memory=requested_memory,
            limited_cpu=limited_cpu,
            limited_memory=limited_memory,
            used_cpu=used_cpu,
            used_memory=used_memory,
        )
        
        # Calculate utilization percentages
        cpu_util = self._calculate_utilization(used_cpu, requested_cpu, resource_type="cpu")
        mem_util = self._calculate_utilization(used_memory, requested_memory, resource_type="memory")
        
        # Determine if over-provisioned
        is_over_provisioned = cpu_util < 20 or mem_util < 20
        
        recommendation = self._generate_recommendation(cpu_util, mem_util, metrics)
        
        return PodAnalysis(
            pod_name=pod_name,
            namespace=namespace,
            container_name=container_name,
            metrics=metrics,
            cpu_utilization_percent=cpu_util,
            memory_utilization_percent=mem_util,
            is_over_provisioned=is_over_provisioned,
            recommendation=recommendation
        )
    
    def _calculate_utilization(self, used: str, requested: str, resource_type: str = "cpu") -> float:
        """Calculate resource utilization percentage"""
        if resource_type == "cpu":
            used_val = self.converter.cpu_to_millicores(used)
            req_val = self.converter.cpu_to_millicores(requested)
        else:
            used_val = self.converter.memory_to_bytes(used)
            req_val = self.converter.memory_to_bytes(requested)
        
        if req_val == 0:
            return 0.0
        return (used_val / req_val) * 100
    
    def _generate_recommendation(
        self,
        cpu_util: float,
        mem_util: float,
        metrics: ResourceMetrics
    ) -> str:
        """Generate optimization recommendation"""
        recommendations = []
        
        if cpu_util < 20:
            recommendations.append("Reduce CPU request (used < 20%)")
        if mem_util < 20:
            recommendations.append("Reduce memory request (used < 20%)")
        if cpu_util > 80:
            recommendations.append("Increase CPU request (used > 80%)")
        if mem_util > 80:
            recommendations.append("Increase memory request (used > 80%)")
        
        if not recommendations:
            return "Resource requests well-tuned"
        return " | ".join(recommendations)
    
    def print_summary(self):
        """Print analysis summary"""
        if not self.analyses:
            print("No pods analyzed")
            return
        
        print("\n=== Kubernetes Resource Cost Analysis ===\n")
        
        over_provisioned = [a for a in self.analyses if a.is_over_provisioned]
        under_provisioned = [a for a in self.analyses if a.cpu_utilization_percent > 80 or a.memory_utilization_percent > 80]
        
        print(f"Total containers analyzed: {len(self.analyses)}")
        print(f"Over-provisioned (< 20% utilization): {len(over_provisioned)}")
        print(f"Under-provisioned (> 80% utilization): {len(under_provisioned)}")
        print(f"Well-tuned: {len(self.analyses) - len(over_provisioned) - len(under_provisioned)}\n")
        
        if over_provisioned:
            print("=== Over-Provisioned Containers ===")
            for analysis in sorted(over_provisioned, key=lambda x: x.cpu_utilization_percent):
                print(f"  {analysis.namespace}/{analysis.pod_name}/{analysis.container_name}")
                print(f"    CPU:    {analysis.cpu_utilization_percent:.1f}% (requested: {analysis.metrics.requested_cpu}, used: {analysis.metrics.used_cpu})")
                print(f"    Memory: {analysis.memory_utilization_percent:.1f}% (requested: {analysis.metrics.requested_memory}, used: {analysis.metrics.used_memory})")
                print(f"    Recommendation: {analysis.recommendation}\n")
        
        if under_provisioned:
            print("\n=== Under-Provisioned Containers ===")
            for analysis in sorted(under_provisioned, key=lambda x: max(x.cpu_utilization_percent, x.memory_utilization_percent), reverse=True):
                print(f"  {analysis.namespace}/{analysis.pod_name}/{analysis.container_name}")
                print(f"    CPU:    {analysis.cpu_utilization_percent:.1f}% (requested: {analysis.metrics.requested_cpu}, used: {analysis.metrics.used_cpu})")
                print(f"    Memory: {analysis.memory_utilization_percent:.1f}% (requested: {analysis.metrics.requested_memory}, used: {analysis.metrics.used_memory})")
                print(f"    Recommendation: {analysis.recommendation}\n")
    
    def to_json(self) -> str:
        """Export analysis as JSON"""
        data = {
            "summary": {
                "total": len(self.analyses),
                "over_provisioned": len([a for a in self.analyses if a.is_over_provisioned]),
            },
            "analyses": [
                {
                    **asdict(analysis),
                    "metrics": asdict(analysis.metrics)
                }
                for analysis in self.analyses
            ]
        }
        return json.dumps(data, indent=2)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze Kubernetes resource costs and efficiency"
    )
    parser.add_argument(
        "--namespace",
        default="default",
        help="Namespace to analyze (default: default)"
    )
    parser.add_argument(
        "--all-namespaces",
        action="store_true",
        help="Analyze all namespaces"
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    
    args = parser.parse_args()
    
    analyzer = CostAnalyzer()
    
    if args.all_namespaces:
        namespaces = analyzer.client.get_namespaces()
        for ns in namespaces:
            analyzer.analyze_namespace(ns)
    else:
        analyzer.analyze_namespace(args.namespace)
    
    if args.output_format == "json":
        print(analyzer.to_json())
    else:
        analyzer.print_summary()


if __name__ == "__main__":
    main()
