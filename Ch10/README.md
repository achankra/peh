# Chapter 10: Publishing Starter Kits - Code Examples

This directory contains the code examples from Chapter 10 of "The Platform Engineer's Handbook". This chapter teaches you how to create and publish starter kit templates that give teams a production-ready foundation from day one, encode best practices for project structure, CI/CD integration, and observability instrumentation, and solve the upgrade problem with Renovate.

## Chapter Overview

Chapter 10 focuses on three core competencies:

1. **Template Architecture** - Understanding the three-layer model: skeleton (project files with Backstage variable placeholders), template.yaml (Backstage scaffolder definition), and scripts (publishing, testing, and validation)
2. **Backstage Integration** - Using Backstage's scaffolder to provide guided template generation with organisational identity integration (OwnerPicker, RepoUrlPicker)
3. **Upgrade Management** - Solving the "template drift" problem where generated projects fall out of sync with template improvements, using Renovate and the platformMetadata block in package.json

The chapter includes practical guidance on when starter kits make sense (3+ teams creating similar projects, multiple product versions needing consistency) and when to skip them (two teams shipping one product, templates that change frequently).

## Directory Structure

```
Ch10/
├── templates/
│   └── backend-service/
│       └── v1/
│           ├── template.yaml              # Backstage scaffolder definition
│           └── skeleton/                  # Project files with variable placeholders
│               ├── package.json           # ${{ values.serviceName }}, platformMetadata
│               ├── Dockerfile             # Multi-stage build, ${{ values.port }}
│               ├── docker-compose.yml     # Conditional database services
│               ├── tsconfig.json          # TypeScript configuration
│               ├── catalog-info.yaml      # Backstage service registration
│               ├── README.md              # Project README template
│               ├── dev.py                 # Development helper script
│               ├── .github/
│               │   └── workflows/
│               │       └── ci.yml         # Reusable CI workflow reference
│               ├── database/
│               │   ├── postgresql/
│               │   │   └── connection.js  # PostgreSQL connection module
│               │   └── mongodb/
│               │       └── connection.js  # MongoDB connection module
│               └── infrastructure/
│                   ├── postgresql-claim.yaml  # Crossplane PostgreSQL claim
│                   └── mongodb-claim.yaml     # Crossplane MongoDB claim
├── publish.py                 # Publish templates to Backstage catalog
├── test_templates.py          # Pytest suite for template validation
├── validate-workflow.py       # End-to-end workflow validation
├── dev.py                     # Development helper (also ships in skeleton)
├── load-secrets.sh            # Bitwarden credential loader
└── README.md                  # This file
```

## Code-to-Chapter Mapping

### Backstage Template Definition

| File | Chapter Section | Purpose |
|------|-----------------|---------|
| **templates/backend-service/v1/template.yaml** | 10.3 - Scaffolding with Backstage | Backstage scaffolder template defining the self-service form: parameters (serviceName, team, database, port, repoUrl), conditional steps (fetch:template, database config, infrastructure claims, publish:github, catalog:register), and output links. |

### Skeleton Files (Project Template)

| File | Chapter Section | Purpose |
|------|-----------------|---------|
| **skeleton/package.json** | 10.4 - Template Files with Upgrade Tracking | Node.js package.json with `${{ values.serviceName }}`, conditional database dependencies, and platformMetadata block for Renovate upgrade tracking. |
| **skeleton/Dockerfile** | 10.4 - Template Files with Upgrade Tracking | Multi-stage Docker build with `${{ values.port }}` for dynamic port configuration. Builder stage for compilation, production stage with non-root user. |
| **skeleton/docker-compose.yml** | 10.6 - Local Development Configuration | Local dev environment with Nunjucks conditionals (`{%- if values.database == 'postgresql' %}`) for database services. |
| **skeleton/.github/workflows/ci.yml** | 10.4 - Template Files with Upgrade Tracking | CI workflow using platform-provided reusable workflows. |
| **skeleton/catalog-info.yaml** | 10.3 - Scaffolding with Backstage | Backstage Component registration with `${{ values.serviceName }}` and `${{ values.team }}`. |
| **skeleton/dev.py** | 10.6 - Local Development Configuration | Consistent CLI for start, test, lint, clean, and validate commands. |
| **skeleton/database/** | 10.6 - Local Development Configuration | Database connection modules for PostgreSQL and MongoDB (conditionally included). |
| **skeleton/infrastructure/** | 10.6 - Local Development Configuration | Crossplane infrastructure claims for PostgreSQL and MongoDB (conditionally included). |

### Publishing and Validation Scripts

| File | Chapter Section | Purpose |
|------|-----------------|---------|
| **publish.py** | 10.3 - Scaffolding with Backstage | Discovers templates, validates structure, registers in Backstage catalog via `/api/catalog/locations` API. |
| **validate-workflow.py** | 10.7 - Testing Starter Kit Templates | End-to-end validation: clone, build, test, lint, container build, catalog registration, infrastructure claim. |
| **test_templates.py** | 10.7 - Testing Starter Kit Templates | Pytest suite with structural tests (YAML valid, required files exist) and generation tests (substitute variables, build, lint, test). |

### Secrets Management

| File | Purpose |
|------|---------|
| **load-secrets.sh** | Retrieves `BACKSTAGE_URL` and `BACKSTAGE_TOKEN` from Bitwarden vault. Sources `bw-helper.sh` from Ch01. |

## Prerequisites

### Required Tools

```bash
# Python 3 (for publishing and validation scripts)
python3 >= 3.9

# Docker and Docker Compose (for containerisation and local dev)
docker >= 20.10
docker compose >= 2.0

# Node.js and npm (for generation tests that run npm install/build)
node >= 20.0.0
npm >= 9.0.0
```

### Python Dependencies

```bash
pip install --break-system-packages pyyaml requests pytest
```

### Backstage Setup

To test publishing to Backstage, you need a running Backstage instance (from Chapter 7):

```bash
# Verify Backstage pods are running
kubectl get pods -n backstage

# Port-forward to make Backstage accessible
kubectl port-forward -n backstage svc/backstage 7007:7007 &

# Verify health
curl -s http://localhost:7007/.backstage/health/v1/readiness
```

Store Backstage credentials in Bitwarden and use `load-secrets.sh`:

```bash
export BW_SESSION=$(bw unlock --raw)
source load-secrets.sh
```

Or set manually:

```bash
export BACKSTAGE_URL=http://localhost:7007
export BACKSTAGE_TOKEN=<your-backstage-api-token>
```

## Step-by-Step Instructions

### Phase 1: Understanding the Template Architecture

#### Step 1.1: Review the Repository Structure

Understand the versioned template layout:

```bash
ls templates/backend-service/v1/
```

Expected: `skeleton/  template.yaml`

Each template version is self-contained. The skeleton holds project files with Backstage variable placeholders, and template.yaml is the Backstage scaffolder definition.

#### Step 1.2: Walk Through the Backstage Template

Review the scaffolder definition that drives the self-service form:

```bash
cat templates/backend-service/v1/template.yaml
```

Key sections to understand: parameters define form fields (serviceName, team, database, port, repoUrl). Steps execute in order: `fetch:template` copies the skeleton and replaces variables, conditional steps add database config and Crossplane claims, `publish:github` creates the repo, and `catalog:register` adds the service to Backstage.

#### Step 1.3: Inspect Skeleton Files

Review how Backstage variable interpolation works:

```bash
cat templates/backend-service/v1/skeleton/package.json
cat templates/backend-service/v1/skeleton/Dockerfile
cat templates/backend-service/v1/skeleton/docker-compose.yml
```

The skeleton uses `${{ values.xxx }}` for simple substitution and `{%- if values.database == 'postgresql' %}` / `{%- endif %}` for conditional blocks. These are Nunjucks expressions processed by Backstage's scaffolder at generation time.

The platformMetadata block in package.json tracks which template version generated the project, enabling Renovate-based upgrades.

### Phase 2: Validate the Template

#### Step 2.1: Run Structural Tests

```bash
pytest test_templates.py -v -k 'Structure'
```

Structural tests verify: template.yaml is valid Backstage YAML (correct apiVersion, kind, parameters, steps), and all required skeleton files exist (Dockerfile, README.md, package.json, tsconfig.json, CI workflow for backend templates).

#### Step 2.2: Run Generation Tests (Optional)

These tests copy the skeleton, substitute variables, and run npm install/build/lint:

```bash
pytest test_templates.py -v -k 'Generation'
```

Generation tests require Node.js and take longer. They catch issues like broken template syntax, missing dependencies, or linting failures.

### Phase 3: Publish to Backstage

#### Step 3.1: Review the Publishing Script

```bash
cat publish.py
```

publish.py has three stages: discover_templates() finds every template.yaml, validate_template() checks required files and YAML structure, and publish_template() registers templates with Backstage via the catalog API.

#### Step 3.2: Publish Templates

```bash
python3 publish.py --local
```

The `--local` flag deploys a lightweight pod inside the Kind cluster to serve template.yaml, then registers the template with Backstage using the in-cluster Service URL.

Expected output:
```
Deploying template server in cluster... ready
Published backend-service/v1
Waiting for Backstage to ingest template... ready!
```

Use `--refresh --local` to remove previously registered templates and re-publish:
```bash
python3 publish.py --refresh --local
```

In production, templates live in a Git repository and you would omit `--local` — Backstage fetches directly from the repo URL.

#### Step 3.3: Verify in Backstage UI

Navigate to http://localhost:7007/create in your browser. The Backend Service template should appear. Click it to see the scaffolding form with fields matching the parameters in template.yaml.

### Phase 4: Review the Development Experience

#### Step 4.1: Examine the Dev Script

```bash
cat templates/backend-service/v1/skeleton/dev.py
```

dev.py provides a consistent CLI for every generated project: `start` launches the dev environment, `test` runs the test suite, `lint` runs the linter, `clean` removes build artifacts, and `validate` checks project configuration.

#### Step 4.2: Review the Workflow Validation Script

```bash
cat validate-workflow.py
```

validate-workflow.py tests the complete lifecycle: clone, npm install/build/test/lint, Docker build, catalog-info.yaml validation, and infrastructure claim verification.

### Phase 5: Understanding Upgrade Management

#### Step 5.1: Review the platformMetadata Pattern

```bash
cat templates/backend-service/v1/skeleton/package.json | grep -A 5 platformMetadata
```

The platformMetadata block records templateName, templateVersion, and generatedAt. When you publish a new template version, Renovate (a GitHub App) detects the version change and opens PRs in every dependent project.

Renovate is conceptual in this chapter — it is a GitHub App installed at the org level, not a local CLI tool. The key pattern is: version tracking in platformMetadata, automated PR creation by Renovate, and human-reviewed adoption by teams.

## Troubleshooting

### Backstage Port-Forward Dies

If publish.py fails with a connection error:

```bash
# Check if port-forward is still running
jobs

# Restart if needed
kubectl port-forward -n backstage svc/backstage 7007:7007 &
```

### Backstage Publishing Fails

Verify connectivity:

```bash
curl -s "$BACKSTAGE_URL/api/catalog/locations" | head -20
```

### Template Not Showing in Create Page

If `publish.py --local` says "Published" but the template doesn't appear:

```bash
# Check if Backstage ingested the template entity
curl -s "$BACKSTAGE_URL/api/catalog/entities/by-name/template/default/backend-service-v1" | head -5

# If empty, re-publish with --refresh --local
python3 publish.py --refresh --local
```

### Structural Tests Fail

If pytest reports missing files, check the skeleton directory:

```bash
ls templates/backend-service/v1/skeleton/
```

Ensure all required files are present: Dockerfile, README.md, package.json, tsconfig.json, catalog-info.yaml, and .github/workflows/ci.yml.

### Docker Compose Port Conflicts

If ports are already in use (Kind uses port 8080 for its control-plane):

```bash
# Use a different host port
sed -i 's/"8080:8080"/"8081:8080"/g' docker-compose.yml
```

## Related Chapters

- **Chapter 7**: Developer Portal with Backstage (where templates are published and discovered)
- **Chapter 8**: CI/CD as a Platform Service (the ci.yml reusable workflow integration)
- **Chapter 9**: Self-Service Infrastructure Management (Crossplane claims in the skeleton)
- **Chapter 11**: Policy-as-Code (adding compliance checks to templates)

## Additional Resources

- **Backstage Software Templates**: https://backstage.io/docs/features/software-templates/
- **Nunjucks Templating**: https://mozilla.github.io/nunjucks/ (used by Backstage scaffolder)
- **Renovate Docs**: https://docs.renovatebot.com/
- **Docker Compose Reference**: https://docs.docker.com/compose/compose-file/
