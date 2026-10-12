#!/usr/bin/env python3
"""
Chaos Experiment Runner and Monitoring

This script orchestrates chaos experiments, monitors their impact on systems,
and generates resilience reports. It supports both Chaos Mesh and LitmusChaos.

Usage:
    python3 chaos-runner.py --experiment chaos-experiment-pod-kill.yaml
    python3 chaos-runner.py --list-experiments
    python3 chaos-runner.py --generate-report
"""

import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Chaos experiment status values."""
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    PAUSED = "Paused"


@dataclass
class ExperimentMetrics:
    """Metrics collected during chaos experiment."""
    start_time: str
    end_time: Optional[str]
    duration_seconds: float
    error_count: int
    error_rate: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    pod_restarts: int
    pods_affected: int
    data_available: bool = True


def experiment_phase(experiment: Dict) -> str:
    """Summarize a PodChaos/NetworkChaos object as an ExperimentStatus value.

    Chaos Mesh 2.x has no single phase field; progress is reported through the
    AllInjected / AllRecovered conditions and status.experiment.desiredPhase.
    """
    conditions = {
        c.get("type"): c.get("status")
        for c in experiment.get("status", {}).get("conditions", [])
    }
    desired = experiment.get("status", {}).get("experiment", {}).get("desiredPhase")

    if desired == "Stop" and conditions.get("AllRecovered") == "True":
        return ExperimentStatus.COMPLETED.value
    # pod-kill and container-kill are one-shot: they inject once and never "recover"
    if (experiment.get("spec", {}).get("action") in ("pod-kill", "container-kill")
            and conditions.get("AllInjected") == "True"):
        return ExperimentStatus.COMPLETED.value
    if conditions.get("Paused") == "True":
        return ExperimentStatus.PAUSED.value
    if conditions.get("AllInjected") == "True":
        return ExperimentStatus.RUNNING.value
    return ExperimentStatus.PENDING.value


class ChaosExperimentRunner:
    """Runs and monitors chaos experiments."""

    def __init__(self, chaos_namespace: str = "chaos-testing"):
        """Initialize chaos experiment runner.
        
        Args:
            chaos_namespace: Kubernetes namespace for chaos experiments
        """
        self.chaos_namespace = chaos_namespace
        self.experiments = {}

    def _run_command(self, command: List[str]) -> Tuple[int, str, str]:
        """Execute shell command and return output.
        
        Args:
            command: Command to execute as list of strings
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout: {' '.join(command)}")
            return 124, "", "Command timeout"
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return 1, "", str(e)

    def create_experiment(
        self,
        experiment_name: str,
        yaml_file: str
    ) -> bool:
        """Create a chaos experiment from YAML file.
        
        Args:
            experiment_name: Name for the experiment
            yaml_file: Path to YAML file defining experiment
            
        Returns:
            True if experiment created successfully
        """
        logger.info(f"Creating chaos experiment from {yaml_file}")
        
        # Create namespace if it doesn't exist
        self._ensure_namespace_exists(self.chaos_namespace)
        
        cmd = ["kubectl", "apply", "-f", yaml_file, "-n", self.chaos_namespace]
        returncode, stdout, stderr = self._run_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to create experiment: {stderr}")
            return False
        
        logger.info(f"Experiment created: {experiment_name}")
        # `kubectl apply` prints "podchaos.chaos-mesh.org/<name> created|configured|unchanged";
        # keep the PodChaos/NetworkChaos names so they can be waited on individually
        objects = [
            line.split()[0].split("/", 1)[1]
            for line in stdout.splitlines()
            if line.startswith(("podchaos.", "networkchaos."))
        ]
        self.experiments[experiment_name] = {
            "status": ExperimentStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "yaml_file": yaml_file,
            "objects": objects
        }
        return True

    def _ensure_namespace_exists(self, namespace: str) -> bool:
        """Ensure Kubernetes namespace exists.
        
        Args:
            namespace: Namespace name
            
        Returns:
            True if namespace exists or was created
        """
        cmd = ["kubectl", "get", "namespace", namespace]
        returncode, _, _ = self._run_command(cmd)
        
        if returncode == 0:
            return True
        
        logger.info(f"Creating namespace: {namespace}")
        cmd = ["kubectl", "create", "namespace", namespace]
        returncode, _, stderr = self._run_command(cmd)
        
        if returncode != 0:
            logger.warning(f"Failed to create namespace: {stderr}")
            return False
        
        return True

    def list_experiments(self) -> List[Dict]:
        """List all chaos experiments in namespace.
        
        Returns:
            List of experiment dictionaries
        """
        cmd = [
            "kubectl", "get", "podchaos,networkchaos",
            "-n", self.chaos_namespace,
            "-o", "json"
        ]
        returncode, stdout, stderr = self._run_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to list experiments: {stderr}")
            return []
        
        try:
            data = json.loads(stdout)
            experiments = data.get("items", [])
            
            result = []
            for exp in experiments:
                result.append({
                    "name": exp.get("metadata", {}).get("name"),
                    "kind": exp.get("kind"),
                    "status": experiment_phase(exp),
                    "created": exp.get("metadata", {}).get("creationTimestamp")
                })
            
            return result
        except json.JSONDecodeError:
            logger.error("Failed to parse experiments JSON")
            return []

    def get_experiment_status(self, experiment_name: str) -> Dict:
        """Get detailed status of an experiment.
        
        Args:
            experiment_name: Name of the experiment
            
        Returns:
            Status dictionary
        """
        # Try PodChaos first
        cmd = [
            "kubectl", "get", "podchaos", experiment_name,
            "-n", self.chaos_namespace,
            "-o", "json"
        ]
        returncode, stdout, stderr = self._run_command(cmd)
        
        if returncode != 0:
            # Try NetworkChaos
            cmd = [
                "kubectl", "get", "networkchaos", experiment_name,
                "-n", self.chaos_namespace,
                "-o", "json"
            ]
            returncode, stdout, stderr = self._run_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to get experiment status: {stderr}")
            return {}
        
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            logger.error("Failed to parse experiment status JSON")
            return {}

    def wait_for_experiment(
        self,
        experiment_name: str,
        timeout_seconds: int = 600
    ) -> bool:
        """Wait for experiment to complete.
        
        Args:
            experiment_name: Name of the experiment
            timeout_seconds: Maximum time to wait
            
        Returns:
            True if experiment completed successfully
        """
        logger.info(f"Waiting for experiment to complete: {experiment_name}")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            status = self.get_experiment_status(experiment_name)
            phase = experiment_phase(status) if status else None

            if phase == ExperimentStatus.COMPLETED.value:
                logger.info(f"Experiment completed: {experiment_name}")
                return True

            logger.info(f"Experiment status: {phase}")
            time.sleep(10)
        
        logger.error(f"Experiment timeout: {experiment_name}")
        return False

    def collect_metrics(
        self,
        duration_seconds: int = 600
    ) -> ExperimentMetrics:
        """Collect metrics during chaos experiment.
        
        Args:
            duration_seconds: Duration to collect metrics
            
        Returns:
            Metrics collected during experiment
        """
        logger.info(f"Collecting metrics for {duration_seconds} seconds...")
        
        metrics = ExperimentMetrics(
            start_time=datetime.utcnow().isoformat(),
            end_time=None,
            duration_seconds=duration_seconds,
            error_count=0,
            error_rate=0.0,
            latency_p50=0.0,
            latency_p95=0.0,
            latency_p99=0.0,
            pod_restarts=0,
            pods_affected=0
        )
        
        # Query Prometheus for metrics
        # This is a simplified example
        results = []  # raw query results; None means Prometheus had no data
        try:
            # Query error rate
            error_rate = self._query_prometheus(
                'rate(http_requests_total{status=~"5.."}[5m])'
            )
            results.append(error_rate)
            metrics.error_rate = float(error_rate) if error_rate else 0.0
            
            # Query latency percentiles
            p99 = self._query_prometheus(
                'histogram_quantile(0.99, rate(request_duration_seconds_bucket[5m]))'
            )
            results.append(p99)
            metrics.latency_p99 = float(p99) if p99 else 0.0
            
            p95 = self._query_prometheus(
                'histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m]))'
            )
            results.append(p95)
            metrics.latency_p95 = float(p95) if p95 else 0.0
            
            # Query pod restarts
            restarts = self._query_prometheus(
                'increase(kube_pod_container_status_restarts_total[5m])'
            )
            results.append(restarts)
            metrics.pod_restarts = int(float(restarts)) if restarts else 0
            
        except Exception as e:
            logger.warning(f"Failed to collect Prometheus metrics: {e}")

        # No result at all: Prometheus unreachable on localhost:9090, or the workload
        # does not export these metrics. A real zero is still data.
        metrics.data_available = any(value is not None for value in results)

        metrics.end_time = datetime.utcnow().isoformat()
        return metrics

    def _query_prometheus(self, query: str) -> Optional[str]:
        """Query Prometheus for a metric value.
        
        Args:
            query: PromQL query string
            
        Returns:
            Metric value or None
        """
        try:
            # This assumes Prometheus is accessible at localhost:9090
            # In production, use requests library or official client
            import urllib.parse
            import urllib.request
            import json

            url = f"http://localhost:9090/api/v1/query?query={urllib.parse.quote(query)}"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read())
                result = data.get("data", {}).get("result", [])
                if result:
                    return result[0].get("value", [None, None])[1]
            return None
        except Exception as e:
            logger.debug(f"Prometheus query failed: {e}")
            return None

    def delete_experiment(self, experiment_name: str) -> bool:
        """Delete a chaos experiment.
        
        Args:
            experiment_name: Name of the experiment
            
        Returns:
            True if deleted successfully
        """
        cmd = [
            "kubectl", "delete", "podchaos,networkchaos",
            experiment_name,
            "-n", self.chaos_namespace,
            "--ignore-not-found"
        ]
        
        returncode, _, stderr = self._run_command(cmd)
        
        if returncode != 0:
            logger.error(f"Failed to delete experiment: {stderr}")
            return False
        
        logger.info(f"Experiment deleted: {experiment_name}")
        return True

    def generate_report(
        self,
        experiment_name: str,
        metrics: ExperimentMetrics
    ) -> str:
        """Generate resilience report for an experiment.
        
        Args:
            experiment_name: Name of the experiment
            metrics: Metrics collected during experiment
            
        Returns:
            Report as formatted string
        """
        report = []
        report.append("=" * 70)
        report.append("CHAOS EXPERIMENT RESILIENCE REPORT")
        report.append("=" * 70)
        report.append("")
        
        report.append(f"Experiment: {experiment_name}")
        report.append(f"Started: {metrics.start_time}")
        report.append(f"Completed: {metrics.end_time}")
        report.append(f"Duration: {metrics.duration_seconds} seconds")
        report.append("")
        
        report.append("IMPACT METRICS:")
        report.append("-" * 70)
        report.append(f"Error Rate: {metrics.error_rate:.4f} (errors/second)")
        report.append(f"Error Count: {metrics.error_count}")
        report.append(f"Latency p50: {metrics.latency_p50*1000:.2f}ms")
        report.append(f"Latency p95: {metrics.latency_p95*1000:.2f}ms")
        report.append(f"Latency p99: {metrics.latency_p99*1000:.2f}ms")
        report.append(f"Pod Restarts: {metrics.pod_restarts}")
        report.append(f"Pods Affected: {metrics.pods_affected}")
        report.append("")
        
        report.append("RESILIENCE ASSESSMENT:")
        report.append("-" * 70)

        if not metrics.data_available:
            report.append("! No Prometheus data returned (check the port-forward to localhost:9090")
            report.append("  and that the workload exports http_requests_total and")
            report.append("  request_duration_seconds_bucket); the checks below are not meaningful.")

        # Assess resilience based on metrics
        assessments = []

        if metrics.error_rate < 0.001:
            assessments.append("✓ System maintained availability during experiment")
        else:
            assessments.append("✗ Error rate exceeded acceptable threshold")
        
        if metrics.latency_p99 < 0.5:
            assessments.append("✓ Latency remained within SLO targets")
        else:
            assessments.append("✗ Latency exceeded SLO targets")
        
        if metrics.pod_restarts < 5:
            assessments.append("✓ Pod restart behavior within normal parameters")
        else:
            assessments.append("✗ Excessive pod restarts detected")
        
        for assessment in assessments:
            report.append(assessment)
        
        report.append("")
        report.append("RECOMMENDATIONS:")
        report.append("-" * 70)
        
        if metrics.error_rate > 0.001:
            report.append("1. Implement circuit breakers to handle cascading failures")
        
        if metrics.latency_p99 > 0.5:
            report.append("2. Review timeout configurations and add retry logic")
        
        if metrics.pod_restarts > 5:
            report.append("3. Investigate pod stability issues and resource limits")
        
        report.append("")
        
        return "\n".join(report)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Chaos experiment runner and monitoring"
    )
    parser.add_argument(
        "--experiment",
        help="YAML file defining chaos experiment"
    )
    parser.add_argument(
        "--list-experiments",
        action="store_true",
        help="List all active chaos experiments"
    )
    parser.add_argument(
        "--get-status",
        help="Get status of specific experiment"
    )
    parser.add_argument(
        "--wait",
        metavar="EXPERIMENT",
        help="Wait for experiment to complete"
    )
    parser.add_argument(
        "--generate-report",
        metavar="EXPERIMENT",
        help="Generate report for experiment"
    )
    parser.add_argument(
        "--delete",
        metavar="EXPERIMENT",
        help="Delete chaos experiment"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate experiment without running"
    )
    
    args = parser.parse_args()
    
    runner = ChaosExperimentRunner()
    
    # Create and run experiment
    if args.experiment:
        if args.dry_run:
            # Validate YAML syntax
            logger.info("Validating experiment YAML...")
            cmd = ["kubectl", "apply", "-f", args.experiment, "--dry-run=client"]
            returncode, _, stderr = runner._run_command(cmd)
            if returncode == 0:
                logger.info("Validation successful")
                sys.exit(0)
            else:
                logger.error(f"Validation failed: {stderr}")
                sys.exit(1)
        else:
            exp_name = args.experiment.split('/')[-1].replace('.yaml', '')
            success = runner.create_experiment(exp_name, args.experiment)
            
            if success:
                # Wait for completion and collect metrics
                # A YAML file can define several experiments; wait for each one
                for obj_name in runner.experiments[exp_name]["objects"]:
                    runner.wait_for_experiment(obj_name, timeout_seconds=900)
                metrics = runner.collect_metrics()
                report = runner.generate_report(exp_name, metrics)
                print(report)
            
            sys.exit(0 if success else 1)
    
    # List experiments
    if args.list_experiments:
        experiments = runner.list_experiments()
        for exp in experiments:
            print(f"{exp['name']}: {exp['status']} ({exp['kind']})")
        sys.exit(0)
    
    # Get status
    if args.get_status:
        status = runner.get_experiment_status(args.get_status)
        print(f"Status: {experiment_phase(status) if status else 'Not found'}")
        sys.exit(0)
    
    # Wait for experiment
    if args.wait:
        success = runner.wait_for_experiment(args.wait)
        sys.exit(0 if success else 1)
    
    # Generate report
    if args.generate_report:
        metrics = runner.collect_metrics()
        report = runner.generate_report(args.generate_report, metrics)
        print(report)
        sys.exit(0)
    
    # Delete experiment
    if args.delete:
        success = runner.delete_experiment(args.delete)
        sys.exit(0 if success else 1)
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
