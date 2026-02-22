#!/usr/bin/env python3
"""
AI Guardrails Framework for Agent Safety.

Implements safeguards for AI agent actions:
- Action allowlists: Only approved actions can execute
- Confidence thresholds: High confidence required for risky actions
- Human approval gates: Critical actions require human review
- Audit logging: Complete audit trail of all actions

This framework ensures AI agents operate safely within defined boundaries.
"""

import json
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Set, Optional, Tuple, Callable
from enum import Enum


class ActionSeverity(Enum):
    """Action severity levels."""
    READONLY = "readonly"  # Read-only operations
    LOW = "low"  # Low-risk changes
    MEDIUM = "medium"  # Moderate changes
    HIGH = "high"  # Significant changes
    CRITICAL = "critical"  # System-critical or destructive


class ApprovalStatus(Enum):
    """Approval status of an action."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    AUTO_APPROVED = "auto_approved"


@dataclass
class GuardedAction:
    """Represents an action subject to guardrails."""
    action_id: str
    agent_id: str
    action_type: str
    target: str
    confidence: float
    severity: ActionSeverity
    parameters: Dict
    timestamp: float
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    approval_request_id: Optional[str] = None
    executed: bool = False
    result: Optional[Dict] = None
    error: Optional[str] = None


@dataclass
class ApprovalRequest:
    """Request for human approval."""
    request_id: str
    action_id: str
    agent_id: str
    action_description: str
    severity: ActionSeverity
    reason: str
    created_at: float
    approved_at: Optional[float] = None
    approved_by: Optional[str] = None
    comments: Optional[str] = None


class ActionAllowlist:
    """
    Defines which actions agents are allowed to perform.
    
    Actions are organized by severity level and agent role.
    """
    
    def __init__(self):
        """Initialize allowlist."""
        self.allowed_actions: Dict[str, Set[str]] = {
            ActionSeverity.READONLY.value: set(),
            ActionSeverity.LOW.value: set(),
            ActionSeverity.MEDIUM.value: set(),
            ActionSeverity.HIGH.value: set(),
            ActionSeverity.CRITICAL.value: set(),
        }
        self.agent_capabilities: Dict[str, Set[str]] = {}
        self._setup_defaults()
    
    def _setup_defaults(self):
        """Setup default allowed actions."""
        # Read-only actions
        self.allowed_actions[ActionSeverity.READONLY.value] = {
            'get_service_status',
            'list_services',
            'get_logs',
            'get_metrics',
            'check_health',
            'list_alerts',
            'describe_incident',
        }
        
        # Low risk
        self.allowed_actions[ActionSeverity.LOW.value] = {
            'acknowledge_alert',
            'create_dashboard',
            'update_monitoring_config',
            'send_notification',
        }
        
        # Medium risk
        self.allowed_actions[ActionSeverity.MEDIUM.value] = {
            'scale_service',
            'update_config',
            'clear_cache',
            'restart_service',
        }
        
        # High risk
        self.allowed_actions[ActionSeverity.HIGH.value] = {
            'deploy_version',
            'promote_to_production',
            'database_migration',
            'backup_data',
        }
        
        # Critical (always requires approval)
        self.allowed_actions[ActionSeverity.CRITICAL.value] = {
            'delete_data',
            'destroy_infrastructure',
            'modify_security_policy',
            'disable_monitoring',
        }
        
        # Setup agent capabilities
        self.agent_capabilities['triage_agent'] = {
            'get_service_status', 'list_services', 'get_logs', 'get_metrics',
            'acknowledge_alert', 'send_notification'
        }
        
        self.agent_capabilities['diagnosis_agent'] = {
            'get_logs', 'get_metrics', 'check_health', 'list_alerts',
            'create_dashboard', 'update_monitoring_config'
        }
        
        self.agent_capabilities['remediation_agent'] = {
            'acknowledge_alert', 'scale_service', 'restart_service',
            'clear_cache', 'send_notification'
        }
    
    def is_action_allowed(self, agent_id: str, action_type: str, 
                         severity: ActionSeverity) -> bool:
        """
        Check if action is allowed for agent.
        
        Args:
            agent_id: ID of agent attempting action
            action_type: Type of action
            severity: Action severity level
            
        Returns:
            True if action is allowed
        """
        # Check if action is in severity category
        if action_type not in self.allowed_actions[severity.value]:
            return False
        
        # Check agent capabilities
        if agent_id in self.agent_capabilities:
            return action_type in self.agent_capabilities[agent_id]
        
        # Unknown agent not allowed
        return False
    
    def get_required_approval(self, severity: ActionSeverity) -> bool:
        """Check if action of given severity requires approval."""
        return severity in {
            ActionSeverity.MEDIUM,
            ActionSeverity.HIGH,
            ActionSeverity.CRITICAL
        }


class ConfidenceValidator:
    """
    Validates action confidence levels.
    
    Higher severity actions require higher confidence.
    """
    
    # Minimum confidence thresholds by severity
    MIN_THRESHOLDS = {
        ActionSeverity.READONLY: 0.0,  # No threshold
        ActionSeverity.LOW: 0.6,
        ActionSeverity.MEDIUM: 0.75,
        ActionSeverity.HIGH: 0.85,
        ActionSeverity.CRITICAL: 0.95,
    }
    
    @staticmethod
    def is_confident_enough(confidence: float, 
                           severity: ActionSeverity) -> bool:
        """
        Check if confidence is sufficient for action.
        
        Args:
            confidence: Agent's confidence (0.0-1.0)
            severity: Action severity
            
        Returns:
            True if confidence meets threshold
        """
        threshold = ConfidenceValidator.MIN_THRESHOLDS.get(severity, 0.9)
        return confidence >= threshold
    
    @staticmethod
    def get_reason_for_rejection(confidence: float,
                                severity: ActionSeverity) -> Optional[str]:
        """Get reason if action would be rejected."""
        threshold = ConfidenceValidator.MIN_THRESHOLDS.get(severity, 0.9)
        if confidence < threshold:
            return f"Confidence {confidence:.1%} below threshold {threshold:.1%} for {severity.value} action"
        return None


class ApprovalManager:
    """
    Manages approval requests and decisions.
    """
    
    def __init__(self):
        """Initialize approval manager."""
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.completed_requests: List[ApprovalRequest] = []
        self.auto_approved_actions: Set[str] = set()
    
    def create_approval_request(self, action: GuardedAction,
                               reason: str = "") -> ApprovalRequest:
        """
        Create approval request for action.
        
        Args:
            action: GuardedAction requiring approval
            reason: Reason for action
            
        Returns:
            ApprovalRequest
        """
        request_id = f"approval-{int(time.time())}"
        
        request = ApprovalRequest(
            request_id=request_id,
            action_id=action.action_id,
            agent_id=action.agent_id,
            action_description=f"{action.action_type} on {action.target}",
            severity=action.severity,
            reason=reason or f"Agent {action.agent_id} requested {action.action_type}",
            created_at=time.time()
        )
        
        self.pending_requests[request_id] = request
        action.approval_request_id = request_id
        return request
    
    def approve_action(self, request_id: str, approved_by: str,
                      comments: str = "") -> bool:
        """
        Approve an action request.
        
        Args:
            request_id: ID of approval request
            approved_by: Who approved it (username)
            comments: Optional comments
            
        Returns:
            True if approved
        """
        if request_id not in self.pending_requests:
            return False
        
        request = self.pending_requests.pop(request_id)
        request.approved_at = time.time()
        request.approved_by = approved_by
        request.comments = comments
        
        self.completed_requests.append(request)
        return True
    
    def reject_action(self, request_id: str, approved_by: str,
                     comments: str = "") -> bool:
        """
        Reject an action request.
        
        Args:
            request_id: ID of approval request
            approved_by: Who rejected it
            comments: Optional comments
            
        Returns:
            True if rejected
        """
        if request_id not in self.pending_requests:
            return False
        
        request = self.pending_requests.pop(request_id)
        request.approved_at = time.time()
        request.approved_by = approved_by
        request.comments = f"REJECTED: {comments}"
        
        self.completed_requests.append(request)
        return False
    
    def get_pending_requests(self, agent_id: Optional[str] = None) -> List[ApprovalRequest]:
        """Get pending approval requests."""
        requests = list(self.pending_requests.values())
        
        if agent_id:
            requests = [r for r in requests if r.agent_id == agent_id]
        
        return requests


class AuditLogger:
    """
    Logs all action attempts and results.
    
    Maintains audit trail for compliance and debugging.
    """
    
    def __init__(self):
        """Initialize audit logger."""
        self.audit_log: List[Dict] = []
    
    def log_action(self, action: GuardedAction, 
                  event_type: str,
                  details: Optional[Dict] = None) -> None:
        """
        Log an action event.
        
        Args:
            action: GuardedAction
            event_type: Type of event (created, approved, rejected, executed, etc)
            details: Additional details
        """
        entry = {
            'timestamp': time.time(),
            'action_id': action.action_id,
            'agent_id': action.agent_id,
            'action_type': action.action_type,
            'target': action.target,
            'event_type': event_type,
            'severity': action.severity.value,
            'confidence': action.confidence,
            'details': details or {}
        }
        
        self.audit_log.append(entry)
    
    def get_audit_trail(self, action_id: Optional[str] = None) -> List[Dict]:
        """Get audit trail for action or all actions."""
        if action_id:
            return [e for e in self.audit_log if e['action_id'] == action_id]
        return self.audit_log


class GuardrailsFramework:
    """
    Main framework combining all guardrails.
    
    Validates, approves, and executes actions safely.
    """
    
    def __init__(self):
        """Initialize framework."""
        self.allowlist = ActionAllowlist()
        self.approval_manager = ApprovalManager()
        self.audit_logger = AuditLogger()
        self.actions: Dict[str, GuardedAction] = {}
    
    def validate_action(self, agent_id: str, action_type: str, target: str,
                       confidence: float, 
                       severity: ActionSeverity,
                       parameters: Optional[Dict] = None) -> GuardedAction:
        """
        Validate and create a guarded action.
        
        Args:
            agent_id: ID of agent
            action_type: Type of action
            target: Target (service/component)
            confidence: Agent's confidence (0.0-1.0)
            severity: Action severity
            parameters: Action parameters
            
        Returns:
            GuardedAction object
        """
        action_id = f"act-{int(time.time())}"
        
        action = GuardedAction(
            action_id=action_id,
            agent_id=agent_id,
            action_type=action_type,
            target=target,
            confidence=confidence,
            severity=severity,
            parameters=parameters or {},
            timestamp=time.time()
        )
        
        self.audit_logger.log_action(action, 'created')
        self.actions[action_id] = action
        
        return action
    
    def is_safe(self, action: GuardedAction) -> Tuple[bool, List[str]]:
        """
        Check if action is safe to execute.
        
        Args:
            action: GuardedAction to validate
            
        Returns:
            Tuple of (is_safe, list of violations)
        """
        violations = []
        
        # Check allowlist
        if not self.allowlist.is_action_allowed(action.agent_id, 
                                                action.action_type,
                                                action.severity):
            violations.append(
                f"Action {action.action_type} not in allowlist for {action.agent_id}"
            )
        
        # Check confidence
        if not ConfidenceValidator.is_confident_enough(action.confidence, action.severity):
            reason = ConfidenceValidator.get_reason_for_rejection(action.confidence, action.severity)
            violations.append(reason)
        
        is_safe = len(violations) == 0
        return is_safe, violations
    
    def request_approval_if_needed(self, action: GuardedAction) -> Optional[ApprovalRequest]:
        """
        Request approval if action requires it.
        
        Args:
            action: GuardedAction
            
        Returns:
            ApprovalRequest if approval needed, None otherwise
        """
        if self.allowlist.get_required_approval(action.severity):
            request = self.approval_manager.create_approval_request(
                action,
                reason=f"Approval required for {action.severity.value} action"
            )
            self.audit_logger.log_action(action, 'approval_requested', 
                                        {'request_id': request.request_id})
            return request
        
        # Auto-approve low-risk actions
        action.approval_status = ApprovalStatus.AUTO_APPROVED
        self.audit_logger.log_action(action, 'auto_approved')
        return None
    
    def execute_action(self, action: GuardedAction) -> bool:
        """
        Execute action if approved.
        
        Args:
            action: GuardedAction to execute
            
        Returns:
            True if executed successfully
        """
        if action.approval_status == ApprovalStatus.PENDING:
            action.error = "Action requires approval"
            self.audit_logger.log_action(action, 'execution_blocked',
                                        {'error': 'pending_approval'})
            return False
        
        if action.approval_status == ApprovalStatus.REJECTED:
            action.error = "Action was rejected"
            self.audit_logger.log_action(action, 'execution_blocked',
                                        {'error': 'rejected'})
            return False
        
        # Simulate execution
        action.executed = True
        action.result = {
            'status': 'success',
            'message': f'Successfully executed {action.action_type} on {action.target}'
        }
        
        self.audit_logger.log_action(action, 'executed', action.result)
        return True
    
    def get_statistics(self) -> Dict:
        """Get guardrails statistics."""
        total = len(self.actions)
        auto_approved = sum(1 for a in self.actions.values() 
                           if a.approval_status == ApprovalStatus.AUTO_APPROVED)
        manual_approved = sum(1 for a in self.actions.values()
                             if a.approval_status == ApprovalStatus.APPROVED)
        rejected = sum(1 for a in self.actions.values()
                      if a.approval_status == ApprovalStatus.REJECTED)
        
        return {
            'total_actions': total,
            'auto_approved': auto_approved,
            'manual_approved': manual_approved,
            'rejected': rejected,
            'pending_approvals': len(self.approval_manager.pending_requests),
            'audit_log_entries': len(self.audit_logger.audit_log)
        }


def main():
    """Demonstrate guardrails framework."""
    print("=" * 70)
    print("AI Guardrails Framework Demo")
    print("=" * 70)
    
    framework = GuardrailsFramework()
    
    # Test cases
    test_actions = [
        # Low confidence, read-only (should auto-approve)
        ('diagnosis_agent', 'get_metrics', 'api-service', 0.5, ActionSeverity.READONLY),
        
        # High confidence, low-risk (should auto-approve)
        ('triage_agent', 'acknowledge_alert', 'alert-123', 0.8, ActionSeverity.LOW),
        
        # Medium confidence, medium-risk (requires approval)
        ('remediation_agent', 'scale_service', 'api-service', 0.7, ActionSeverity.MEDIUM),
        
        # High confidence, high-risk (requires approval)
        ('remediation_agent', 'deploy_version', 'api-service', 0.9, ActionSeverity.HIGH),
        
        # Low confidence, critical (should be rejected)
        ('remediation_agent', 'delete_data', 'database', 0.5, ActionSeverity.CRITICAL),
    ]
    
    print("\nTesting guardrails with sample actions:\n")
    print("-" * 70)
    
    for i, (agent_id, action_type, target, confidence, severity) in enumerate(test_actions, 1):
        print(f"\nTest {i}: {action_type} on {target}")
        print(f"  Agent: {agent_id}, Confidence: {confidence:.1%}, Severity: {severity.value}")
        
        # Create action
        action = framework.validate_action(
            agent_id=agent_id,
            action_type=action_type,
            target=target,
            confidence=confidence,
            severity=severity
        )
        
        # Check safety
        is_safe, violations = framework.is_safe(action)
        print(f"  Safety: {'PASS' if is_safe else 'FAIL'}")
        
        if violations:
            for v in violations:
                print(f"    - {v}")
        
        # Request approval if needed
        approval_req = framework.request_approval_if_needed(action)
        
        if approval_req:
            print(f"  Approval: REQUIRED ({approval_req.request_id})")
            # Simulate approval
            framework.approval_manager.approve_action(
                approval_req.request_id,
                approved_by="on_call_engineer"
            )
            action.approval_status = ApprovalStatus.APPROVED
            print(f"  Approval: GRANTED")
        else:
            print(f"  Approval: AUTO-APPROVED")
        
        # Execute
        success = framework.execute_action(action)
        print(f"  Execution: {'SUCCESS' if success else 'FAILED'}")
    
    # Statistics
    stats = framework.get_statistics()
    print("\n" + "-" * 70)
    print("Framework Statistics:")
    print(f"  Total actions: {stats['total_actions']}")
    print(f"  Auto-approved: {stats['auto_approved']}")
    print(f"  Manual approved: {stats['manual_approved']}")
    print(f"  Rejected: {stats['rejected']}")
    print(f"  Pending approvals: {stats['pending_approvals']}")
    print(f"  Audit log entries: {stats['audit_log_entries']}")


if __name__ == "__main__":
    main()
