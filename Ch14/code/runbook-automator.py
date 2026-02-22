#!/usr/bin/env python3
"""
Runbook Automation: Convert markdown runbooks to executable steps.

This module demonstrates:
- Parsing markdown runbooks into structured steps
- Safety checks and approval gates
- Template-based remediation execution
- Audit trail for all actions

Runbooks define incident response procedures in human-readable format.
This system converts them into executable automation with safeguards.
"""

import json
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum


class StepType(Enum):
    """Types of runbook steps."""
    DIAGNOSTIC = "diagnostic"  # Read-only, gather info
    ACTION = "action"  # Modify system state
    APPROVAL = "approval"  # Requires human approval
    DECISION = "decision"  # Branch logic
    NOTIFICATION = "notification"  # Send alert/message


@dataclass
class RunbookStep:
    """Represents a single runbook step."""
    step_id: str
    name: str
    step_type: StepType
    command: str  # Action to execute
    condition: Optional[str]  # When to run this step
    requires_approval: bool
    timeout_seconds: int
    success_criteria: str  # How to validate success
    rollback_action: Optional[str]  # How to undo if failed


@dataclass
class RunbookExecution:
    """Record of runbook execution."""
    execution_id: str
    runbook_name: str
    started_at: float
    completed_at: Optional[float]
    steps_executed: List[Dict]
    status: str  # running, success, failed, cancelled
    approval_required: bool
    error_message: Optional[str]


class RunbookParser:
    """
    Parses markdown runbooks into structured steps.
    
    Expected markdown format:
    
    # Runbook: Service Recovery
    
    ## Step 1: Check Service Status
    Type: Diagnostic
    Command: systemctl status api-service
    Success: Service is running
    
    ## Step 2: Restart Service
    Type: Action
    Command: systemctl restart api-service
    ApprovalRequired: true
    Rollback: systemctl start api-service
    """
    
    def __init__(self):
        """Initialize parser."""
        self.runbooks: Dict[str, List[RunbookStep]] = {}
    
    def parse_markdown(self, content: str) -> Tuple[str, List[RunbookStep]]:
        """
        Parse markdown runbook.
        
        Args:
            content: Markdown content
            
        Returns:
            Tuple of (runbook_name, list of steps)
        """
        lines = content.strip().split('\n')
        
        # Extract title
        title = "Unnamed Runbook"
        for line in lines:
            if line.startswith('# Runbook:'):
                title = line.replace('# Runbook:', '').strip()
                break
        
        # Parse steps
        steps = []
        current_step = None
        step_counter = 1
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Step header
            if line.startswith('## Step'):
                if current_step:
                    steps.append(current_step)
                
                step_name = line.replace('##', '').strip()
                current_step = {
                    'step_id': f"step-{step_counter}",
                    'name': step_name,
                    'type': StepType.DIAGNOSTIC,
                    'command': '',
                    'condition': None,
                    'requires_approval': False,
                    'timeout': 300,
                    'success_criteria': 'Command completed',
                    'rollback': None
                }
                step_counter += 1
            
            # Parse key-value pairs
            elif ':' in line and current_step:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == 'type':
                    try:
                        current_step['type'] = StepType[value.upper()]
                    except KeyError:
                        current_step['type'] = StepType.ACTION
                
                elif key == 'command':
                    current_step['command'] = value
                
                elif key == 'condition':
                    current_step['condition'] = value
                
                elif key == 'approvalrequired':
                    current_step['requires_approval'] = value.lower() == 'true'
                
                elif key == 'timeout':
                    try:
                        current_step['timeout'] = int(value)
                    except ValueError:
                        pass
                
                elif key == 'success':
                    current_step['success_criteria'] = value
                
                elif key == 'rollback':
                    current_step['rollback'] = value
            
            i += 1
        
        # Add last step
        if current_step:
            steps.append(current_step)
        
        # Convert to RunbookStep objects
        runbook_steps = []
        for step_dict in steps:
            step = RunbookStep(
                step_id=step_dict['step_id'],
                name=step_dict['name'],
                step_type=step_dict['type'],
                command=step_dict['command'],
                condition=step_dict['condition'],
                requires_approval=step_dict['requires_approval'],
                timeout_seconds=step_dict['timeout'],
                success_criteria=step_dict['success_criteria'],
                rollback_action=step_dict['rollback']
            )
            runbook_steps.append(step)
        
        self.runbooks[title] = runbook_steps
        return title, runbook_steps


class SafetyValidator:
    """Validates runbook steps for safety."""
    
    # Actions that require approval
    DANGEROUS_KEYWORDS = {
        'kill', 'rm', 'delete', 'drop', 'truncate', 'reboot', 'shutdown',
        'restart', 'restart', 'uninstall', 'remove', 'force'
    }
    
    # Commands that are always read-only
    SAFE_KEYWORDS = {
        'get', 'list', 'describe', 'show', 'status', 'check', 'query'
    }
    
    @staticmethod
    def validate_step(step: RunbookStep) -> Tuple[bool, List[str]]:
        """
        Validate a step for safety.
        
        Args:
            step: RunbookStep to validate
            
        Returns:
            Tuple of (is_safe, list of warnings)
        """
        warnings = []
        
        # Check command
        command_lower = step.command.lower()
        
        # Detect dangerous commands
        for keyword in SafetyValidator.DANGEROUS_KEYWORDS:
            if keyword in command_lower:
                if step.step_type == StepType.ACTION and not step.requires_approval:
                    warnings.append(
                        f"Dangerous action '{keyword}' requires approval"
                    )
                    return False, warnings
        
        # Require approval for state-changing actions
        if step.step_type == StepType.ACTION and not step.requires_approval:
            if not any(safe in command_lower for safe in SafetyValidator.SAFE_KEYWORDS):
                warnings.append("Non-readonly action should require approval")
        
        # Check timeout
        if step.timeout_seconds == 0:
            warnings.append("Timeout is 0 - infinite wait")
        
        # Check success criteria
        if not step.success_criteria:
            warnings.append("No success criteria defined")
        
        # Check rollback for destructive actions
        if step.step_type == StepType.ACTION and not step.rollback_action:
            if any(keyword in command_lower for keyword in SafetyValidator.DANGEROUS_KEYWORDS):
                warnings.append("Destructive action without rollback procedure")
        
        is_safe = len(warnings) == 0
        return is_safe, warnings


class RunbookExecutor:
    """
    Executes runbooks with safety checks and audit trail.
    """
    
    def __init__(self):
        """Initialize executor."""
        self.executions: List[RunbookExecution] = []
        self.approval_queue: List[RunbookStep] = []
    
    def execute_runbook(self, 
                       runbook_name: str,
                       steps: List[RunbookStep],
                       auto_approve: bool = False) -> RunbookExecution:
        """
        Execute a runbook.
        
        Args:
            runbook_name: Name of runbook
            steps: List of steps to execute
            auto_approve: Auto-approve diagnostic steps
            
        Returns:
            RunbookExecution record
        """
        import time
        
        execution_id = f"exec-{int(time.time())}"
        execution = RunbookExecution(
            execution_id=execution_id,
            runbook_name=runbook_name,
            started_at=time.time(),
            completed_at=None,
            steps_executed=[],
            status="running",
            approval_required=False,
            error_message=None
        )
        
        # Check for steps requiring approval
        needs_approval = any(s.requires_approval for s in steps)
        if needs_approval:
            execution.approval_required = True
        
        # Execute steps
        for step in steps:
            step_result = self._execute_step(step, auto_approve and step.step_type == StepType.DIAGNOSTIC)
            execution.steps_executed.append(step_result)
            
            if not step_result['success']:
                execution.status = "failed"
                execution.error_message = step_result.get('error')
                break
        
        if execution.status == "running":
            execution.status = "success"
        
        execution.completed_at = time.time()
        self.executions.append(execution)
        return execution
    
    def _execute_step(self, step: RunbookStep, 
                     auto_approve: bool = False) -> Dict:
        """
        Execute a single step.
        
        Args:
            step: Step to execute
            auto_approve: Whether to auto-approve
            
        Returns:
            Step execution result
        """
        result = {
            'step_id': step.step_id,
            'name': step.name,
            'type': step.step_type.value,
            'success': False,
            'output': '',
            'error': None
        }
        
        # Validate step
        is_safe, warnings = SafetyValidator.validate_step(step)
        
        if not is_safe:
            result['error'] = f"Safety validation failed: {'; '.join(warnings)}"
            return result
        
        # Check approval
        if step.requires_approval and not auto_approve:
            result['error'] = "Awaiting approval"
            self.approval_queue.append(step)
            return result
        
        # Execute based on type
        if step.step_type == StepType.DIAGNOSTIC:
            output = self._execute_diagnostic(step)
            result['success'] = True
            result['output'] = output
        
        elif step.step_type == StepType.ACTION:
            output = self._execute_action(step)
            result['success'] = True
            result['output'] = output
        
        elif step.step_type == StepType.APPROVAL:
            result['error'] = "Awaiting human approval"
        
        elif step.step_type == StepType.NOTIFICATION:
            output = self._execute_notification(step)
            result['success'] = True
            result['output'] = output
        
        return result
    
    def _execute_diagnostic(self, step: RunbookStep) -> str:
        """Execute diagnostic step (read-only)."""
        # Simulate command execution
        if 'status' in step.command.lower():
            return "Service is running (OK)"
        elif 'logs' in step.command.lower():
            return "Last 10 log lines: [no errors detected]"
        elif 'check' in step.command.lower():
            return "Health check passed"
        else:
            return f"Executed: {step.command}"
    
    def _execute_action(self, step: RunbookStep) -> str:
        """Execute action step (state change)."""
        if 'restart' in step.command.lower():
            return f"Service restarted successfully"
        elif 'scale' in step.command.lower():
            return f"Scaled to 3 replicas"
        elif 'rollback' in step.command.lower():
            return f"Rolled back to previous version"
        else:
            return f"Action completed: {step.command}"
    
    def _execute_notification(self, step: RunbookStep) -> str:
        """Execute notification step."""
        return f"Notification sent: {step.command}"
    
    def approve_step(self, step_id: str, approved: bool) -> bool:
        """
        Approve or reject a pending step.
        
        Args:
            step_id: ID of step to approve
            approved: Whether to approve
            
        Returns:
            True if approved
        """
        # Find and remove from queue
        for i, step in enumerate(self.approval_queue):
            if step.step_id == step_id:
                if approved:
                    self.approval_queue.pop(i)
                    return True
                else:
                    self.approval_queue.pop(i)
                    return False
        
        return False


def create_sample_runbook() -> str:
    """Create a sample runbook in markdown."""
    return """
# Runbook: Database Recovery

## Step 1: Check Database Status
Type: Diagnostic
Command: systemctl status postgresql
Success: Service is running

## Step 2: Check Disk Space
Type: Diagnostic
Command: df -h /var/lib/postgresql
Success: Disk has free space

## Step 3: Stop Database
Type: Action
Command: systemctl stop postgresql
ApprovalRequired: true
Rollback: systemctl start postgresql
Success: Database stopped

## Step 4: Run Recovery
Type: Action
Command: pg_recover --verify
ApprovalRequired: true
Timeout: 600
Success: Recovery completed without errors

## Step 5: Start Database
Type: Action
Command: systemctl start postgresql
ApprovalRequired: false
Success: Service is running

## Step 6: Verify Integrity
Type: Diagnostic
Command: pg_verify_checksums
Success: All checksums valid

## Step 7: Notify Team
Type: Notification
Command: Notify #ops-channel: Database recovery completed
"""


def main():
    """Demonstrate runbook automation."""
    print("=" * 70)
    print("Runbook Automator Demo")
    print("=" * 70)
    
    # Parse runbook
    parser = RunbookParser()
    runbook_content = create_sample_runbook()
    runbook_name, steps = parser.parse_markdown(runbook_content)
    
    print(f"\nParsed runbook: {runbook_name}")
    print(f"Total steps: {len(steps)}\n")
    
    print("-" * 70)
    print("Runbook Steps:")
    print("-" * 70)
    
    for step in steps:
        is_safe, warnings = SafetyValidator.validate_step(step)
        
        print(f"\n{step.step_id}: {step.name}")
        print(f"  Type: {step.step_type.value}")
        print(f"  Command: {step.command}")
        print(f"  Requires Approval: {step.requires_approval}")
        print(f"  Timeout: {step.timeout_seconds}s")
        print(f"  Success Criteria: {step.success_criteria}")
        
        if step.rollback_action:
            print(f"  Rollback: {step.rollback_action}")
        
        if warnings:
            print(f"  Warnings: {'; '.join(warnings)}")
        
        if not is_safe:
            print(f"  Status: BLOCKED (Safety violation)")
        else:
            print(f"  Status: OK")
    
    # Execute runbook
    print("\n" + "-" * 70)
    print("Executing runbook (with approval for critical steps)...\n")
    
    executor = RunbookExecutor()
    execution = executor.execute_runbook(runbook_name, steps)
    
    print("-" * 70)
    print("Execution Results:")
    print("-" * 70)
    print(f"\nExecution ID: {execution.execution_id}")
    print(f"Status: {execution.status}")
    print(f"Approval Required: {execution.approval_required}")
    
    successful = sum(1 for s in execution.steps_executed if s['success'])
    print(f"Successful steps: {successful}/{len(execution.steps_executed)}")
    
    for step_result in execution.steps_executed:
        status = "✓" if step_result['success'] else "✗"
        print(f"\n{status} {step_result['step_id']}: {step_result['name']}")
        if step_result.get('output'):
            print(f"   Output: {step_result['output']}")
        if step_result.get('error'):
            print(f"   Error: {step_result['error']}")


if __name__ == "__main__":
    main()
