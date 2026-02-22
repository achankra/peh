#!/usr/bin/env python3
"""
Chapter 14: Measure AI Impact on Platform Metrics
===================================================
Measures the impact of AI-augmented platform tools on key metrics
including MTTR, alert-to-resolution time, and developer productivity.

Usage:
    python measure-ai-impact.py [--demo]

Prerequisites:
    - Access to incident management data (or use --demo mode)
"""

import json
import sys
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List
import statistics


@dataclass
class Incident:
    """Represents a platform incident with timing data."""
    id: str
    severity: str               # P1, P2, P3
    alert_time: datetime
    ack_time: datetime          # When someone acknowledged
    diagnosis_time: datetime    # When root cause identified
    resolution_time: datetime   # When resolved
    ai_assisted: bool           # Whether AI tools were used


def calculate_mttr(incidents: List[Incident]) -> dict:
    """Calculate Mean Time to Resolution for AI vs non-AI incidents."""
    ai_incidents = [i for i in incidents if i.ai_assisted]
    manual_incidents = [i for i in incidents if not i.ai_assisted]

    def avg_minutes(group, start_attr="alert_time", end_attr="resolution_time"):
        if not group:
            return 0
        deltas = [(getattr(i, end_attr) - getattr(i, start_attr)).total_seconds() / 60 for i in group]
        return statistics.mean(deltas)

    ai_mttr = avg_minutes(ai_incidents)
    manual_mttr = avg_minutes(manual_incidents)
    improvement = ((manual_mttr - ai_mttr) / manual_mttr * 100) if manual_mttr > 0 else 0

    return {
        "ai_assisted_mttr_min": round(ai_mttr, 1),
        "manual_mttr_min": round(manual_mttr, 1),
        "improvement_pct": round(improvement, 1),
        "ai_incident_count": len(ai_incidents),
        "manual_incident_count": len(manual_incidents),
    }


def calculate_alert_to_ack(incidents: List[Incident]) -> dict:
    """Measure alert-to-acknowledgment time (triage speed)."""
    ai = [i for i in incidents if i.ai_assisted]
    manual = [i for i in incidents if not i.ai_assisted]

    def avg_ack(group):
        if not group:
            return 0
        return statistics.mean([(i.ack_time - i.alert_time).total_seconds() / 60 for i in group])

    ai_ack = avg_ack(ai)
    manual_ack = avg_ack(manual)
    improvement = ((manual_ack - ai_ack) / manual_ack * 100) if manual_ack > 0 else 0

    return {
        "ai_avg_ack_min": round(ai_ack, 1),
        "manual_avg_ack_min": round(manual_ack, 1),
        "improvement_pct": round(improvement, 1),
    }


def calculate_diagnosis_speed(incidents: List[Incident]) -> dict:
    """Measure time from ack to diagnosis (root cause identification)."""
    ai = [i for i in incidents if i.ai_assisted]
    manual = [i for i in incidents if not i.ai_assisted]

    def avg_diag(group):
        if not group:
            return 0
        return statistics.mean([(i.diagnosis_time - i.ack_time).total_seconds() / 60 for i in group])

    ai_diag = avg_diag(ai)
    manual_diag = avg_diag(manual)
    improvement = ((manual_diag - ai_diag) / manual_diag * 100) if manual_diag > 0 else 0

    return {
        "ai_avg_diagnosis_min": round(ai_diag, 1),
        "manual_avg_diagnosis_min": round(manual_diag, 1),
        "improvement_pct": round(improvement, 1),
    }


def generate_demo_incidents() -> List[Incident]:
    """Generate realistic demo incident data."""
    base = datetime(2025, 1, 15, 8, 0)
    incidents = []

    # Manual incidents (before AI adoption)
    for i in range(10):
        alert = base + timedelta(days=i * 3, hours=i % 8)
        incidents.append(Incident(
            id=f"INC-{100+i}", severity=["P1", "P2", "P3"][i % 3],
            alert_time=alert,
            ack_time=alert + timedelta(minutes=12 + i * 2),
            diagnosis_time=alert + timedelta(minutes=45 + i * 5),
            resolution_time=alert + timedelta(minutes=90 + i * 10),
            ai_assisted=False,
        ))

    # AI-assisted incidents (after AI adoption)
    ai_base = base + timedelta(days=35)
    for i in range(10):
        alert = ai_base + timedelta(days=i * 3, hours=i % 8)
        incidents.append(Incident(
            id=f"INC-{200+i}", severity=["P1", "P2", "P3"][i % 3],
            alert_time=alert,
            ack_time=alert + timedelta(minutes=3 + i),
            diagnosis_time=alert + timedelta(minutes=12 + i * 2),
            resolution_time=alert + timedelta(minutes=30 + i * 5),
            ai_assisted=True,
        ))

    return incidents


def print_report(incidents: List[Incident]):
    """Print a comprehensive AI impact report."""
    mttr = calculate_mttr(incidents)
    ack = calculate_alert_to_ack(incidents)
    diag = calculate_diagnosis_speed(incidents)

    print("\n" + "=" * 60)
    print("  AI IMPACT ON PLATFORM METRICS")
    print("=" * 60)

    print(f"\n--- Mean Time to Resolution (MTTR) ---")
    print(f"  Manual:      {mttr['manual_mttr_min']} min (n={mttr['manual_incident_count']})")
    print(f"  AI-Assisted: {mttr['ai_assisted_mttr_min']} min (n={mttr['ai_incident_count']})")
    print(f"  Improvement: {mttr['improvement_pct']}%")

    print(f"\n--- Alert-to-Acknowledgment ---")
    print(f"  Manual:      {ack['manual_avg_ack_min']} min")
    print(f"  AI-Assisted: {ack['ai_avg_ack_min']} min")
    print(f"  Improvement: {ack['improvement_pct']}%")

    print(f"\n--- Diagnosis Speed ---")
    print(f"  Manual:      {diag['manual_avg_diagnosis_min']} min")
    print(f"  AI-Assisted: {diag['ai_avg_diagnosis_min']} min")
    print(f"  Improvement: {diag['improvement_pct']}%")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    incidents = generate_demo_incidents()
    print_report(incidents)
