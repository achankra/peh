#!/usr/bin/env python3
"""
Developer Portal Evaluation Framework

This tool evaluates different developer portal solutions against configurable
criteria with weighted scoring. It provides a structured methodology for
comparing portal features, community support, and architectural requirements.

Usage:
    python3 portal-evaluation-framework.py --portals backstage keycloak argocd
    python3 portal-evaluation-framework.py --output-format json
    python3 portal-evaluation-framework.py --add-custom-criteria "Custom Feature:8"
"""

import argparse
import json
import sys
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict


@dataclass
class Criterion:
    """Represents an evaluation criterion."""
    name: str
    weight: float
    description: str
    max_score: float = 10.0


@dataclass
class PortalScore:
    """Represents a portal's score for a single criterion."""
    criterion: str
    score: float
    notes: str = ""


class PortalEvaluationFramework:
    """
    Framework for evaluating and comparing developer portal solutions.
    
    Attributes:
        criteria: Dictionary of evaluation criteria with weights
        portals: Dictionary of portal configurations and scores
    """
    
    def __init__(self):
        """Initialize the evaluation framework with default criteria."""
        self.criteria: Dict[str, Criterion] = self._initialize_default_criteria()
        self.portals: Dict[str, Dict[str, Any]] = {}
        self.scores: Dict[str, List[PortalScore]] = {}
    
    def _initialize_default_criteria(self) -> Dict[str, Criterion]:
        """
        Initialize default evaluation criteria.
        
        Returns:
            Dictionary of Criterion objects
        """
        return {
            'extensibility': Criterion(
                name='Extensibility',
                weight=0.25,
                description='Ability to extend with custom plugins and integrations'
            ),
            'community': Criterion(
                name='Community Support',
                weight=0.20,
                description='Active community, documentation, and ecosystem'
            ),
            'sso_support': Criterion(
                name='SSO/Auth Support',
                weight=0.20,
                description='Support for OAuth, SAML, Keycloak, and other SSO providers'
            ),
            'catalog': Criterion(
                name='Catalog Management',
                weight=0.20,
                description='Service catalog features, entity management, and discovery'
            ),
            'templates': Criterion(
                name='Templates & Scaffolding',
                weight=0.15,
                description='Support for project templates and code generation'
            ),
        }
    
    def add_criterion(
        self,
        key: str,
        name: str,
        weight: float,
        description: str
    ) -> None:
        """
        Add a custom evaluation criterion.
        
        Args:
            key: Unique identifier for the criterion
            name: Display name
            weight: Weight in overall scoring (will be normalized)
            description: Description of what is being evaluated
        """
        self.criteria[key] = Criterion(
            name=name,
            weight=weight,
            description=description
        )
        self._normalize_weights()
    
    def _normalize_weights(self) -> None:
        """Normalize criterion weights to sum to 1.0."""
        total_weight = sum(c.weight for c in self.criteria.values())
        if total_weight > 0:
            for criterion in self.criteria.values():
                criterion.weight = criterion.weight / total_weight
    
    def register_portal(
        self,
        name: str,
        description: str,
        website: str,
        open_source: bool = True
    ) -> None:
        """
        Register a portal solution for evaluation.
        
        Args:
            name: Portal name
            description: Brief description
            website: Website or documentation URL
            open_source: Whether the solution is open source
        """
        self.portals[name.lower()] = {
            'name': name,
            'description': description,
            'website': website,
            'open_source': open_source,
            'scores': {}
        }
    
    def score_portal(
        self,
        portal_name: str,
        criterion_key: str,
        score: float,
        notes: str = ""
    ) -> None:
        """
        Score a portal on a specific criterion.
        
        Args:
            portal_name: Name of the portal
            criterion_key: Criterion identifier
            score: Score (0-10)
            notes: Additional notes about the score
        """
        portal_key = portal_name.lower()
        
        if portal_key not in self.portals:
            print(f"Warning: Portal '{portal_name}' not registered")
            return
        
        if criterion_key not in self.criteria:
            print(f"Warning: Criterion '{criterion_key}' not found")
            return
        
        # Clamp score between 0 and 10
        clamped_score = max(0, min(10, score))
        
        self.portals[portal_key]['scores'][criterion_key] = {
            'score': clamped_score,
            'notes': notes
        }
    
    def calculate_total_score(self, portal_name: str) -> Tuple[float, Dict[str, float]]:
        """
        Calculate total weighted score for a portal.
        
        Args:
            portal_name: Name of the portal
            
        Returns:
            Tuple of (total_score, breakdown_by_criterion)
        """
        portal_key = portal_name.lower()
        
        if portal_key not in self.portals:
            return 0, {}
        
        portal = self.portals[portal_key]
        total_score = 0
        breakdown = {}
        
        for criterion_key, criterion in self.criteria.items():
            if criterion_key in portal['scores']:
                score = portal['scores'][criterion_key]['score']
                weighted_score = score * criterion.weight
                breakdown[criterion.name] = weighted_score
                total_score += weighted_score
        
        return total_score, breakdown
    
    def get_portal_summary(self, portal_name: str) -> Dict[str, Any]:
        """
        Get detailed evaluation summary for a portal.
        
        Args:
            portal_name: Name of the portal
            
        Returns:
            Dictionary with portal information and scores
        """
        portal_key = portal_name.lower()
        
        if portal_key not in self.portals:
            return {}
        
        portal = self.portals[portal_key]
        total_score, breakdown = self.calculate_total_score(portal_name)
        
        return {
            'name': portal['name'],
            'description': portal['description'],
            'website': portal['website'],
            'open_source': portal['open_source'],
            'total_score': round(total_score, 2),
            'score_breakdown': {k: round(v, 2) for k, v in breakdown.items()},
            'criterion_scores': {
                k: {
                    'score': v['score'],
                    'notes': v['notes']
                }
                for k, v in portal['scores'].items()
            }
        }
    
    def compare_portals(self, portal_names: List[str] = None) -> Dict[str, Any]:
        """
        Compare multiple portals and rank them.
        
        Args:
            portal_names: List of portal names to compare (None = all)
            
        Returns:
            Comparison results with rankings
        """
        if not portal_names:
            portal_names = list(self.portals.keys())
        
        results = []
        for name in portal_names:
            summary = self.get_portal_summary(name)
            if summary:
                results.append(summary)
        
        # Sort by total score (descending)
        results.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Add ranking
        for i, result in enumerate(results, 1):
            result['rank'] = i
        
        return {
            'comparison': results,
            'criteria': {
                k: {
                    'name': v.name,
                    'weight': round(v.weight, 3),
                    'description': v.description
                }
                for k, v in self.criteria.items()
            }
        }
    
    def print_comparison_table(self, portal_names: List[str] = None) -> None:
        """
        Print a formatted comparison table.
        
        Args:
            portal_names: List of portal names to compare
        """
        comparison = self.compare_portals(portal_names)
        results = comparison['comparison']
        
        if not results:
            print("No portals to compare")
            return
        
        print("\n" + "=" * 80)
        print("PORTAL EVALUATION COMPARISON")
        print("=" * 80)
        
        # Header
        print(f"\n{'Rank':<5} {'Portal':<20} {'Score':<8} {'Extensibility':<15} {'Community':<12}")
        print("-" * 80)
        
        # Rows
        for result in results:
            rank = result['rank']
            name = result['name'][:20]
            score = result['total_score']
            
            # Get specific scores
            breakdown = result['score_breakdown']
            extensibility = breakdown.get('Extensibility', 0)
            community = breakdown.get('Community Support', 0)
            
            print(f"{rank:<5} {name:<20} {score:<8.2f} {extensibility:<15.2f} {community:<12.2f}")
        
        print("-" * 80)
        
        # Detailed scores
        print("\nDetailed Scores:")
        print("-" * 80)
        
        for result in results:
            print(f"\n{result['rank']}. {result['name']}")
            print(f"   Total Score: {result['total_score']}")
            print(f"   Breakdown:")
            for criterion, score in result['score_breakdown'].items():
                print(f"     - {criterion}: {score:.2f}")
            if result['criterion_scores']:
                print(f"   Notes:")
                for key, details in result['criterion_scores'].items():
                    if details['notes']:
                        print(f"     - {details['notes']}")
        
        print("\n" + "=" * 80 + "\n")
    
    def export_to_json(self, portal_names: List[str] = None) -> str:
        """
        Export comparison results as JSON.
        
        Args:
            portal_names: List of portal names to export
            
        Returns:
            JSON string
        """
        comparison = self.compare_portals(portal_names)
        return json.dumps(comparison, indent=2)


def initialize_default_portals(framework: PortalEvaluationFramework) -> None:
    """
    Register default portal solutions and scores.
    
    Args:
        framework: PortalEvaluationFramework instance
    """
    # Backstage
    framework.register_portal(
        'Backstage',
        'Open source platform from Spotify for building developer platforms',
        'https://backstage.io'
    )
    framework.score_portal('Backstage', 'extensibility', 9.5, 'Highly extensible with plugin system')
    framework.score_portal('Backstage', 'community', 9.0, 'Large community, excellent documentation')
    framework.score_portal('Backstage', 'sso_support', 8.5, 'OIDC, SAML, OAuth support')
    framework.score_portal('Backstage', 'catalog', 9.0, 'Comprehensive service catalog')
    framework.score_portal('Backstage', 'templates', 9.0, 'Scaffolder plugin for templates')
    
    # Keycloak
    framework.register_portal(
        'Keycloak',
        'Open source identity and access management',
        'https://www.keycloak.org'
    )
    framework.score_portal('Keycloak', 'extensibility', 8.0, 'Extensible with providers and themes')
    framework.score_portal('Keycloak', 'community', 8.5, 'Good community support')
    framework.score_portal('Keycloak', 'sso_support', 10.0, 'Complete OIDC, SAML, OAuth support')
    framework.score_portal('Keycloak', 'catalog', 4.0, 'Not a service catalog solution')
    framework.score_portal('Keycloak', 'templates', 3.0, 'Limited to theme customization')
    
    # Gitea
    framework.register_portal(
        'Gitea',
        'Lightweight Git service with web interface',
        'https://gitea.io'
    )
    framework.score_portal('Gitea', 'extensibility', 7.0, 'Plugin system available')
    framework.score_portal('Gitea', 'community', 7.5, 'Active open source community')
    framework.score_portal('Gitea', 'sso_support', 7.5, 'OIDC and OAuth support')
    framework.score_portal('Gitea', 'catalog', 5.0, 'Basic repository management')
    framework.score_portal('Gitea', 'templates', 6.0, 'Limited template capabilities')


def main():
    """Main entry point for the evaluation framework."""
    parser = argparse.ArgumentParser(
        description='Evaluate and compare developer portal solutions'
    )
    parser.add_argument(
        '--portals',
        nargs='+',
        help='Portal names to evaluate (backstage, keycloak, gitea, etc.)'
    )
    parser.add_argument(
        '--output-format',
        choices=['table', 'json'],
        default='table',
        help='Output format for results'
    )
    parser.add_argument(
        '--output-file',
        help='Save results to file'
    )
    parser.add_argument(
        '--add-custom-criteria',
        nargs='+',
        help='Add custom criteria (format: "Name:weight")'
    )
    
    args = parser.parse_args()
    
    # Initialize framework
    framework = PortalEvaluationFramework()
    
    # Add custom criteria
    if args.add_custom_criteria:
        for criterion in args.add_custom_criteria:
            parts = criterion.split(':')
            if len(parts) == 2:
                name, weight = parts
                framework.add_criterion(
                    name.lower().replace(' ', '_'),
                    name,
                    float(weight),
                    f"Custom criterion: {name}"
                )
    
    # Initialize default portals
    initialize_default_portals(framework)
    
    # Determine which portals to compare
    portal_names = args.portals if args.portals else list(framework.portals.keys())
    
    # Generate output
    if args.output_format == 'json':
        output = framework.export_to_json(portal_names)
        print(output)
        
        if args.output_file:
            with open(args.output_file, 'w') as f:
                f.write(output)
    else:
        framework.print_comparison_table(portal_names)
        
        if args.output_file:
            with open(args.output_file, 'w') as f:
                f.write(framework.export_to_json(portal_names))


if __name__ == '__main__':
    main()

