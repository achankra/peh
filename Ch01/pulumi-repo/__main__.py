"""
__main__.py — GitHub Repository and Team Automation
=====================================================
Pulumi program for Chapter 1 of "The Platform Engineer's Handbook."

Creates and manages:
  - GitHub repositories defined in config/platform_team_values.yaml
  - GitHub organization membership for platform team members
  - Branch protection rules (signed commits, required reviews) on each repo

Usage:
    pulumi preview    # dry-run: shows what would be created/changed
    pulumi up         # apply: create repositories and memberships
    pulumi destroy    # tear down (repositories are delete-protected by default)

Prerequisites:
    pip install pulumi pulumi-github pyyaml
    export PULUMI_ACCESS_TOKEN=<your-token>   # or set via pulumi login
    pulumi config set github:token  <ghp_...>
    pulumi config set github:owner  <your-org>

Configuration:
    All repositories and team members are defined in config/platform_team_values.yaml.
    Edit that file and re-run `pulumi up` to add or update resources.
"""

from __future__ import annotations

import yaml
import pulumi
import pulumi_github as github
from pulumi import ResourceOptions, export

# ── Load configuration ────────────────────────────────────────────────────────
CONFIG_FILE = "config/platform_team_values.yaml"

with open(CONFIG_FILE) as f:
    data = yaml.safe_load(f)

# ── GitHub provider ───────────────────────────────────────────────────────────
# Credentials come from Pulumi config (set via `pulumi config set`).
# The token is pulled from Bitwarden by your CI/CD pipeline or loaded
# manually with `source load-secrets.sh` before running pulumi up.
github_provider = github.Provider(
    "platform-github-provider",
    token=pulumi.Config("github").require("token"),
    owner=pulumi.Config("github").require("owner"),
)

# ── Create GitHub repositories ────────────────────────────────────────────────
repositories: dict[str, github.Repository] = {}

for repo_def in data.get("github_repositories", []):
    repo_name: str = repo_def["name"]
    # YAML folded scalars (`>`) keep a trailing newline; GitHub's API rejects
    # control characters in a repo description, so strip it here.
    repo_description: str = repo_def.get("description", "").strip()
    visibility: str = repo_def.get("visibility", "private")

    repo = github.Repository(
        repo_name,
        name=repo_name,
        description=repo_description,
        visibility=visibility,
        # Delete protection: prevents `pulumi destroy` from removing repositories.
        # Remove this flag only when intentionally decommissioning a repo.
        allow_auto_merge=False,
        delete_branch_on_merge=False,
        opts=ResourceOptions(
            provider=github_provider,
            protect=True,  # prevents accidental deletion via pulumi destroy
        ),
    )
    repositories[repo_name] = repo

    # ── Branch protection: enforce signed commits on main ─────────────────────
    # Every commit to main must be GPG- or SSH-signed by the committing developer.
    # This satisfies code-commit signing requirements in regulated environments
    # (SOC 2, ISO 27001) and provides a cryptographic audit trail.
    github.BranchProtection(
        f"{repo_name}-main-branch-protection",
        repository_id=repo.node_id,
        pattern="main",
        enforce_admins=True,
        require_signed_commits=True,
        required_pull_request_reviews=[
            github.BranchProtectionRequiredPullRequestReviewArgs(
                dismiss_stale_reviews=True,
                required_approving_review_count=1,
            )
        ],
        opts=ResourceOptions(
            provider=github_provider,
            depends_on=[repo],
        ),
    )

    # Export the repository name for use by other Pulumi stacks
    export(f"{repo_name}_repo_name", repo.name)
    export(f"{repo_name}_repo_url", repo.html_url)


# ── Add GitHub organization members ──────────────────────────────────────────
# Team members are added to the organization with the role defined in config.
# Note: you cannot automate management of the organization owner.
# Add a second GitHub account (e.g. youremail+peh-team-member@gmail.com)
# to test member onboarding as described in Chapter 1.

for member_def in data.get("github_organization_members", []):
    username: str = member_def["github-username"]
    role: str = member_def.get("github-role", "member")

    github.Membership(
        f"github-membership-{username}",
        username=username,
        role=role,
        opts=ResourceOptions(provider=github_provider),
    )

    pulumi.log.info(f"Managing GitHub membership: {username} ({role})")
