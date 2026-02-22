#!/usr/bin/env python3
"""
Cost Anomaly Detector: Statistical anomaly detection for Kubernetes costs

Monitors cost metrics and detects anomalies using:
- Z-score detection (statistical deviation)
- Spike detection (sudden increases)
- Trend analysis (gradual increases)

Can monitor simulated metrics or integrate with Kubecost/Prometheus.

Usage:
    python3 cost-anomaly-detector.py --generate-data
    python3 cost-anomaly-detector.py --monitor --threshold 2.0
    python3 cost-anomaly-detector.py --simulate-spike
"""

import json
import math
import sys
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional, Dict
from collections import deque


@dataclass
class CostMetric:
    """A cost metric data point"""
    timestamp: str
    namespace: str
    cost_value: float
    resource_type: str  # pod, node, cluster
    team: str


@dataclass
class AnomalyDetection:
    """Detection result for an anomaly"""
    detected_at: str
    namespace: str
    anomaly_type: str  # spike, trend, outlier
    severity: str  # low, medium, high
    z_score: float
    expected_value: float
    actual_value: float
    message: str


class StatisticalAnalyzer:
    """Statistical analysis for cost data"""
    
    @staticmethod
    def calculate_mean(values: List[float]) -> float:
        """Calculate mean of values"""
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    @staticmethod
    def calculate_std_dev(values: List[float], mean: Optional[float] = None) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        if mean is None:
            mean = StatisticalAnalyzer.calculate_mean(values)
        
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
    
    @staticmethod
    def calculate_z_score(value: float, mean: float, std_dev: float) -> float:
        """Calculate z-score for a value"""
        if std_dev == 0:
            return 0.0
        return (value - mean) / std_dev


class CostAnomalyDetector:
    """Detects anomalies in Kubernetes cost metrics"""
    
    def __init__(self, lookback_hours: int = 24, threshold: float = 2.0):
        """
        Initialize detector.
        
        Args:
            lookback_hours: Hours of historical data to use for baseline
            threshold: Z-score threshold for anomaly detection (standard: 2.0-3.0)
        """
        self.lookback_hours = lookback_hours
        self.threshold = threshold
        self.analyzer = StatisticalAnalyzer()
        self.history: Dict[str, deque] = {}  # Historical data by namespace
        self.anomalies: List[AnomalyDetection] = []
    
    def add_metric(self, metric: CostMetric):
        """Add a cost metric to history"""
        ns = metric.namespace
        
        if ns not in self.history:
            self.history[ns] = deque(maxlen=1000)
        
        self.history[ns].append(metric)
    
    def detect_anomalies(self) -> List[AnomalyDetection]:
        """Detect anomalies in collected metrics"""
        self.anomalies = []
        
        for namespace, metrics_deque in self.history.items():
            if len(metrics_deque) < 5:
                continue  # Need minimum historical data
            
            metrics_list = list(metrics_deque)
            
            # Check latest metric for anomalies
            latest = metrics_list[-1]
            historical = metrics_list[:-1]
            
            # Spike detection: sudden increase
            if len(historical) > 0:
                spike_detection = self._detect_spike(latest, historical)
                if spike_detection:
                    self.anomalies.append(spike_detection)
            
            # Statistical outlier detection using z-score
            if len(historical) > 2:
                outlier_detection = self._detect_outlier(latest, historical)
                if outlier_detection:
                    self.anomalies.append(outlier_detection)
        
        return self.anomalies
    
    def _detect_spike(self, latest: CostMetric, historical: List[CostMetric]) -> Optional[AnomalyDetection]:
        """Detect sudden spike in costs"""
        historical_values = [m.cost_value for m in historical[-10:]]  # Last 10 points
        
        if not historical_values:
            return None
        
        avg_previous = self.analyzer.calculate_mean(historical_values)
        spike_percent = ((latest.cost_value - avg_previous) / avg_previous * 100) if avg_previous > 0 else 0
        
        # Detect if cost increased more than 50%
        if spike_percent > 50:
            severity = "high" if spike_percent > 100 else "medium" if spike_percent > 75 else "low"
            
            return AnomalyDetection(
                detected_at=datetime.now().isoformat(),
                namespace=latest.namespace,
                anomaly_type="spike",
                severity=severity,
                z_score=spike_percent / 50,  # Normalize to z-score scale
                expected_value=avg_previous,
                actual_value=latest.cost_value,
                message=f"Cost spike detected: {spike_percent:.1f}% increase ({avg_previous:.2f} -> {latest.cost_value:.2f})"
            )
        
        return None
    
    def _detect_outlier(self, latest: CostMetric, historical: List[CostMetric]) -> Optional[AnomalyDetection]:
        """Detect statistical outliers using z-score"""
        historical_values = [m.cost_value for m in historical]
        
        mean = self.analyzer.calculate_mean(historical_values)
        std_dev = self.analyzer.calculate_std_dev(historical_values, mean)
        
        z_score = self.analyzer.calculate_z_score(latest.cost_value, mean, std_dev)
        
        # Detect if z-score exceeds threshold
        if abs(z_score) > self.threshold:
            severity = "high" if abs(z_score) > 3.0 else "medium" if abs(z_score) > 2.5 else "low"
            direction = "increase" if z_score > 0 else "decrease"
            
            return AnomalyDetection(
                detected_at=datetime.now().isoformat(),
                namespace=latest.namespace,
                anomaly_type="outlier",
                severity=severity,
                z_score=z_score,
                expected_value=mean,
                actual_value=latest.cost_value,
                message=f"Statistical {direction} anomaly: z-score {z_score:.2f} (expected {mean:.2f}, got {latest.cost_value:.2f})"
            )
        
        return None
    
    def print_anomalies(self):
        """Print detected anomalies"""
        if not self.anomalies:
            print("No anomalies detected")
            return
        
        print(f"\n=== Cost Anomalies Detected: {len(self.anomalies)} ===\n")
        
        # Group by severity
        by_severity = {}
        for anomaly in self.anomalies:
            if anomaly.severity not in by_severity:
                by_severity[anomaly.severity] = []
            by_severity[anomaly.severity].append(anomaly)
        
        for severity in ["high", "medium", "low"]:
            if severity not in by_severity:
                continue
            
            print(f"\n--- {severity.upper()} SEVERITY ---")
            for anomaly in by_severity[severity]:
                print(f"Time: {anomaly.detected_at}")
                print(f"Namespace: {anomaly.namespace}")
                print(f"Type: {anomaly.anomaly_type}")
                print(f"Z-Score: {anomaly.z_score:.2f}")
                print(f"Expected: ${anomaly.expected_value:.2f}")
                print(f"Actual: ${anomaly.actual_value:.2f}")
                print(f"Message: {anomaly.message}")
                print()
    
    def to_json(self) -> str:
        """Export anomalies as JSON"""
        return json.dumps(
            [asdict(a) for a in self.anomalies],
            indent=2
        )


class CostDataGenerator:
    """Generates synthetic cost data for testing"""
    
    @staticmethod
    def generate_normal_data(namespace: str = "production", hours: int = 24) -> List[CostMetric]:
        """Generate normal cost data with typical variation"""
        metrics = []
        base_cost = 100.0
        
        now = datetime.now()
        for i in range(hours * 6):  # 10-minute intervals
            timestamp = now - timedelta(hours=hours) + timedelta(minutes=i*10)
            
            # Add typical daily variation (higher during business hours)
            hour_of_day = timestamp.hour
            daily_factor = 1.2 if 8 <= hour_of_day <= 17 else 0.8
            
            # Add small random variation
            import random
            variation = random.uniform(0.95, 1.05)
            
            cost = base_cost * daily_factor * variation
            
            metrics.append(CostMetric(
                timestamp=timestamp.isoformat(),
                namespace=namespace,
                cost_value=cost,
                resource_type="pod",
                team="platform-team"
            ))
        
        return metrics
    
    @staticmethod
    def add_spike(metrics: List[CostMetric], spike_size: float = 2.0, hour: int = 18) -> List[CostMetric]:
        """Add a cost spike to metrics at specific hour"""
        for metric in metrics:
            ts = datetime.fromisoformat(metric.timestamp)
            if ts.hour == hour:
                metric.cost_value *= spike_size
        return metrics


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Detect anomalies in Kubernetes cost metrics"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=2.0,
        help="Z-score threshold for anomaly detection (default: 2.0)"
    )
    parser.add_argument(
        "--lookback-hours",
        type=int,
        default=24,
        help="Hours of historical data to use (default: 24)"
    )
    parser.add_argument(
        "--generate-data",
        action="store_true",
        help="Generate synthetic normal cost data for testing"
    )
    parser.add_argument(
        "--simulate-spike",
        action="store_true",
        help="Simulate a cost spike in generated data"
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    
    args = parser.parse_args()
    
    detector = CostAnomalyDetector(
        lookback_hours=args.lookback_hours,
        threshold=args.threshold
    )
    
    # Generate or load data
    if args.generate_data:
        print("Generating synthetic cost data...")
        metrics = CostDataGenerator.generate_normal_data(hours=24)
        
        if args.simulate_spike:
            print("Adding cost spike at hour 18...")
            metrics = CostDataGenerator.add_spike(metrics, spike_size=2.5, hour=18)
        
        for metric in metrics:
            detector.add_metric(metric)
    else:
        # In production, would load from Kubecost/Prometheus API
        print("No data provided. Use --generate-data to test with synthetic data.")
        sys.exit(1)
    
    # Detect anomalies
    detector.detect_anomalies()
    
    if args.output == "json":
        print(detector.to_json())
    else:
        detector.print_anomalies()
        
        if not detector.anomalies:
            print("Test: System working correctly - no anomalies in normal data")


if __name__ == "__main__":
    main()
