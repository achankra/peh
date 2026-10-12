#!/usr/bin/env python3
"""
keycloak_groups.py
Chapter 7 — Keycloak Group Management via Admin API

When the onboarding API provisions a new team, it also creates the
corresponding Keycloak groups so that SSO-authenticated users are
automatically placed in the right RBAC binding on first login.

This module is called by onboarding_api.py after Kubernetes namespace
provisioning when KEYCLOAK_ADMIN_CLIENT_SECRET is set (opt-in). It creates
three groups per team:
  {teamName}-admins
  {teamName}-developers
  {teamName}-viewers

These group names match the OIDC subject names in team-rbac.yaml:
  oidc:{teamName}-admins / oidc:{teamName}-developers / etc.

Usage (standalone):
  export KEYCLOAK_URL=http://localhost:8180
  export KEYCLOAK_REALM=platform-engineering
  export KEYCLOAK_ADMIN_CLIENT_ID=platform-client
  export KEYCLOAK_ADMIN_CLIENT_SECRET=<secret>
  python3 keycloak_groups.py

Full companion code: https://github.com/peh-book/ch7
"""

import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

KEYCLOAK_URL          = os.getenv('KEYCLOAK_URL', 'http://localhost:8180')
KEYCLOAK_REALM        = os.getenv('KEYCLOAK_REALM', 'platform-engineering')
ADMIN_CLIENT_ID       = os.getenv('KEYCLOAK_ADMIN_CLIENT_ID', 'platform-client')
ADMIN_CLIENT_SECRET   = os.getenv('KEYCLOAK_ADMIN_CLIENT_SECRET', '')


def get_admin_token() -> str:
    """
    Obtain a short-lived admin access token from the Keycloak token endpoint.
    Uses the client_credentials grant with the admin-cli service account.
    """
    url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
    resp = requests.post(url, data={
        'grant_type':    'client_credentials',
        'client_id':     ADMIN_CLIENT_ID,
        'client_secret': ADMIN_CLIENT_SECRET,
    }, timeout=10)
    resp.raise_for_status()
    return resp.json()['access_token']


def create_group(token: str, group_name: str) -> Optional[str]:
    """
    Create a Keycloak group in the platform realm.
    Idempotent: returns the existing group ID if it already exists.

    Returns the group ID (UUID), or None on failure.
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type':  'application/json',
    }
    base_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/groups"

    # Check if the group already exists
    search_resp = requests.get(base_url, headers=headers,
                               params={'search': group_name}, timeout=10)
    search_resp.raise_for_status()
    existing = [g for g in search_resp.json() if g['name'] == group_name]
    if existing:
        logger.info(f"Keycloak group '{group_name}' already exists (idempotent).")
        return existing[0]['id']

    # Create the group
    create_resp = requests.post(base_url, headers=headers,
                                json={'name': group_name}, timeout=10)
    if create_resp.status_code == 201:
        # Location header contains the new group URL; extract the UUID
        location = create_resp.headers.get('Location', '')
        group_id = location.rstrip('/').split('/')[-1]
        logger.info(f"Created Keycloak group '{group_name}' (id={group_id})")
        return group_id
    else:
        logger.error(f"Failed to create group '{group_name}': {create_resp.text}")
        create_resp.raise_for_status()


def add_user_to_group(token: str, user_email: str, group_id: str) -> bool:
    """
    Add a user (looked up by email) to a Keycloak group.
    Idempotent: safe to call if the user is already a member.
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type':  'application/json',
    }
    base_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}"

    # Find the user by email
    user_resp = requests.get(f"{base_url}/users",
                             headers=headers,
                             params={'email': user_email, 'exact': 'true'},
                             timeout=10)
    user_resp.raise_for_status()
    users = user_resp.json()
    if not users:
        logger.warning(f"User '{user_email}' not found in Keycloak — skipping group assignment.")
        return False

    user_id = users[0]['id']

    # Add user to the group
    put_resp = requests.put(
        f"{base_url}/users/{user_id}/groups/{group_id}",
        headers=headers,
        timeout=10
    )
    if put_resp.status_code in (204, 409):   # 204 = added, 409 = already member
        logger.info(f"User '{user_email}' added to group {group_id}")
        return True
    put_resp.raise_for_status()
    return False


def provision_team_groups(team_name: str, members: list, lead_email: str) -> dict:
    """
    Provision the three standard Keycloak groups for a new team and
    assign the team lead to the admins group.

    Called by the onboarding API after Kubernetes namespace provisioning.

    Args:
        team_name:   team slug (e.g. "team-beta")
        members:     list of member email addresses
        lead_email:  email of the team lead (assigned to -admins group)

    Returns:
        dict with group IDs: { 'admins': id, 'developers': id, 'viewers': id }
    """
    token = get_admin_token()

    group_ids = {}
    for suffix in ['admins', 'developers', 'viewers']:
        group_name = f"{team_name}-{suffix}"
        gid = create_group(token, group_name)
        group_ids[suffix] = gid

    # Assign the team lead to the admins group
    if lead_email and group_ids.get('admins'):
        add_user_to_group(token, lead_email, group_ids['admins'])

    # Assign all members to the developers group
    if group_ids.get('developers'):
        for email in members:
            add_user_to_group(token, email, group_ids['developers'])

    logger.info(f"Keycloak groups provisioned for team '{team_name}'")
    return group_ids


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s')

    # Standalone smoke test
    result = provision_team_groups(
        team_name='platform',
        members=['alice@example.com', 'bob@example.com'],
        lead_email='alice@example.com'
    )
    print(f"Provisioned groups: {result}")
