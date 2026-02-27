#!/usr/bin/env python3
"""
Audit Logger Module

Provides audit logging functionality for the onboarding platform.
Records all operations (team creation, member addition, permission changes, etc.)
with timestamps, actors, and resource information.

This enables compliance, troubleshooting, and security auditing.

Features:
- Structured logging of all onboarding actions
- Persistent storage (file-based, easily extensible to DB)
- Query interface for retrieving audit history
- Idempotent operations tracking
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Configuration
AUDIT_LOG_PATH = os.getenv('ONBOARDING_AUDIT_LOG_PATH', './audit.log')


class AuditLogger:
    """
    Audit logger for recording all onboarding platform operations.
    
    Each log entry contains:
    - timestamp: When the action occurred (ISO 8601 format)
    - event_id: Unique identifier for this log entry
    - action: Type of action (team_created, member_added, etc.)
    - actor: Who performed the action (user email or system)
    - resource_type: Type of resource affected (team, member, project, etc.)
    - resource_id: Identifier of the affected resource
    - status: Result of the action (success, failure)
    - details: Additional context and details
    """
    
    def __init__(self, log_path: str = AUDIT_LOG_PATH):
        """
        Initialize the audit logger.
        
        Args:
            log_path: Path to the audit log file
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._event_counter = 0
        
    def log_event(
        self,
        action: str,
        actor: str,
        resource_type: str,
        resource_id: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an audit event.
        
        Args:
            action: Type of action (e.g., team_created, member_added)
            actor: Who performed the action (email or system identifier)
            resource_type: Type of resource (team, member, project, etc.)
            resource_id: Identifier of the affected resource
            status: Result of action (success, failure)
            details: Optional additional information
            
        Returns:
            Event ID of the logged event
        """
        self._event_counter += 1
        now = datetime.utcnow()
        event_id = f"{now.strftime('%Y%m%d%H%M%S')}-{self._event_counter}"
        
        event = {
            'event_id': event_id,
            'timestamp': now.isoformat() + 'Z',
            'action': action,
            'actor': actor,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'status': status,
            'details': details or {}
        }
        
        # Append to log file (one JSON per line)
        try:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            print(f"Error writing audit log: {str(e)}")
        
        return event_id
    
    def get_events(
        self,
        action: Optional[str] = None,
        actor: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit events with optional filtering.
        
        Args:
            action: Filter by action type
            actor: Filter by actor
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            status: Filter by status (success/failure)
            limit: Maximum number of events to return
            
        Returns:
            List of matching audit events
        """
        events = []
        
        if not self.log_path.exists():
            return events
        
        try:
            with open(self.log_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        event = json.loads(line)
                        
                        # Apply filters
                        if action and event.get('action') != action:
                            continue
                        if actor and event.get('actor') != actor:
                            continue
                        if resource_type and event.get('resource_type') != resource_type:
                            continue
                        if resource_id and event.get('resource_id') != resource_id:
                            continue
                        if status and event.get('status') != status:
                            continue
                        
                        events.append(event)
                        
                        # Stop if we reach the limit
                        if len(events) >= limit:
                            break
                            
                    except json.JSONDecodeError:
                        print(f"Error parsing audit log line: {line}")
                        continue
                        
        except Exception as e:
            print(f"Error reading audit log: {str(e)}")
        
        return events
    
    def get_team_history(self, team_id: str) -> List[Dict[str, Any]]:
        """
        Get complete audit history for a specific team.
        
        Args:
            team_id: Team identifier
            
        Returns:
            List of all events related to this team
        """
        return self.get_events(resource_id=team_id, limit=10000)
    
    def get_member_history(self, team_id: str, member_email: str) -> List[Dict[str, Any]]:
        """
        Get complete audit history for a specific team member.
        
        Args:
            team_id: Team identifier
            member_email: Member email address
            
        Returns:
            List of all events related to this member in the team
        """
        resource_id = f"{team_id}/{member_email}"
        return self.get_events(resource_id=resource_id, limit=10000)
    
    def get_user_actions(self, actor: str) -> List[Dict[str, Any]]:
        """
        Get all actions performed by a specific user.
        
        Args:
            actor: User email or identifier
            
        Returns:
            List of all actions performed by this user
        """
        return self.get_events(actor=actor, limit=10000)
    
    def get_failed_operations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all failed operations for troubleshooting.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of failed operations
        """
        return self.get_events(status='failure', limit=limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about audit log.
        
        Returns:
            Dictionary with counts and summaries
        """
        all_events = self.get_events(limit=100000)
        
        if not all_events:
            return {
                'total_events': 0,
                'actions': {},
                'actors': {},
                'resource_types': {},
                'statuses': {}
            }
        
        stats = {
            'total_events': len(all_events),
            'actions': {},
            'actors': {},
            'resource_types': {},
            'statuses': {}
        }
        
        for event in all_events:
            # Count by action
            action = event.get('action', 'unknown')
            stats['actions'][action] = stats['actions'].get(action, 0) + 1
            
            # Count by actor
            actor = event.get('actor', 'unknown')
            stats['actors'][actor] = stats['actors'].get(actor, 0) + 1
            
            # Count by resource type
            resource_type = event.get('resource_type', 'unknown')
            stats['resource_types'][resource_type] = stats['resource_types'].get(resource_type, 0) + 1
            
            # Count by status
            status = event.get('status', 'unknown')
            stats['statuses'][status] = stats['statuses'].get(status, 0) + 1
        
        return stats
    
    def clear_log(self) -> None:
        """
        Clear all audit logs (use with caution!).
        Should only be used in development environments.
        """
        if self.log_path.exists():
            self.log_path.unlink()
            print(f"Audit log cleared: {self.log_path}")


def print_audit_events(events: List[Dict[str, Any]]) -> None:
    """
    Pretty print audit events.
    
    Args:
        events: List of audit events
    """
    if not events:
        print("No events found")
        return
    
    for event in events:
        print(f"\n[{event['timestamp']}] {event['event_id']}")
        print(f"  Action: {event['action']}")
        print(f"  Actor: {event['actor']}")
        print(f"  Resource: {event['resource_type']}/{event['resource_id']}")
        print(f"  Status: {event['status']}")
        if event['details']:
            print(f"  Details: {json.dumps(event['details'], indent=2)}")


if __name__ == '__main__':
    """
    Example usage and testing of the audit logger.
    """
    import sys
    
    logger = AuditLogger()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'add-sample':
            # Add sample events for testing
            logger.log_event(
                action='team_created',
                actor='admin@example.com',
                resource_type='team',
                resource_id='platform-team',
                status='success',
                details={
                    'display_name': 'Platform Engineering Team',
                    'lead': 'alice@example.com'
                }
            )
            
            logger.log_event(
                action='member_added',
                actor='alice@example.com',
                resource_type='team_member',
                resource_id='platform-team/bob@example.com',
                status='success',
                details={'role': 'developer'}
            )
            
            print("Sample events added")
        
        elif command == 'show':
            # Show all events
            events = logger.get_events(limit=100)
            print_audit_events(events)
        
        elif command == 'stats':
            # Show statistics
            stats = logger.get_statistics()
            print("\nAudit Log Statistics:")
            print(f"Total Events: {stats['total_events']}")
            print(f"\nActions: {json.dumps(stats['actions'], indent=2)}")
            print(f"Actors: {json.dumps(stats['actors'], indent=2)}")
            print(f"Resource Types: {json.dumps(stats['resource_types'], indent=2)}")
            print(f"Statuses: {json.dumps(stats['statuses'], indent=2)}")
        
        elif command == 'failures':
            # Show failed operations
            events = logger.get_failed_operations()
            print(f"Failed Operations: {len(events)}")
            print_audit_events(events)
        
        elif command == 'clear':
            # Clear the log
            logger.clear_log()
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: add-sample, show, stats, failures, clear")
    
    else:
        # Default: show all events
        events = logger.get_events(limit=50)
        print(f"Showing {len(events)} audit events (max 50):\n")
        print_audit_events(events)
        
        if not events:
            print("No audit events found. Run with 'add-sample' to create test events.")
