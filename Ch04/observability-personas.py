#!/usr/bin/env python3
"""
Observability Personas Dashboard Generator.

Generates persona-specific dashboard configurations for different platform stakeholders:
- Developer: Application performance, errors, latency (what's my service doing?)
- SRE: Infrastructure health, resource usage, reliability (is the platform healthy?)
- Management: Business metrics, availability, user impact (are we meeting SLAs?)
- Security: CVE tracking, compliance, unauthorized access (are we secure?)

Each persona gets a tailored view of the same observability data through Grafana.

Usage:
    python3 observability-personas.py --output-dir ./dashboards
    python3 observability-personas.py --persona developer --print
"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any


def create_dashboard(title: str, description: str, tags: List[str], panels: List[Dict]) -> Dict:
    """Create a Grafana dashboard JSON structure."""
    return {
        "annotations": {"list": []},
        "editable": True,
        "gnetId": None,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "panels": panels,
        "refresh": "30s",
        "schemaVersion": 38,
        "style": "dark",
        "tags": tags,
        "templating": {"list": []},
        "time": {"from": "now-6h", "to": "now"},
        "timepicker": {},
        "timezone": "",
        "title": title,
        "description": description,
        "version": 1
    }


def create_panel(
    id: int,
    title: str,
    queries: List[str],
    position: tuple,
    viz_type: str = "timeseries"
) -> Dict:
    """Create a dashboard panel."""
    height, width, x, y = position
    targets = [
        {"expr": query, "refId": chr(65 + i), "legendFormat": title}
        for i, query in enumerate(queries)
    ]
    
    return {
        "datasource": "Prometheus",
        "fieldConfig": {
            "defaults": {"color": {"mode": "palette-classic"}, "custom": {}},
            "overrides": []
        },
        "gridPos": {"h": height, "w": width, "x": x, "y": y},
        "id": id,
        "targets": targets,
        "title": title,
        "type": viz_type
    }


class PersonaGenerator:
    """Generate persona-specific observability dashboards."""
    
    @staticmethod
    def developer_dashboard() -> Dict:
        """
        Developer Persona Dashboard.
        
        Focus: Application performance, debugging, error tracing
        Questions: What's my service doing? Why is it slow? What went wrong?
        """
        panels = [
            create_panel(
                1,
                "Request Latency by Endpoint",
                [
                    "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job=~'.*app.*'}[5m]))",
                    "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{job=~'.*app.*'}[5m]))"
                ],
                (8, 12, 0, 0)
            ),
            create_panel(
                2,
                "Error Rate by Endpoint",
                [
                    "sum(rate(http_requests_total{status=~'5..', job=~'.*app.*'}[5m])) by (handler)"
                ],
                (8, 12, 12, 0)
            ),
            create_panel(
                3,
                "Request Count",
                [
                    "sum(rate(http_requests_total{job=~'.*app.*'}[5m])) by (handler)"
                ],
                (8, 12, 0, 8)
            ),
            create_panel(
                4,
                "Response Size Distribution",
                [
                    "histogram_quantile(0.95, rate(http_response_size_bytes_bucket{job=~'.*app.*'}[5m]))"
                ],
                (8, 12, 12, 8)
            ),
            create_panel(
                5,
                "Database Query Latency",
                [
                    "histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))"
                ],
                (8, 12, 0, 16)
            ),
            create_panel(
                6,
                "Cache Hit Rate",
                [
                    "rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))"
                ],
                (8, 12, 12, 16)
            ),
        ]
        
        return create_dashboard(
            "Developer Dashboard - Application Metrics",
            "Debug and optimize your application performance. View latency, errors, and resource usage by endpoint.",
            ["developer", "application", "debug"],
            panels
        )
    
    @staticmethod
    def sre_dashboard() -> Dict:
        """
        SRE Persona Dashboard.
        
        Focus: Infrastructure health, reliability, resource utilization
        Questions: Is the platform healthy? Are we meeting SLAs? What's failing?
        """
        panels = [
            create_panel(
                1,
                "Pod Availability",
                [
                    "sum(rate(kubelet_running_pods[5m])) / sum(kube_node_status_allocatable{resource='pods'})"
                ],
                (8, 12, 0, 0)
            ),
            create_panel(
                2,
                "Node Resource Utilization",
                [
                    "100 * (1 - avg(rate(node_cpu_seconds_total{mode='idle'}[5m])))",
                    "100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))"
                ],
                (8, 12, 12, 0)
            ),
            create_panel(
                3,
                "Service Error Rate (1 min)",
                [
                    "sum(rate(http_requests_total{status=~'5..'}[1m])) by (job) / sum(rate(http_requests_total[1m])) by (job)"
                ],
                (8, 12, 0, 8)
            ),
            create_panel(
                4,
                "P99 Latency SLA Compliance",
                [
                    "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) < 1.0"
                ],
                (8, 12, 12, 8)
            ),
            create_panel(
                5,
                "Pod Restart Rate",
                [
                    "sum(rate(kube_pod_container_status_restarts_total[5m])) by (namespace)"
                ],
                (8, 12, 0, 16)
            ),
            create_panel(
                6,
                "Persistent Volume Usage",
                [
                    "kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes"
                ],
                (8, 12, 12, 16)
            ),
        ]
        
        return create_dashboard(
            "SRE Dashboard - Platform Health",
            "Monitor platform reliability and resource utilization. Track SLA compliance and incident metrics.",
            ["sre", "infrastructure", "reliability"],
            panels
        )
    
    @staticmethod
    def management_dashboard() -> Dict:
        """
        Management Persona Dashboard.
        
        Focus: Business metrics, SLA compliance, user impact
        Questions: Are we meeting our commitments? What's the business impact?
        """
        panels = [
            create_panel(
                1,
                "Service Availability (SLA)",
                [
                    "sum(rate(http_requests_total{status=~'2..'}[5m])) / sum(rate(http_requests_total[5m]))"
                ],
                (8, 12, 0, 0)
            ),
            create_panel(
                2,
                "Mean Time To Recovery (MTTR)",
                [
                    "histogram_quantile(0.95, incident_duration_seconds)"
                ],
                (8, 12, 12, 0)
            ),
            create_panel(
                3,
                "Request Volume (Business Transaction)",
                [
                    "sum(rate(http_requests_total{status='200'}[5m]))"
                ],
                (8, 12, 0, 8)
            ),
            create_panel(
                4,
                "Critical Incidents (30 days)",
                [
                    "sum(incidents_critical_total[30d])"
                ],
                (8, 12, 12, 8)
            ),
            create_panel(
                5,
                "Revenue Impact Hours",
                [
                    "sum(revenue_impact_seconds{severity='critical'} / 3600)"
                ],
                (8, 12, 0, 16)
            ),
            create_panel(
                6,
                "Customer Reported Issues",
                [
                    "customer_reported_issues_total"
                ],
                (8, 12, 12, 16)
            ),
        ]
        
        return create_dashboard(
            "Management Dashboard - Business Impact",
            "Executive view of service health and business metrics. Monitor SLA compliance, incidents, and revenue impact.",
            ["management", "business", "executive"],
            panels
        )
    
    @staticmethod
    def security_dashboard() -> Dict:
        """
        Security Persona Dashboard.
        
        Focus: CVE tracking, compliance, unauthorized access, vulnerability management
        Questions: Are we secure? What vulnerabilities exist? Is there suspicious activity?
        """
        panels = [
            create_panel(
                1,
                "Critical CVEs in Production",
                [
                    "cve_severity_critical_count"
                ],
                (8, 12, 0, 0)
            ),
            create_panel(
                2,
                "Vulnerability Scan Results",
                [
                    "image_vulnerability_count{severity=~'CRITICAL|HIGH'}"
                ],
                (8, 12, 12, 0)
            ),
            create_panel(
                3,
                "Unauthorized Access Attempts (401)",
                [
                    "sum(rate(http_requests_total{status='401'}[5m])) by (source_ip)"
                ],
                (8, 12, 0, 8)
            ),
            create_panel(
                4,
                "Suspicious API Activity (403/404)",
                [
                    "sum(rate(http_requests_total{status=~'403|404'}[5m])) by (endpoint)"
                ],
                (8, 12, 12, 8)
            ),
            create_panel(
                5,
                "Compliance Status",
                [
                    "compliance_check_pass_rate{framework=~'PCI-DSS|SOC2|ISO27001'}"
                ],
                (8, 12, 0, 16)
            ),
            create_panel(
                6,
                "Container Image Scan Coverage",
                [
                    "container_images_scanned / container_images_total"
                ],
                (8, 12, 12, 16)
            ),
        ]
        
        return create_dashboard(
            "Security Dashboard - CVE & Compliance",
            "Security and compliance monitoring. Track vulnerabilities, unauthorized access, and compliance status.",
            ["security", "compliance", "cve"],
            panels
        )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate observability dashboards for different personas"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./dashboards"),
        help="Output directory for dashboard JSON files"
    )
    parser.add_argument(
        "--persona",
        choices=["developer", "sre", "management", "security", "all"],
        default="all",
        help="Generate dashboard for specific persona or all"
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="Print dashboard JSON to stdout instead of writing to file"
    )
    
    args = parser.parse_args()
    
    # Create generators
    personas = {
        "developer": PersonaGenerator.developer_dashboard(),
        "sre": PersonaGenerator.sre_dashboard(),
        "management": PersonaGenerator.management_dashboard(),
        "security": PersonaGenerator.security_dashboard(),
    }
    
    # Generate dashboards
    if args.persona == "all":
        selected_personas = personas
    else:
        selected_personas = {args.persona: personas[args.persona]}
    
    for name, dashboard in selected_personas.items():
        if args.print:
            print(json.dumps(dashboard, indent=2))
        else:
            # Create output directory
            args.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Write dashboard file
            output_file = args.output_dir / f"dashboard-{name}.json"
            with open(output_file, "w") as f:
                json.dump(dashboard, f, indent=2)
            
            print(f"Generated: {output_file}", file=sys.stderr)
            print(f"Prometheus data source: {dashboard['title']}", file=sys.stderr)
            print(f"  - Persona: {name}", file=sys.stderr)
            print(f"  - Tags: {', '.join(dashboard['tags'])}", file=sys.stderr)
            print(f"  - Panels: {len(dashboard['panels'])}", file=sys.stderr)
            print()
    
    if not args.print:
        print(f"\nAll dashboards generated in {args.output_dir}", file=sys.stderr)
        print("\nImport into Grafana:", file=sys.stderr)
        print("  1. Open Grafana: http://localhost:3000", file=sys.stderr)
        print("  2. Go to: Dashboards → New → Import", file=sys.stderr)
        print("  3. Upload each JSON file from the dashboards directory", file=sys.stderr)


if __name__ == "__main__":
    main()

