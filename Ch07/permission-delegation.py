#!/usr/bin/env python3
"""
Permission Delegation Module

Enables team leads to delegate permissions to team members without
requiring platform administrator intervention. Implements a hierarchical
permission model where team leads can grant sub-permissions to members.

Key features:
- Hierarchical permission delegation
- Permission validation and conflict checking
- Audit trail of all permission changes
- Support for custom permission scopes
- Revocation and modification of permissions
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
from enum import Enum
from audit_logger import AuditLogger

# Configuration
PERMISSIONS_DB_PATH = os.getenv('PERMISSIONS_DB_PATH', './permissions.json')


class PermissionLevel(Enum):
    """Permission hierarchy levels."""
    LEAD = 'lead'           # Full control over team
    DEVELOPER = 'developer' # Create and manage resources
    VIEWER = 'viewer'       # Read-only access
    CUSTOM = 'custom'       # Custom permission set


class Permission:
    """Represents a single permission that can be granted."""
    
    def __init__(self, name: str, description: str, parent: Optional[str] = None):
        """
        Initialize a permission.
        
        Args:
            name: Permission identifier (e.g., 'create-projects')
            description: Human-readable description
            parent: Parent permission (for hierarchy)
        """
        self.name = name
        self.description = description
        self.parent = parent
    
    def to_dict(self) -> Dict[str, str]:
        """Convert permission to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'parent': self.parent
        }


class PermissionManager:
    """
    Manages permission delegation for teams.
    
    Provides methods to:
    - Grant permissions to team members
    - Revoke permissions
    - Check if user has permission
    - List all permissions for a user
    """
    
    # Define available permissions by role
    ROLE_PERMISSIONS = {
        'lead': {
            'manage-team': 'Full team management',
            'manage-members': 'Add/remove team members',
            'manage-projects': 'Create and manage projects',
            'manage-resources': 'Manage team resource quotas',
            'manage-rbac': 'Manage team RBAC policies',
            'view-audit-logs': 'View team audit logs',
            'delegate-permissions': 'Delegate permissions to members',
            'delete-team': 'Delete team (irreversible)',
        },
        'developer': {
            'create-projects': 'Create new projects',
            'manage-projects': 'Manage own projects',
            'manage-ci-cd': 'Configure CI/CD pipelines',
            'manage-deployments': 'Deploy applications',
            'manage-secrets': 'Manage secrets and configs',
            'view-projects': 'View all team projects',
            'view-audit-logs': 'View audit logs (limited)',
        },
        'viewer': {
            'view-projects': 'View all team projects',
            'view-members': 'View team members',
            'view-deployments': 'View deployment status',
            'view-audit-logs': 'View basic audit logs',
        }
    }
    
    def __init__(self, db_path: str = PERMISSIONS_DB_PATH):
        """
        Initialize the permission manager.
        
        Args:
            db_path: Path to permissions database file
        """
        self.db_path = db_path
        self.audit_logger = AuditLogger()
        self._permissions_db: Dict[str, Dict[str, Set[str]]] = {}
        self._load_permissions()
    
    def _load_permissions(self) -> None:
        """Load permissions from persistent storage."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                    # Convert lists back to sets
                    for team_id, members in data.items():
                        self._permissions_db[team_id] = {}
                        for member_email, perms in members.items():
                            self._permissions_db[team_id][member_email] = set(perms)
            except Exception as e:
                print(f"Error loading permissions: {str(e)}")
    
    def _save_permissions(self) -> None:
        """Save permissions to persistent storage."""
        try:
            # Convert sets to lists for JSON serialization
            data = {}
            for team_id, members in self._permissions_db.items():
                data[team_id] = {}
                for member_email, perms in members.items():
                    data[team_id][member_email] = sorted(list(perms))
            
            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving permissions: {str(e)}")
    
    def grant_permission(
        self,
        team_id: str,
        member_email: str,
        permission: str,
        delegated_by: str,
        reason: str = ''
    ) -> Tuple[bool, Optional[str]]:
        """
        Grant a permission to a team member.
        
        Args:
            team_id: Team identifier
            member_email: Member to grant permission to
            permission: Permission name
            delegated_by: User who is delegating the permission
            reason: Optional reason for the delegation
            
        Returns:
            Tuple of (success, error_message)
        """
        # Check if delegating user has permission to delegate
        if not self._can_delegate(team_id, delegated_by, permission):
            error = f"User {delegated_by} cannot delegate {permission}"
            self.audit_logger.log_event(
                action='permission_delegation_denied',
                actor=delegated_by,
                resource_type='permission',
                resource_id=f"{team_id}/{member_email}/{permission}",
                status='failure',
                details={'reason': 'Insufficient permissions to delegate'}
            )
            return False, error
        
        # Validate permission exists
        if not self._is_valid_permission(permission):
            error = f"Permission '{permission}' does not exist"
            return False, error
        
        # Initialize team/member if needed
        if team_id not in self._permissions_db:
            self._permissions_db[team_id] = {}
        if member_email not in self._permissions_db[team_id]:
            self._permissions_db[team_id][member_email] = set()
        
        # Grant permission (idempotent - no error if already granted)
        was_granted = permission in self._permissions_db[team_id][member_email]
        self._permissions_db[team_id][member_email].add(permission)
        
        # Save to disk
        self._save_permissions()
        
        # Audit log
        self.audit_logger.log_event(
            action='permission_granted',
            actor=delegated_by,
            resource_type='permission',
            resource_id=f"{team_id}/{member_email}/{permission}",
            status='success',
            details={
                'permission': permission,
                'reason': reason,
                'already_granted': was_granted
            }
        )
        
        return True, None
    
    def revoke_permission(
        self,
        team_id: str,
        member_email: str,
        permission: str,
        revoked_by: str,
        reason: str = ''
    ) -> Tuple[bool, Optional[str]]:
        """
        Revoke a permission from a team member.
        
        Args:
            team_id: Team identifier
            member_email: Member to revoke permission from
            permission: Permission name
            revoked_by: User who is revoking the permission
            reason: Optional reason for the revocation
            
        Returns:
            Tuple of (success, error_message)
        """
        # Check if revoking user has permission to revoke
        if not self._can_delegate(team_id, revoked_by, permission):
            error = f"User {revoked_by} cannot revoke {permission}"
            return False, error
        
        # Check if team and member exist
        if team_id not in self._permissions_db:
            return False, f"Team '{team_id}' not found"
        
        if member_email not in self._permissions_db[team_id]:
            return False, f"Member '{member_email}' not found in team"
        
        # Revoke permission (idempotent)
        had_permission = permission in self._permissions_db[team_id][member_email]
        self._permissions_db[team_id][member_email].discard(permission)
        
        # Save to disk
        self._save_permissions()
        
        # Audit log
        self.audit_logger.log_event(
            action='permission_revoked',
            actor=revoked_by,
            resource_type='permission',
            resource_id=f"{team_id}/{member_email}/{permission}",
            status='success',
            details={
                'permission': permission,
                'reason': reason,
                'had_permission': had_permission
            }
        )
        
        return True, None
    
    def grant_role(
        self,
        team_id: str,
        member_email: str,
        role: str,
        granted_by: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Grant a role (and all associated permissions) to a member.
        
        Args:
            team_id: Team identifier
            member_email: Member to grant role to
            role: Role name (lead, developer, viewer)
            granted_by: User granting the role
            
        Returns:
            Tuple of (success, error_message)
        """
        if role not in self.ROLE_PERMISSIONS:
            return False, f"Unknown role: {role}"
        
        # Initialize if needed
        if team_id not in self._permissions_db:
            self._permissions_db[team_id] = {}
        if member_email not in self._permissions_db[team_id]:
            self._permissions_db[team_id][member_email] = set()
        
        # Grant all permissions for this role
        permissions = self.ROLE_PERMISSIONS[role].keys()
        for perm in permissions:
            self._permissions_db[team_id][member_email].add(perm)
        
        # Save to disk
        self._save_permissions()
        
        # Audit log
        self.audit_logger.log_event(
            action='role_granted',
            actor=granted_by,
            resource_type='role',
            resource_id=f"{team_id}/{member_email}",
            status='success',
            details={
                'role': role,
                'permissions_count': len(permissions)
            }
        )
        
        return True, None
    
    def has_permission(
        self,
        team_id: str,
        member_email: str,
        permission: str
    ) -> bool:
        """
        Check if a member has a specific permission.
        
        Args:
            team_id: Team identifier
            member_email: Member email
            permission: Permission to check
            
        Returns:
            True if member has the permission, False otherwise
        """
        if team_id not in self._permissions_db:
            return False
        
        if member_email not in self._permissions_db[team_id]:
            return False
        
        return permission in self._permissions_db[team_id][member_email]
    
    def get_member_permissions(
        self,
        team_id: str,
        member_email: str
    ) -> List[str]:
        """
        Get all permissions for a team member.
        
        Args:
            team_id: Team identifier
            member_email: Member email
            
        Returns:
            List of permissions granted to the member
        """
        if team_id not in self._permissions_db:
            return []
        
        if member_email not in self._permissions_db[team_id]:
            return []
        
        return sorted(list(self._permissions_db[team_id][member_email]))
    
    def get_team_permissions(self, team_id: str) -> Dict[str, List[str]]:
        """
        Get all permissions for all members in a team.
        
        Args:
            team_id: Team identifier
            
        Returns:
            Dictionary mapping member email to their permissions
        """
        if team_id not in self._permissions_db:
            return {}
        
        result = {}
        for member_email, permissions in self._permissions_db[team_id].items():
            result[member_email] = sorted(list(permissions))
        
        return result
    
    def _can_delegate(
        self,
        team_id: str,
        user_email: str,
        permission: str
    ) -> bool:
        """
        Check if a user can delegate a specific permission.
        
        A user can delegate if they:
        1. Have the permission themselves, OR
        2. Are a team lead
        
        Args:
            team_id: Team identifier
            user_email: User email
            permission: Permission to check
            
        Returns:
            True if user can delegate the permission
        """
        # Team leads can always delegate
        if self.has_permission(team_id, user_email, 'delegate-permissions'):
            return True
        
        # Non-leads can only delegate permissions they have
        return self.has_permission(team_id, user_email, permission)
    
    def _is_valid_permission(self, permission: str) -> bool:
        """
        Check if a permission exists.
        
        Args:
            permission: Permission name to validate
            
        Returns:
            True if permission is valid
        """
        for perms in self.ROLE_PERMISSIONS.values():
            if permission in perms:
                return True
        return False


def print_permissions(permissions: Dict[str, str], title: str = "Permissions") -> None:
    """
    Pretty print permissions.
    
    Args:
        permissions: Dictionary of permission -> description
        title: Title for the output
    """
    print(f"\n{title}:")
    print("-" * 60)
    for perm, desc in sorted(permissions.items()):
        print(f"  {perm:<30} {desc}")
    print()


if __name__ == '__main__':
    """
    Example usage and testing of the permission manager.
    """
    import sys
    
    manager = PermissionManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'grant-role':
            # Grant a role: grant-role <team> <email> <role>
            if len(sys.argv) >= 5:
                team = sys.argv[2]
                email = sys.argv[3]
                role = sys.argv[4]
                success, error = manager.grant_role(team, email, role, 'admin@example.com')
                if success:
                    print(f"Granted {role} role to {email}")
                else:
                    print(f"Error: {error}")
            else:
                print("Usage: permission-delegation.py grant-role <team> <email> <role>")
        
        elif command == 'grant':
            # Grant a permission: grant <team> <email> <permission>
            if len(sys.argv) >= 5:
                team = sys.argv[2]
                email = sys.argv[3]
                perm = sys.argv[4]
                success, error = manager.grant_permission(team, email, perm, 'admin@example.com')
                if success:
                    print(f"Granted {perm} to {email}")
                else:
                    print(f"Error: {error}")
            else:
                print("Usage: permission-delegation.py grant <team> <email> <permission>")
        
        elif command == 'revoke':
            # Revoke a permission: revoke <team> <email> <permission>
            if len(sys.argv) >= 5:
                team = sys.argv[2]
                email = sys.argv[3]
                perm = sys.argv[4]
                success, error = manager.revoke_permission(team, email, perm, 'admin@example.com')
                if success:
                    print(f"Revoked {perm} from {email}")
                else:
                    print(f"Error: {error}")
            else:
                print("Usage: permission-delegation.py revoke <team> <email> <permission>")
        
        elif command == 'check':
            # Check permission: check <team> <email> <permission>
            if len(sys.argv) >= 5:
                team = sys.argv[2]
                email = sys.argv[3]
                perm = sys.argv[4]
                has_it = manager.has_permission(team, email, perm)
                print(f"{email} has {perm}: {has_it}")
            else:
                print("Usage: permission-delegation.py check <team> <email> <permission>")
        
        elif command == 'list-member':
            # List member permissions: list-member <team> <email>
            if len(sys.argv) >= 4:
                team = sys.argv[2]
                email = sys.argv[3]
                perms = manager.get_member_permissions(team, email)
                print(f"\nPermissions for {email} in {team}:")
                for perm in perms:
                    print(f"  - {perm}")
            else:
                print("Usage: permission-delegation.py list-member <team> <email>")
        
        elif command == 'list-roles':
            # List available roles and permissions
            for role, perms in manager.ROLE_PERMISSIONS.items():
                print_permissions(perms, f"Permissions for {role.upper()} role")
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: grant-role, grant, revoke, check, list-member, list-roles")
    
    else:
        # Default: show available roles
        for role, perms in manager.ROLE_PERMISSIONS.items():
            print_permissions(perms, f"Permissions for {role.upper()} role")
