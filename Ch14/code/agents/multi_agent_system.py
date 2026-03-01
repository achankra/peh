#!/usr/bin/env python3
"""
Multi-agent system for autonomous Kubernetes operations with human-in-the-loop controls.
Features include investigation, planning, execution agents coordinated by a supervisor,
audit logging, and approval gates for destructive actions.
"""

import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import hashlib

# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(agent_id)s] - %(message)s'
)
logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of actions agents can perform."""
    INVESTIGATION = "investigation"
    PLANNING = "planning"
    EXECUTION = "execution"
    APPROVAL = "approval"


class ActionSeverity(Enum):
    """Severity levels for actions."""
    READ_ONLY = "read_only"
    MODIFICATION = "modification"
    DESTRUCTIVE = "destructive"
    CRITICAL = "critical"


@dataclass
class AuditLog:
    """Audit log entry for tracking all operations."""
    timestamp: str
    agent_id: str
    agent_type: str
    action_type: str
    severity: str
    description: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    status: str
    error_message: Optional[str] = None
    approval_required: bool = False
    approval_status: Optional[str] = None
    approval_user: Optional[str] = None

    def to_json(self) -> str:
        """Convert audit log to JSON string."""
        return json.dumps(asdict(self), indent=2)


class Agent(ABC):
    """Base class for all agents."""

    def __init__(self, agent_type: str):
        self.agent_id = f"{agent_type}-{uuid.uuid4().hex[:8]}"
        self.agent_type = agent_type
        self.logger = logging.getLogger(f"{__name__}.{agent_type}")
        self.logger.extra = {"agent_id": self.agent_id}
        self.audit_logs: List[AuditLog] = []

    def log_action(
        self,
        action_type: str,
        severity: str,
        description: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        status: str,
        error_message: Optional[str] = None,
        approval_required: bool = False
    ) -> AuditLog:
        """Create and log an action."""
        log_entry = AuditLog(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            action_type=action_type,
            severity=severity,
            description=description,
            input_data=input_data,
            output_data=output_data,
            status=status,
            error_message=error_message,
            approval_required=approval_required
        )
        self.audit_logs.append(log_entry)
        self.logger.info(f"{action_type}: {description} - Status: {status}")
        return log_entry

    @abstractmethod
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's task. Must be implemented by subclasses."""
        pass


class InvestigationAgent(Agent):
    """Agent for investigating cluster state and issues."""

    def __init__(self):
        super().__init__("InvestigationAgent")

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Investigate cluster issues."""
        self.logger.info(f"Starting investigation: {task.get('issue_type', 'unknown')}")

        try:
            # Simulate investigation
            investigation_type = task.get("issue_type", "general")

            if investigation_type == "pod_crash_loop":
                findings = self._investigate_pod_crash_loop(task)
            elif investigation_type == "resource_shortage":
                findings = self._investigate_resource_shortage(task)
            elif investigation_type == "network_issue":
                findings = self._investigate_network_issue(task)
            else:
                findings = self._investigate_general(task)

            # Log successful investigation
            self.log_action(
                action_type="investigation",
                severity=ActionSeverity.READ_ONLY.value,
                description=f"Investigated {investigation_type}",
                input_data=task,
                output_data=findings,
                status="success"
            )

            return findings

        except Exception as e:
            error_msg = str(e)
            self.log_action(
                action_type="investigation",
                severity=ActionSeverity.READ_ONLY.value,
                description=f"Investigation failed: {error_msg}",
                input_data=task,
                output_data={},
                status="failed",
                error_message=error_msg
            )
            raise

    def _investigate_pod_crash_loop(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Investigate pod crash loops."""
        namespace = task.get("namespace", "default")
        pod_name = task.get("pod_name", "unknown")

        return {
            "issue_type": "pod_crash_loop",
            "namespace": namespace,
            "pod_name": pod_name,
            "findings": [
                "High restart count detected",
                "OOMKilled status in last restart",
                "Insufficient memory requests"
            ],
            "confidence": 0.95,
            "recommended_action": "Increase memory requests or investigate application logs"
        }

    def _investigate_resource_shortage(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Investigate resource shortage issues."""
        return {
            "issue_type": "resource_shortage",
            "findings": [
                "Node memory utilization at 95%",
                "Multiple pods pending scheduling",
                "Non-essential workloads can be evicted"
            ],
            "confidence": 0.88,
            "recommended_action": "Scale up cluster or evict low-priority workloads"
        }

    def _investigate_network_issue(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Investigate network issues."""
        return {
            "issue_type": "network_issue",
            "findings": [
                "High latency detected between services",
                "Network policy might be blocking traffic",
                "Pod-to-pod connectivity test failing"
            ],
            "confidence": 0.82,
            "recommended_action": "Check network policies and CNI plugin configuration"
        }

    def _investigate_general(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """General investigation."""
        return {
            "issue_type": "general",
            "findings": ["Cluster appears healthy"],
            "confidence": 0.75,
            "recommended_action": "Continue monitoring"
        }


class PlanningAgent(Agent):
    """Agent for planning remediation actions."""

    def __init__(self):
        super().__init__("PlanningAgent")

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create an action plan based on findings."""
        self.logger.info("Creating remediation plan")

        try:
            findings = task.get("findings", {})
            issue_type = findings.get("issue_type", "unknown")

            if issue_type == "pod_crash_loop":
                plan = self._plan_pod_crash_loop_fix(findings)
            elif issue_type == "resource_shortage":
                plan = self._plan_resource_scaling(findings)
            elif issue_type == "network_issue":
                plan = self._plan_network_fix(findings)
            else:
                plan = self._plan_general_monitoring(findings)

            self.log_action(
                action_type="planning",
                severity=ActionSeverity.READ_ONLY.value,
                description=f"Created plan for {issue_type}",
                input_data=task,
                output_data=plan,
                status="success"
            )

            return plan

        except Exception as e:
            error_msg = str(e)
            self.log_action(
                action_type="planning",
                severity=ActionSeverity.READ_ONLY.value,
                description="Planning failed",
                input_data=task,
                output_data={},
                status="failed",
                error_message=error_msg
            )
            raise

    def _plan_pod_crash_loop_fix(self, findings: Dict[str, Any]) -> Dict[str, Any]:
        """Plan fix for pod crash loop."""
        return {
            "plan_id": f"plan-{uuid.uuid4().hex[:8]}",
            "steps": [
                {
                    "step": 1,
                    "action": "update_resource_requests",
                    "description": "Increase memory request from 256Mi to 512Mi",
                    "severity": ActionSeverity.MODIFICATION.value,
                    "requires_approval": True
                },
                {
                    "step": 2,
                    "action": "restart_pod",
                    "description": "Restart pod after resource update",
                    "severity": ActionSeverity.MODIFICATION.value,
                    "requires_approval": False
                }
            ],
            "estimated_time_minutes": 5,
            "rollback_plan": "Revert to previous resource requests if pod still crashes"
        }

    def _plan_resource_scaling(self, findings: Dict[str, Any]) -> Dict[str, Any]:
        """Plan resource scaling."""
        return {
            "plan_id": f"plan-{uuid.uuid4().hex[:8]}",
            "steps": [
                {
                    "step": 1,
                    "action": "scale_cluster",
                    "description": "Add 2 additional nodes to cluster",
                    "severity": ActionSeverity.MODIFICATION.value,
                    "requires_approval": True
                },
                {
                    "step": 2,
                    "action": "wait_for_nodes",
                    "description": "Wait for nodes to be ready (estimated 3-5 minutes)",
                    "severity": ActionSeverity.READ_ONLY.value
                }
            ],
            "estimated_time_minutes": 10,
            "cost_impact": "Additional compute resources will incur cost"
        }

    def _plan_network_fix(self, findings: Dict[str, Any]) -> Dict[str, Any]:
        """Plan network issue fix."""
        return {
            "plan_id": f"plan-{uuid.uuid4().hex[:8]}",
            "steps": [
                {
                    "step": 1,
                    "action": "review_network_policy",
                    "description": "Review and analyze network policies",
                    "severity": ActionSeverity.READ_ONLY.value
                },
                {
                    "step": 2,
                    "action": "update_network_policy",
                    "description": "Update network policy to allow traffic",
                    "severity": ActionSeverity.MODIFICATION.value,
                    "requires_approval": True
                }
            ],
            "estimated_time_minutes": 15,
            "rollback_plan": "Previous network policy can be quickly restored"
        }

    def _plan_general_monitoring(self, findings: Dict[str, Any]) -> Dict[str, Any]:
        """Plan general monitoring."""
        return {
            "plan_id": f"plan-{uuid.uuid4().hex[:8]}",
            "steps": [
                {
                    "step": 1,
                    "action": "continue_monitoring",
                    "description": "Continue monitoring cluster health",
                    "severity": ActionSeverity.READ_ONLY.value
                }
            ],
            "estimated_time_minutes": 0
        }


class ExecutionAgent(Agent):
    """Agent for executing planned remediation actions."""

    def __init__(self):
        super().__init__("ExecutionAgent")

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the action plan."""
        self.logger.info("Executing remediation actions")

        try:
            plan = task.get("plan", {})
            steps = plan.get("steps", [])
            execution_results = []

            for step in steps:
                action = step.get("action", "unknown")
                severity = step.get("severity", ActionSeverity.READ_ONLY.value)

                # Check if approval is required
                if step.get("requires_approval"):
                    self.logger.warning(f"Step {step['step']} requires approval: {action}")
                    self.log_action(
                        action_type="execution",
                        severity=severity,
                        description=f"Waiting for approval: {action}",
                        input_data=step,
                        output_data={},
                        status="waiting_for_approval",
                        approval_required=True
                    )
                    # In real scenario, this would trigger approval workflow
                    execution_results.append({
                        "step": step["step"],
                        "status": "waiting_for_approval",
                        "requires_human_input": True
                    })
                else:
                    # Execute step
                    result = self._execute_step(action, step)
                    execution_results.append(result)

                    self.log_action(
                        action_type="execution",
                        severity=severity,
                        description=f"Executed: {action}",
                        input_data=step,
                        output_data=result,
                        status="completed"
                    )

            return {
                "execution_id": f"exec-{uuid.uuid4().hex[:8]}",
                "plan_id": plan.get("plan_id"),
                "steps_executed": len([r for r in execution_results if r.get("status") == "completed"]),
                "steps_waiting_approval": len([r for r in execution_results if r.get("status") == "waiting_for_approval"]),
                "results": execution_results,
                "timestamp": datetime.utcnow().isoformat() + 'Z'
            }

        except Exception as e:
            error_msg = str(e)
            self.log_action(
                action_type="execution",
                severity=ActionSeverity.CRITICAL.value,
                description="Execution failed",
                input_data=task,
                output_data={},
                status="failed",
                error_message=error_msg
            )
            raise

    def _execute_step(self, action: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step."""
        self.logger.info(f"Executing step: {action}")

        if action == "update_resource_requests":
            return {"action": action, "status": "completed", "changes": "Memory: 256Mi -> 512Mi"}
        elif action == "restart_pod":
            return {"action": action, "status": "completed", "pod_restarted": True}
        elif action == "scale_cluster":
            return {"action": action, "status": "completed", "nodes_added": 2}
        elif action == "wait_for_nodes":
            return {"action": action, "status": "completed", "wait_time_seconds": 180}
        elif action == "review_network_policy":
            return {"action": action, "status": "completed", "policies_reviewed": 5}
        elif action == "update_network_policy":
            return {"action": action, "status": "completed", "policies_updated": 1}
        elif action == "continue_monitoring":
            return {"action": action, "status": "completed", "monitoring_active": True}
        else:
            return {"action": action, "status": "completed", "result": "Action executed"}


class SupervisorAgent(Agent):
    """Supervisor agent that coordinates investigation, planning, and execution agents."""

    def __init__(self):
        super().__init__("SupervisorAgent")
        self.investigation_agent = InvestigationAgent()
        self.planning_agent = PlanningAgent()
        self.execution_agent = ExecutionAgent()

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate the remediation workflow."""
        self.logger.info(f"Starting remediation workflow for issue: {task.get('issue_type', 'unknown')}")

        workflow_result = {
            "workflow_id": f"workflow-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "steps": {}
        }

        try:
            # Step 1: Investigation
            self.logger.info("Step 1: Investigation phase")
            investigation_task = {
                "issue_type": task.get("issue_type", "general"),
                "namespace": task.get("namespace", "default"),
                "pod_name": task.get("pod_name")
            }
            findings = self.investigation_agent.execute(investigation_task)
            workflow_result["steps"]["investigation"] = findings

            # Check confidence level
            if findings.get("confidence", 0) < 0.7:
                self.logger.warning("Low confidence in investigation results")
                workflow_result["status"] = "investigation_low_confidence"
                workflow_result["manual_review_required"] = True
                return workflow_result

            # Step 2: Planning
            self.logger.info("Step 2: Planning phase")
            planning_task = {"findings": findings}
            plan = self.planning_agent.execute(planning_task)
            workflow_result["steps"]["planning"] = plan

            # Step 3: Execution with approval gate
            self.logger.info("Step 3: Execution phase")

            # Check for destructive actions
            destructive_steps = [s for s in plan.get("steps", [])
                               if s.get("severity") in [ActionSeverity.DESTRUCTIVE.value, ActionSeverity.CRITICAL.value]]

            if destructive_steps:
                self.logger.warning(f"Found {len(destructive_steps)} destructive action(s) requiring approval")
                workflow_result["approval_required"] = True
                workflow_result["pending_approvals"] = destructive_steps

                # In production, this would trigger human approval workflow
                approval_status = self._request_human_approval(plan, destructive_steps)

                if not approval_status.get("approved"):
                    self.logger.info("Destructive actions not approved - stopping workflow")
                    self.log_action(
                        action_type="execution",
                        severity=ActionSeverity.CRITICAL.value,
                        description="Destructive actions denied by reviewer",
                        input_data=plan,
                        output_data={},
                        status="denied",
                        approval_required=True,
                        approval_status="denied"
                    )
                    workflow_result["status"] = "approval_denied"
                    return workflow_result

                self.log_action(
                    action_type="execution",
                    severity=ActionSeverity.CRITICAL.value,
                    description="Destructive actions approved by reviewer",
                    input_data=plan,
                    output_data={"approved_by": approval_status.get("approved_by")},
                    status="approved",
                    approval_required=True,
                    approval_status="approved",
                    approval_user=approval_status.get("approved_by")
                )

            # Execute the plan
            execution_task = {"plan": plan}
            execution_result = self.execution_agent.execute(execution_task)
            workflow_result["steps"]["execution"] = execution_result

            # Final status
            workflow_result["status"] = "completed"
            self.logger.info("Remediation workflow completed successfully")

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Workflow failed: {error_msg}")
            self.log_action(
                action_type="workflow",
                severity=ActionSeverity.CRITICAL.value,
                description="Workflow execution failed",
                input_data=task,
                output_data={},
                status="failed",
                error_message=error_msg
            )
            workflow_result["status"] = "failed"
            workflow_result["error"] = error_msg

        return workflow_result

    def _request_human_approval(self, plan: Dict[str, Any], destructive_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Request human approval for destructive actions."""
        self.logger.info(f"Requesting human approval for {len(destructive_steps)} destructive action(s)")

        # In production, this would integrate with approval service (e.g., Slack, email, web UI)
        approval_summary = {
            "plan_id": plan.get("plan_id"),
            "destructive_steps": destructive_steps,
            "estimated_impact": "Service may experience brief downtime",
            "rollback_available": True
        }

        self.logger.warning(f"APPROVAL REQUIRED: {json.dumps(approval_summary, indent=2)}")

        # Simulate approval (in production, would wait for actual user response)
        # For this example, we'll auto-approve after logging
        return {
            "approved": True,
            "approved_by": "system-admin",
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "reason": "Auto-approved for demo purposes"
        }

    def get_audit_trail(self) -> List[AuditLog]:
        """Get complete audit trail from all agents."""
        audit_trail = self.audit_logs.copy()
        audit_trail.extend(self.investigation_agent.audit_logs)
        audit_trail.extend(self.planning_agent.audit_logs)
        audit_trail.extend(self.execution_agent.audit_logs)
        return sorted(audit_trail, key=lambda x: x.timestamp)


def main():
    """Main entry point for the multi-agent system."""
    # Create supervisor
    supervisor = SupervisorAgent()

    # Define remediation task
    task = {
        "issue_type": "pod_crash_loop",
        "namespace": "default",
        "pod_name": "demo-app-5d4f7c8b9-xyz"
    }

    # Execute workflow
    result = supervisor.execute(task)

    # Print results
    print("\n=== Remediation Workflow Result ===")
    print(json.dumps(result, indent=2))

    # Print audit trail
    print("\n=== Complete Audit Trail ===")
    audit_trail = supervisor.get_audit_trail()
    for log in audit_trail:
        print(log.to_json())


if __name__ == "__main__":
    main()
