"""
Incident Triage Agent: Multi-signal incident analysis and root cause detection.

This module implements an intelligent incident triage agent that:
1. Correlates signals from logs, metrics, and deployments
2. Detects incident patterns using ML models
3. Generates root cause hypotheses using LLM
4. Recommends remediation runbook steps
5. Provides human-readable incident summaries
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib

try:
    from langchain.chat_models import ChatOpenAI
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
except ImportError:
    ChatOpenAI = None


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class SignalData:
    """Represents a single observable signal."""
    signal_type: str  # "error_rate", "latency", "deployment", "log_entry"
    severity: str     # "low", "medium", "high", "critical"
    value: float
    timestamp: str
    source: str       # e.g., "prometheus", "cloudtrail", "application_logs"
    details: Dict


@dataclass
class IncidentAnalysis:
    """Complete incident analysis result."""
    incident_id: str
    title: str
    severity: str
    root_cause: str
    confidence_score: float
    affected_components: List[str]
    timeline: List[str]
    related_signals: List[SignalData]
    runbook_steps: List[str]
    estimated_impact: Dict
    human_override: bool = False


class IncidentTriageAgent:
    """
    Intelligent incident triage and root cause analysis agent.
    
    Correlates multiple signal types to rapidly identify root causes
    and recommend remediation steps.
    """
    
    def __init__(self, mock_mode: bool = False):
        """
        Initialize incident triage agent.
        
        Args:
            mock_mode: If True, use mock data instead of real systems
        """
        self.mock_mode = mock_mode or not os.getenv("OPENAI_API_KEY")
        self.llm = self._init_llm()
        self.incident_patterns = self._load_incident_patterns()
        self.runbook_index = self._load_runbooks()
        
    def _init_llm(self):
        """Initialize language model."""
        if not self.mock_mode:
            try:
                return ChatOpenAI(
                    model="gpt-4-turbo-preview",
                    temperature=0.3,  # Lower temp for consistency
                    max_tokens=1000
                )
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}. Using mock mode.")
                return MockLLM()
        return MockLLM()
    
    def _load_incident_patterns(self) -> Dict:
        """Load known incident patterns for correlation."""
        return {
            "deployment_error": {
                "signals": ["deployment", "error_rate_spike"],
                "components": ["deployment_service"],
                "resolution": "Rollback recent deployment"
            },
            "database_connection_pool_exhaustion": {
                "signals": ["connection_timeout", "latency_spike"],
                "components": ["database", "connection_pool"],
                "resolution": "Increase connection pool size or restart service"
            },
            "memory_leak": {
                "signals": ["memory_usage_spike", "service_restart"],
                "components": ["application"],
                "resolution": "Review recent code changes, enable memory profiling"
            },
            "cascading_failure": {
                "signals": ["upstream_failure", "downstream_timeout", "queue_backlog"],
                "components": ["multiple"],
                "resolution": "Circuit breaker, rate limiting, graceful degradation"
            },
            "traffic_spike": {
                "signals": ["request_rate_spike", "latency_increase"],
                "components": ["api_gateway", "application"],
                "resolution": "Auto-scaling, caching, rate limiting"
            },
            "dns_failure": {
                "signals": ["connection_refused", "name_resolution_failed"],
                "components": ["network", "dns"],
                "resolution": "Check DNS server status, verify configuration"
            }
        }
    
    def _load_runbooks(self) -> Dict:
        """Load runbook templates for common issues."""
        return {
            "deployment_service": {
                "title": "Deployment Service Incident",
                "steps": [
                    "Check deployment service logs: kubectl logs -n platform deployment-service",
                    "Verify recent deployments: helm list -a",
                    "Review application errors: kubectl logs -n apps --tail=100 -f app",
                    "Check resource usage: kubectl top nodes && kubectl top pods",
                    "Rollback if necessary: helm rollback <release> <revision>"
                ]
            },
            "database": {
                "title": "Database Connectivity Issue",
                "steps": [
                    "Check database pod status: kubectl get pods -n data",
                    "Review connection pool metrics: curl metrics:9090/query?query=pg_conn_*",
                    "Check database logs: kubectl logs -n data db-primary",
                    "Verify network connectivity: kubectl exec -it <pod> -- psql -c 'SELECT 1'",
                    "Increase pool size if needed: kubectl patch deploy db-proxy -p '{}'",
                    "Monitor recovery: watch 'kubectl get pods -n data'"
                ]
            },
            "api_gateway": {
                "title": "API Gateway Issue",
                "steps": [
                    "Check gateway status: kubectl get pods -n ingress",
                    "Review recent config changes: git log --oneline -10 config/",
                    "Check rate limiter state: redis-cli INFO",
                    "Review access logs: kubectl logs -n ingress api-gateway",
                    "Verify backend services: kubectl get svc --all-namespaces",
                    "Test connectivity: curl -v http://service:port/health"
                ]
            },
            "application": {
                "title": "Application Issue",
                "steps": [
                    "Gather error logs: kubectl logs -n apps --since=5m --timestamps=true",
                    "Check resource limits: kubectl describe pod <pod> | grep -A5 Limits",
                    "Review recent deployments: kubectl rollout history deploy/<name>",
                    "Check dependencies: kubectl get svc -n apps",
                    "Monitor system metrics: kubectl top pods -n apps",
                    "Execute health checks: kubectl exec <pod> -- /bin/health-check.sh"
                ]
            }
        }
    
    def triage(self, incident_data: Dict) -> IncidentAnalysis:
        """
        Perform incident triage and analysis.
        
        Args:
            incident_data: Dict with 'alert', 'severity', 'timestamp', 'signals'
        
        Returns:
            IncidentAnalysis with root cause and recommendations
        """
        incident_id = self._generate_incident_id(incident_data)
        
        # Parse incident data
        signals = self._collect_signals(incident_data)
        
        # Correlate signals
        correlated_signals, patterns_matched = self._correlate_signals(signals)
        
        # Identify affected components
        affected_components = self._identify_components(signals)
        
        # Generate root cause analysis
        root_cause, confidence = self._analyze_root_cause(
            signals, patterns_matched, incident_data
        )
        
        # Build timeline
        timeline = self._build_timeline(signals)
        
        # Recommend runbook steps
        runbook_steps = self._get_runbook_steps(affected_components, root_cause)
        
        # Estimate impact
        impact = self._estimate_impact(signals, incident_data)
        
        analysis = IncidentAnalysis(
            incident_id=incident_id,
            title=incident_data.get("alert", "Unknown Incident"),
            severity=incident_data.get("severity", "medium"),
            root_cause=root_cause,
            confidence_score=confidence,
            affected_components=affected_components,
            timeline=timeline,
            related_signals=correlated_signals,
            runbook_steps=runbook_steps,
            estimated_impact=impact
        )
        
        logger.info(f"Incident {incident_id} triaged: {root_cause} (confidence: {confidence})")
        return analysis
    
    def _generate_incident_id(self, incident_data: Dict) -> str:
        """Generate unique incident ID."""
        content = f"{incident_data.get('timestamp', '')}{incident_data.get('alert', '')}"
        hash_val = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"INC-{hash_val.upper()}"
    
    def _collect_signals(self, incident_data: Dict) -> List[SignalData]:
        """Collect and parse signals from incident data."""
        signals = []
        
        # Parse provided signals
        for signal_dict in incident_data.get("signals", []):
            signals.append(SignalData(
                signal_type=signal_dict.get("type", "unknown"),
                severity=signal_dict.get("severity", "medium"),
                value=signal_dict.get("value", 0.0),
                timestamp=signal_dict.get("timestamp", datetime.now().isoformat()),
                source=signal_dict.get("source", "unknown"),
                details=signal_dict.get("details", {})
            ))
        
        # If no signals provided, generate from alert
        if not signals and incident_data.get("alert"):
            signals.append(SignalData(
                signal_type="alert",
                severity=incident_data.get("severity", "medium"),
                value=1.0,
                timestamp=incident_data.get("timestamp", datetime.now().isoformat()),
                source="alert_system",
                details={"alert_message": incident_data.get("alert")}
            ))
        
        return signals
    
    def _correlate_signals(self, signals: List[SignalData]) -> Tuple[List[SignalData], List[str]]:
        """
        Correlate signals to identify patterns.
        
        Returns:
            Tuple of (correlated_signals, matched_pattern_names)
        """
        patterns_matched = []
        
        # Check against known patterns
        signal_types = {s.signal_type for s in signals}
        for pattern_name, pattern in self.incident_patterns.items():
            pattern_signals = set(pattern["signals"])
            if pattern_signals.issubset(signal_types):
                patterns_matched.append(pattern_name)
        
        # Time-based correlation (signals within 5 minutes)
        if signals:
            signals_sorted = sorted(signals, key=lambda s: s.timestamp)
            time_correlations = []
            
            for i, sig in enumerate(signals_sorted):
                sig_time = datetime.fromisoformat(sig.timestamp)
                related = [sig]
                
                for other_sig in signals_sorted[i+1:]:
                    other_time = datetime.fromisoformat(other_sig.timestamp)
                    time_diff = abs((other_time - sig_time).total_seconds())
                    if time_diff < 300:  # 5 minutes
                        related.append(other_sig)
                
                if len(related) > 1:
                    time_correlations.extend(related)
        
        return signals, patterns_matched
    
    def _identify_components(self, signals: List[SignalData]) -> List[str]:
        """Identify affected components from signals."""
        components = set()
        
        for signal in signals:
            source = signal.source.lower()
            
            if any(x in source for x in ["db", "database", "postgres", "mysql"]):
                components.add("database")
            if any(x in source for x in ["api", "gateway", "http", "endpoint"]):
                components.add("api_gateway")
            if any(x in source for x in ["deploy", "helm", "kubernetes"]):
                components.add("deployment_service")
            if any(x in source for x in ["app", "service", "application"]):
                components.add("application")
            if any(x in source for x in ["network", "dns", "tcp", "socket"]):
                components.add("network")
            if any(x in source for x in ["cache", "redis", "memcached"]):
                components.add("cache")
            if any(x in source for x in ["queue", "kafka", "rabbitmq", "sqs"]):
                components.add("message_queue")
        
        return sorted(list(components))
    
    def _analyze_root_cause(
        self,
        signals: List[SignalData],
        patterns_matched: List[str],
        incident_data: Dict
    ) -> Tuple[str, float]:
        """
        Analyze root cause using LLM and pattern matching.
        
        Returns:
            Tuple of (root_cause_text, confidence_score)
        """
        # Start with pattern-based analysis
        if patterns_matched:
            pattern_name = patterns_matched[0]  # Most likely pattern
            pattern = self.incident_patterns[pattern_name]
            root_cause = pattern["resolution"]
            confidence = 0.85
        else:
            confidence = 0.6
            root_cause = "Unknown - pattern matching found no matches"
        
        # Use LLM for detailed analysis
        if not self.mock_mode and self.llm:
            signal_summary = "\n".join([
                f"- {s.signal_type}: {s.severity} at {s.timestamp}"
                for s in signals[:5]
            ])
            
            prompt = f"""Given these incident signals, what is the root cause?

Signals:
{signal_summary}

Alert: {incident_data.get('alert', 'Unknown')}

Provide a concise root cause and remediation steps."""
            
            try:
                response = self.llm.invoke(prompt)
                if hasattr(response, 'content'):
                    root_cause = response.content
                else:
                    root_cause = str(response)
                confidence = 0.75
            except Exception as e:
                logger.warning(f"LLM analysis failed: {e}")
        
        return root_cause, confidence
    
    def _build_timeline(self, signals: List[SignalData]) -> List[str]:
        """Build incident timeline from signals."""
        timeline = []
        
        signals_sorted = sorted(signals, key=lambda s: s.timestamp)
        
        for signal in signals_sorted:
            time_str = signal.timestamp
            summary = f"{signal.signal_type.upper()}: {signal.details.get('message', signal.severity)}"
            timeline.append(f"{time_str} - {summary}")
        
        return timeline
    
    def _get_runbook_steps(self, components: List[str], root_cause: str) -> List[str]:
        """Get recommended runbook steps for affected components."""
        steps = []
        
        # Add header
        steps.append("INCIDENT REMEDIATION STEPS")
        steps.append("=" * 50)
        steps.append("")
        
        # Add component-specific steps
        for component in components:
            if component in self.runbook_index:
                runbook = self.runbook_index[component]
                steps.append(f"## {runbook['title']}")
                steps.extend(runbook['steps'])
                steps.append("")
        
        # Add generic steps if no specific runbook
        if not components:
            steps.extend([
                "1. Check application logs: kubectl logs -f <pod>",
                "2. Monitor metrics: kubectl top pods",
                "3. Verify service health: curl http://service/health",
                "4. Check recent deployments: kubectl rollout history",
                "5. Escalate to on-call engineer if issue persists"
            ])
        
        return steps
    
    def _estimate_impact(self, signals: List[SignalData], incident_data: Dict) -> Dict:
        """Estimate incident impact on users and services."""
        severity = incident_data.get("severity", "medium")
        severity_multiplier = {
            "low": 0.1,
            "medium": 0.5,
            "high": 0.8,
            "critical": 1.0
        }.get(severity, 0.5)
        
        # Estimate affected users (mock calculation)
        estimated_users = int(1000 * severity_multiplier * len(signals))
        
        # Estimate duration
        duration_minutes = 30 if severity == "critical" else 60
        
        return {
            "estimated_affected_users": estimated_users,
            "estimated_duration_minutes": duration_minutes,
            "estimated_revenue_impact_usd": estimated_users * 0.01 * duration_minutes,
            "severity_level": severity
        }
    
    def batch_triage(self, incidents: List[Dict]) -> List[IncidentAnalysis]:
        """Triage multiple incidents."""
        return [self.triage(incident) for incident in incidents]
    
    def to_slack_message(self, analysis: IncidentAnalysis) -> Dict:
        """Format incident analysis as Slack message."""
        return {
            "text": f"Incident Detected: {analysis.title}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"Incident {analysis.incident_id}: {analysis.title}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity:*\n{analysis.severity.upper()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Root Cause Confidence:*\n{analysis.confidence_score:.0%}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Root Cause:*\n{analysis.root_cause[:100]}..."
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Affected Components:*\n{', '.join(analysis.affected_components)}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Impact:*\n"
                              f"Users: {analysis.estimated_impact.get('estimated_affected_users', 0)}\n"
                              f"Duration: {analysis.estimated_impact.get('estimated_duration_minutes', 0)}m"
                    }
                }
            ]
        }


class MockLLM:
    """Mock LLM for testing without OpenAI."""
    
    def invoke(self, prompt: str) -> str:
        """Return mock response."""
        if "database" in prompt.lower():
            return "Root Cause: Database connection pool exhaustion. Increase pool size or restart service."
        if "deployment" in prompt.lower():
            return "Root Cause: Recent deployment caused regression. Rollback to previous version."
        return "Root Cause: Service degradation detected. Check logs and metrics for details."


if __name__ == "__main__":
    # Example usage
    agent = IncidentTriageAgent()
    
    incident = {
        "alert": "High error rate on payment service",
        "severity": "critical",
        "timestamp": datetime.now().isoformat(),
        "signals": [
            {
                "type": "error_rate_spike",
                "severity": "critical",
                "value": 25.5,
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                "source": "prometheus",
                "details": {"threshold": 5.0, "current": 25.5}
            },
            {
                "type": "deployment",
                "severity": "high",
                "value": 1.0,
                "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat(),
                "source": "kubernetes",
                "details": {"deployment": "payment-service", "revision": 42}
            }
        ]
    }
    
    analysis = agent.triage(incident)
    
    print(f"Incident ID: {analysis.incident_id}")
    print(f"Root Cause: {analysis.root_cause}")
    print(f"Confidence: {analysis.confidence_score:.0%}")
    print(f"Affected Components: {', '.join(analysis.affected_components)}")
    print("\nRunbook Steps:")
    for step in analysis.runbook_steps[:5]:
        print(f"  {step}")
