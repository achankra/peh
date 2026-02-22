#!/usr/bin/env python3
"""
Team Topology Generator

Generates a text/markdown visualization of team topology showing:
- Platform team organization and responsibilities
- Stream-aligned teams and their interaction with the platform
- Interaction modes (collaboration, communication, facilitation)

This implements Team Topologies concepts from Chapter 1.

Usage:
    python team-topology-generator.py

Output:
    Markdown/text visualization of team structure and interactions.
"""

from typing import Dict, List


class TeamTopologyGenerator:
    """Generate team topology visualizations."""

    def __init__(self):
        """Initialize team topology data."""
        self.platform_team = {
            "name": "Platform Team",
            "size": 8,
            "members": [
                {"role": "Platform Lead", "focus": "Strategy & Roadmap"},
                {"role": "Backend Engineer", "focus": "Platform Services"},
                {"role": "Backend Engineer", "focus": "Platform Services"},
                {"role": "DevOps Engineer", "focus": "Infrastructure & Deployment"},
                {"role": "DevOps Engineer", "focus": "Infrastructure & Deployment"},
                {"role": "Security Engineer", "focus": "Security & Compliance"},
                {
                    "role": "Developer Advocate",
                    "focus": "Documentation & Support",
                },
                {"role": "Data Engineer", "focus": "Observability & Analytics"},
            ],
            "responsibilities": [
                "Develop and maintain platform services",
                "Define golden paths and standards",
                "Operate infrastructure",
                "Support stream-aligned teams",
                "Drive platform adoption",
            ],
        }

        self.stream_aligned_teams = [
            {
                "name": "Payments Team",
                "size": 6,
                "products": ["Payment Processing", "Billing"],
            },
            {
                "name": "User Management Team",
                "size": 5,
                "products": ["Authentication", "Authorization", "User Profiles"],
            },
            {"name": "Analytics Team", "size": 4, "products": ["Analytics", "Reporting"]},
            {
                "name": "Notifications Team",
                "size": 3,
                "products": ["Email", "SMS", "Push Notifications"],
            },
        ]

        self.interaction_modes = {
            "collaboration": {
                "description": "Working together on shared problems",
                "duration": "Ongoing",
                "frequency": "2-3 times per week",
            },
            "communication": {
                "description": "Asynchronous information sharing",
                "duration": "As needed",
                "frequency": "Daily updates",
            },
            "facilitation": {
                "description": "Platform team facilitates, but stream-aligned team executes",
                "duration": "Short-term",
                "frequency": "1-2 times per week",
            },
        }

    def generate_platform_team_chart(self) -> str:
        """Generate ASCII chart of platform team structure."""
        chart = "\nPlatform Team Structure\n"
        chart += "=" * 50 + "\n\n"
        chart += "Platform Lead\n"
        chart += "  ├── Backend Engineers (2)\n"
        chart += "  ├── DevOps Engineers (2)\n"
        chart += "  ├── Security Engineer\n"
        chart += "  ├── Developer Advocate\n"
        chart += "  └── Data Engineer\n\n"

        return chart

    def generate_team_details(self) -> str:
        """Generate detailed team information."""
        details = "Team Details\n"
        details += "=" * 50 + "\n\n"

        details += f"**{self.platform_team['name']}** (Size: {self.platform_team['size']})\n\n"

        details += "Members by Role:\n"
        for member in self.platform_team["members"]:
            details += f"  - {member['role']}: {member['focus']}\n"

        details += "\nResponsibilities:\n"
        for resp in self.platform_team["responsibilities"]:
            details += f"  - {resp}\n"

        details += "\n" + "-" * 50 + "\n\n"

        details += "Stream-Aligned Teams:\n\n"
        for i, team in enumerate(self.stream_aligned_teams, 1):
            details += f"{i}. **{team['name']}** (Size: {team['size']})\n"
            details += "   Products:\n"
            for product in team["products"]:
                details += f"     - {product}\n"
            details += "\n"

        return details

    def generate_interaction_matrix(self) -> str:
        """Generate interaction modes matrix."""
        matrix = "\nInteraction Modes Matrix\n"
        matrix += "=" * 50 + "\n\n"

        matrix += "Platform Team ↔ Stream-Aligned Teams\n\n"

        for mode_name, mode_details in self.interaction_modes.items():
            matrix += f"**{mode_name.title()}**\n"
            matrix += f"  Description: {mode_details['description']}\n"
            matrix += f"  Typical Duration: {mode_details['duration']}\n"
            matrix += f"  Frequency: {mode_details['frequency']}\n\n"

        return matrix

    def generate_dependency_diagram(self) -> str:
        """Generate dependency diagram between teams."""
        diagram = "\nTeam Dependencies & Interactions\n"
        diagram += "=" * 50 + "\n\n"

        diagram += """
                    ┌─────────────────────────┐
                    │   Platform Team         │
                    │  (Infrastructure & SRE) │
                    └──────────┬──────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
      ┌─────────▼────┐  ┌─────▼──────┐  ┌───▼─────────┐
      │ Payments     │  │ User Mgmt   │  │ Analytics   │
      │ Team         │  │ Team        │  │ Team        │
      └──────────────┘  └─────────────┘  └─────────────┘

Interaction Modes:
  ━━━ Collaboration (ongoing partnership)
  - - Communication (async updates)
  ··· Facilitation (platform enables)
"""

        return diagram

    def generate_platform_services(self) -> str:
        """Generate list of platform services."""
        services = "\nPlatform Services & Capabilities\n"
        services += "=" * 50 + "\n\n"

        services_list = {
            "Compute & Orchestration": [
                "Kubernetes cluster management",
                "Container registry",
                "Deployment automation",
            ],
            "CI/CD": [
                "Build pipelines",
                "Test automation",
                "Release workflows",
                "Deployment gates",
            ],
            "Networking & Security": [
                "Service mesh (Istio)",
                "Network policies",
                "API gateway",
                "WAF & DDoS protection",
            ],
            "Observability": [
                "Metrics collection (Prometheus)",
                "Centralized logging (ELK)",
                "Distributed tracing (Jaeger)",
                "Alerting & on-call management",
            ],
            "Data & Storage": [
                "Managed PostgreSQL",
                "Cache layer (Redis)",
                "Message queue (Kafka)",
                "Object storage (S3)",
            ],
            "Developer Experience": [
                "Internal Developer Portal",
                "Service templates",
                "Golden paths",
                "Documentation",
            ],
        }

        for category, items in services_list.items():
            services += f"\n**{category}**\n"
            for item in items:
                services += f"  • {item}\n"

        return services

    def generate_interaction_examples(self) -> str:
        """Generate examples of typical interactions."""
        examples = "\nTypical Interaction Examples\n"
        examples += "=" * 50 + "\n\n"

        interactions = [
            {
                "type": "Collaboration",
                "scenario": "Payments team needs new encryption requirement",
                "interaction": "Platform & Payments teams co-design solution, implement together",
                "outcome": "New security capability available to all teams",
            },
            {
                "type": "Communication",
                "scenario": "Platform deploys new monitoring dashboard",
                "interaction": "Platform sends async notification with new feature details",
                "outcome": "Teams adopt dashboard at their own pace",
            },
            {
                "type": "Facilitation",
                "scenario": "Analytics team needs to deploy new service",
                "interaction": "Platform provides template, docs, examples; team executes",
                "outcome": "Analytics team self-serves deployment with platform support",
            },
            {
                "type": "Facilitation",
                "scenario": "User team requests new database feature",
                "interaction": "Platform enables feature, provides examples and docs",
                "outcome": "User team can leverage feature independently",
            },
        ]

        for i, interaction in enumerate(interactions, 1):
            examples += f"{i}. **{interaction['type']}** Mode\n"
            examples += f"   Scenario: {interaction['scenario']}\n"
            examples += f"   Interaction: {interaction['interaction']}\n"
            examples += f"   Outcome: {interaction['outcome']}\n\n"

        return examples

    def generate_metrics(self) -> str:
        """Generate platform metrics and KPIs."""
        metrics = "\nPlatform Metrics & KPIs\n"
        metrics += "=" * 50 + "\n\n"

        kpis = {
            "Velocity": [
                "Deployment frequency: >= 1x/day",
                "Lead time for changes: < 1 hour",
                "Mean time to recovery: < 15 minutes",
            ],
            "Quality": [
                "Change failure rate: < 15%",
                "Availability: >= 99.9%",
                "Test coverage: >= 80%",
            ],
            "Adoption": [
                "Teams using golden paths: >= 80%",
                "Platform feature adoption: >= 75%",
                "Self-service fulfillment: >= 95%",
            ],
            "Satisfaction": [
                "Developer satisfaction (NPS): >= 50",
                "Platform support feedback: >= 4/5",
                "Time to support: < 1 hour",
            ],
        }

        for category, items in kpis.items():
            metrics += f"**{category}**\n"
            for item in items:
                metrics += f"  • {item}\n"
            metrics += "\n"

        return metrics

    def generate_full_report(self) -> str:
        """Generate complete team topology report."""
        report = "\n" + "=" * 70 + "\n"
        report += "TEAM TOPOLOGY REPORT\n"
        report += "=" * 70

        report += self.generate_platform_team_chart()
        report += self.generate_team_details()
        report += self.generate_interaction_matrix()
        report += self.generate_dependency_diagram()
        report += self.generate_platform_services()
        report += self.generate_interaction_examples()
        report += self.generate_metrics()

        report += "\n" + "=" * 70 + "\n"
        report += "RECOMMENDATIONS\n"
        report += "=" * 70 + "\n\n"

        report += """
1. **Establish Interaction Patterns**
   - Define clear interaction modes with each stream-aligned team
   - Document SLAs for each interaction type
   - Schedule regular sync-ups during collaboration periods

2. **Create Feedback Loops**
   - Conduct quarterly surveys with stream-aligned teams
   - Review platform metrics monthly
   - Adjust priorities based on team feedback

3. **Invest in Developer Experience**
   - Build and maintain internal developer portal
   - Provide excellent documentation
   - Offer training and office hours

4. **Scale Responsibly**
   - As platform grows, consider sub-teams
   - Establish clear escalation paths
   - Document runbooks for common issues

5. **Measure Success**
   - Track metrics regularly
   - Share reports with stakeholders
   - Use data to drive decisions

"""

        report += "=" * 70 + "\n"

        return report


if __name__ == "__main__":
    # Example usage
    generator = TeamTopologyGenerator()
    report = generator.generate_full_report()
    print(report)
