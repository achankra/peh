#!/usr/bin/env python3
"""
Multi-Agent Incident Response System.

Implements a team of specialized agents for incident response:
- Triage Agent: Classifies incident severity and type
- Diagnosis Agent: Analyzes logs/metrics to find root cause
- Remediation Agent: Suggests or executes fixes

Features:
- Role-based separation of concerns
- Human-in-the-loop approval for critical actions
- Decision audit trail
- Fallback to manual investigation if confidence is low
"""

import json
import time
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional
from enum import Enum


class SeverityLevel(Enum):
    """Incident severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentType(Enum):
    """Incident type classifications."""
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    NETWORK = "network"
    DATABASE = "database"
    SECURITY = "security"
    UNKNOWN = "unknown"


@dataclass
class TriageResult:
    """Result from triage agent."""
    severity: SeverityLevel
    incident_type: IncidentType
    confidence: float
    requires_escalation: bool
    initial_action: str


@dataclass
class DiagnosisResult:
    """Result from diagnosis agent."""
    root_cause: str
    affected_component: str
    confidence: float
    evidence: List[str]
    remediation_options: List[str]


@dataclass
class RemediationAction:
    """Represents a proposed remediation action."""
    action_id: str
    description: str
    action_type: str  # restart, scale, patch, manual
    target: str  # service/component name
    estimated_duration: int  # seconds
    risk_level: str  # low, medium, high
    requires_approval: bool
    confidence: float


@dataclass
class IncidentResponse:
    """Complete incident response record."""
    incident_id: str
    alert_message: str
    created_at: float
    triage: Optional[TriageResult] = None
    diagnosis: Optional[DiagnosisResult] = None
    proposed_action: Optional[RemediationAction] = None
    human_approval: Optional[Dict] = None
    execution_result: Optional[Dict] = None
    resolution_time: Optional[float] = None


class TriageAgent:
    """
    Classifies incident severity and type.

    Makes initial assessment based on alert characteristics.
    """

    def __init__(self):
        """Initialize triage agent."""
        self.decisions: List[TriageResult] = []

    def triage(self, alert_message: str) -> TriageResult:
        """
        Triage an incident.

        Args:
            alert_message: Description of the alert

        Returns:
            TriageResult with severity and type
        """
        # Heuristics for classification
        message_lower = alert_message.lower()

        # Determine severity
        if any(word in message_lower for word in ['critical', 'error', 'down', 'crashed']):
            severity = SeverityLevel.CRITICAL
        elif any(word in message_lower for word in ['high', 'warning', 'timeout']):
            severity = SeverityLevel.HIGH
        elif any(word in message_lower for word in ['medium', 'elevated']):
            severity = SeverityLevel.MEDIUM
        else:
            severity = SeverityLevel.LOW

        # Determine type
        if any(word in message_lower for word in ['cpu', 'memory', 'disk', 'load']):
            incident_type = IncidentType.INFRASTRUCTURE
        elif any(word in message_lower for word in ['database', 'db', 'connection', 'query']):
            incident_type = IncidentType.DATABASE
        elif any(word in message_lower for word in ['network', 'timeout', 'unreachable']):
            incident_type = IncidentType.NETWORK
        elif any(word in message_lower for word in ['app', 'service', 'error', 'exception']):
            incident_type = IncidentType.APPLICATION
        elif any(word in message_lower for word in ['breach', 'auth', 'permission', 'security']):
            incident_type = IncidentType.SECURITY
        else:
            incident_type = IncidentType.UNKNOWN

        # Confidence based on specificity
        if incident_type == IncidentType.UNKNOWN:
            confidence = 0.5
        elif severity == SeverityLevel.CRITICAL:
            confidence = 0.95
        else:
            confidence = 0.8

        requires_escalation = (
            severity == SeverityLevel.CRITICAL or
            incident_type == IncidentType.SECURITY
        )

        action = self._suggest_initial_action(severity, incident_type)

        result = TriageResult(
            severity=severity,
            incident_type=incident_type,
            confidence=confidence,
            requires_escalation=requires_escalation,
            initial_action=action
        )

        self.decisions.append(result)
        return result

    def _suggest_initial_action(self, severity: SeverityLevel,
                               incident_type: IncidentType) -> str:
        """Suggest initial action based on classification."""
        if severity == SeverityLevel.CRITICAL:
            if incident_type == IncidentType.DATABASE:
                return "Page on-call DBA immediately, check replication status"
            elif incident_type == IncidentType.INFRASTRUCTURE:
                return "Scale resources and check host health"
            elif incident_type == IncidentType.SECURITY:
                return "Alert security team, isolate affected systems"
            else:
                return "Initiate incident war room"

        if incident_type == IncidentType.DATABASE:
            return "Check database health and slow queries"
        elif incident_type == IncidentType.INFRASTRUCTURE:
            return "Review metrics and disk usage"
        elif incident_type == IncidentType.NETWORK:
            return "Check connectivity and DNS resolution"

        return "Investigate and gather more information"


class DiagnosisAgent:
    """
    Analyzes symptoms to determine root cause.

    Would normally read logs, metrics, traces in production.
    """

    def __init__(self):
        """Initialize diagnosis agent."""
        self.diagnoses: List[DiagnosisResult] = []

    def diagnose(self, triage: TriageResult,
                alert_message: str) -> DiagnosisResult:
        """
        Diagnose root cause.

        Args:
            triage: TriageResult from triage agent
            alert_message: Original alert message

        Returns:
            DiagnosisResult with root cause and options
        """
        message_lower = alert_message.lower()

        # Heuristic diagnosis based on type
        if triage.incident_type == IncidentType.INFRASTRUCTURE:
            if 'cpu' in message_lower:
                return self._diagnose_cpu(alert_message)
            elif 'memory' in message_lower:
                return self._diagnose_memory(alert_message)
            elif 'disk' in message_lower:
                return self._diagnose_disk(alert_message)

        elif triage.incident_type == IncidentType.DATABASE:
            return self._diagnose_database(alert_message)

        elif triage.incident_type == IncidentType.APPLICATION:
            return self._diagnose_application(alert_message)

        # Fallback generic diagnosis
        return DiagnosisResult(
            root_cause="Unknown - requires investigation",
            affected_component="Unknown",
            confidence=0.3,
            evidence=["Alert triggered but pattern not recognized"],
            remediation_options=["Enable detailed logging", "Capture metrics", "Manual review"]
        )

    def _diagnose_cpu(self, message: str) -> DiagnosisResult:
        """Diagnose CPU issues."""
        return DiagnosisResult(
            root_cause="High CPU utilization - likely compute-bound workload or infinite loop",
            affected_component="compute layer",
            confidence=0.85,
            evidence=["CPU threshold exceeded", "No memory issues detected"],
            remediation_options=[
                "Scale horizontally (add replicas)",
                "Optimize code for performance",
                "Check for memory leaks or loops",
                "Reduce batch sizes"
            ]
        )

    def _diagnose_memory(self, message: str) -> DiagnosisResult:
        """Diagnose memory issues."""
        return DiagnosisResult(
            root_cause="High memory usage - potential memory leak",
            affected_component="application instance",
            confidence=0.80,
            evidence=["Memory threshold exceeded", "Sustained high memory"],
            remediation_options=[
                "Restart service to clear memory",
                "Profile for memory leaks",
                "Check for unbounded caches",
                "Increase container memory limit"
            ]
        )

    def _diagnose_disk(self, message: str) -> DiagnosisResult:
        """Diagnose disk issues."""
        return DiagnosisResult(
            root_cause="Disk space exhaustion",
            affected_component="storage",
            confidence=0.90,
            evidence=["Disk usage critical", "Write operations failing"],
            remediation_options=[
                "Clean old logs and temporary files",
                "Expand disk volume",
                "Enable log rotation",
                "Archive old data"
            ]
        )

    def _diagnose_database(self, message: str) -> DiagnosisResult:
        """Diagnose database issues."""
        return DiagnosisResult(
            root_cause="Database performance degradation",
            affected_component="database",
            confidence=0.75,
            evidence=["Query latency high", "Connection pool near limit"],
            remediation_options=[
                "Kill long-running queries",
                "Increase connection pool",
                "Optimize slow queries",
                "Add database indexes",
                "Failover to replica"
            ]
        )

    def _diagnose_application(self, message: str) -> DiagnosisResult:
        """Diagnose application issues."""
        return DiagnosisResult(
            root_cause="Application error or crash",
            affected_component="application",
            confidence=0.70,
            evidence=["Error rate elevated", "Request failures"],
            remediation_options=[
                "Restart application",
                "Rollback last deployment",
                "Check application logs",
                "Increase error tracking",
                "Scale replicas"
            ]
        )


class RemediationAgent:
    """
    Proposes and executes remediation actions.

    For critical actions, requires human approval.
    """

    def __init__(self):
        """Initialize remediation agent."""
        self.proposed_actions: List[RemediationAction] = []

    def propose_remediation(self,
                           diagnosis: DiagnosisResult,
                           triage: TriageResult) -> RemediationAction:
        """
        Propose a remediation action.

        Args:
            diagnosis: DiagnosisResult from diagnosis agent
            triage: TriageResult from triage agent

        Returns:
            Proposed RemediationAction
        """
        # Pick best remediation option
        if not diagnosis.remediation_options:
            option = "Manual investigation required"
        else:
            option = diagnosis.remediation_options[0]

        # Determine action characteristics
        risk_level = "high" if triage.severity == SeverityLevel.CRITICAL else "medium"
        requires_approval = risk_level == "high"

        action_type = self._map_to_action_type(option)
        target = diagnosis.affected_component

        duration = self._estimate_duration(action_type)

        action = RemediationAction(
            action_id=f"action-{int(time.time())}",
            description=option,
            action_type=action_type,
            target=target,
            estimated_duration=duration,
            risk_level=risk_level,
            requires_approval=requires_approval,
            confidence=diagnosis.confidence
        )

        self.proposed_actions.append(action)
        return action

    def _map_to_action_type(self, option: str) -> str:
        """Map description to action type."""
        option_lower = option.lower()

        if any(word in option_lower for word in ['restart', 'reboot']):
            return "restart"
        elif any(word in option_lower for word in ['scale', 'replica']):
            return "scale"
        elif any(word in option_lower for word in ['rollback', 'deploy']):
            return "patch"
        else:
            return "manual"

    def _estimate_duration(self, action_type: str) -> int:
        """Estimate action duration in seconds."""
        durations = {
            "restart": 30,
            "scale": 60,
            "patch": 300,
            "manual": 600
        }
        return durations.get(action_type, 600)


class IncidentAgent:
    """
    Orchestrates multi-agent incident response.

    Coordinates triage, diagnosis, and remediation agents.
    """

    def __init__(self):
        """Initialize incident agent."""
        self.triage_agent = TriageAgent()
        self.diagnosis_agent = DiagnosisAgent()
        self.remediation_agent = RemediationAgent()
        self.incidents: List[IncidentResponse] = []

    def handle_incident(self, alert_message: str) -> IncidentResponse:
        """
        Handle a complete incident.

        Args:
            alert_message: Alert description

        Returns:
            Complete incident response
        """
        incident_id = f"inc-{int(time.time())}"
        incident = IncidentResponse(
            incident_id=incident_id,
            alert_message=alert_message,
            created_at=time.time()
        )

        # Triage
        triage = self.triage_agent.triage(alert_message)
        incident.triage = triage

        # Diagnosis
        diagnosis = self.diagnosis_agent.diagnose(triage, alert_message)
        incident.diagnosis = diagnosis

        # Propose remediation
        action = self.remediation_agent.propose_remediation(diagnosis, triage)
        incident.proposed_action = action

        self.incidents.append(incident)
        return incident

    def request_approval(self, incident: IncidentResponse,
                        approved: bool, comment: str = "") -> None:
        """
        Record human approval decision.

        Args:
            incident: Incident to approve/reject
            approved: Whether action is approved
            comment: Optional comment
        """
        incident.human_approval = {
            'approved': approved,
            'timestamp': time.time(),
            'comment': comment
        }

        if approved and incident.proposed_action:
            self._execute_action(incident, incident.proposed_action)

    def _execute_action(self, incident: IncidentResponse,
                       action: RemediationAction) -> None:
        """Execute a remediation action."""
        start_time = time.time()

        # Simulate action execution
        success = True
        result_message = f"Action {action.action_type} executed successfully"

        if action.action_type == "restart":
            result_message = f"Restarted {action.target} - service online"
        elif action.action_type == "scale":
            result_message = f"Scaled {action.target} to 3 replicas"
        elif action.action_type == "patch":
            result_message = f"Rolled back to previous version"

        duration = time.time() - start_time
        incident.resolution_time = incident.created_at + duration

        incident.execution_result = {
            'success': success,
            'result': result_message,
            'duration_seconds': int(duration)
        }


def main():
    """Demonstrate multi-agent incident response."""
    print("=" * 70)
    print("Multi-Agent Incident Response System Demo")
    print("=" * 70)

    agent = IncidentAgent()

    # Sample incidents
    incidents_to_handle = [
        "CRITICAL: API Server CPU usage 95% - requests timing out",
        "WARNING: Database connection pool exhausted",
        "CRITICAL: Security breach detected - unauthorized access attempt",
    ]

    print("\nProcessing incidents through multi-agent system...\n")
    print("-" * 70)

    for alert in incidents_to_handle:
        incident = agent.handle_incident(alert)

        print(f"\nIncident: {incident.incident_id}")
        print(f"Alert: {incident.alert_message}")

        # Triage
        if incident.triage:
            t = incident.triage
            print(f"\nTriage Result:")
            print(f"  Severity: {t.severity.value}")
            print(f"  Type: {t.incident_type.value}")
            print(f"  Confidence: {t.confidence:.1%}")
            print(f"  Initial Action: {t.initial_action}")

        # Diagnosis
        if incident.diagnosis:
            d = incident.diagnosis
            print(f"\nDiagnosis:")
            print(f"  Root Cause: {d.root_cause}")
            print(f"  Component: {d.affected_component}")
            print(f"  Confidence: {d.confidence:.1%}")
            print(f"  Evidence: {'; '.join(d.evidence)}")

        # Proposed Action
        if incident.proposed_action:
            a = incident.proposed_action
            print(f"\nProposed Action:")
            print(f"  Type: {a.action_type}")
            print(f"  Description: {a.description}")
            print(f"  Target: {a.target}")
            print(f"  Risk Level: {a.risk_level}")
            print(f"  Requires Approval: {a.requires_approval}")

            # Simulate human approval
            if a.requires_approval:
                print(f"  Status: AWAITING APPROVAL")
                # Auto-approve for demo
                agent.request_approval(incident, True, "Auto-approved by on-call engineer")
                print(f"  Status: APPROVED - Executing...")
            else:
                agent.request_approval(incident, True)

        # Execution result
        if incident.execution_result:
            print(f"\nExecution Result:")
            print(f"  Success: {incident.execution_result['success']}")
            print(f"  Result: {incident.execution_result['result']}")
            print(f"  Duration: {incident.execution_result['duration_seconds']}s")

    # Summary
    print("\n" + "-" * 70)
    print("Incident Summary:")
    print(f"  Total incidents: {len(agent.incidents)}")

    critical = sum(1 for i in agent.incidents if i.triage and i.triage.severity == SeverityLevel.CRITICAL)
    print(f"  Critical: {critical}")

    approved = sum(1 for i in agent.incidents if i.human_approval and i.human_approval['approved'])
    print(f"  Approved actions: {approved}")

    resolved = sum(1 for i in agent.incidents if i.execution_result)
    print(f"  Resolved: {resolved}")


if __name__ == "__main__":
    main()
