#!/usr/bin/env python3
"""
Platform Maturity Assessment Tool

This tool helps engineering teams evaluate their platform maturity across
key dimensions using a questionnaire-based approach. It provides scoring
and generates a maturity report showing areas of strength and improvement.

The assessment covers four core dimensions:
- Self-Service: Degree of automation and self-service capabilities
- Observability: Monitoring, logging, and visibility
- Security: Security practices and controls
- DevEx: Developer experience and ease of use

Usage:
    python platform-maturity-assessment.py

The tool will guide you through questions and calculate maturity scores.
"""

import json
from typing import Dict, List, Tuple


class PlatformMaturityAssessment:
    """Assess platform maturity across multiple dimensions."""

    def __init__(self):
        """Initialize the assessment with dimension definitions."""
        self.dimensions = {
            "self-service": {
                "name": "Self-Service Capabilities",
                "description": "Ability for teams to provision and manage resources independently",
                "questions": [
                    "Can teams provision new environments without platform team assistance?",
                    "Is there an internal developer portal or self-service catalog?",
                    "Can teams deploy applications without manual process steps?",
                    "Are provisioning policies automated and enforced?",
                    "Do teams have clear documentation for common self-service tasks?",
                ],
            },
            "observability": {
                "name": "Observability",
                "description": "Visibility into platform health, performance, and issues",
                "questions": [
                    "Do you have centralized logging across all platform components?",
                    "Is platform health visible through dashboards?",
                    "Can you trace requests across service boundaries?",
                    "Do you have alerting for critical platform issues?",
                    "Can teams easily debug issues in production?",
                ],
            },
            "security": {
                "name": "Security & Compliance",
                "description": "Security practices, controls, and compliance enforcement",
                "questions": [
                    "Are secrets managed securely and rotated regularly?",
                    "Do you have automated security scanning in your CI/CD pipeline?",
                    "Are access controls enforced based on least privilege?",
                    "Do you regularly audit security posture and compliance?",
                    "Are security guardrails baked into the platform?",
                ],
            },
            "devex": {
                "name": "Developer Experience",
                "description": "Ease of use, productivity, and developer satisfaction",
                "questions": [
                    "Is onboarding a new team to the platform straightforward?",
                    "Are platform APIs and tools well-documented?",
                    "Do developers have a good local development experience?",
                    "Are error messages and failures easy to understand?",
                    "Do you regularly gather developer feedback and iterate?",
                ],
            },
        }
        self.scores: Dict[str, float] = {}

    def ask_question(self, question: str, dimension: str) -> int:
        """
        Ask a single question and get a score (1-5).

        Args:
            question: The question to ask
            dimension: The dimension being assessed

        Returns:
            Score from 1 (strongly disagree) to 5 (strongly agree)
        """
        print(f"\n{question}")
        print("  1 = Strongly Disagree")
        print("  2 = Disagree")
        print("  3 = Neutral")
        print("  4 = Agree")
        print("  5 = Strongly Agree")

        while True:
            try:
                score = int(input("Your score (1-5): "))
                if 1 <= score <= 5:
                    return score
                print("Please enter a number between 1 and 5")
            except ValueError:
                print("Please enter a valid number")

    def assess_dimension(self, dimension_key: str) -> float:
        """
        Assess a single dimension by asking all questions.

        Args:
            dimension_key: Key of the dimension to assess

        Returns:
            Average score for the dimension (1-5)
        """
        dimension = self.dimensions[dimension_key]
        print(f"\n{'=' * 70}")
        print(f"Assessing: {dimension['name']}")
        print(f"Description: {dimension['description']}")
        print(f"{'=' * 70}")

        scores = []
        for i, question in enumerate(dimension["questions"], 1):
            score = self.ask_question(f"{i}. {question}", dimension_key)
            scores.append(score)

        average = sum(scores) / len(scores)
        self.scores[dimension_key] = average
        return average

    def run_assessment(self) -> Dict[str, float]:
        """
        Run the complete platform maturity assessment.

        Returns:
            Dictionary of dimension scores
        """
        print("\n" + "=" * 70)
        print("PLATFORM MATURITY ASSESSMENT")
        print("=" * 70)
        print(
            """
This assessment evaluates your platform across four key dimensions.
For each question, rate your agreement on a scale of 1-5.

The assessment typically takes 5-10 minutes to complete.
"""
        )

        for dimension_key in self.dimensions.keys():
            self.assess_dimension(dimension_key)

        return self.scores

    def generate_report(self) -> str:
        """
        Generate a maturity report based on assessment results.

        Returns:
            Formatted report string
        """
        if not self.scores:
            return "No assessment data available. Run assessment first."

        report = "\n" + "=" * 70 + "\n"
        report += "PLATFORM MATURITY ASSESSMENT REPORT\n"
        report += "=" * 70 + "\n\n"

        # Overall score
        overall_score = sum(self.scores.values()) / len(self.scores)
        report += f"Overall Maturity Score: {overall_score:.2f}/5.0\n\n"

        # Maturity level
        if overall_score >= 4.5:
            level = "Optimized"
        elif overall_score >= 3.5:
            level = "Advanced"
        elif overall_score >= 2.5:
            level = "Intermediate"
        elif overall_score >= 1.5:
            level = "Basic"
        else:
            level = "Initial"

        report += f"Maturity Level: {level}\n\n"

        # Dimension scores
        report += "Scores by Dimension:\n"
        report += "-" * 70 + "\n"

        dimensions_sorted = sorted(
            self.scores.items(), key=lambda x: x[1], reverse=True
        )

        for dimension_key, score in dimensions_sorted:
            dimension = self.dimensions[dimension_key]
            bar_length = int(score / 5 * 30)
            bar = "█" * bar_length + "░" * (30 - bar_length)
            report += f"{dimension['name']:<30} {score:>5.2f}/5.0 [{bar}]\n"

        report += "\n" + "-" * 70 + "\n\n"

        # Recommendations
        report += "Recommendations:\n\n"

        lowest_dimension = min(self.scores.items(), key=lambda x: x[1])
        lowest_key, lowest_score = lowest_dimension
        lowest_name = self.dimensions[lowest_key]["name"]

        report += f"1. Priority Area: {lowest_name} (Score: {lowest_score:.2f}/5.0)\n"
        report += (
            "   Focus on improving this dimension as it shows the most opportunity.\n\n"
        )

        for dimension_key, score in dimensions_sorted:
            if score < 3.5:
                dimension = self.dimensions[dimension_key]
                report += f"2. {dimension['name']} (Score: {score:.2f}/5.0)\n"
                report += "   This dimension needs improvement. Review the questions\n"
                report += "   that received low scores and create an action plan.\n\n"

        report += "Next Steps:\n"
        report += "1. Review questions with low scores in each dimension\n"
        report += "2. Identify root causes for gaps\n"
        report += "3. Create improvement roadmap prioritized by impact\n"
        report += "4. Assign owners for each improvement initiative\n"
        report += "5. Schedule follow-up assessment in 3-6 months\n"

        report += "\n" + "=" * 70 + "\n"

        return report

    def export_results(self, filename: str = "assessment_results.json") -> None:
        """
        Export assessment results to JSON file.

        Args:
            filename: Output filename
        """
        results = {
            "scores": self.scores,
            "overall_score": sum(self.scores.values()) / len(self.scores)
            if self.scores
            else 0,
        }

        with open(filename, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\nResults exported to {filename}")


if __name__ == "__main__":
    # Example usage
    assessment = PlatformMaturityAssessment()

    # For demonstration, you can run the assessment interactively
    # or use example data for testing
    try:
        # Uncomment the line below to run interactive assessment
        scores = assessment.run_assessment()

        # Generate and print report
        report = assessment.generate_report()
        print(report)

        # Export results
        assessment.export_results()

    except KeyboardInterrupt:
        print("\n\nAssessment cancelled.")
