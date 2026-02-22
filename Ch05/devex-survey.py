#!/usr/bin/env python3
"""
Developer Experience (DevEx) Survey Tool

This module implements a CLI survey that collects developer feedback on various
aspects of the platform experience and calculates a composite DevEx score.

Topics Covered:
- Onboarding time and ease
- Deployment friction points
- Documentation quality
- Developer tooling satisfaction
- Feedback loop effectiveness

The tool collects responses on a 1-5 scale and produces a DevEx score (0-100).
"""

import json
import sys
from typing import Dict, List, Tuple


class DevExSurvey:
    """Administers a developer experience survey and calculates metrics."""

    def __init__(self):
        """Initialize the survey with predefined questions."""
        self.responses: Dict[str, int] = {}
        self.questions: List[Tuple[str, str]] = [
            (
                "onboarding_time",
                "How long did it take to set up your local development environment? (1=Days, 5=Minutes)"
            ),
            (
                "onboarding_clarity",
                "How clear were the onboarding instructions? (1=Confusing, 5=Crystal Clear)"
            ),
            (
                "deployment_ease",
                "How easy is it to deploy your changes? (1=Very Difficult, 5=One Command)"
            ),
            (
                "deployment_feedback",
                "How quickly do you get feedback on deployment status? (1=Hours, 5=Seconds)"
            ),
            (
                "documentation_quality",
                "How complete is the platform documentation? (1=Non-existent, 5=Comprehensive)"
            ),
            (
                "documentation_clarity",
                "How clear is the documentation? (1=Confusing, 5=Easy to Follow)"
            ),
            (
                "tooling_satisfaction",
                "How satisfied are you with the developer tools provided? (1=Very Unsatisfied, 5=Very Satisfied)"
            ),
            (
                "api_design",
                "How intuitive is the platform API design? (1=Confusing, 5=Intuitive)"
            ),
            (
                "error_messages",
                "How helpful are error messages? (1=Cryptic, 5=Perfectly Clear)"
            ),
            (
                "feedback_loop",
                "How quickly can you validate changes in production-like environment? (1=Days, 5=Minutes)"
            ),
        ]

    def run_interactive(self) -> None:
        """Run the survey in interactive mode, collecting user responses."""
        print("\n" + "=" * 70)
        print("DEVELOPER EXPERIENCE (DevEx) SURVEY")
        print("=" * 70)
        print("\nThis survey evaluates your experience with the platform.")
        print("Please rate each statement from 1 to 5:\n")

        for index, (key, question) in enumerate(self.questions, 1):
            while True:
                try:
                    print(f"\n[{index}/{len(self.questions)}] {question}")
                    response = input("Your rating (1-5): ").strip()
                    rating = int(response)
                    if 1 <= rating <= 5:
                        self.responses[key] = rating
                        break
                    else:
                        print("Please enter a number between 1 and 5.")
                except ValueError:
                    print("Invalid input. Please enter a number between 1 and 5.")

    def calculate_devex_score(self) -> int:
        """
        Calculate the overall DevEx score.

        Returns:
            int: DevEx score from 0-100
        """
        if not self.responses:
            return 0

        total_possible = len(self.responses) * 5
        total_actual = sum(self.responses.values())
        devex_score = int((total_actual / total_possible) * 100)

        return devex_score

    def calculate_category_scores(self) -> Dict[str, float]:
        """
        Calculate scores by category.

        Returns:
            Dict[str, float]: Category name to score mapping
        """
        if not self.responses:
            return {}

        categories = {
            "Onboarding": ["onboarding_time", "onboarding_clarity"],
            "Deployment": ["deployment_ease", "deployment_feedback"],
            "Documentation": ["documentation_quality", "documentation_clarity"],
            "Developer Tools": ["tooling_satisfaction", "api_design", "error_messages"],
            "Feedback Loops": ["feedback_loop"],
        }

        category_scores = {}
        for category, keys in categories.items():
            relevant_scores = [self.responses[k] for k in keys if k in self.responses]
            if relevant_scores:
                avg_score = sum(relevant_scores) / len(relevant_scores)
                category_scores[category] = round(avg_score, 2)

        return category_scores

    def print_results(self) -> None:
        """Print survey results in a formatted manner."""
        devex_score = self.calculate_devex_score()
        category_scores = self.calculate_category_scores()

        print("\n" + "=" * 70)
        print("SURVEY RESULTS")
        print("=" * 70)

        print(f"\nOverall DevEx Score: {devex_score}/100")

        # Score interpretation
        if devex_score >= 80:
            interpretation = "Excellent - Developer experience is strong"
        elif devex_score >= 60:
            interpretation = "Good - Room for improvement in some areas"
        elif devex_score >= 40:
            interpretation = "Fair - Significant friction points identified"
        else:
            interpretation = "Poor - Critical improvements needed"

        print(f"Interpretation: {interpretation}\n")

        print("Category Breakdown:")
        print("-" * 70)
        for category, score in sorted(category_scores.items(), key=lambda x: x[1]):
            bar_length = int(score / 5)
            bar = "█" * bar_length + "░" * (10 - bar_length)
            print(f"  {category:20s} {bar} {score:.1f}/5")

        print("\n" + "=" * 70)
        print("Detailed Responses:")
        print("-" * 70)
        for key, response in self.responses.items():
            # Convert key to readable format
            readable_key = key.replace("_", " ").title()
            print(f"  {readable_key:30s}: {response}/5")

        print("\n" + "=" * 70)

    def export_results(self, filename: str) -> None:
        """
        Export survey results to a JSON file.

        Args:
            filename: Path to output JSON file
        """
        devex_score = self.calculate_devex_score()
        category_scores = self.calculate_category_scores()

        results = {
            "overall_score": devex_score,
            "category_scores": category_scores,
            "detailed_responses": self.responses,
        }

        try:
            with open(filename, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\nResults exported to {filename}")
        except IOError as e:
            print(f"\nError exporting results: {e}", file=sys.stderr)


def main():
    """Main entry point for the DevEx survey."""
    survey = DevExSurvey()
    survey.run_interactive()
    survey.print_results()

    # Optional: export to JSON
    export_choice = input("\nExport results to JSON? (y/n): ").strip().lower()
    if export_choice == "y":
        filename = input("Enter filename (default: devex_results.json): ").strip()
        if not filename:
            filename = "devex_results.json"
        survey.export_results(filename)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSurvey cancelled.", file=sys.stderr)
        sys.exit(1)
