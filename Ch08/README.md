# Chapter 8: CI/CD as a Platform Service

**The Platform Engineer's Handbook** by Packt Publishing

This directory contains comprehensive examples and tools for implementing CI/CD as a composable platform service. The code demonstrates modern platform engineering practices including reusable workflow components, progressive delivery strategies, observability integration, and automated rollback mechanisms.

## Chapter Overview

Modern platform engineering treats CI/CD not as a monolithic set of pipelines, but as a configurable, composable platform service that enables teams to build secure, observable, and reliable delivery pipelines. This chapter covers:

- **Reusable CI/CD Components**: Build, test, security scanning, and deployment workflows that teams can compose into complete pipelines
- **Pipeline Composition Engines**: Automatic pipeline generation from simple configuration files, reducing boilerplate and promoting consistency
- **Progressive Delivery Strategies**: Canary and blue-green deployment patterns for risk-managed releases to production
- **Observability-First Deployments**: Integration with metrics, health checks, and logging for real-time deployment monitoring
- **Automated Rollback**: Health-aware rollback controllers that respond to deployment failures using objective metrics
- **Golden Paths**: Reference implementations that teams can use as starting points for their own deployments

## Code-to-Chapter Mapping

This section maps each file in the repository to specific chapter sections and listings.

### Reusable Workflow Components (Section: Building Reusable Workflows)

#### reusable-workflows/build-and-test.yaml
**Chapter Mapping**: Section 8.2 "Reusable Workflow Components" - Build & Test Workflow
**Purpose**: GitHub Actions reusable workflow providing language-agnostic build and test capabilities
**Key Concepts**:
- `workflow_call` trigger for reusable workflows
- Multi-language support (Python, Node.js, Go)
- Configurable build and test commands
- Test result publishing with `publish-unit-test-result-action`
- Coverage report generation and artifact upload
**Usage Pattern**: Called by orchestration workflows to standardize build processes across teams
**Expected Output**: Build artifacts uploaded to GitHub, test results published, coverage reports generated

#### reusable-workflows/security-scan.yaml
**Chapter Mapping**: Section 8.3 "Security as Part of the Platform" - Security Scanning Workflow
**Purpose**: Comprehensive security scanning across container images, dependencies, and code
**Key Concepts**:
- Dependency scanning with pip-audit (Python) and npm audit (Node.js)
- Container image scanning with Aqua Security Trivy
- Software Bill of Materials (SBOM) generation using CycloneDX
- License compliance checking with pip-licenses
- CodeQL analysis for static code analysis
- Configurable failure behavior based on vulnerability severity
**Integration Points**:
  - Container image scanning validates container safety
  - SBOM generation for supply chain transparency
  - CodeQL integration with GitHub Advanced Security
**Security Controls**: Fail-on-critical option allows teams to enforce policies

#### reusable-workflows/deploy.yaml
**Chapter Mapping**: Section 8.4 "Progressive Delivery Patterns" - Universal Deployment Workflow
**Purpose**: Unified deployment workflow supporting multiple deployment strategies
**Key Concepts**:
- Pluggable deployment strategies: direct, canary, blue-green
- Health checks and readiness probes
- Graceful rollout status monitoring
- Environment-specific configuration
- Multi-step deployment with validation
**Strategy Implementations**:
  - **Direct**: Immediate deployment with kubectl apply
  - **Blue-Green**: Deploy to separate "green" environment, switch service selector after validation
  - **Canary**: Deploy with 1 replica for initial testing
**Workflow Outputs**: Deployment ID and status for tracking and rollback decisions
**Integration**: Works with both standalone manifests and manifest directories

### Pipeline Composition & Orchestration (Section: Composable Pipeline Architecture)

#### pipeline-composer.py
**Chapter Mapping**: Section 8.5 "Pipeline Composition Engine" - Listing 8.1 Pipeline Composer
**Purpose**: Python tool that generates complete GitHub Actions workflows from YAML configuration
**Key Concepts**:
- Configuration-driven workflow generation reduces template duplication
- Automatic job dependency ordering
- Environment variable injection
- Support for multi-stage pipelines with environment-specific variations
- Dry-run capability for validation before generation
**Usage**:
```bash
python3 pipeline-composer.py --config pipeline-config.yaml --output .github/workflows/main.yaml
python3 pipeline-composer.py --config pipeline-config.yaml --dry-run  # Preview output
```
**Composable Elements**:
1. Build job (calls build-and-test.yaml)
2. Security job (calls security-scan.yaml)
3. Deployment jobs (calls deploy.yaml with strategy parameter)
4. Notification job for pipeline completion
**Configuration Format**: Simplified YAML supporting:
- Application name and language
- Build settings (version, custom commands)
- Deployment stages with strategies
- Environment specifications

#### .github/workflows/backend-pipeline.yml
**Chapter Mapping**: Section 8.5 "Pipeline Composition Engine" - Listing 8.2 Backend Service Pipeline Example
**Purpose**: Example workflow demonstrating a production backend service pipeline
**Key Concepts**:
- Real-world multi-job pipeline structure
- Node.js-specific build and test configuration
- Integration with codecov for coverage tracking
- Container build with custom action
- Environment-based deployment
**Workflow Stages**:
1. **build-and-test**: Node.js build, test with coverage
2. **security-scan**: npm audit, ESLint linting
3. **container-build**: Docker build/push with Trivy scanning
4. **deploy**: kubectl-based deployment to environment-specific clusters
**Outputs**: Image tag propagated through pipeline for consistent versioning
**Integration**: Demonstrates use of custom GitHub Actions alongside reusable workflows

### Custom GitHub Actions (Section: Building Custom Actions)

#### .github/actions/container-build/action.yml
**Chapter Mapping**: Section 8.2 "Custom Actions for Container Publishing"
**Purpose**: Composite action for building and pushing container images with security scanning
**Key Concepts**:
- Composite action structure (using: composite)
- Multi-step Docker build with layer caching (GHA cache backend)
- Push to container registry (ghcr.io default)
- Post-build Trivy vulnerability scanning
- SARIF format results for GitHub Security integration
**Docker Best Practices**:
- Layer caching with `cache-from: type=gha`
- Multi-tag support (SHA and latest)
- Buildx for cross-platform builds
**Security Integration**: Trivy scan results automatically uploaded to GitHub code scanning
**Registry Flexibility**: Supports custom registry input parameter

### Deployment Strategies (Section: Progressive Delivery in Practice)

#### blue-green-deployment.yaml
**Chapter Mapping**: Section 8.4 "Blue-Green Deployments" - Listing 8.3 Blue-Green Manifests
**Purpose**: Complete Kubernetes manifests for blue-green deployment pattern
**Key Concepts**:
- Dual deployment pattern (blue and green)
- Service selector switching for traffic control
- Zero-downtime deployment and fast rollback
- Independent scaling and health checks for each color
**Manifest Components**:
1. **Namespace**: Application namespace with labels
2. **Blue Deployment** (replicas: 3): Current production version (v1.0.0)
3. **Green Deployment** (replicas: 0): New version, scaled up only during deployment
4. **Service**: Exposes both deployments, initially selecting blue
5. **Ingress**: External traffic routing with TLS
6. **HPA for Blue**: Auto-scaling based on CPU/memory (2-10 replicas)
7. **HPA for Green**: Auto-scaling during promotion (0-10 replicas)
8. **ConfigMap**: Operational scripts for manual deployment procedures
**Operational Scripts** (in ConfigMap):
- `scale-green.sh`: Scale green to match blue replicas
- `test-green.sh`: Health check green deployment
- `switch-to-green.sh`: Patch service to route to green
- `rollback-to-blue.sh`: Emergency rollback
- `deploy-full.sh`: Complete deployment with validation
**Health Probes**:
- **Startup Probe**: Allow 5 minutes for slow-starting apps
- **Liveness Probe**: Restart on unresponsiveness
- **Readiness Probe**: Exclude unhealthy pods from traffic
**Resource Management**: Defined requests/limits for proper scheduling
**Security Context**: Non-root user, read-only filesystem, dropped capabilities

#### canary-deployment.yaml
**Chapter Mapping**: Section 8.4 "Canary Deployments with Istio" - Listing 8.4 Canary Manifests
**Purpose**: Kubernetes and Istio manifests for progressive canary deployments
**Prerequisites**:
- Istio 1.10+ with VirtualService and DestinationRule support
- Prometheus for metrics collection
- prometheus-operator for ServiceMonitor/PrometheusRule resources
**Manifest Components**:
1. **Stable Deployment** (replicas: 3): Current production version
2. **Canary Deployment** (replicas: 1): New version for testing
3. **Service**: Kubernetes service for both stable and canary
4. **VirtualService**: Istio traffic management with initial 90% stable / 10% canary split
5. **DestinationRule**: Subset definitions and traffic policies (outlier detection, connection pooling)
6. **ServiceMonitor**: Prometheus scrape configuration
7. **PrometheusRule**: Canary validation alerts
8. **ConfigMap**: Promotion script for progressive traffic shifts
**Traffic Splitting Strategy**:
- Initial: 90% stable, 10% canary
- Promotion steps: 10% → 50% → 100% (based on health checks)
- Automatic rollback if errors exceed thresholds
**Prometheus Alerts** (PrometheusRule):
- `CanaryHighErrorRate`: Alert if error rate > 5%
- `CanaryHighLatency`: Alert if p95 latency increases > 25%
- `CanaryHighMemory`: Alert if memory usage > 100MB
**Promotion Logic** (promote.sh):
- Checks canary health metrics
- Gradually shifts traffic when health is good
- Holds at current weight if problems detected
**Outlier Detection**: Ejects endpoints with 5+ consecutive 5xx errors

### Runtime Intelligence & Observability (Section: Automated Rollback Decisions)

#### rollback-controller.py
**Chapter Mapping**: Section 8.6 "Automated Rollback Controller" - Listing 8.5 Health-Aware Rollback
**Purpose**: Health-monitoring system that triggers automatic rollbacks when deployments degrade
**Key Concepts**:
- Continuous deployment health monitoring using kubectl
- Threshold-based automatic rollback decisions
- Pod readiness ratio validation (80% minimum)
- Configurable check intervals and max iterations
**Health Checks**:
- Desired vs. ready replica comparison
- Ready ratio percentage calculation
- Timeout handling for cluster communication failures
**Configuration** (RollbackConfig dataclass):
- `deployment`: Target deployment name (default: "demo-app")
- `namespace`: Kubernetes namespace (default: "default")
- `error_rate_threshold`: Error rate trigger for rollback (default: 5%)
- `check_interval_seconds`: Time between health checks (default: 10s)
- `max_checks`: Maximum checks before giving up (default: 30)
- `min_ready_ratio`: Minimum ready pod percentage (default: 0.8)
**Execution Flow**:
1. Query deployment status via kubectl
2. Calculate ready pod ratio
3. If below threshold, execute kubectl rollout undo
4. Log results for incident tracking
**Usage**:
```bash
python3 rollback-controller.py --deployment myapp --namespace production
python3 rollback-controller.py --demo  # Simulation mode showing health degradation and recovery
```
**Integration Points**:
- Can be run as Kubernetes job after deployment
- Can be integrated with deployment workflow
- Supports custom health check implementations

### Observability & Metrics (Section: Metrics-Driven Deployments)

#### scripts/ci_metrics.py
**Chapter Mapping**: Section 8.7 "Observability Integration" - CI/CD Metrics Collection
**Purpose**: Collect and analyze CI/CD pipeline metrics from GitHub Actions API
**Key Concepts**:
- GitHub Actions API integration for workflow data
- Historical trend analysis over configurable time periods
- Pipeline performance metrics aggregation
- JSON output for integration with dashboards
**Metrics Collected**:
- Total runs, successful runs, failed runs
- Average pipeline duration (minutes)
- Success rate and failure rate percentages
- Min/max duration for performance bounds
- Daily trend analysis
**CIMetricsCollector Methods**:
- `get_workflow_runs()`: Retrieve workflow executions from GitHub API
- `calculate_pipeline_metrics()`: Aggregate metrics from runs
- `get_build_performance_trend()`: Daily breakdown of performance
- `collect_all_metrics()`: Multi-workflow metric collection
**Usage**:
```bash
export GITHUB_TOKEN="ghp_..."
export GITHUB_OWNER="myorg"
export GITHUB_REPO="myrepo"
export OUTPUT_FILE="/tmp/metrics.json"
python3 scripts/ci_metrics.py
```
**Configuration via Environment Variables**:
- `GITHUB_TOKEN`: GitHub API authentication
- `GITHUB_OWNER`: Repository owner/organization
- `GITHUB_REPO`: Repository name
- `WORKFLOWS`: Comma-separated workflow file names
- `OUTPUT_FILE`: Optional JSON output file path
**Output Format**: Timestamped JSON with per-workflow metrics and trends
**Integration**: Output can feed into monitoring dashboards and SLO tracking

### Testing & Validation (Section: Testing the Platform)

#### test-pipelines.py
**Chapter Mapping**: Section 8.8 "Testing Platform Implementations" - Integration Tests
**Purpose**: Test suite validating reusable workflow configurations and deployment patterns
**Test Coverage**:
1. **TestReusableWorkflows**: Validates reusable workflow structure
   - Checks presence of build-and-test.yaml, deploy.yaml, security-scan.yaml
   - Verifies workflow_call trigger for reusability
   - Tests expected inputs/outputs definitions

2. **TestDeploymentStrategies**: Validates deployment strategy configurations
   - Confirms blue-green manifest existence
   - Confirms canary manifest existence
   - Validates weight/traffic parameters in canary config

3. **TestRollbackController**: Validates controller and composer code
   - Checks Python syntax validity of rollback-controller.py
   - Checks Python syntax validity of pipeline-composer.py
   - Tests import compatibility

**Running Tests**:
```bash
python3 -m pytest test-pipelines.py -v
python3 test-pipelines.py  # Direct execution with unittest
```

**Expected Output**:
- 8-10 test cases covering main components
- Validation that all workflows are properly structured
- Syntax verification for Python tools

## Orphan Files

The following files exist in the repository but lack specific chapter mapping documentation:

1. **__pycache__/** - Python bytecode cache (generated, should be in .gitignore)
2. **.github/workflows/backend-pipeline.yml** - Partially covered; exists as example but may not be explicitly discussed in chapter

**Recommendation**: Ensure .gitignore includes `__pycache__/` to prevent cache files from being committed.

## Why GitHub Actions (not CircleCI)?

In Chapter 1 we used CircleCI for infrastructure deployment pipelines with Pulumi. That was deliberate — a good platform team is CI-tool-agnostic. The underlying patterns (reusable workflows, progressive delivery, automated rollback) work across any CI/CD system. We switch to GitHub Actions here because: (1) it has the richest ecosystem for demonstrating reusable workflow composition via `workflow_call`, (2) GitHub Actions is included free with every GitHub repo — no extra vendor signup, and (3) these composable patterns translate directly to GitLab CI includes, Jenkins shared libraries, or CircleCI orbs. Think of Chapter 1's CircleCI pipeline as the *infrastructure track* and Chapter 8's GitHub Actions as the *application delivery track*. In practice, many organizations run both.

## Prerequisites

### Software Requirements

- **Python**: 3.8+ (for pipeline-composer.py, rollback-controller.py, test-pipelines.py, ci_metrics.py)
- **kubectl**: Latest version (for deployment and health monitoring)
- **Docker/Docker Buildx**: Latest (for container builds in GitHub Actions)
- **Kubernetes**: 1.24+ (Kind cluster from Chapter 2)
- **Istio**: 1.10+ (only for canary deployments with traffic splitting — see install instructions below)
- **Prometheus**: 2.30+ (for metrics collection and canary validation alerts)
- **prometheus-operator**: Latest (for ServiceMonitor and PrometheusRule resources)

### Installing Istio

Istio is required for the canary deployment steps (Steps 4–5). Install it before running those steps:

```bash
# Option A: Homebrew (recommended on macOS)
brew install istioctl

# Option B: Direct download
curl -L https://istio.io/downloadIstio | sh -
export PATH="$PWD/istio-*/bin:$PATH"
```

Then install the demo profile into your Kind cluster:

```bash
istioctl install --set profile=demo -y

# Verify Istio is running:
kubectl get pods -n istio-system
# Expected: istiod, istio-ingressgateway, istio-egressgateway all Running
```

### Python Dependencies

```bash
pip install pyyaml requests pytest --break-system-packages
```

### Environment Setup

Load secrets from Bitwarden (recommended):

```bash
export BW_SESSION=$(bw unlock --raw)
source load-secrets.sh
```

Or export manually:

```bash
export GITHUB_TOKEN=ghp_YourActualTokenHere
export GITHUB_OWNER=platformetrics
export GITHUB_REPO=peh-companion-code
```

### GitHub Environment

- GitHub Actions enabled in repository
- Secrets configured:
  - `KUBE_CONFIG`: Base64-encoded kubeconfig for deployments
  - `GITHUB_TOKEN`: For API authentication in ci_metrics.py

### Kubernetes Setup

- RBAC permissions for deployment rollout management
- Namespace pre-created or deployment has create namespace permission
- Container registry access (ghcr.io or custom registry)

### Optional but Recommended

- **CodeQL**: For code scanning (GitHub Advanced Security)
- **Trivy**: For container vulnerability scanning
- **CycloneDX**: For SBOM generation
- **Codecov**: For coverage tracking

## Step-by-Step Instructions

### Step 1: Set Up Repository Structure

Create the required directory structure in your repository:

```bash
# Create workflow directories
mkdir -p .github/workflows/reusable
mkdir -p .github/actions/container-build
mkdir -p k8s/
mkdir -p scripts/

# Copy reusable workflows
cp reusable-workflows/*.yaml .github/workflows/reusable/

# Copy custom actions
cp -r .github/actions/container-build/* .github/actions/container-build/

# Create initial pipeline config
cat > pipeline-config.yaml << 'EOF'
name: myapp
language: python
language-version: '3.10'
image-registry: ghcr.io/myorg
stages:
  - name: build-and-test
    tasks: [build-and-test, security-scan]
  - name: deploy-staging
    deploy-strategy: blue-green
    environment: staging
  - name: deploy-production
    deploy-strategy: canary
    environment: production
EOF
```

**Expected Output**:
```
.github/
  workflows/
    reusable/
      build-and-test.yaml
      security-scan.yaml
      deploy.yaml
  actions/
    container-build/
      action.yml
pipeline-config.yaml
```

### Step 2: Generate Pipeline with Composer

Use the pipeline-composer to generate your CI/CD workflow from configuration:

```bash
# Dry-run to preview the generated workflow
python3 pipeline-composer.py --config pipeline-config.yaml --dry-run

# Generate the actual workflow
python3 pipeline-composer.py --config pipeline-config.yaml \
  --output .github/workflows/main.yaml
```

**Expected Output**:
```
✓ Workflow generated: .github/workflows/main.yaml
  Total jobs: 5
  Configuration: myapp
```

**Verification**:
- Check `.github/workflows/main.yaml` is created
- Verify it contains build, security, and deploy jobs
- Confirm reusable workflow references are correct

### Step 3: Deploy Blue-Green to Staging

Set up staging environment with blue-green deployment:

```bash
# Apply blue-green manifests to staging cluster
kubectl apply -f blue-green-deployment.yaml

# Verify deployments are running
kubectl get deployments -n staging
kubectl get services -n staging

# Expected output:
# NAME             READY   UP-TO-DATE   AVAILABLE   AGE
# myapp-blue       3/3     3            3           10s
# myapp-green      0/0     0            0           10s
```

**Operational Procedure for Blue-Green**:

```bash
# 1. Scale green deployment to match blue
kubectl scale deployment myapp-green -n staging \
  --replicas=$(kubectl get deployment myapp-blue -n staging -o jsonpath='{.spec.replicas}')

# 2. Wait for green to be ready
kubectl rollout status deployment/myapp-green -n staging --timeout=5m

# 3. Run tests against green (via port-forward)
# Note: If port 8080 is in use by Kind, use a different local port (e.g., 8081)
kubectl port-forward -n staging svc/myapp-green 8081:8080 &
curl -f http://localhost:8081/health/ready && echo "Green is healthy"

# 4. Switch traffic to green
kubectl patch service myapp -n staging -p '{"spec":{"selector":{"color":"green"}}}'

# 5. Monitor for issues (5-10 minutes, press Ctrl+C to stop)
watch kubectl get pods -n staging

# 6. If issues, rollback to blue
kubectl patch service myapp -n staging -p '{"spec":{"selector":{"color":"blue"}}}'
```

**Expected Outcomes**:
- Blue deployment handles traffic
- Green deployment successfully scales
- Service selector switch routes traffic with zero downtime
- Rollback available by switching selector back

### Step 4: Deploy Canary to Production

Set up production environment with canary deployment and Istio:

```bash
# Prerequisite: Enable Istio sidecar injection on namespace
kubectl label namespace production istio-injection=enabled

# Apply canary manifests
kubectl apply -f canary-deployment.yaml

# Verify deployments and Istio resources
kubectl get deployments -n production
kubectl get vs -n production
kubectl get dr -n production

# Expected output shows stable (3 replicas) and canary (1 replica)
```

**Canary Promotion Procedure**:

```bash
# 1. Monitor metrics for 5-10 minutes at 10% traffic
# Check Prometheus alerts:
# - CanaryHighErrorRate (> 5%)
# - CanaryHighLatency (> 25% increase)
# - CanaryHighMemory (> 100MB)

# 2. If metrics are healthy, promote to 50% traffic
kubectl patch vs myapp -n production --type merge \
  -p '{"spec":{"http":[{"route":[{"destination":{"host":"myapp","subset":"stable"},"weight":50},{"destination":{"host":"myapp","subset":"canary"},"weight":50}]}]}}'

# 3. Monitor for another 5-10 minutes

# 4. If still healthy, promote to 100%
kubectl patch vs myapp -n production --type merge \
  -p '{"spec":{"http":[{"route":[{"destination":{"host":"myapp","subset":"stable"},"weight":0},{"destination":{"host":"myapp","subset":"canary"},"weight":100}]}]}}'

# 5. If problems detected, instant rollback to 100% stable
kubectl patch vs myapp -n production --type merge \
  -p '{"spec":{"http":[{"route":[{"destination":{"host":"myapp","subset":"stable"},"weight":100},{"destination":{"host":"myapp","subset":"canary"},"weight":0}]}]}}'
```

**Expected Outcomes**:
- Stable version receives all traffic initially
- Canary version receives 10% traffic with monitoring
- Gradual traffic shift based on health metrics
- Instant rollback capability if problems detected

### Step 5: Monitor Deployments with Rollback Controller

Set up automated health monitoring and rollback:

```bash
# Demo mode to see how rollback controller works
python3 rollback-controller.py --demo

# Output shows simulated health degradation and rollback:
# --- Demo: Rollback Controller Simulation ---
# Check #1: 3/3 ready - Healthy
# Check #2: 2/3 ready - Degraded
# Check #3: 1/3 ready - CRITICAL - Triggering rollback
# Check #4: 3/3 ready - Rollback complete - Healthy

# Real deployment monitoring
python3 rollback-controller.py \
  --deployment myapp \
  --namespace production
```

**Integration with Deployment Job**:

Add to your deployment workflow:

```yaml
- name: Monitor and Rollback
  if: success()
  run: |
    python3 rollback-controller.py \
      --deployment myapp \
      --namespace ${{ inputs.environment }} &
    ROLLBACK_PID=$!
    sleep 300  # Monitor for 5 minutes
    kill $ROLLBACK_PID || true
```

**Expected Behavior**:
- Continuous health monitoring post-deployment
- Automatic rollback if pods drop below readiness ratio
- Graceful handling of cluster communication failures

### Step 6: Collect and Analyze Metrics

Set up CI/CD metrics collection:

```bash
# Set up environment
export GITHUB_TOKEN="ghp_your_token_here"
export GITHUB_OWNER="myorg"
export GITHUB_REPO="myrepo"
export OUTPUT_FILE="/tmp/ci-metrics.json"

# Run metrics collector
python3 scripts/ci_metrics.py

# Output shows:
# Collecting metrics for workflow: backend-pipeline.yml
# {
#   "collected_at": "2025-02-21T10:30:00.000000",
#   "repository": "myorg/myrepo",
#   "workflows": {
#     "backend-pipeline.yml": {
#       "current_metrics": {
#         "total_runs": 45,
#         "successful_runs": 43,
#         "failed_runs": 2,
#         "avg_duration_minutes": 12.34,
#         "success_rate_percent": 95.56,
#         ...
#       },
#       "trend": { ... }
#     }
#   }
# }

# Review metrics file
cat /tmp/ci-metrics.json | jq '.workflows."backend-pipeline.yml".current_metrics'
```

**Integration with Dashboards**:
- Feed JSON output to Grafana for visualization
- Set up SLO alerts based on success_rate_percent
- Track build duration trends over time

### Step 7: Run Tests

Validate your implementation:

```bash
# Run full test suite
python3 -m pytest test-pipelines.py -v

# Expected output:
# test_build_and_test_workflow_exists PASSED
# test_deploy_workflow_exists PASSED
# test_security_scan_workflow_exists PASSED
# test_workflows_are_reusable PASSED
# test_blue_green_exists PASSED
# test_canary_exists PASSED
# test_canary_has_weight PASSED
# test_rollback_script_valid PASSED
# test_pipeline_composer_valid PASSED

# Or run with unittest directly
python3 test-pipelines.py
```

**Test Results**:
- All workflow files exist and are readable
- Reusable workflows have workflow_call trigger
- Deployment strategy manifests contain expected configuration
- Python scripts are syntactically valid

## Companion Website Integration

**Note**: The companion website (peh-packt.platformetrics.com) is not currently accessible. The following alignment is based on typical platform engineering handbook structure:

### Expected Website Content Alignment

1. **Videos**: Chapter 8 video content demonstrating:
   - Workflow composition in action
   - Blue-green deployment walkthrough
   - Canary rollout with Istio
   - Rollback controller handling failures

2. **Additional Code Examples**: Extended examples may include:
   - Multi-service orchestration
   - Custom health check implementations
   - Integration with specific cloud providers
   - ArgoCD/Flux integration for GitOps

3. **Interactive Demos**: Browser-based demonstrations of:
   - Pipeline composition UI
   - Canary traffic split visualization
   - Metrics dashboard integration

4. **Discussion Forums**: Community Q&A on:
   - Deploying workflows to specific CI/CD systems
   - Adapting patterns to existing infrastructure
   - Best practices for large-scale deployments

### Accessing Companion Resources

When the website becomes accessible:
1. Visit the Chapter 8 section
2. Download any supplementary code examples
3. Reference video tutorials for visual walkthroughs
4. Check for platform-specific guides (GitLab CI, Jenkins, CircleCI)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│            Pipeline Configuration (YAML)                    │
│  - App name, language, build settings                       │
│  - Stages with strategies and environment targets           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
        ┌──────────────────────────────────────┐
        │   Pipeline Composer Engine           │
        │   (Generates GitHub Actions workflows)
        │   - Validates configuration          │
        │   - Composes reusable components    │
        │   - Injects environment variables   │
        └──────────────────┬───────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   ┌─────────┐      ┌──────────┐    ┌─────────┐
   │  Build  │      │ Security │    │ Deploy  │
   │  & Test │      │   Scan   │    │         │
   │ (Reuse) │      │ (Reuse)  │    │ (Reuse) │
   └────┬────┘      └────┬─────┘    └────┬────┘
        │                │               │
        └────────────────┼───────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  Deployment Strategies             │
        │  ┌──────────┐  ┌──────────────┐   │
        │  │ Direct   │  │ Blue-Green   │   │
        │  │Deploy    │  │ Deployment   │   │
        │  │(kubectl) │  │ (K8s Service)│   │
        │  └──────────┘  └──────────────┘   │
        │  ┌──────────┐                     │
        │  │ Canary   │                     │
        │  │Deploy    │                     │
        │  │(Istio VirtualService)          │
        │  └──────────┘                     │
        └────────────┬─────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │  Observability & Metrics           │
        │  - Prometheus scraping             │
        │  - Health checks (readiness/live)  │
        │  - GitHub Actions metrics API      │
        └────────────────┬────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │   Automated Rollback Controller    │
        │   - Health monitoring              │
        │   - Pod readiness ratio checking   │
        │   - kubectl rollout undo trigger   │
        └────────────────────────────────────┘
```

## Best Practices

### Composition & Reusability

1. **Modular Workflows**: Keep reusable workflows focused on single responsibilities
2. **Clear Contracts**: Define explicit inputs/outputs for each workflow
3. **Flexible Configuration**: Use configurable parameters instead of hardcoded values
4. **Composition Priority**: Compose from reusable components rather than creating monolithic workflows

### Progressive Delivery

1. **Canary Before Rollout**: Always validate with canary traffic before full rollout
2. **Metrics-Driven**: Base promotion decisions on objective metrics, not time
3. **Fast Rollback**: Design deployments to enable quick rollback (< 2 minutes)
4. **Gradual Traffic Shift**: Increase traffic incrementally (10% → 50% → 100%)

### Security Integration

1. **Shift Left**: Run security scans as part of build, not just at deployment
2. **SBOM for Supply Chain**: Generate and track Software Bill of Materials
3. **Container Scanning**: Always scan final container images before deployment
4. **Dependency Management**: Regular dependency audits with automated remediation

### Observability

1. **Instrument Everything**: Add metrics to all deployment steps
2. **Define Health Criteria**: Clear thresholds for success (error rate, latency, memory)
3. **Correlated Monitoring**: Link deployment metadata with application metrics
4. **Retain History**: Keep deployment audit logs for post-mortems

### Automation & Control

1. **Automate Low-Risk Decisions**: Rollback on objective health metrics
2. **Manual Gates for High-Risk**: Require approval for production on first promotion
3. **Incident Tracking**: Log all rollbacks with metrics and timeline
4. **Test Regularly**: Run deployment playbooks in non-production to catch issues

## Execution Examples

### Complete Python Web Service Pipeline

```yaml
# pipeline-config.yaml
name: python-api
language: python
language-version: '3.10'
image-registry: ghcr.io/platform-org

build:
  python-version: '3.10'
  custom-build: 'poetry build'

security:
  scan-container: true
  scan-dependencies: true

stages:
  - name: build-test-scan
    tasks: [build-and-test, security-scan]
  - name: deploy-staging
    strategy: blue-green
    environment: staging
  - name: deploy-prod
    strategy: canary
    environment: production
    canary:
      initial-weight: 10
      max-weight: 100
      interval-minutes: 5
```

### Complete Node.js Service Pipeline

See `.github/workflows/backend-pipeline.yml` for a real-world example with:
- Node.js dependency caching
- Coverage collection with codecov
- Custom container build action
- Environment-based deployment

## Testing the Examples

Run the comprehensive test suite to validate implementation:

```bash
# Unit tests for all components
python3 -m pytest test-pipelines.py -v --tb=short

# Demo rollback controller simulation
python3 rollback-controller.py --demo

# Dry-run pipeline composition
python3 pipeline-composer.py --config pipeline-config.yaml --dry-run

# Validate metrics collection (requires GITHUB_TOKEN)
GITHUB_TOKEN="..." python3 scripts/ci_metrics.py
```

## Troubleshooting

### Workflow Composition Issues

**Problem**: Pipeline composer fails with "Configuration file not found"
```bash
# Solution: Ensure YAML config exists with correct path
ls -la pipeline-config.yaml
python3 pipeline-composer.py --config ./pipeline-config.yaml
```

**Problem**: Generated workflow missing jobs
```bash
# Solution: Check config structure with dry-run first
python3 pipeline-composer.py --config pipeline-config.yaml --dry-run | head -20
```

### Deployment Strategy Issues

**Blue-Green**: Green deployment stuck in pending
```bash
# Check cluster resources
kubectl describe deployment myapp-green -n staging
kubectl top nodes
kubectl logs -n staging -l app=myapp,color=green --tail=20
```

**Canary**: Traffic not splitting in Istio
```bash
# Verify VirtualService configuration
kubectl get vs -n production -o yaml
# Check DestinationRule subsets
kubectl get dr -n production -o yaml
# Validate Prometheus metrics availability
kubectl port-forward -n monitoring prometheus-0 9090:9090
```

### Metrics Collection Issues

**Problem**: CI metrics script returns "API rate limit exceeded"
```bash
# Solution: Use GitHub token with higher rate limits
# Or reduce frequency of collection
export GITHUB_TOKEN="ghp_token_with_full_access"
python3 scripts/ci_metrics.py
```

## Further Reading

### Official Documentation

- **GitHub Actions**: https://docs.github.com/en/actions
- **Reusable Workflows**: https://docs.github.com/en/actions/learn-github-actions/workflow-syntax-for-github-actions#jobsjob_iduses
- **Kubernetes**: https://kubernetes.io/docs/concepts/
- **Istio**: https://istio.io/latest/docs/
- **Prometheus**: https://prometheus.io/docs/

### Platform Engineering References

- **GitOps with Flux**: https://fluxcd.io/
- **ArgoCD Deployments**: https://argoproj.github.io/cd/
- **Progressive Delivery**: https://www.gartner.com/en/documents/3894628
- **SRE Practices**: https://sre.google/

### Related Topics

- **Container Security**: https://aquasecurity.github.io/trivy/
- **SBOM Standards**: https://cyclonedx.org/
- **CodeQL Security**: https://codeql.github.com/

## License

These examples are provided as-is for educational purposes as part of The Platform Engineer's Handbook by Packt Publishing.

---

**Last Updated**: February 2025
**Chapter**: 8 - CI/CD as a Platform Service
**Edition**: Platform Engineer's Handbook (Packt)
