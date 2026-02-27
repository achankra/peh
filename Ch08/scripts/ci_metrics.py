#!/usr/bin/env python3
"""
CI Metrics Collector
Collects CI/CD pipeline metrics from GitHub Actions using the GitHub API.
Metrics include pipeline duration, failure rates, and build performance trends.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

GITHUB_API_BASE = "https://api.github.com"


class CIMetricsCollector:
    """Collect CI/CD metrics from GitHub Actions workflows."""

    def __init__(self, github_token: str, owner: str, repo: str):
        """
        Initialize the metrics collector.

        Args:
            github_token: GitHub API token
            owner: Repository owner
            repo: Repository name
        """
        self.github_token = github_token
        self.owner = owner
        self.repo = repo
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def get_workflow_runs(
        self, workflow_id: str, days_back: int = 7
    ) -> Optional[List[Dict]]:
        """
        Get workflow runs for the past N days.

        Args:
            workflow_id: Workflow ID or filename
            days_back: Number of days to look back

        Returns:
            List of workflow runs
        """
        since_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).isoformat()

        url = (
            f"{GITHUB_API_BASE}/repos/{self.owner}/{self.repo}/"
            f"actions/workflows/{workflow_id}/runs"
        )
        params = {"created": f">={since_date}", "per_page": 100}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get("workflow_runs", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching workflow runs: {e}", file=sys.stderr)
            return None

    def calculate_pipeline_metrics(self, runs: List[Dict]) -> Dict:
        """
        Calculate metrics from workflow runs.

        Args:
            runs: List of workflow runs

        Returns:
            Dictionary with calculated metrics
        """
        if not runs:
            return {
                "total_runs": 0,
                "avg_duration_minutes": 0,
                "success_rate": 0,
                "failure_rate": 0,
            }

        total_runs = len(runs)
        successful_runs = sum(1 for run in runs if run["conclusion"] == "success")
        failed_runs = sum(1 for run in runs if run["conclusion"] == "failure")

        # Calculate average duration in minutes
        durations = []
        for run in runs:
            created = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
            updated = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
            duration_minutes = (updated - created).total_seconds() / 60
            durations.append(duration_minutes)

        avg_duration = sum(durations) / len(durations) if durations else 0
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
        failure_rate = (failed_runs / total_runs * 100) if total_runs > 0 else 0

        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "avg_duration_minutes": round(avg_duration, 2),
            "success_rate_percent": round(success_rate, 2),
            "failure_rate_percent": round(failure_rate, 2),
            "min_duration_minutes": round(min(durations), 2) if durations else 0,
            "max_duration_minutes": round(max(durations), 2) if durations else 0,
        }

    def get_build_performance_trend(
        self, workflow_id: str, days_back: int = 30
    ) -> Dict:
        """
        Get build performance trend over time.

        Args:
            workflow_id: Workflow ID or filename
            days_back: Number of days to analyze

        Returns:
            Dictionary with trend data
        """
        runs = self.get_workflow_runs(workflow_id, days_back)
        if not runs:
            return {"error": "No runs found"}

        # Group runs by date
        daily_stats = {}
        for run in runs:
            created = datetime.fromisoformat(
                run["created_at"].replace("Z", "+00:00")
            )
            date_key = created.strftime("%Y-%m-%d")

            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "durations": [],
                }

            daily_stats[date_key]["total"] += 1
            if run["conclusion"] == "success":
                daily_stats[date_key]["successful"] += 1
            else:
                daily_stats[date_key]["failed"] += 1

            # Calculate duration
            updated = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
            duration_minutes = (updated - created).total_seconds() / 60
            daily_stats[date_key]["durations"].append(duration_minutes)

        # Calculate daily metrics
        trend = {}
        for date_key in sorted(daily_stats.keys()):
            stats = daily_stats[date_key]
            avg_duration = sum(stats["durations"]) / len(stats["durations"])
            success_rate = (stats["successful"] / stats["total"] * 100) if stats["total"] > 0 else 0

            trend[date_key] = {
                "total_runs": stats["total"],
                "successful_runs": stats["successful"],
                "failed_runs": stats["failed"],
                "avg_duration_minutes": round(avg_duration, 2),
                "success_rate_percent": round(success_rate, 2),
            }

        return trend

    def collect_all_metrics(self, workflow_ids: List[str]) -> Dict:
        """
        Collect metrics for all specified workflows.

        Args:
            workflow_ids: List of workflow IDs or filenames

        Returns:
            Dictionary with metrics for all workflows
        """
        all_metrics = {
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "repository": f"{self.owner}/{self.repo}",
            "workflows": {},
        }

        for workflow_id in workflow_ids:
            print(f"Collecting metrics for workflow: {workflow_id}")
            runs = self.get_workflow_runs(workflow_id)
            if runs:
                metrics = self.calculate_pipeline_metrics(runs)
                trend = self.get_build_performance_trend(workflow_id)
                all_metrics["workflows"][workflow_id] = {
                    "current_metrics": metrics,
                    "trend": trend,
                }

        return all_metrics


def main():
    """Main entry point."""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Example usage
    owner = os.getenv("GITHUB_OWNER", "my-org")
    repo = os.getenv("GITHUB_REPO", "my-repo")
    workflows = os.getenv("WORKFLOWS", "").split(",")

    if not workflows or workflows == [""]:
        workflows = ["backend-pipeline.yml", "frontend-pipeline.yml"]

    collector = CIMetricsCollector(github_token, owner, repo)
    metrics = collector.collect_all_metrics(workflows)

    print(json.dumps(metrics, indent=2))

    # Optionally save to file
    output_file = os.getenv("OUTPUT_FILE")
    if output_file:
        with open(output_file, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"Metrics saved to {output_file}")


if __name__ == "__main__":
    main()
