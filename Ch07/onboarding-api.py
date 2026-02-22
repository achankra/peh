#!/usr/bin/env python3
"""
Self-Service Platform Onboarding API

A Flask-based REST API that enables teams to self-service provision
infrastructure, manage members, and set up RBAC without platform admin
intervention. All operations are idempotent and fully audited.

Key features:
- Team creation with namespace provisioning
- Member management with RBAC
- Automatic Kubernetes namespace setup with quotas and network policies
- Audit logging of all operations
- Idempotent team and member creation
"""

import json
import logging
import subprocess
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from flask import Flask, request, jsonify
from audit_logger import AuditLogger

# Configuration
KUBERNETES_CLUSTER = os.getenv('KUBERNETES_CLUSTER', 'default')
API_PORT = int(os.getenv('ONBOARDING_API_PORT', 5000))
API_HOST = os.getenv('ONBOARDING_API_HOST', '127.0.0.1')
DEBUG = os.getenv('ONBOARDING_API_DEBUG', 'False').lower() == 'true'

# Default resource quotas for new teams
DEFAULT_QUOTA = {
    'cpu': '10',
    'memory': '50Gi',
    'pods': 100,
    'storage': '100Gi'
}

# In-memory storage (use persistent DB in production)
teams_db: Dict[str, Dict[str, Any]] = {}
members_db: Dict[str, List[Dict[str, Any]]] = {}

# Initialize Flask app and audit logger
app = Flask(__name__)
audit_logger = AuditLogger()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_team_id(team_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate team ID format.
    
    Team IDs must be lowercase alphanumeric with hyphens,
    starting and ending with alphanumeric characters.
    
    Args:
        team_id: The team identifier to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    import re
    pattern = r'^[a-z0-9][a-z0-9-]*[a-z0-9]$'
    
    if len(team_id) < 3 or len(team_id) > 63:
        return False, "Team ID must be between 3 and 63 characters"
    
    if not re.match(pattern, team_id):
        return False, "Team ID must contain only lowercase letters, numbers, and hyphens"
    
    return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, None


def create_kubernetes_namespace(team_id: str, quota: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Create a Kubernetes namespace for the team with RBAC and quotas.
    
    This function is idempotent - it won't fail if the namespace already exists.
    
    Args:
        team_id: Team identifier
        quota: Resource quota configuration
        
    Returns:
        Tuple of (success, error_message)
    """
    namespace_name = f"team-{team_id}"
    
    # Build Kubernetes manifest
    manifest = {
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {
            'name': namespace_name,
            'labels': {
                'team': team_id,
                'managed-by': 'onboarding-api'
            }
        }
    }
    
    try:
        # Apply namespace (idempotent)
        manifest_json = json.dumps(manifest)
        result = subprocess.run(
            ['kubectl', 'apply', '-f', '-'],
            input=manifest_json.encode(),
            capture_output=True,
            timeout=10
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.decode()
            logger.error(f"Failed to create namespace: {error_msg}")
            return False, f"Namespace creation failed: {error_msg}"
        
        logger.info(f"Kubernetes namespace created/updated: {namespace_name}")
        
        # Create ResourceQuota
        quota_manifest = {
            'apiVersion': 'v1',
            'kind': 'ResourceQuota',
            'metadata': {
                'name': f"{team_id}-quota",
                'namespace': namespace_name
            },
            'spec': {
                'hard': {
                    'requests.cpu': quota['cpu'],
                    'requests.memory': quota['memory'],
                    'limits.cpu': quota['cpu'],
                    'limits.memory': quota['memory'],
                    'pods': str(quota['pods'])
                }
            }
        }
        
        result = subprocess.run(
            ['kubectl', 'apply', '-f', '-'],
            input=json.dumps(quota_manifest).encode(),
            capture_output=True,
            timeout=10
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to create ResourceQuota: {result.stderr.decode()}")
        
        # Create RBAC bindings
        create_rbac_for_team(team_id, namespace_name)
        
        return True, None
        
    except subprocess.TimeoutExpired:
        return False, "Kubernetes operation timed out"
    except Exception as e:
        logger.error(f"Error creating namespace: {str(e)}")
        return False, str(e)


def create_rbac_for_team(team_id: str, namespace: str) -> bool:
    """
    Create RBAC ClusterRoleBindings for team roles.
    
    Sets up three roles:
    - lead: Full control over namespace resources
    - developer: Create and modify resources
    - viewer: Read-only access
    
    Args:
        team_id: Team identifier
        namespace: Kubernetes namespace name
        
    Returns:
        True if successful, False otherwise
    """
    roles = {
        'lead': 'admin',
        'developer': 'edit',
        'viewer': 'view'
    }
    
    try:
        for role, binding in roles.items():
            # Create RoleBinding for each role
            rolebinding = {
                'apiVersion': 'rbac.authorization.k8s.io/v1',
                'kind': 'RoleBinding',
                'metadata': {
                    'name': f"team-{role}",
                    'namespace': namespace
                },
                'roleRef': {
                    'apiGroup': 'rbac.authorization.k8s.io',
                    'kind': 'ClusterRole',
                    'name': binding
                },
                'subjects': [
                    {
                        'kind': 'Group',
                        'name': f"team:{team_id}:{role}",
                        'apiGroup': 'rbac.authorization.k8s.io'
                    }
                ]
            }
            
            result = subprocess.run(
                ['kubectl', 'apply', '-f', '-'],
                input=json.dumps(rolebinding).encode(),
                capture_output=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.warning(f"Failed to create RoleBinding for {role}: {result.stderr.decode()}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating RBAC: {str(e)}")
        return False


@app.route('/teams', methods=['POST'])
def create_team():
    """
    POST /teams - Create a new team.
    
    Request body:
    {
        "name": "team-id",
        "display_name": "Team Display Name",
        "lead": "lead@example.com",
        "description": "Optional team description",
        "resource_quota": {"cpu": "10", "memory": "50Gi", "pods": 100}
    }
    
    Returns:
    - 201: Team created successfully
    - 400: Invalid request
    - 409: Team already exists (but returns success for idempotency)
    - 500: Internal error
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'code': 'INVALID_REQUEST',
                'message': 'Request body must be JSON'
            }), 400
        
        # Validate required fields
        required_fields = ['name', 'display_name', 'lead']
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            return jsonify({
                'code': 'MISSING_FIELDS',
                'message': f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        team_id = data['name']
        
        # Validate team ID format
        valid, error = validate_team_id(team_id)
        if not valid:
            return jsonify({
                'code': 'INVALID_TEAM_ID',
                'message': error
            }), 400
        
        # Validate lead email
        valid, error = validate_email(data['lead'])
        if not valid:
            return jsonify({
                'code': 'INVALID_EMAIL',
                'message': error
            }), 400
        
        # Check if team already exists (idempotent)
        if team_id in teams_db:
            logger.info(f"Team {team_id} already exists, returning existing team")
            return jsonify(teams_db[team_id]), 201
        
        # Get resource quota
        quota = data.get('resource_quota', DEFAULT_QUOTA)
        
        # Create Kubernetes namespace
        success, error = create_kubernetes_namespace(team_id, quota)
        if not success:
            return jsonify({
                'code': 'NAMESPACE_CREATION_FAILED',
                'message': error
            }), 500
        
        # Create team record
        now = datetime.utcnow().isoformat() + 'Z'
        team = {
            'id': team_id,
            'name': team_id,
            'display_name': data['display_name'],
            'lead': data['lead'],
            'description': data.get('description', ''),
            'created_at': now,
            'namespace': {
                'name': f"team-{team_id}",
                'status': 'active',
                'resource_quota': quota
            },
            'status': 'active',
            'member_count': 1
        }
        
        teams_db[team_id] = team
        members_db[team_id] = [
            {
                'email': data['lead'],
                'name': '',
                'role': 'lead',
                'joined_at': now,
                'permissions': []
            }
        ]
        
        # Audit log
        audit_logger.log_event(
            action='team_created',
            actor=data.get('created_by', 'system'),
            resource_type='team',
            resource_id=team_id,
            status='success',
            details={'display_name': data['display_name'], 'lead': data['lead']}
        )
        
        logger.info(f"Team created: {team_id}")
        return jsonify(team), 201
        
    except Exception as e:
        logger.error(f"Error creating team: {str(e)}")
        return jsonify({
            'code': 'INTERNAL_ERROR',
            'message': 'An internal error occurred'
        }), 500


@app.route('/teams', methods=['GET'])
def list_teams():
    """
    GET /teams - List all teams with pagination.
    
    Query parameters:
    - offset: Number of teams to skip (default: 0)
    - limit: Maximum teams to return (default: 20, max: 100)
    
    Returns:
    - 200: List of teams
    """
    try:
        offset = int(request.args.get('offset', 0))
        limit = min(int(request.args.get('limit', 20)), 100)
        
        all_teams = list(teams_db.values())
        paginated = all_teams[offset:offset + limit]
        
        return jsonify({
            'teams': paginated,
            'total': len(all_teams),
            'offset': offset,
            'limit': limit
        }), 200
        
    except ValueError:
        return jsonify({
            'code': 'INVALID_PARAMS',
            'message': 'Invalid pagination parameters'
        }), 400


@app.route('/teams/<team_id>', methods=['GET'])
def get_team(team_id: str):
    """
    GET /teams/{team_id} - Get team details.
    
    Returns:
    - 200: Team details
    - 404: Team not found
    """
    if team_id not in teams_db:
        return jsonify({
            'code': 'TEAM_NOT_FOUND',
            'message': f"Team '{team_id}' does not exist"
        }), 404
    
    return jsonify(teams_db[team_id]), 200


@app.route('/teams/<team_id>', methods=['DELETE'])
def delete_team(team_id: str):
    """
    DELETE /teams/{team_id} - Delete a team.
    
    This will also delete the associated Kubernetes namespace.
    
    Returns:
    - 204: Team deleted successfully
    - 404: Team not found
    """
    if team_id not in teams_db:
        return jsonify({
            'code': 'TEAM_NOT_FOUND',
            'message': f"Team '{team_id}' does not exist"
        }), 404
    
    try:
        # Delete Kubernetes namespace
        namespace = f"team-{team_id}"
        result = subprocess.run(
            ['kubectl', 'delete', 'namespace', namespace],
            capture_output=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.warning(f"Failed to delete namespace {namespace}: {result.stderr.decode()}")
        
        # Delete from database
        del teams_db[team_id]
        if team_id in members_db:
            del members_db[team_id]
        
        # Audit log
        audit_logger.log_event(
            action='team_deleted',
            actor='system',
            resource_type='team',
            resource_id=team_id,
            status='success'
        )
        
        logger.info(f"Team deleted: {team_id}")
        return '', 204
        
    except Exception as e:
        logger.error(f"Error deleting team: {str(e)}")
        return jsonify({
            'code': 'INTERNAL_ERROR',
            'message': 'Failed to delete team'
        }), 500


@app.route('/teams/<team_id>/members', methods=['POST'])
def add_team_member(team_id: str):
    """
    POST /teams/{team_id}/members - Add member to team.
    
    Request body:
    {
        "email": "member@example.com",
        "name": "Member Name",
        "role": "developer"  # lead, developer, or viewer
    }
    
    Returns:
    - 201: Member added successfully
    - 404: Team not found
    - 400: Invalid request
    """
    if team_id not in teams_db:
        return jsonify({
            'code': 'TEAM_NOT_FOUND',
            'message': f"Team '{team_id}' does not exist"
        }), 404
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'code': 'INVALID_REQUEST',
                'message': 'Request body must be JSON'
            }), 400
        
        # Validate required fields
        if 'email' not in data or 'role' not in data:
            return jsonify({
                'code': 'MISSING_FIELDS',
                'message': 'Missing required fields: email, role'
            }), 400
        
        email = data['email']
        role = data['role']
        
        # Validate email
        valid, error = validate_email(email)
        if not valid:
            return jsonify({
                'code': 'INVALID_EMAIL',
                'message': error
            }), 400
        
        # Validate role
        valid_roles = ['lead', 'developer', 'viewer']
        if role not in valid_roles:
            return jsonify({
                'code': 'INVALID_ROLE',
                'message': f"Role must be one of: {', '.join(valid_roles)}"
            }), 400
        
        # Check if member already exists
        members = members_db[team_id]
        for member in members:
            if member['email'] == email:
                logger.info(f"Member {email} already in team {team_id}, returning existing member")
                return jsonify(member), 201
        
        # Create member record
        now = datetime.utcnow().isoformat() + 'Z'
        member = {
            'email': email,
            'name': data.get('name', ''),
            'role': role,
            'joined_at': now,
            'permissions': []
        }
        
        members_db[team_id].append(member)
        teams_db[team_id]['member_count'] = len(members_db[team_id])
        
        # Audit log
        audit_logger.log_event(
            action='member_added',
            actor=data.get('added_by', 'system'),
            resource_type='team_member',
            resource_id=f"{team_id}/{email}",
            status='success',
            details={'role': role}
        )
        
        logger.info(f"Member {email} added to team {team_id}")
        return jsonify(member), 201
        
    except Exception as e:
        logger.error(f"Error adding member: {str(e)}")
        return jsonify({
            'code': 'INTERNAL_ERROR',
            'message': 'An internal error occurred'
        }), 500


@app.route('/teams/<team_id>/members', methods=['GET'])
def list_team_members(team_id: str):
    """
    GET /teams/{team_id}/members - List team members.
    
    Returns:
    - 200: List of team members
    - 404: Team not found
    """
    if team_id not in teams_db:
        return jsonify({
            'code': 'TEAM_NOT_FOUND',
            'message': f"Team '{team_id}' does not exist"
        }), 404
    
    return jsonify({
        'members': members_db[team_id],
        'total': len(members_db[team_id])
    }), 200


@app.route('/teams/<team_id>/members/<member_id>', methods=['DELETE'])
def remove_team_member(team_id: str, member_id: str):
    """
    DELETE /teams/{team_id}/members/{member_id} - Remove member from team.
    
    Returns:
    - 204: Member removed successfully
    - 404: Team or member not found
    """
    if team_id not in teams_db:
        return jsonify({
            'code': 'TEAM_NOT_FOUND',
            'message': f"Team '{team_id}' does not exist"
        }), 404
    
    members = members_db[team_id]
    member_index = None
    
    # Find member by email
    for i, member in enumerate(members):
        if member['email'] == member_id:
            member_index = i
            break
    
    if member_index is None:
        return jsonify({
            'code': 'MEMBER_NOT_FOUND',
            'message': f"Member '{member_id}' not found in team '{team_id}'"
        }), 404
    
    try:
        member = members.pop(member_index)
        teams_db[team_id]['member_count'] = len(members)
        
        # Audit log
        audit_logger.log_event(
            action='member_removed',
            actor='system',
            resource_type='team_member',
            resource_id=f"{team_id}/{member_id}",
            status='success'
        )
        
        logger.info(f"Member {member_id} removed from team {team_id}")
        return '', 204
        
    except Exception as e:
        logger.error(f"Error removing member: {str(e)}")
        return jsonify({
            'code': 'INTERNAL_ERROR',
            'message': 'Failed to remove member'
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'code': 'NOT_FOUND',
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'code': 'METHOD_NOT_ALLOWED',
        'message': 'Method not allowed'
    }), 405


if __name__ == '__main__':
    logger.info(f"Starting Onboarding API on {API_HOST}:{API_PORT}")
    app.run(host=API_HOST, port=API_PORT, debug=DEBUG)
