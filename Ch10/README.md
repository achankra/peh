# Chapter 10: Publishing Starter Kits - Code Examples

This directory contains the code examples from Chapter 10 of "The Platform Engineer's Handbook". This chapter teaches you how to create and publish starter kit templates that give teams a production-ready foundation from day one, encode best practices for project structure, CI/CD integration, and observability instrumentation, and solve the upgrade problem with Renovate.

## Chapter Overview

Chapter 10 focuses on three core competencies:

1. **Template Architecture** - Understanding the three-layer model (Template Layer, Scaffolding Layer, Distribution Layer) that separates concerns for maintainability and versioning
2. **Backstage Integration** - Using Backstage's scaffolder to provide guided template generation with organizational identity integration
3. **Upgrade Management** - Solving the "template drift" problem where generated projects fall out of sync with template improvements using Renovate and template manifests

The chapter includes practical guidance on when starter kits make sense (3+ teams creating similar projects, multiple product versions needing consistency) and when to skip them (two teams shipping one product, templates that change frequently).

## Code-to-Chapter Mapping

This section maps each code file to its specific chapter section and concept.

### Yeoman Generator (Scaffolding Layer)

| File | Chapter Section | Concept | Purpose |
|------|-----------------|---------|---------|
| **generator-index.js** | 10.3 - Scaffolding with Backstage | CLI-based project generation | Main Yeoman generator for creating Node.js backend services. Supports both interactive prompts (for local CLI usage) and non-interactive CLI options (for CI/CD automation). Demonstrates parameter collection and conditional file generation based on database selection. |

**Key Features**:
- Interactive prompts for service name, team, description, database type, and port
- Non-interactive mode with CLI options for automation
- Conditional database configuration (PostgreSQL, MongoDB, or none)
- Git initialization and initial commit
- Dependency installation and project scaffolding

### Template Files (Template Layer)

| File | Chapter Section | Concept | Purpose |
|------|-----------------|---------|---------|
| **package.json.ejs** | 10.4 - Template Files with Upgrade Tracking | Variable interpolation and metadata embedding | Node.js package.json template with conditional dependencies based on database selection. Includes platformMetadata section for version tracking and future upgrade management (enables Renovate-based updates). |
| **Dockerfile.ejs** | 10.4 - Template Files with Upgrade Tracking | Multi-stage build process | Multi-stage Dockerfile for production-ready Node.js services. Includes build stage and lightweight production stage with non-root user for security. Health checks and dynamic port configuration. |
| **docker-compose.yml.ejs** | 10.6 - Local Development Configuration | Complete dev environment | Local development environment template with conditional services for database (PostgreSQL or MongoDB), OpenTelemetry collector for observability, and volume mounts for hot-reload development. |
| **ci.yml.ejs** | 10.4 - Template Files with Upgrade Tracking | Platform-provided reusable workflows | CI/CD workflow using platform-provided reusable workflow from platform-org/platform-actions. Demonstrates integration with platform infrastructure and automated deployment stages. |

**Key Features**:
- EJS template syntax for conditional content (`<% if %>` blocks)
- Variable substitution for service name, team, port, and database configuration
- Best practices for containerization and local development
- Integration with platform CI/CD actions

### Backstage Integration (Distribution Layer)

| File | Chapter Section | Concept | Purpose |
|------|-----------------|---------|---------|
| **backstage-template.yaml** | 10.3 - Scaffolding with Backstage | Backstage scaffolder template definition | Complete Backstage scaffolder template defining the user interface parameters and multi-step workflow. Includes service information collection, configuration options, repository selection, template instantiation, GitHub publishing, namespace creation, and catalog registration. Demonstrates integration with organizational identity (OwnerPicker, RepoUrlPicker). |

**Key Features**:
- Scaffolder template specification (apiVersion v1beta3)
- Multi-step parameter collection (Service Information, Configuration, Repository)
- Integration with organizational systems (owner picker, repo picker)
- Automated steps for GitHub publishing and Kubernetes namespace creation
- Output links and next-steps guidance

### Publishing and Validation Scripts

| File | Chapter Section | Concept | Purpose |
|------|-----------------|---------|---------|
| **publish.py** | 10.3 - Scaffolding with Backstage | Template publishing automation | Python script to discover, validate, and publish starter kit templates to Backstage. Handles template discovery from repository structure, validation of required files and YAML structure, and registration with Backstage catalog API. |
| **validate-workflow.py** | 10.7 - Testing Starter Kit Templates | End-to-end workflow validation | Comprehensive validation testing the entire journey from project generation to deployment readiness. Validates generation, local development (build, test, lint), container build, and catalog registration. Demonstrates the "ESLint Incident" principle: catching behavioral mistakes that hurt developers. |
| **test_templates.py** | 10.7 - Testing Starter Kit Templates | Automated template testing | Pytest-based test suite validating template structure and generated project functionality. Tests include YAML validation, required file existence, generator execution, build success, and lint passing. Prevents issues like the ESLint misconfiguration described in section 10.7. |
| **dev-scripts.py** | 10.6 - Local Development Configuration | Development helper interface | Consistent interface for common development operations (start, test, lint, database migrations, clean, validate). Provides abstraction over underlying tooling and supports both docker-compose and npm-based development workflows. |

### Secrets Management (Bitwarden Integration)

| File | Chapter Section | Concept | Purpose |
|------|-----------------|---------|---------|
| **load-secrets.sh** | Secrets Management (cross-chapter) | Secure credential retrieval | Retrieves `BACKSTAGE_URL` and `BACKSTAGE_TOKEN` from Bitwarden vault for template publishing. Sources `bw-helper.sh` from Ch1. |

## Orphan Files

No orphan files identified. All files in the repository have clear mappings to chapter concepts.

## Prerequisites

### Required Tools

```bash
# Node.js and npm
node >= 20.0.0
npm >= 9.0.0

# Yeoman (for CLI-based scaffolding)
npm install -g yo

# Renovate (for template upgrade management - Section 10.5)
# Option 1 (recommended): Install Renovate GitHub App at https://github.com/apps/renovate
# Option 2 (self-hosted): npm install -g renovate

# Python 3 (for publishing and validation scripts)
python >= 3.9

# Docker and Docker Compose (for containerization and local dev)
docker >= 20.10
docker-compose >= 2.0
```

### Python Dependencies

```bash
# Required for publishing and validation scripts
pip install pyyaml requests pytest
```

### Installation for Development

```bash
# Clone the starter-kits repository
git clone https://github.com/platform-org/starter-kits.git
cd starter-kits

# Install Yeoman generator locally for testing
cd templates/backend-service/v1/generator
npm install
npm link

# Return to root and install Python dependencies
cd ../../../..
pip install -r requirements.txt
```

### Optional: Backstage Setup

To test publishing to Backstage, you'll need:
- A running Backstage instance (see Chapter 6 references)
- Backstage API token for authentication
- Environment variables: `BACKSTAGE_URL` and `BACKSTAGE_TOKEN`
- **Recommended:** Store Backstage credentials in Bitwarden and use `load-secrets.sh`:
  ```bash
  source load-secrets.sh   # loads BACKSTAGE_URL and BACKSTAGE_TOKEN from vault
  ```

## Step-by-Step Instructions

### Phase 1: Understanding the Template Architecture

#### Step 1.1: Review Template Structure

First, understand the three-layer architecture described in section 10.2:

```bash
starter-kits/
├── templates/
│   ├── backend-service/
│   │   └── v1/
│   │       ├── template/           # Template Layer
│   │       │   ├── package.json.ejs
│   │       │   ├── Dockerfile.ejs
│   │       │   ├── docker-compose.yml.ejs
│   │       │   └── .github/workflows/ci.yml.ejs
│   │       ├── generator/          # Scaffolding Layer
│   │       │   └── index.js
│   │       └── backstage/          # Distribution Layer
│   │           └── template.yaml
├── scripts/                        # Automation
│   ├── publish.py
│   ├── validate-workflow.py
│   └── test_templates.py
└── tests/
    └── test_templates.py
```

**Expected Outcome**: You understand the separation of concerns between template files, scaffolding logic, and distribution mechanisms.

#### Step 1.2: Examine the Generator Code

Review the Yeoman generator to understand how templates are scaffolded:

```bash
cat templates/backend-service/v1/generator/index.js
```

**Key Concepts**:
- Command-line options support non-interactive CI/CD usage
- Interactive prompts collect service configuration
- Conditional file generation based on database selection
- Git initialization and initial commit

**Expected Outcome**: You understand how to collect user input and conditionally generate files.

#### Step 1.3: Review Template Variables

Examine how templates use EJS syntax for variable substitution:

```bash
cat templates/backend-service/v1/template/package.json.ejs
cat templates/backend-service/v1/template/Dockerfile.ejs
```

**Key Concepts**:
- `<%= serviceName %>` - Simple variable substitution
- `<% if (database === 'postgresql') { %>` - Conditional content
- `platformMetadata` section for upgrade tracking (section 10.5)

**Expected Outcome**: You can create templates with conditional sections and understand metadata for Renovate tracking.

### Phase 2: Generate a Project from the Template

#### Step 2.1: Interactive CLI Generation

Generate a test project using the Yeoman generator with interactive prompts:

```bash
# Link the generator if not already done
cd templates/backend-service/v1/generator
npm link
cd ../../../..

# Run the generator
yo @platform/backend-service
```

When prompted:
- Service name: `my-api-service` (lowercase, alphanumeric, hyphens)
- Team identifier: `platform-team`
- Service description: `Example API service`
- Database requirement: `postgresql`
- Service port: `8080`

**Expected Output**:
```
✓ Service created successfully!

Next steps:
  cd my-api-service
  npm run dev          # Start local development
  npm test             # Run tests
  npm run build        # Build for production

To deploy to the platform:
  git remote add origin <your-repo-url>
  git push -u origin main
```

**Expected Directory Structure**:
```
my-api-service/
├── src/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── package.json
├── .github/workflows/ci.yml
├── infrastructure/database.yaml
├── catalog-info.yaml
└── README.md
```

#### Step 2.2: Non-Interactive CLI Generation

Generate a project using CLI options (for CI/CD automation):

```bash
yo @platform/backend-service \
  --name order-service \
  --team team-alpha \
  --database mongodb
```

**Expected Outcome**: A new `order-service` directory with MongoDB configuration instead of PostgreSQL.

#### Step 2.3: Examine Generated Files

Review the generated project to see template interpolation in action:

```bash
cd my-api-service
cat package.json | head -20
cat Dockerfile | head -15
cat docker-compose.yml | grep -A 5 "mongo:"
```

**Expected Output Examples**:

From package.json:
- Service name set to `my-api-service`
- PostgreSQL dependencies included (`pg`, `drizzle-orm`)
- `platformMetadata` section with team and generator version

From Dockerfile:
- Port set to 8080
- Health check configured for port 8080

From docker-compose.yml:
- PostgreSQL service configured
- Database name set to `my-api-service`
- OpenTelemetry collector for observability (section 10.1 best practice)

### Phase 3: Local Development Workflow

#### Step 3.1: Start Local Development Environment

Use Docker Compose for a complete local development setup:

```bash
cd my-api-service
docker-compose up --build
```

**Expected Output**:
```
app_1        | npm WARN ... (npm output)
app_1        | > my-api-service@0.1.0 dev
app_1        | > tsx watch src/index.ts
app_1        | (app starting...)
postgres_1   | LOG:  database system is ready to accept connections
otel-collector_1 | ... (OTEL collector startup logs)
```

The application should start on port 8080 with:
- Hot-reload enabled (src directory mounted)
- PostgreSQL database accessible on localhost:5432
- OpenTelemetry collector for observability on localhost:4317

#### Step 3.2: Use Development Helper Scripts

The `dev-scripts.py` provides a consistent interface for development operations:

```bash
# Start development environment (abstraction over docker-compose or npm)
python dev-scripts.py start

# Run tests with watch mode
python dev-scripts.py test --watch

# Fix linting issues
python dev-scripts.py lint --fix

# Run database migrations
python dev-scripts.py db:migrate

# Seed database with test data
python dev-scripts.py db:seed

# Validate project configuration
python dev-scripts.py validate

# Clean build artifacts and containers
python dev-scripts.py clean
```

**Expected Outcome**: You can manage the project lifecycle with consistent commands, whether it uses Docker Compose or npm directly.

#### Step 3.3: Verify Generated Configuration

Run the validate command to verify the generated project is properly structured:

```bash
python dev-scripts.py validate
```

**Expected Output**:
```
Validating project configuration...
  [✓] package.json exists
  [✓] Dockerfile exists
  [✓] CI workflow exists
  [✓] README exists
```

This validation ensures the ESLint-like mistakes mentioned in section 10.7 are caught immediately.

### Phase 4: Testing Templates

#### Step 4.1: Run Unit Tests on Generated Project

```bash
cd my-api-service
npm install
npm test
npm run lint
npm run build
```

**Expected Outcomes**:
- Tests pass with no failures
- Linting shows no errors (prevents the ESLint incident described in section 10.7)
- Build completes successfully with no type errors

#### Step 4.2: Run Template Test Suite

Return to the starter-kits root and run the comprehensive test suite:

```bash
cd ../..
pytest test_templates.py -v
```

**Expected Output**:
```
test_templates.py::TestTemplate::test_backstage_yaml_valid[backend-service-v1] PASSED
test_templates.py::TestTemplate::test_required_files_exist[backend-service-v1] PASSED
test_templates.py::TestTemplate::test_generator_produces_valid_project[backend-service-v1] PASSED
test_templates.py::TestTemplate::test_generated_project_builds[backend-service-v1] PASSED
test_templates.py::TestTemplate::test_generated_project_passes_lint[backend-service-v1] PASSED
==================== 5 passed in 12.34s ====================
```

**Tests Validate**:
- Backstage template YAML structure (section 10.3)
- All required template files exist
- Generator produces valid projects
- Generated projects build successfully
- Generated projects pass linting (catches the ESLint incident)

#### Step 4.3: Run End-to-End Workflow Validation

Run the complete workflow validation as described in section 10.7:

```bash
python validate-workflow.py
```

**Expected Output**:
```
Testing project generation...
✓ Generation: PASSED
Testing local development...
✓ Local development: PASSED
Testing container build...
✓ Container build: PASSED
Testing catalog registration...
✓ Catalog registration: PASSED

✓ All workflow validations PASSED!
```

**Workflow Validates**:
1. Project generation with database configuration
2. Local development (install, build, test, lint)
3. Docker container builds successfully
4. catalog-info.yaml is valid for Backstage registration

This is the behavioral testing approach described in section 10.7 that catches mistakes developers care about.

### Phase 5: Publishing to Backstage

#### Step 5.1: Set Up Backstage Environment

Configure Backstage connectivity:

```bash
export BACKSTAGE_URL=http://localhost:7007
export BACKSTAGE_TOKEN=your-backstage-api-token
```

If using Backstage locally (see Chapter 6), ensure it's running:

```bash
# (In your Backstage instance directory)
yarn dev
```

#### Step 5.2: Publish Templates to Backstage

Use the publish script to register templates with Backstage:

```bash
python publish.py
```

**Expected Output**:
```
✓ Published backend-service/v1
Published: 1
Failed: 0
```

**What This Does**:
1. Discovers all templates in the `templates/` directory
2. Validates each template YAML structure and required files
3. Registers templates with Backstage catalog via HTTP API
4. Makes templates available for self-service generation in the portal

#### Step 5.3: Verify in Backstage Portal

Navigate to your Backstage instance:

```
http://localhost:7007
```

1. Go to "Create" (or "Create a Component")
2. You should see "Backend Service" template
3. Click to use the template
4. Fill in the parameters (same as CLI prompts)
5. Complete the workflow to generate a new microservice repository

**Expected Outcome**: The template is now available for non-CLI users and junior developers to use through the Backstage portal interface.

### Phase 6: Understanding Upgrade Management

#### Step 6.1: Review Template Manifest Approach

Section 10.5 describes the upgrade problem and Renovate solution. Review the concept:

```bash
# The template manifest package that generated projects depend on
# This would be published to npm registry
# When you publish a new manifest version, Renovate opens PRs in dependent projects

# Example manifest structure:
cat <<'EOF'
{
  "name": "@platform/template-manifest",
  "version": "1.2.0",
  "metadata": {
    "backend-service": {
      "template-version": "1.2.0",
      "generator-version": "1.2.0",
      "minimum-node-version": "20.0.0"
    }
  }
}
EOF
```

**Key Concept**: Generated projects include the template manifest in their package.json dependencies. When you fix security issues or improve templates, you publish a new manifest version. Renovate automatically opens PRs to upgrade generated projects.

#### Step 6.2: Examine platformMetadata in Generated Project

Review how the generated project tracks template version:

```bash
cd my-api-service
cat package.json | grep -A 5 '"platformMetadata"'
```

**Expected Output**:
```json
"platformMetadata": {
  "team": "platform-team",
  "generatorVersion": "1.0.0",
  "templateVersion": "1.0.0"
}
```

This metadata enables future upgrade automation. When you update templates, you increment templateVersion and publish a new manifest package that generated projects depend on.

#### Step 6.3: Set Up Renovate Configuration

The generated project includes a Renovate configuration (in CI workflow) that enables automatic template manifest updates:

```bash
cat .github/workflows/ci.yml | grep -A 10 'renovate'
```

Generated projects use platform-provided reusable workflows that integrate with Renovate for automated upgrades.

### Phase 7: Production Deployment

#### Step 7.1: Push to GitHub

Set up your Git repository and push:

```bash
cd my-api-service
git remote add origin https://github.com/your-org/my-api-service.git
git branch -M main
git push -u origin main
```

#### Step 7.2: Verify CI/CD Pipeline

The generated project includes a CI/CD workflow (ci.yml.ejs) that:
- Runs tests and linting
- Builds a Docker image
- Publishes to container registry
- Deploys to preview/staging/production environments

Check the workflow status in GitHub Actions.

#### Step 7.3: Register in Catalog

The Backstage workflow (section 10.3) automatically registers the generated project in the catalog:

```bash
# Verify catalog-info.yaml
cat catalog-info.yaml
```

The project now appears in the Backstage catalog and can be tracked as a service.

## Companion Website Alignment

The companion website (https://peh-packt.platformetrics.com/) provides the following sections corresponding to the code examples:

| Website Section | Code Files | Description |
|-----------------|-----------|-------------|
| **10.1 When Starter Kits Make Sense** | (Conceptual) | Guidance on when to build (3+ teams, multiple versions, repeated incidents) vs. skip (two teams, frequent changes, good docs). |
| **10.2 Template Architecture** | All template files | Three-layer model: Template Layer (package.json.ejs, Dockerfile.ejs, etc.), Scaffolding Layer (generator-index.js), Distribution Layer (backstage-template.yaml) |
| **10.3 Scaffolding with Backstage** | backstage-template.yaml, generator-index.js | Backstage scaffolder integration with organizational identity (OwnerPicker, RepoUrlPicker) vs. CLI tools. Guided wizard interface. |
| **10.4 Template Files with Upgrade Tracking** | package.json.ejs, Dockerfile.ejs, ci.yml.ejs | EJS template syntax, variable interpolation, platformMetadata for version tracking |
| **10.5 Solving the Upgrade Problem with Renovate** | (Concept + package.json.ejs) | Template manifest approach, platformMetadata for tracking, Renovate automation for upgrades |
| **10.6 Local Development Configuration** | docker-compose.yml.ejs, dev-scripts.py | Complete development environment with database, observability, volume mounts. Helper scripts abstraction. |
| **10.7 Testing Starter Kit Templates** | test_templates.py, validate-workflow.py | Structural tests (files exist, YAML valid) and behavioral tests (builds, lints, registers). Prevents ESLint-type incidents. |

### Notable Website Features Covered by Code

- **Explain Code / Show Code buttons**: The website provides interactive code viewers with explanations
- **Exercises**: Chapter 10 includes two practical exercises:
  1. Create and publish a starter kit template with platformMetadata and validation tests
  2. Validate the complete developer workflow from generation to deployment

## Recommended Workflow Order

1. **Understand the Architecture** (Steps 1.1-1.3): Learn the three-layer model
2. **Generate a Project** (Steps 2.1-2.3): See templates in action
3. **Develop Locally** (Steps 3.1-3.3): Use the generated project with Docker Compose
4. **Test Everything** (Steps 4.1-4.3): Run unit tests and end-to-end validation
5. **Publish to Backstage** (Steps 5.1-5.3): Make templates discoverable
6. **Understand Upgrades** (Steps 6.1-6.3): Learn the Renovate integration
7. **Deploy to Production** (Steps 7.1-7.3): Push and verify CI/CD

## Troubleshooting

### Generator Not Found

If `yo @platform/backend-service` fails:

```bash
cd templates/backend-service/v1/generator
npm install
npm link
cd ../../../..
yo @platform/backend-service
```

### Docker Compose Port Conflicts

If ports are already in use (note: Kind uses port 8080 for its control-plane port mapping):

```bash
# Change ports in generated docker-compose.yml
# Port 8080 is used by Kind control-plane, so use 8081 instead
sed -i 's/"8080:8080"/"8081:8080"/g' docker-compose.yml
sed -i 's/"5432:5432"/"5433:5432"/g' docker-compose.yml
```

> **Kind Cluster Note**: If you're running a Kind cluster from Chapter 2, port 8080 on the host is already mapped to Kind's control-plane ingress. Generated services should use port 8081 or higher to avoid conflicts.

### Tests Fail with ESLint Errors

The test suite specifically catches ESLint misconfigurations (section 10.7). If `npm run lint` fails:

```bash
# Fix linting issues automatically
npm run lint:fix

# Or in generated projects:
python dev-scripts.py lint --fix
```

### Backstage Publishing Fails

Verify Backstage connectivity:

```bash
# Check API endpoint
curl -H "Authorization: Bearer $BACKSTAGE_TOKEN" \
  "$BACKSTAGE_URL/api/catalog/locations" | head -20

# Ensure token is valid and BACKSTAGE_URL is correct
echo "BACKSTAGE_URL=$BACKSTAGE_URL"
```

## Related Chapters

- **Chapter 6**: Developer Portal with Backstage (Distribution Layer deployment)
- **Chapter 7**: Self-Service Onboarding (How users discover and use templates)
- **Chapter 8**: CI/CD as a Platform Service (The ci.yml.ejs integration)
- **Chapter 9**: Self-Service Infrastructure Management (The namespace creation step in Backstage workflow)
- **Chapter 11**: Validating Compliance (How to add compliance checks to templates)

## Additional Resources

- **Yeoman Documentation**: https://yeoman.io/
- **Backstage Scaffolder**: https://backstage.io/docs/features/software-catalog/software-templates/
- **Renovate Docs**: https://www.whitesourcesoftware.com/free-developer-tools/renovate/
- **EJS Template Syntax**: https://ejs.co/
- **Docker Compose Reference**: https://docs.docker.com/compose/compose-file/

## Summary

Chapter 10 teaches you to build scalable starter kit templates using a three-layer architecture. The code examples demonstrate:

- **Yeoman generators** for flexible template scaffolding
- **Backstage integration** for portal-based self-service discovery
- **EJS templating** for conditional content and variable substitution
- **platformMetadata** for enabling automatic upgrades via Renovate
- **Docker Compose** for complete local development environments
- **Comprehensive testing** that catches both structural and behavioral issues
- **Python automation** for publishing and validation

By implementing this pattern, teams get consistent, production-ready projects from day one, maintenance costs are reduced through centralized template management, and upgrade problems are solved through Renovate automation.
