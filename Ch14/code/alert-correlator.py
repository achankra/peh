#!/usr/bin/env python3
"""
Alert Correlator: AI-powered alert grouping and root cause analysis.

This module demonstrates:
- Grouping related alerts based on temporal, metric, and host proximity
- Deduplicating similar alerts
- Identifying root cause patterns
- Reducing alert noise

The correlator uses heuristics suitable for real-time processing,
with optional LLM integration for advanced pattern recognition.
"""

import json
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import math


@dataclass
class Alert:
    """Represents a single alert event."""
    id: str
    timestamp: float
    alert_type: str
    severity: str  # critical, warning, info
    source: str  # host/service generating alert
    metric: str  # what metric triggered alert
    value: float  # current metric value
    threshold: float  # alert threshold
    message: str


@dataclass
class CorrelatedIncident:
    """Represents a group of correlated alerts."""
    incident_id: str
    severity: str
    created_at: float
    alerts: List[Alert]
    root_cause: Optional[str]
    correlation_score: float
    suggested_action: str


class AlertCorrelator:
    """
    Groups related alerts and identifies root cause patterns.

    Configuration:
    - TIME_WINDOW: seconds within which alerts are considered related
    - SIMILARITY_THRESHOLD: metric similarity score for correlation
    - DEDUP_THRESHOLD: exact duplicate detection
    """

    TIME_WINDOW = 300  # 5 minutes
    SIMILARITY_THRESHOLD = 0.7
    DEDUP_THRESHOLD = 0.95

    def __init__(self):
        """Initialize the correlator."""
        self.pending_alerts: List[Alert] = []
        self.incidents: List[CorrelatedIncident] = []
        self.correlation_patterns: Dict[str, Dict] = {}

    def ingest_alert(self, alert: Alert) -> None:
        """
        Ingest a new alert into the correlation engine.

        Args:
            alert: Alert to process
        """
        # Check for exact duplicates
        if self._is_duplicate(alert):
            return

        self.pending_alerts.append(alert)

    def correlate(self, alerts: Optional[List[Alert]] = None) -> List[CorrelatedIncident]:
        """
        Correlate pending alerts into incidents.

        Args:
            alerts: Optional list of alerts (uses pending_alerts if None)

        Returns:
            List of correlated incidents
        """
        if alerts:
            self.pending_alerts = alerts

        if not self.pending_alerts:
            return []

        # Group by time windows
        time_groups = self._group_by_time()

        incidents = []
        for group in time_groups:
            # Further correlate within time group
            correlations = self._correlate_group(group)
            for correlation in correlations:
                incident = self._create_incident(correlation)
                self._analyze_root_cause(incident)
                incidents.append(incident)

        self.incidents.extend(incidents)
        self.pending_alerts = []
        return incidents

    def _is_duplicate(self, alert: Alert) -> bool:
        """Check if alert is a duplicate of recent alert."""
        for pending in self.pending_alerts:
            similarity = self._calculate_similarity(alert, pending)
            if similarity > self.DEDUP_THRESHOLD:
                return True
        return False

    def _group_by_time(self) -> List[List[Alert]]:
        """Group alerts by time windows."""
        if not self.pending_alerts:
            return []

        # Sort by timestamp
        sorted_alerts = sorted(self.pending_alerts, key=lambda a: a.timestamp)

        groups = []
        current_group = [sorted_alerts[0]]

        for alert in sorted_alerts[1:]:
            time_diff = alert.timestamp - current_group[-1].timestamp
            if time_diff <= self.TIME_WINDOW:
                current_group.append(alert)
            else:
                groups.append(current_group)
                current_group = [alert]

        if current_group:
            groups.append(current_group)

        return groups

    def _correlate_group(self, alerts: List[Alert]) -> List[List[Alert]]:
        """
        Correlate alerts within a time window using similarity.
        Uses a simple clustering approach based on metric and host.
        """
        if not alerts:
            return []

        correlated = []
        used = set()

        for i, alert in enumerate(alerts):
            if i in used:
                continue

            cluster = [alert]
            used.add(i)

            for j, other in enumerate(alerts[i+1:], start=i+1):
                if j in used:
                    continue

                similarity = self._calculate_similarity(alert, other)
                if similarity > self.SIMILARITY_THRESHOLD:
                    cluster.append(other)
                    used.add(j)

            correlated.append(cluster)

        return correlated

    def _calculate_similarity(self, alert1: Alert, alert2: Alert) -> float:
        """
        Calculate similarity between two alerts.

        Factors:
        - Same metric type (0.5 weight)
        - Similar values (0.3 weight)
        - Same source (0.2 weight)
        """
        score = 0.0

        # Metric similarity
        if alert1.metric == alert2.metric:
            score += 0.5

        # Value similarity (normalized)
        if alert1.threshold > 0 and alert2.threshold > 0:
            ratio1 = alert1.value / alert1.threshold
            ratio2 = alert2.value / alert2.threshold
            value_diff = min(abs(ratio1 - ratio2), 1.0)
            value_sim = 1.0 - value_diff
            score += value_sim * 0.3

        # Source similarity
        if alert1.source == alert2.source:
            score += 0.2
        elif self._is_related_host(alert1.source, alert2.source):
            score += 0.1

        return score

    def _is_related_host(self, host1: str, host2: str) -> bool:
        """Check if two hosts are likely related (e.g., same service)."""
        # Simple heuristic: same prefix or in same service group
        parts1 = host1.split('-')
        parts2 = host2.split('-')

        if len(parts1) > 1 and len(parts2) > 1:
            return parts1[0] == parts2[0]  # Same service prefix

        return False

    def _create_incident(self, alerts: List[Alert]) -> CorrelatedIncident:
        """Create an incident from correlated alerts."""
        # Use earliest timestamp
        sorted_alerts = sorted(alerts, key=lambda a: a.timestamp)

        # Determine severity (highest from group)
        severity_order = {'critical': 3, 'warning': 2, 'info': 1}
        severity = max(
            alerts,
            key=lambda a: severity_order.get(a.severity, 0)
        ).severity

        # Calculate correlation score
        correlation_score = self._calculate_group_score(alerts)

        incident_id = f"inc-{int(sorted_alerts[0].timestamp)}-{len(alerts)}"

        return CorrelatedIncident(
            incident_id=incident_id,
            severity=severity,
            created_at=sorted_alerts[0].timestamp,
            alerts=alerts,
            root_cause=None,
            correlation_score=correlation_score,
            suggested_action=""
        )

    def _calculate_group_score(self, alerts: List[Alert]) -> float:
        """Calculate how well alerts are correlated (0.0-1.0)."""
        if len(alerts) <= 1:
            return 1.0

        # Calculate average pairwise similarity
        similarities = []
        for i, alert1 in enumerate(alerts):
            for alert2 in alerts[i+1:]:
                similarities.append(self._calculate_similarity(alert1, alert2))

        if not similarities:
            return 0.0

        return sum(similarities) / len(similarities)

    def _analyze_root_cause(self, incident: CorrelatedIncident) -> None:
        """
        Analyze root cause patterns for incident.

        Uses heuristics:
        - If all alerts on same host, likely host issue
        - If same metric across hosts, likely resource constraint
        - If cascading pattern, identify primary alert
        """
        alerts = incident.alerts

        # Check host concentration
        hosts = set(a.source for a in alerts)
        if len(hosts) == 1:
            incident.root_cause = f"Host issue on {hosts.pop()}"
            incident.suggested_action = f"Investigate host health"
            return

        # Check metric concentration
        metrics = {}
        for alert in alerts:
            metrics[alert.metric] = metrics.get(alert.metric, 0) + 1

        dominant_metric = max(metrics.items(), key=lambda x: x[1])[0]
        if metrics[dominant_metric] >= len(alerts) * 0.7:
            incident.root_cause = f"Resource constraint: {dominant_metric}"
            incident.suggested_action = f"Scale {dominant_metric} capacity"
            return

        # Cascading failure pattern (timestamp spread)
        sorted_alerts = sorted(alerts, key=lambda a: a.timestamp)
        time_spread = sorted_alerts[-1].timestamp - sorted_alerts[0].timestamp

        if time_spread > 0 and len(alerts) > 2:
            incident.root_cause = "Cascading failure pattern detected"
            incident.suggested_action = f"Address primary issue in {sorted_alerts[0].message}"
        else:
            incident.root_cause = f"Multiple correlated issues ({len(alerts)} alerts)"
            incident.suggested_action = "Manual investigation required"

    def get_incidents(self) -> List[CorrelatedIncident]:
        """Get all incidents."""
        return self.incidents

    def get_statistics(self) -> Dict:
        """Get correlation statistics."""
        if not self.incidents:
            return {
                'total_incidents': 0,
                'avg_correlation_score': 0,
                'critical_count': 0
            }

        scores = [i.correlation_score for i in self.incidents]
        critical = sum(1 for i in self.incidents if i.severity == 'critical')

        return {
            'total_incidents': len(self.incidents),
            'total_alerts': sum(len(i.alerts) for i in self.incidents),
            'avg_alerts_per_incident': sum(len(i.alerts) for i in self.incidents) / len(self.incidents),
            'avg_correlation_score': sum(scores) / len(scores),
            'critical_count': critical,
            'noise_reduction': f"{(1 - sum(len(i.alerts) for i in self.incidents) / sum(1 for i in self.incidents)) * 100:.1f}%"
        }


def create_sample_alerts() -> List[Alert]:
    """Create sample alerts for demonstration."""
    now = time.time()

    return [
        Alert(
            id="alert-1",
            timestamp=now,
            alert_type="threshold",
            severity="critical",
            source="api-server-1",
            metric="cpu_usage",
            value=95.0,
            threshold=80.0,
            message="CPU usage critical on api-server-1"
        ),
        Alert(
            id="alert-2",
            timestamp=now + 10,
            alert_type="threshold",
            severity="critical",
            source="api-server-2",
            metric="cpu_usage",
            value=92.0,
            threshold=80.0,
            message="CPU usage critical on api-server-2"
        ),
        Alert(
            id="alert-3",
            timestamp=now + 15,
            alert_type="threshold",
            severity="warning",
            source="api-server-1",
            metric="memory_usage",
            value=85.0,
            threshold=75.0,
            message="Memory usage high on api-server-1"
        ),
        Alert(
            id="alert-4",
            timestamp=now + 20,
            alert_type="service",
            severity="critical",
            source="db-server",
            metric="connection_pool",
            value=100.0,
            threshold=80.0,
            message="DB connection pool exhausted"
        ),
        Alert(
            id="alert-5",
            timestamp=now + 120,  # Outside time window
            alert_type="threshold",
            severity="info",
            source="cache-server",
            metric="eviction_rate",
            value=50.0,
            threshold=40.0,
            message="Cache eviction rate elevated"
        ),
    ]


def main():
    """Demonstrate alert correlation."""
    print("=" * 70)
    print("Alert Correlator Demo")
    print("=" * 70)

    correlator = AlertCorrelator()
    alerts = create_sample_alerts()

    print(f"\nIngesting {len(alerts)} raw alerts...")
    for alert in alerts:
        correlator.ingest_alert(alert)

    print("Correlating alerts...")
    incidents = correlator.correlate()

    print(f"\nGenerated {len(incidents)} incidents from {len(alerts)} alerts:")
    print("-" * 70)

    for incident in incidents:
        print(f"\nIncident: {incident.incident_id}")
        print(f"  Severity: {incident.severity}")
        print(f"  Alert count: {len(incident.alerts)}")
        print(f"  Correlation score: {incident.correlation_score:.2f}")
        print(f"  Root cause: {incident.root_cause}")
        print(f"  Suggested action: {incident.suggested_action}")
        print(f"  Alerts:")
        for alert in incident.alerts:
            print(f"    - {alert.alert_type}: {alert.message}")

    stats = correlator.get_statistics()
    print(f"\n" + "-" * 70)
    print("Statistics:")
    print(f"  Total incidents: {stats['total_incidents']}")
    print(f"  Total alerts: {stats['total_alerts']}")
    print(f"  Avg alerts/incident: {stats['avg_alerts_per_incident']:.1f}")
    print(f"  Avg correlation score: {stats['avg_correlation_score']:.2f}")
    print(f"  Critical incidents: {stats['critical_count']}")
    print(f"  Noise reduction: {stats['noise_reduction']}")


if __name__ == "__main__":
    main()
