#!/usr/bin/env python3
"""
Backstage Catalog Entity Registration Script

This script discovers and registers catalog entities from GitHub repositories
into a Backstage instance. It supports batch registration, validation, and
error handling with retry logic.

Usage:
    python3 register-catalog-entities.py --backstage-url http://localhost:7007 \
        --token YOUR_API_TOKEN --github-org your-organization \
        --github-token YOUR_GITHUB_TOKEN
"""

import argparse
import json
import sys
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class CatalogEntityRegistrar:
    """
    Manages registration of catalog entities with Backstage.
    
    Attributes:
        backstage_url: Base URL of Backstage instance
        api_token: Authentication token for Backstage API
        github_token: Authentication token for GitHub API
        max_retries: Maximum number of retry attempts
        retry_delay: Delay in seconds between retries
    """
    
    def __init__(
        self,
        backstage_url: str,
        api_token: str,
        github_token: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        """
        Initialize the catalog registrar.
        
        Args:
            backstage_url: Base URL of Backstage instance
            api_token: Authentication token for Backstage API
            github_token: Authentication token for GitHub API
            max_retries: Maximum number of retry attempts
            retry_delay: Delay in seconds between retries
        """
        self.backstage_url = backstage_url.rstrip('/')
        self.api_token = api_token
        self.github_token = github_token
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.registered_entities = []
        self.failed_entities = []
    
    def _make_api_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        retry: bool = True
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the Backstage API.
        
        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            endpoint: API endpoint path
            data: Request body data
            retry: Whether to retry on failure
            
        Returns:
            Response JSON data
            
        Raises:
            HTTPError: If API request fails after retries
        """
        url = urljoin(self.backstage_url, endpoint)
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
        }
        
        request_data = None
        if data:
            request_data = json.dumps(data).encode('utf-8')
        
        for attempt in range(self.max_retries if retry else 1):
            try:
                req = Request(url, data=request_data, headers=headers, method=method)
                with urlopen(req) as response:
                    return json.loads(response.read().decode('utf-8'))
            except HTTPError as e:
                if e.code in [429, 500, 502, 503]:  # Retryable errors
                    if attempt < self.max_retries - 1:
                        print(f"  Retry {attempt + 1}/{self.max_retries} after {self.retry_delay}s...")
                        time.sleep(self.retry_delay)
                        continue
                raise
            except URLError as e:
                if retry and attempt < self.max_retries - 1:
                    print(f"  Connection error, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
                raise
        
        raise Exception(f"Failed to connect to {url}")
    
    def register_entity(self, catalog_info_url: str) -> bool:
        """
        Register a single catalog entity with Backstage.
        
        Args:
            catalog_info_url: URL to catalog-info.yaml file
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            print(f"Registering entity from: {catalog_info_url}")
            
            # Register the entity location with Backstage
            response = self._make_api_request(
                'POST',
                '/api/catalog/locations',
                {
                    'type': 'url',
                    'target': catalog_info_url,
                }
            )
            
            location_id = response.get('id')
            print(f"  Successfully registered entity (ID: {location_id})")
            self.registered_entities.append({
                'url': catalog_info_url,
                'location_id': location_id
            })
            return True
            
        except HTTPError as e:
            if e.code == 409:  # Conflict - entity already exists
                print(f"  Entity already registered")
                self.registered_entities.append({'url': catalog_info_url})
                return True
            else:
                print(f"  Error registering entity: HTTP {e.code}")
                self.failed_entities.append({
                    'url': catalog_info_url,
                    'error': str(e)
                })
                return False
        except Exception as e:
            print(f"  Error registering entity: {e}")
            self.failed_entities.append({
                'url': catalog_info_url,
                'error': str(e)
            })
            return False
    
    def discover_github_entities(
        self,
        org: str,
        repo: Optional[str] = None
    ) -> List[str]:
        """
        Discover catalog-info.yaml files in GitHub organization repositories.
        
        Args:
            org: GitHub organization name
            repo: Specific repository name (optional)
            
        Returns:
            List of catalog-info.yaml URLs
        """
        catalog_urls = []
        
        try:
            print(f"Discovering entities in GitHub org: {org}")
            
            if repo:
                # Search in specific repository
                catalog_url = (
                    f"https://raw.githubusercontent.com/{org}/{repo}/main/catalog-info.yaml"
                )
                catalog_urls.append(catalog_url)
            else:
                # Search in all repositories (requires GitHub API)
                print("  Note: Full repo discovery requires GitHub API implementation")
                print("  Provide --repo flag to register specific repositories")
            
            return catalog_urls
            
        except Exception as e:
            print(f"Error discovering entities: {e}")
            return catalog_urls
    
    def register_entities_from_file(self, file_path: str) -> None:
        """
        Register multiple catalog entities from a file.
        
        File format: One URL per line
        
        Args:
            file_path: Path to file containing catalog-info.yaml URLs
        """
        try:
            with open(file_path, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            print(f"Registering {len(urls)} entities from {file_path}")
            for url in urls:
                self.register_entity(url)
                
        except FileNotFoundError:
            print(f"Error: File not found: {file_path}")
        except Exception as e:
            print(f"Error reading file: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of registration results.
        
        Returns:
            Dictionary with summary statistics
        """
        return {
            'total_registered': len(self.registered_entities),
            'total_failed': len(self.failed_entities),
            'registered': self.registered_entities,
            'failed': self.failed_entities
        }
    
    def print_summary(self) -> None:
        """Print summary of registration results."""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("REGISTRATION SUMMARY")
        print("=" * 60)
        print(f"Successfully Registered: {summary['total_registered']}")
        print(f"Failed: {summary['total_failed']}")
        
        if summary['failed']:
            print("\nFailed Registrations:")
            for failed in summary['failed']:
                print(f"  - {failed['url']}")
                print(f"    Error: {failed['error']}")
        
        print("=" * 60 + "\n")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Register catalog entities with Backstage'
    )
    parser.add_argument(
        '--backstage-url',
        required=True,
        help='Base URL of Backstage instance'
    )
    parser.add_argument(
        '--token',
        required=True,
        help='Backstage API authentication token'
    )
    parser.add_argument(
        '--github-token',
        help='GitHub API authentication token'
    )
    parser.add_argument(
        '--github-org',
        help='GitHub organization to discover entities from'
    )
    parser.add_argument(
        '--repo',
        help='Specific repository name'
    )
    parser.add_argument(
        '--entity-url',
        help='Single catalog-info.yaml URL to register'
    )
    parser.add_argument(
        '--file',
        help='File containing catalog-info.yaml URLs (one per line)'
    )
    parser.add_argument(
        '--output',
        help='Output file for registration results (JSON format)'
    )
    
    args = parser.parse_args()
    
    # Initialize registrar
    registrar = CatalogEntityRegistrar(
        backstage_url=args.backstage_url,
        api_token=args.token,
        github_token=args.github_token
    )
    
    # Register entities based on provided arguments
    if args.entity_url:
        registrar.register_entity(args.entity_url)
    elif args.file:
        registrar.register_entities_from_file(args.file)
    elif args.github_org:
        urls = registrar.discover_github_entities(args.github_org, args.repo)
        for url in urls:
            registrar.register_entity(url)
    else:
        parser.print_help()
        sys.exit(1)
    
    # Print summary
    registrar.print_summary()
    
    # Save results if output file specified
    if args.output:
        summary = registrar.get_summary()
        with open(args.output, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Results saved to: {args.output}")
    
    # Exit with error code if any registrations failed
    if registrar.failed_entities:
        sys.exit(1)


if __name__ == '__main__':
    main()

