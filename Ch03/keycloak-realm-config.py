#!/usr/bin/env python3
"""
Keycloak Realm Configuration Script

Purpose:
    Automate the creation and configuration of a Keycloak realm for
    platform SSO (Single Sign-On) integration. Creates realm, OAuth client,
    roles, and user mappings.

Features:
    - Create Keycloak realm for platform
    - Configure OAuth2/OIDC client
    - Create platform roles
    - Set up user groups and mappings
    - Configure realm policies

Prerequisites:
    - Keycloak instance running and accessible
    - Admin credentials with realm creation permissions
    - requests library: pip install requests

Environment Variables:
    KEYCLOAK_URL: Keycloak server URL (default: http://localhost:8080)
    KEYCLOAK_ADMIN: Admin username (default: admin)
    KEYCLOAK_PASSWORD: Admin password
    KEYCLOAK_REALM: Realm to create (default: platform-engineering)

Usage:
    python keycloak-realm-config.py
    python keycloak-realm-config.py --verify
    python keycloak-realm-config.py --cleanup
    python keycloak-realm-config.py --users config.json

Author: Platform Engineering Handbook
License: Example code for educational purposes
"""

import json
import os
import sys
import argparse
import logging
from typing import Dict, Any, Optional
from urllib.parse import urljoin

try:
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KeycloakRealm:
    """Manage Keycloak realm configuration."""

    def __init__(
        self,
        keycloak_url: str,
        admin_user: str,
        admin_password: str,
        realm_name: str = "platform-engineering"
    ):
        """
        Initialize Keycloak realm manager.

        Args:
            keycloak_url: Keycloak server URL
            admin_user: Admin username
            admin_password: Admin password
            realm_name: Realm name to create/manage
        """
        self.keycloak_url = keycloak_url.rstrip('/')
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.realm_name = realm_name
        self.access_token = None
        self.session = requests.Session()

    def authenticate(self) -> bool:
        """
        Authenticate with Keycloak admin console.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            url = urljoin(self.keycloak_url, '/realms/master/protocol/openid-connect/token')
            data = {
                'grant_type': 'password',
                'client_id': 'admin-cli',
                'username': self.admin_user,
                'password': self.admin_password,
            }

            response = self.session.post(url, data=data, verify=False)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data.get('access_token')

            if self.access_token:
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                })
                logger.info("Successfully authenticated with Keycloak")
                return True

            logger.error("No access token received")
            return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def create_realm(self) -> bool:
        """
        Create a new Keycloak realm.

        Returns:
            True if realm created successfully, False otherwise
        """
        try:
            url = urljoin(self.keycloak_url, '/admin/realms')

            realm_config = {
                'realm': self.realm_name,
                'displayName': 'Platform Engineering',
                'enabled': True,
                'sslRequired': 'external',
                'passwordPolicy': 'length(8) and specialChars(1) and digits(1) and lowerCase(1) and upperCase(1)',
                'offlineSessionIdleTimeout': 2592000,  # 30 days
                'accessTokenLifespan': 3600,  # 1 hour
                'refreshTokenMaxReuse': 0,
                'defaultRole': {
                    'name': 'default-roles-' + self.realm_name,
                    'description': 'Default roles for all users'
                }
            }

            response = self.session.post(url, json=realm_config, verify=False)

            if response.status_code == 201:
                logger.info(f"Realm '{self.realm_name}' created successfully")
                return True
            elif response.status_code == 409:
                logger.info(f"Realm '{self.realm_name}' already exists")
                return True
            else:
                logger.error(f"Failed to create realm: {response.status_code}")
                logger.error(response.text)
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating realm: {e}")
            return False

    def create_oauth_client(self) -> Optional[str]:
        """
        Create OAuth2/OIDC client for platform.

        Returns:
            Client ID if successful, None otherwise
        """
        try:
            url = urljoin(self.keycloak_url, f'/admin/realms/{self.realm_name}/clients')

            client_config = {
                'clientId': 'platform-client',
                'name': 'Platform Engineering Client',
                'description': 'OAuth2/OIDC client for platform SSO',
                'enabled': True,
                'publicClient': False,
                'directAccessGrantsEnabled': True,
                'standardFlowEnabled': True,
                'implicitFlowEnabled': True,
                'serviceAccountsEnabled': True,
                'authorizationServicesEnabled': True,
                'redirectUris': [
                    'http://localhost:3000/*',
                    'http://localhost:8000/*',
                    'https://platform.example.com/*'
                ],
                'webOrigins': [
                    'http://localhost:3000',
                    'http://localhost:8000',
                    'https://platform.example.com'
                ],
                'validRedirectUris': [
                    'http://localhost:3000/*',
                    'http://localhost:8000/*',
                    'https://platform.example.com/*'
                ],
                'attributes': {
                    'access.token.lifespan': '3600',
                    'refresh.token.lifespan': '86400'
                }
            }

            response = self.session.post(url, json=client_config, verify=False)

            if response.status_code == 201:
                client_id = response.headers.get('Location', '').split('/')[-1]
                logger.info(f"OAuth2 client created: {client_id}")
                return client_id
            elif response.status_code == 409:
                logger.info("OAuth2 client already exists")
                # Get existing client
                get_url = urljoin(
                    self.keycloak_url,
                    f'/admin/realms/{self.realm_name}/clients'
                )
                get_response = self.session.get(get_url, verify=False)
                clients = get_response.json()
                for client in clients:
                    if client.get('clientId') == 'platform-client':
                        return client.get('id')
            else:
                logger.error(f"Failed to create client: {response.status_code}")
                logger.error(response.text)

            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating OAuth client: {e}")
            return None

    def create_roles(self) -> bool:
        """
        Create platform roles in the realm.

        Returns:
            True if roles created successfully, False otherwise
        """
        try:
            roles = [
                {
                    'name': 'platform-admin',
                    'description': 'Platform administrator with full access'
                },
                {
                    'name': 'platform-developer',
                    'description': 'Platform developer with deployment permissions'
                },
                {
                    'name': 'platform-operator',
                    'description': 'Platform operator for operational tasks'
                },
                {
                    'name': 'platform-auditor',
                    'description': 'Platform auditor with read-only access'
                }
            ]

            url = urljoin(self.keycloak_url, f'/admin/realms/{self.realm_name}/roles')

            for role in roles:
                response = self.session.post(url, json=role, verify=False)

                if response.status_code == 201:
                    logger.info(f"Role '{role['name']}' created")
                elif response.status_code == 409:
                    logger.info(f"Role '{role['name']}' already exists")
                else:
                    logger.warning(f"Failed to create role '{role['name']}': {response.status_code}")

            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating roles: {e}")
            return False

    def create_users(self, users_config: list) -> bool:
        """
        Create users in the realm.

        Args:
            users_config: List of user configurations

        Returns:
            True if users created successfully, False otherwise
        """
        try:
            url = urljoin(self.keycloak_url, f'/admin/realms/{self.realm_name}/users')

            for user_config in users_config:
                user_data = {
                    'username': user_config.get('username'),
                    'email': user_config.get('email'),
                    'firstName': user_config.get('firstName', ''),
                    'lastName': user_config.get('lastName', ''),
                    'enabled': True,
                    'emailVerified': True,
                    'credentials': [
                        {
                            'type': 'password',
                            'value': user_config.get('password', 'TempPassword123!'),
                            'temporary': True
                        }
                    ]
                }

                response = self.session.post(url, json=user_data, verify=False)

                if response.status_code == 201:
                    logger.info(f"User '{user_config.get('username')}' created")
                elif response.status_code == 409:
                    logger.info(f"User '{user_config.get('username')}' already exists")
                else:
                    logger.warning(f"Failed to create user: {response.status_code}")

            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating users: {e}")
            return False

    def verify_configuration(self) -> bool:
        """
        Verify realm configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Check realm exists
            url = urljoin(self.keycloak_url, f'/admin/realms/{self.realm_name}')
            response = self.session.get(url, verify=False)

            if response.status_code != 200:
                logger.error(f"Realm '{self.realm_name}' not found")
                return False

            realm_info = response.json()
            logger.info(f"Realm verified: {realm_info.get('realm')}")

            # Check for roles
            roles_url = urljoin(self.keycloak_url, f'/admin/realms/{self.realm_name}/roles')
            roles_response = self.session.get(roles_url, verify=False)
            roles = roles_response.json()
            logger.info(f"Found {len(roles)} roles")

            # Check for clients
            clients_url = urljoin(
                self.keycloak_url,
                f'/admin/realms/{self.realm_name}/clients'
            )
            clients_response = self.session.get(clients_url, verify=False)
            clients = clients_response.json()
            logger.info(f"Found {len(clients)} clients")

            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error verifying configuration: {e}")
            return False

    def cleanup_realm(self) -> bool:
        """
        Delete the realm and all its configuration.

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            url = urljoin(self.keycloak_url, f'/admin/realms/{self.realm_name}')
            response = self.session.delete(url, verify=False)

            if response.status_code == 204:
                logger.info(f"Realm '{self.realm_name}' deleted successfully")
                return True
            else:
                logger.error(f"Failed to delete realm: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting realm: {e}")
            return False


def load_users_from_file(filepath: str) -> Optional[list]:
    """
    Load user configuration from JSON file.

    Args:
        filepath: Path to JSON file with user configuration

    Returns:
        List of user configurations or None if error
    """
    try:
        with open(filepath, 'r') as f:
            users = json.load(f)
        logger.info(f"Loaded {len(users)} users from {filepath}")
        return users
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {filepath}")
        return None


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Configure Keycloak realm for platform SSO'
    )
    parser.add_argument(
        '--url',
        default=os.getenv('KEYCLOAK_URL', 'http://localhost:8080'),
        help='Keycloak server URL'
    )
    parser.add_argument(
        '--admin',
        default=os.getenv('KEYCLOAK_ADMIN', 'admin'),
        help='Keycloak admin username'
    )
    parser.add_argument(
        '--password',
        default=os.getenv('KEYCLOAK_PASSWORD'),
        help='Keycloak admin password'
    )
    parser.add_argument(
        '--realm',
        default=os.getenv('KEYCLOAK_REALM', 'platform-engineering'),
        help='Realm name'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify existing realm configuration'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Delete the realm'
    )
    parser.add_argument(
        '--users',
        help='JSON file with user configurations'
    )

    args = parser.parse_args()

    if not args.password:
        print("Error: Keycloak admin password not provided")
        print("Set KEYCLOAK_PASSWORD environment variable or use --password")
        sys.exit(1)

    # Suppress SSL warnings for self-signed certificates
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Initialize realm manager
    realm_manager = KeycloakRealm(
        keycloak_url=args.url,
        admin_user=args.admin,
        admin_password=args.password,
        realm_name=args.realm
    )

    # Authenticate
    if not realm_manager.authenticate():
        logger.error("Failed to authenticate with Keycloak")
        sys.exit(1)

    # Handle different operations
    if args.cleanup:
        if realm_manager.cleanup_realm():
            logger.info("Cleanup completed successfully")
            sys.exit(0)
        else:
            logger.error("Cleanup failed")
            sys.exit(1)

    elif args.verify:
        if realm_manager.verify_configuration():
            logger.info("Configuration verification completed")
            sys.exit(0)
        else:
            logger.error("Configuration verification failed")
            sys.exit(1)

    else:
        # Default: create realm and configure
        logger.info(f"Configuring Keycloak realm: {args.realm}")

        # Create realm
        if not realm_manager.create_realm():
            logger.error("Failed to create realm")
            sys.exit(1)

        # Create OAuth client
        client_id = realm_manager.create_oauth_client()
        if not client_id:
            logger.warning("Failed to create OAuth client")

        # Create roles
        if not realm_manager.create_roles():
            logger.warning("Failed to create roles")

        # Load and create users if file provided
        if args.users:
            users = load_users_from_file(args.users)
            if users:
                realm_manager.create_users(users)

        # Verify configuration
        if realm_manager.verify_configuration():
            logger.info("Realm configuration completed successfully")
            sys.exit(0)
        else:
            logger.warning("Realm created but verification failed")
            sys.exit(1)


if __name__ == '__main__':
    main()
