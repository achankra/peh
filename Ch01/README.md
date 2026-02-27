# Chapter 1: Laying the Groundwork - Code Examples

This folder contains practical code examples and tools for Chapter 1 of "The Platform Engineer's Handbook," covering platform-as-a-product principles, design principles, release workflows, and platform team setup.

## Overview

Chapter 1 establishes the foundational concepts for platform engineering, including treating your platform as a product, implementing core design principles (self-service, guardrails, golden paths, extensibility, observability, and security), designing effective release workflows with approval gates, and structuring platform teams using team topologies.

---

## Code-to-Chapter Mapping

This section maps each code file to its corresponding chapter concept and usage:

### Core Platform Tools

| File | Chapter Concept | Purpose | Type |
|------|-----------------|---------|------|
| `platform-maturity-assessment.py` | Section 1.2: Platform-as-a-Product Metrics | Interactive CLI tool for assessing platform maturity across four dimensions (Self-Service, Observability, Security, DevEx) | Python Script |
| `design-principles-checklist.py` | Section 1.3: Core Design Principles | Validates a platform configuration against six core design principles | Python Script |
| `platform-config.yaml` | Section 1.3: Design Principles & Configuration | Sample platform configuration defining principles, team structure, golden paths, policies, and infrastructure setup | YAML Config |
| `team-topology-generator.py` | Section 1.4: Platform Team Structure | Generates text/markdown visualization of team topology showing platform team, stream-aligned teams, and interaction modes | Python Script |

### Release Workflow & CI/CD

| File | Chapter Concept | Purpose | Type |
|------|-----------------|---------|------|
| `release-workflow.yaml` | Section 1.5: Release Workflow Pattern | GitHub Actions reusable workflow demonstrating the multi-stage release process: Build → Test → Security Scan → Deploy to Staging → Approval Gate → Deploy to Production | GitHub Workflow |
| `.circleci/config.yml` | Section 1.5: Infrastructure Deployment Workflow | CircleCI configuration for Pulumi infrastructure-as-code deployments with preview/approval/apply pattern | CI/CD Config |

### Configuration & Testing

| File | Chapter Concept | Purpose | Type |
|------|-----------------|---------|------|
| `test-platform-config.py` | Section 1.3: Configuration Validation | Unit tests validating platform configuration structure, required sections, data types, and compliance with design principles | Python Test Suite |
| `.env_example` | Section 1.6: Secrets Management | Template for environment variables required for Bitwarden secrets management integration | Config Template |

### Automation Scripts

| File | Chapter Concept | Purpose | Type |
|------|-----------------|---------|------|
| `scripts/install-githooks.sh` | Section 1.5: Development Workflow Standards | Bash script to install Git hooks (commit-msg validation) for enforcing conventional commits format across the team | Bash Script |
| `scripts/upload-secrets.sh` | Section 1.6: Secrets Management Pipeline | Bash script to securely upload infrastructure secrets to Bitwarden vault for CI/CD pipeline access | Bash Script |
| `scripts/bw-helper.sh` | Section 1.6: Secrets Management | Shared Bitwarden helper library with `bw_init`, `bw_get`, `bw_export`, and `bw_cleanup` functions. Sourced by `load-secrets.sh` scripts in Ch3, Ch7, Ch9, Ch10, and Ch14. | Bash Library |
| `.git-hooks/commit-msg` | Section 1.5: Commit Message Standards | Git hook enforcing conventional commits format (feat, fix, docs, etc.) for semantic versioning and changelog automation | Git Hook |

### Secrets & Support Files

| File | Chapter Concept | Purpose | Type |
|------|-----------------|---------|------|
| `secrets-setup/github_secrets.json` | Section 1.6: Secrets Storage Structure | Bitwarden item template for storing GitHub secrets and authentication tokens | JSON Template |
| `assessment_results.json` | Section 1.2: Assessment Output | Sample output from the platform maturity assessment tool showing dimension scores | Sample Output |

---

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Bash**: For running shell scripts (sh-compatible)
- **Git**: For repository and Git hook operations

### Python Dependencies

Install dependencies using pip:

```bash
pip install pyyaml pytest
```

**Package Details:**
- **pyyaml**: Required for parsing `platform-config.yaml` in all validation and assessment tools
- **pytest**: Optional but recommended for running the unit tests (`test-platform-config.py`)

### Optional Tools (for full workflow execution)

- **Pulumi** (v3.0+): Infrastructure as Code engine referenced in `.circleci/config.yml` for preview/apply workflows
  ```bash
  # macOS: brew install pulumi/tap/pulumi
  # Linux: curl -fsSL https://get.pulumi.com | sh
  ```

- **pre-commit**: Git hook framework for enforcing code quality checks before commits
  ```bash
  # macOS: brew install pre-commit
  # Linux/Windows: pip install pre-commit
  ```

- **Bitwarden CLI** (`bw`): Required to run `scripts/upload-secrets.sh` for secrets management
  ```bash
  npm install -g @bitwarden/cli
  ```

- **CircleCI CLI** (optional): For testing CircleCI workflows locally

### Environment Setup

1. Copy `.env_example` to `.env` and fill in your Bitwarden credentials:
   ```bash
   cp .env_example .env
   ```

2. Set the following environment variables in `.env`:
   - `BW_CLIENTID`: Bitwarden API Client ID
   - `BW_CLIENTSECRET`: Bitwarden API Client Secret
   - `BW_PASSWORD`: Bitwarden Master Password

---

## Step-by-Step Instructions

Follow this execution order to work through the Chapter 1 concepts:

### Step 1: Understand Platform Maturity (5-10 minutes)

Run the platform maturity assessment to evaluate where your organization stands:

```bash
python platform-maturity-assessment.py
```

**What it does:**
- Interactively asks 20 questions across four dimensions:
  - Self-Service Capabilities
  - Observability
  - Security & Compliance
  - Developer Experience
- Calculates maturity scores (1-5 scale) for each dimension
- Generates a comprehensive report with strengths and improvement areas
- Exports results to `assessment_results.json`

**Expected Output:**
```
======================================================================
PLATFORM MATURITY ASSESSMENT
======================================================================

[Assessment questions for each dimension...]

======================================================================
ASSESSMENT REPORT
======================================================================

Dimension Scores:
  Self-Service Capabilities: 4.2/5.0 (HIGH)
  ...

Overall Platform Maturity Score: 3.8/5.0
```

**Next Step:** Review the results to identify baseline maturity across dimensions.

---

### Step 2: Customize Platform Configuration (15-20 minutes)

Edit `platform-config.yaml` to match your organization:

```bash
# Review the current configuration
cat platform-config.yaml

# Edit with your favorite editor (vi, nano, vscode, etc.)
nano platform-config.yaml
```

**Key sections to customize:**

1. **Platform Identity** (lines 1-10):
   - Update `platform.name` and `platform.owner-team`
   - Change `version` if needed

2. **Platform Principles** (lines 12-50):
   - Keep the six core principles (Self-Service, Guardrails, etc.)
   - Update `description` and `measurable` fields to reflect your goals

3. **Team Structure** (lines 52-80):
   - Modify the `teams` section with your actual team names and sizes
   - Add or remove team members as appropriate

4. **Golden Paths** (lines 81-130):
   - Define recommended technology stacks for your organization
   - Add deployment patterns and best practices

5. **Security Policies** (lines 131-160):
   - Configure compliance requirements (SOC2, ISO 27001, HIPAA, etc.)
   - Set security scanning and secret management requirements

**Example modification:**
```yaml
platform:
  name: "Acme Corp Developer Platform"
  owner-team: "DevEx Engineering"
  # ... rest of config
```

**Next Step:** Validate your configuration against design principles (Step 3).

---

### Step 3: Validate Design Principles (5 minutes)

Check that your platform configuration adheres to core design principles:

```bash
python design-principles-checklist.py platform-config.yaml
```

**What it does:**
- Validates all six design principles:
  - Self-Service: Can teams self-serve without bottlenecks?
  - Guardrails: Are safe boundaries in place?
  - Golden Paths: Are recommended patterns clear?
  - Extensibility: Can the platform be extended?
  - Observability: Can platform health be monitored?
  - Security: Are security practices enforced?
- Checks configuration completeness
- Identifies gaps and improvement areas

**Expected Output:**
```
======================================================================
DESIGN PRINCIPLES VALIDATION REPORT
======================================================================

PRINCIPLE: Self-Service Capabilities
  ✓ Internal developer portal defined
  ✓ 5 self-service templates available
  ✓ High automation level
  ...

PRINCIPLE: Security & Compliance
  ✗ Security scanning not configured
  ⚠ Compliance requirements incomplete
  ...

Summary: 5/6 principles fully compliant
```

**Next Step:** Address any failed checks by updating `platform-config.yaml`.

---

### Step 4: Run Configuration Tests (5 minutes)

Execute the unit tests to ensure configuration validity:

```bash
# Using pytest (recommended)
python -m pytest test-platform-config.py -v

# Or run directly
python test-platform-config.py
```

**What it tests:**
- YAML syntax and structure validation
- Required configuration sections present
- Configuration completeness checks
- Data type validation
- Platform principles requirements
- Team structure requirements

**Expected Output:**
```
test-platform-config.py::test_config_structure PASSED
test-platform-config.py::test_platform_principles PASSED
test-platform-config.py::test_team_structure PASSED
test-platform-config.py::test_golden_paths PASSED
test-platform-config.py::test_security_policies PASSED

=========== 5 passed in 0.23s ===========
```

**Next Step:** Generate team topology visualization (Step 5).

---

### Step 5: Visualize Team Topology (5 minutes)

Generate a markdown visualization of your team structure:

```bash
python team-topology-generator.py
```

**What it does:**
- Displays the platform team organization (roles and responsibilities)
- Shows stream-aligned teams and their relationship to the platform
- Illustrates interaction modes (collaboration, communication, facilitation)
- Generates ASCII/markdown team topology diagram

**Expected Output:**
```
================================================================================
                        TEAM TOPOLOGY VISUALIZATION
================================================================================

┌─────────────────────────────────────────────────────────────────────┐
│ PLATFORM TEAM (8 members)                                           │
│ Responsibilities:                                                   │
│   • Develop and maintain platform services                          │
│   • Define golden paths and standards                               │
│   • Operate infrastructure                                          │
│   • Support stream-aligned teams                                    │
│   • Drive platform adoption                                         │
├─────────────────────────────────────────────────────────────────────┤
│ Roles:                                                              │
│  • Platform Lead - Strategy & Roadmap                               │
│  • Backend Engineer (2) - Platform Services                         │
│  • DevOps Engineer (2) - Infrastructure & Deployment                │
│  • Security Engineer - Security & Compliance                        │
│  • Developer Advocate - Documentation & Support                     │
│  • Data Engineer - Observability & Analytics                        │
└─────────────────────────────────────────────────────────────────────┘

STREAM-ALIGNED TEAMS:
  • Payments Team (6 members): Payment Processing, Billing
  • User Management Team (5 members): Authentication, Authorization
  • Analytics Team (4 members): Analytics, Reporting
  • Notifications Team (3 members): Email, SMS, Push Notifications

INTERACTION MODES:
  • Collaboration: Platform and stream teams work together on shared problems
  • Communication: Asynchronous updates and information sharing
  • Facilitation: Platform team supports and enables stream team success
```

**Next Step:** Review and customize the generator for your actual teams.

---

### Step 6: Set Up Git Hooks for Commit Standards (5 minutes)

Install Git hooks to enforce conventional commits across your team:

```bash
# From repository root
bash scripts/install-githooks.sh
```

**What it does:**
- Copies the `commit-msg` hook from `.git-hooks/` to `.git/hooks/`
- Makes the hook executable
- Validates commit messages against conventional commits format

**Expected Output:**
```
Successfully installed commit-msg hook
Git hooks installation complete
Commit messages will now be validated for conventional commits format
```

**Commit Format:**
The hook enforces the conventional commits format: `type(scope)?: message`

Valid types: `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`, `style`, `test`

**Examples:**
```bash
git commit -m "feat(auth): add OAuth2 login support"      ✓ Valid
git commit -m "fix(database): resolve connection leak"    ✓ Valid
git commit -m "docs: update installation guide"           ✓ Valid
git commit -m "Updated something"                         ✗ Invalid
```

**Next Step:** Review release workflow configuration (Step 7).

---

### Step 7: Review Release Workflow Pattern (10 minutes)

Examine the multi-stage release workflow that implements best practices:

```bash
# View the GitHub Actions workflow
cat release-workflow.yaml

# View the CircleCI infrastructure workflow
cat .circleci/config.yml
```

**GitHub Release Workflow (`release-workflow.yaml`):**

The workflow implements a robust six-stage release process:

1. **Build Stage**
   - Checks out code
   - Sets up Docker Buildx
   - Authenticates to container registry
   - Extracts metadata (tags, versions)
   - Builds and pushes Docker image

2. **Test Stage**
   - Sets up Python environment
   - Runs unit tests with coverage
   - Runs integration tests
   - Uploads coverage reports to Codecov

3. **Security Scan Stage**
   - Runs Trivy vulnerability scanner on filesystem
   - Performs SAST (Static Application Security Testing)
   - Uploads results to GitHub Security tab

4. **Deploy to Staging Stage**
   - Sets up kubectl for cluster access
   - Deploys to staging environment (Kubernetes or Helm)
   - Performs health checks on deployment
   - Runs smoke tests against staging

5. **Approval Gate Stage**
   - Manual approval required before production deployment
   - Provides change record for audit trail

6. **Deploy to Production Stage**
   - Sets up kubectl for cluster access
   - Deploys to production environment
   - Verifies production deployment
   - Creates release tag and release notes

**CircleCI Infrastructure Workflow (`.circleci/config.yml`):**

> **Why CircleCI here and GitHub Actions later?** This chapter uses CircleCI for infrastructure deployment pipelines (Pulumi preview/approve/apply). Chapter 8 switches to GitHub Actions for application CI/CD pipelines. This is intentional — a platform team should be CI-tool-agnostic. The patterns demonstrated (reusable workflows, approval gates, progressive delivery) translate across any CI/CD system. Think of CircleCI here as the *infrastructure track* and GitHub Actions in Chapter 8 as the *application delivery track*. Many organizations run both in production.

Demonstrates infrastructure-as-code deployment with Pulumi:
- **Preview Stage**: Shows infrastructure changes without applying (runs on all pushes to main)
- **Approval Gate**: Requires manual approval (triggered by version tags)
- **Deploy Stage**: Applies infrastructure changes (runs only on approval)

**Integration with Your Repository:**

To use the GitHub workflow in your repository:

```yaml
# In .github/workflows/your-workflow.yml
jobs:
  release:
    uses: ./.github/workflows/release-workflow.yaml
    with:
      service-name: my-service
      environment: production
    secrets:
      REGISTRY_USERNAME: ${{ secrets.REGISTRY_USERNAME }}
      REGISTRY_PASSWORD: ${{ secrets.REGISTRY_PASSWORD }}
```

**Next Step:** Set up secrets management (Step 8).

---

### Step 8: Configure Secrets Management (10 minutes, optional)

Set up secure secrets storage using Bitwarden:

**Note:** This step requires Bitwarden CLI and valid credentials. It's optional but recommended for production use.

**Setup:**

1. **Configure environment variables:**
   ```bash
   cp .env_example .env
   # Edit .env with your Bitwarden credentials
   nano .env
   ```

2. **Install Bitwarden CLI (if not already installed):**
   ```bash
   npm install -g @bitwarden/cli
   ```

3. **Upload secrets to Bitwarden:**
   ```bash
   bash scripts/upload-secrets.sh
   ```

**What the script does:**
- Loads credentials from `.env` file
- Authenticates with Bitwarden using API credentials
- Unlocks the vault using master password
- Creates or updates a "GitHub Secrets" item in Bitwarden
- Stores the GitHub personal access token securely
- Syncs vault with Bitwarden servers
- Locks the vault to invalidate the session

**Expected Output:**
```
Logging into Bitwarden using API credentials...
Unlocking Bitwarden vault...
Creating GitHub Secrets item in Bitwarden...
Syncing Bitwarden vault...
Locking Bitwarden vault...
Successfully uploaded secrets to Bitwarden
```

**Security Best Practices:**
- Keep `.env` file out of version control (already in `.gitignore`)
- Rotate Bitwarden API credentials regularly
- Use strong master passwords
- Enable two-factor authentication on Bitwarden account
- Audit Bitwarden access logs periodically

**Next Step:** Review the template secrets structure in `secrets-setup/github_secrets.json`.

---

### Step 9: Review Outputs and Assessment Results (5 minutes)

After completing the above steps, review the generated outputs:

```bash
# View assessment results
cat assessment_results.json

# View generated team topology (from Step 5)
# Output displayed directly to terminal

# View design principles validation report (from Step 3)
# Output displayed directly to terminal
```

**Key Files Generated:**
- `assessment_results.json`: Platform maturity assessment scores
- Validation reports: Printed to stdout during script execution
- Team topology: Printed to stdout during script execution

---

## Troubleshooting

### Common Issues

**Issue: PyYAML not installed**
```bash
Error: PyYAML not installed. Install with: pip install pyyaml
```
**Solution:** Install PyYAML
```bash
pip install pyyaml
```

**Issue: Python version too old**
```bash
Error: Python 3.8+ required
```
**Solution:** Update Python or use a virtual environment with Python 3.8+
```bash
python3 -m venv venv
source venv/bin/activate
pip install pyyaml pytest
```

**Issue: Git hooks installation fails**
```bash
Error: Not a git repository. Please run this script from the repository root.
```
**Solution:** Ensure you're in a Git repository and run from the root:
```bash
cd /path/to/repository
bash scripts/install-githooks.sh
```

**Issue: Commit message hook rejects valid commits**
```bash
Error: Commit message does not follow conventional commits format
```
**Solution:** Use the correct conventional commits format:
```bash
git commit -m "type(scope): description"
# Example:
git commit -m "feat(platform): add self-service dashboard"
```

**Issue: Design principles validation shows failures**
```
✗ Security scanning not configured
✗ Compliance requirements incomplete
```
**Solution:** Update `platform-config.yaml` to include the missing sections. Check the validation output for specific recommendations.

---

## Key Concepts from Chapter 1

### Platform-as-a-Product
The platform is treated as a product with:
- Clear value proposition
- User-centric design (for platform users/teams)
- Regular feedback loops from development teams
- Continuous improvement based on developer feedback

### Core Design Principles

1. **Self-Service**: Teams can provision resources and deploy applications without waiting for platform team intervention
2. **Guardrails**: Safety measures prevent misconfiguration and ensure compliance without blocking innovation
3. **Golden Paths**: Clear, recommended patterns for common tasks reduce decision paralysis and improve consistency
4. **Extensibility**: Platform can be extended with custom integrations, plugins, and domain-specific tools
5. **Observability**: Platform health, performance, and usage metrics are visible and actionable
6. **Security**: Security is built into the platform by default, not bolted on afterwards

### Release Workflow Pattern

A robust multi-stage workflow ensures quality and safety:
- **Automated testing** catches issues early in the pipeline
- **Security scanning** identifies vulnerabilities before production
- **Staging environment** validates production readiness
- **Approval gates** provide human oversight for critical changes
- **Automated production deployment** ensures consistency and repeatability

### Team Topologies

Effective platform teams use team topologies to define:
- **Platform Team**: Owns and operates the internal developer platform
- **Stream-Aligned Teams**: Product teams that depend on the platform
- **Interaction Modes**: Collaboration, communication, and facilitation patterns

---

## Companion Website & Alignment

The companion website is available at: `https://peh-packt.platformetrics.com/`

**Note:** As of February 2026, the companion website was not accessible during the creation of this README. If you have access, please verify that:
- Code listings in Chapter 1 match the files in this repository
- Any additional resources or updates are documented
- Example output matches the expected output shown in this guide

Please report any discrepancies between the website and this code repository to the publishers.

---

## Exercises and Next Steps

After working through this chapter's code:

1. **Customize `platform-config.yaml`** with your organization's actual platform details
2. **Run the maturity assessment** to establish a baseline
3. **Validate design principles** in your actual platform configuration
4. **Set up Git hooks** for your development team
5. **Adapt the release workflows** to match your CI/CD infrastructure — this book demonstrates both CircleCI (Chapter 1, infrastructure pipelines) and GitHub Actions (Chapter 8, application delivery) to show the patterns are CI-tool-agnostic
6. **Establish team topologies** with clear responsibilities and interaction modes
7. **Document your platform's golden paths** using the configuration as a template
8. **Measure progress** by running the maturity assessment quarterly and tracking improvements

---

## File Structure Summary

```
Ch01/
├── README.md                          # This file
├── platform-maturity-assessment.py    # Platform maturity evaluation tool
├── design-principles-checklist.py     # Design principles validator
├── platform-config.yaml               # Platform configuration template
├── team-topology-generator.py         # Team topology visualizer
├── test-platform-config.py            # Configuration unit tests
├── release-workflow.yaml              # GitHub Actions release workflow
├── .env_example                       # Environment variables template
├── assessment_results.json            # Sample assessment output
│
├── .circleci/
│   └── config.yml                     # CircleCI infrastructure workflow
│
├── .git-hooks/
│   └── commit-msg                     # Git hook for commit validation
│
├── scripts/
│   ├── bw-helper.sh                   # Shared Bitwarden helper (used by all chapters)
│   ├── install-githooks.sh            # Install Git hooks
│   └── upload-secrets.sh              # Upload secrets to Bitwarden
│
└── secrets-setup/
    └── github_secrets.json            # GitHub secrets template
```

---

## Further Reading

For detailed explanations of all concepts in this chapter, refer to:
- **Chapter 1: Laying the Groundwork** in "The Platform Engineer's Handbook"
- The accompanying documentation in the manuscript

For additional resources:
- **Team Topologies**: Read "Team Topologies: Organizing Business and Technology Teams for Fast Flow" by Matthew Skelton and Manuel Pais
- **Platform Engineering**: See "Continuous Delivery" by Jez Humble and David Farley for release workflow best practices
- **Site Reliability Engineering**: Refer to "The Site Reliability Engineering Book" for observability and security patterns
