# Chapter 5: Evaluate the User Experience - Platform Engineering Handbook

## Chapter Overview

Chapter 5 focuses on evaluating developer experience (DevEx) by deploying and testing a demo application that simulates a complete platform engineering workflow. The chapter emphasizes reducing friction in developer workflows through self-service deployments, comprehensive observability, and automated security scanning. The key design principles include:

1. **Self-Service**: Developers deploy independently without manual approvals
2. **Clear Feedback Loops**: Immediate visibility into deployment status
3. **Minimal Cognitive Load**: Clear APIs, good documentation, sensible defaults
4. **Automation First**: Remove manual toil from common workflows
5. **Observable Metrics**: Track and visualize platform performance (DORA metrics)
6. **Progressive Disclosure**: Basic tasks easy, advanced tasks possible

The chapter culminates in a "zero-friction" deployment model where a single command provisions a production-ready application with all operational concerns automatically configured.

---

## Code-to-Chapter Mapping

This section maps each code file to its corresponding section and concept in Chapter 5.

### Demo Application Files

#### **demo-app/app.py** (Listing 5.1 - Conceptual)
**Chapter Section**: 5.3 - Deploying as a user
**Concepts**: REST API design, WSGI/Flask application structure, health checks, CRUD operations
**Purpose**: A minimal Flask/WSGI application serving as the demo app for evaluating deployment UX. Implements:
- Health check endpoint (`GET /health`) - required for Kubernetes probes
- CRUD operations on items (`GET /items`, `POST /items`, `PUT /items/<id>`, `DELETE /items/<id>`)
- In-memory data store for simplicity
- JSON request/response handling
- Error handling and validation

**Usage Context**: Demonstrates how a developer creates and deploys a basic microservice through the platform pipeline.

---

#### **demo-app/Dockerfile** (Listing 5.3 - Multi-stage Docker build)
**Chapter Section**: 5.3 - Deploying as a user
**Concepts**: Container security best practices, multi-stage builds, non-root users, health checks
**Purpose**: Multi-stage Dockerfile following security best practices for containerizing the demo app:
- Stage 1 (Builder): Installs dependencies
- Stage 2 (Runtime): Python slim base image, non-root user (appuser:1000), health check configuration
- Includes HEALTHCHECK directive for container orchestration
- Avoids running as root (security principle)
- Minimizes final image size

**Alignment**: Demonstrates how the platform enforces security through container standards without developer friction.

---

#### **demo-app/k8s-manifests.yaml** (Listing 5.5 - Zero-friction deployment concept)
**Chapter Section**: 5.3 - Deploying as a user
**Concepts**: Kubernetes Deployment, Service, HorizontalPodAutoscaler, PodDisruptionBudget, probes
**Purpose**: Complete Kubernetes manifest for production-ready deployment:
- **Deployment** (2 replicas, rolling update strategy)
  - Three health probes: startup, liveness, readiness
  - Resource requests/limits (CPU: 50-200m, Memory: 64-256Mi)
  - Security context (non-root, dropped ALL capabilities)
  - Environment variables for Flask

- **Service** (ClusterIP for internal access)
  - Internal discovery mechanism for other services

- **HorizontalPodAutoscaler** (scales 2-5 replicas)
  - CPU utilization target: 50%
  - Memory utilization target: 70%
  - Aggressive scale-up (100% per 30s), conservative scale-down (50% per 60s)

- **PodDisruptionBudget** (ensures availability)
  - Minimum 1 pod available during disruptions

**Alignment**: Demonstrates self-service deployment with pre-configured production patterns—developers get high-availability setup automatically.

---

### Observability & Instrumentation Files

#### **instrumentation.js** (Listing 5.7 - OpenTelemetry setup)
**Chapter Section**: 5.4 - Application instrumentation for observability
**Concepts**: OpenTelemetry SDK initialization, auto-instrumentation, resource attributes, exporter configuration
**Purpose**: Configures OpenTelemetry for automatic telemetry collection in Node.js applications:
- Initializes NodeSDK with auto-instrumentations for HTTP, Express, etc.
- Sets up OTLP gRPC exporter (configurable via env vars)
- Defines service metadata (name, version, environment)
- Must be required BEFORE any other modules: `node --require ./instrumentation.js app.js`
- Graceful shutdown on SIGTERM

**Manuscript Quote**: "Using a standard like OpenTelemetry, as discussed earlier, provides vendor-neutral instrumentation that prevents lock-in."

**Prerequisites**:
```bash
npm install @opentelemetry/sdk-node \
  @opentelemetry/auto-instrumentations-node \
  @opentelemetry/exporter-trace-otlp-grpc \
  @opentelemetry/exporter-metrics-otlp-grpc \
  @opentelemetry/resources \
  @opentelemetry/semantic-conventions
```

---

#### **app.js** (Listing 5.8 - Custom spans and metrics)
**Chapter Section**: 5.4 - Application instrumentation for observability
**Concepts**: Custom spans, span attributes, nested spans, error handling, OpenTelemetry API usage
**Purpose**: Demonstrates custom instrumentation in Express.js application:
- Creates custom spans for business logic (`fetch-items`)
- Nested spans for database operations (`db-query`)
- Span attributes (e.g., `db.system`, `db.statement`, `app.items.count`)
- Span events (e.g., `query-started`, `query-completed`)
- Error recording and status management
- Simulated database query for demonstration

**Manuscript Concept**: "Custom spans capture information such as Names, attributes, events, status, duration... tracking the application-specific operations."

**Usage**: Requires instrumentation.js to be pre-loaded:
```bash
node --require ./instrumentation.js app.js
```

---

#### **logger.js** (Listing 5.9 - Structured logging with trace context)
**Chapter Section**: 5.4 - Application instrumentation for observability
**Concepts**: Log-trace correlation, Winston logger, trace context injection, structured logging
**Purpose**: Winston logger configuration that injects OpenTelemetry trace context into every log:
- Custom format function extracts active span context
- Injects `trace_id`, `span_id`, `trace_flags` into every log entry
- Enables log-trace correlation for debugging distributed systems
- JSON output format for log aggregation systems
- Default metadata (service name, environment)

**Manuscript Quote**: "Injecting trace context into logs enables log-trace correlation and can easily jump into tracing from your logs."

**Output Example**:
```json
{
  "level": "info",
  "message": "Processing request",
  "service": "demo-app",
  "trace_id": "abc123...",
  "span_id": "def456...",
  "timestamp": "2025-01-20T10:30:00Z"
}
```

---

### Deployment & Self-Service Files

#### **platform-deploy.sh** (Listing 5.4 - Self-service deployment script)
**Chapter Section**: 5.3 - Deploying as a user (self-service mechanism)
**Concepts**: Self-service CLI, Kustomize overlays, ArgoCD integration, namespace automation
**Purpose**: Developer-friendly deployment script enabling zero-touch deployment:
- Validates prerequisites (kubectl, kustomize, argocd)
- Automatically creates namespaces with labels
- Applies Kustomize overlays for environment-specific configuration
- Integrates with ArgoCD for GitOps-based deployment
- Registers application with ArgoCD for continuous reconciliation
- Provides feedback on deployment success

**Usage**:
```bash
./platform-deploy.sh <app-name> <namespace> [environment]
# Example:
./platform-deploy.sh myapp production prod
```

**Manuscript Context**: Demonstrates the "self-service platform" that allows developers to deploy "rapidly while meeting all specific internal requirements" without manual tickets or approvals.

---

#### **secure-deployment.yaml** (Listing 5.6 - Secure Kubernetes deployment)
**Chapter Section**: 5.3 - Deploying as a user (security in deployment pipeline)
**Concepts**: Security context, pod/container security policies, resource limits, health checks
**Purpose**: Kubernetes Deployment manifest demonstrating security best practices:
- **Pod Security Context**:
  - `runAsNonRoot: true`, `runAsUser: 1000`, `fsGroup: 1000`
  - `seccompProfile: RuntimeDefault`

- **Container Security Context**:
  - `allowPrivilegeEscalation: false`
  - `readOnlyRootFilesystem: true`
  - `capabilities.drop: [ALL]`

- **Resource Constraints**:
  - Requests: 100m CPU, 128Mi memory
  - Limits: 500m CPU, 256Mi memory

- **Health Probes**:
  - Liveness and readiness on `/health` endpoint (HTTPS)

- **Observability**:
  - Prometheus scrape annotations
  - OTEL endpoint configuration

**Manuscript Quote**: "Early security scanning in the deployment pipeline to identify vulnerabilities before production can cover challenges around container image scanning for CVEs, secret detection embedded in the code and RBAC validation for proper permissions."

---

### DevEx Measurement Tools

#### **devex-survey.py** (Section 5.2 - Developer experience measurement)
**Chapter Section**: 5.2 - Developer experience as the backbone of platforms
**Concepts**: DevEx metrics, quantitative UX evaluation, category scoring, developer feedback
**Purpose**: Interactive CLI tool that administers a developer experience survey and calculates a composite DevEx score:

**Survey Categories** (10 questions):
1. **Onboarding** (2 questions): Setup time, instruction clarity
2. **Deployment** (2 questions): Ease of deployment, feedback speed
3. **Documentation** (2 questions): Completeness, clarity
4. **Developer Tools** (3 questions): Tool satisfaction, API intuitiveness, error message helpfulness
5. **Feedback Loops** (1 question): Validation speed

**Output**:
- Overall DevEx Score (0-100)
- Score interpretation (Excellent/Good/Fair/Poor)
- Category breakdown with visual bar chart
- Detailed responses
- JSON export capability

**Usage**:
```bash
python devex-survey.py
# Responds to interactive prompts with 1-5 ratings
```

**Manuscript Connection**: Chapter emphasizes that "measuring DevEx became increasingly prevalent" and that DevEx rests on three pillars: efficiency, satisfaction, and impact.

---

#### **friction-analyzer.py** (Section 5.3 - Friction in deployment workflows)
**Chapter Section**: 5.3 - Deploying as a user (identifying workflow friction)
**Concepts**: Workflow analysis, friction scoring, bottleneck identification, optimization opportunities
**Purpose**: Analyzes developer workflows (in YAML format) to identify friction points and calculate a friction score (0-100):

**Workflow Input Format** (YAML):
- Step name, type (manual/automated/semi_automated)
- Time in minutes, dependencies, cognitive load (1-5), error-prone flag, feedback loop presence

**Friction Scoring**:
- Manual steps: +15 points each
- Missing feedback loops: +20 points each
- High cognitive load: +10 points per level
- Error-prone steps: +15 points each
- Time overhead: +0.5 points per minute
- Dependency chains: +5 points per dependency

**Output**:
- Friction score (0-100) with level classification
- Critical path analysis (longest dependency chain)
- Parallelization potential identification
- Specific friction points with priority ratings
- JSON export for tracking

**Example Workflow**:
```yaml
workflow:
  name: "Deploy to Production"
  steps:
    - name: "Local Setup"
      manual: true
      time_minutes: 30
      dependencies: []
    - name: "Commit & Push"
      manual: true
      time_minutes: 5
      dependencies: ["Local Setup"]
    - name: "CI Pipeline"
      automated: true
      time_minutes: 15
      dependencies: ["Commit & Push"]
```

**Usage**:
```bash
python friction-analyzer.py --workflow workflow.yaml [--export report.json]
```

---

#### **platform-kpi-collector.py** (Section 5.2 - Platform KPIs)
**Chapter Section**: 5.2 - Developer experience as the backbone of platforms (KPI measurement)
**Concepts**: DORA metrics, platform performance measurement, deployment frequency, lead time, MTTR, change failure rate
**Purpose**: Collects and analyzes the Four Key Metrics (DORA metrics) from Kubernetes clusters and git repositories:

**Metrics Collected**:
1. **Deployment Frequency**: Deployments per day (from kubectl rollout history)
2. **Lead Time for Changes**: Time from commit to production (minutes, estimated from git)
3. **Mean Time to Recovery (MTTR)**: Recovery time in minutes (estimated from pod restarts)
4. **Change Failure Rate**: Percentage of deployments requiring hotfixes (from cluster events)

**Performance Classification** (DORA Elite thresholds):
- Elite: >1 deployment/day, <1 day lead time, <1 hour MTTR, <15% failure rate
- High: 3+ metrics meet elite threshold
- Medium: 2+ metrics meet elite threshold
- Low: <2 metrics meet elite threshold

**Output**:
- Formatted table with all four metrics
- Performance level classification
- JSON export with detailed breakdown

**Manuscript Context**: Chapter 5.2 states "Figure 5.2 shows the 3 critical axes of the platform KPIs" and discusses efficiency, satisfaction, and impact as fundamental pillars.

**Usage**:
```bash
python platform-kpi-collector.py --namespace default --git-repo /path/to/repo [--export kpis.json]
```

**Prerequisites**: kubectl (for cluster access), git (for repository analysis)

---

#### **test-demo-app.py** (Section 5.5 - Validation)
**Chapter Section**: 5.4 & 5.5 - Testing and validation
**Concepts**: Unit testing, code validation, syntax verification
**Purpose**: Test suite that validates the demo app and DevEx tool configuration:

**Test Coverage**:
- **Demo App Structure**: Dockerfile, app.py, k8s-manifests.yaml existence
- **App Code Validation**: Python syntax and compilation check
- **DevEx Tool Validation**: Syntax check for survey, friction analyzer, and KPI collector scripts

**Usage**:
```bash
# Using Python's unittest
python test-demo-app.py

# Or with pytest for more detailed output
pytest test-demo-app.py -v
```

---

## Prerequisites

### System Requirements
- **Python**: 3.8+ (for all Python scripts)
- **Node.js**: 16+ (for JavaScript app and instrumentation)
- **Docker**: 20.10+ (for containerization)
- **Kubernetes**: 1.24+ (minikube, Docker Desktop, or cloud cluster) - optional for K8s deployment
- **kubectl**: 1.24+ (for Kubernetes operations) - optional
- **git**: 2.30+ (for repository analysis with KPI collector)

### Python Dependencies
Install all Python dependencies:
```bash
pip install -r requirements.txt  # If provided
# Or install individually:
pip install flask pyyaml winston  # For demo app and friction analyzer
```

### Node.js Dependencies
For the Express app with OpenTelemetry instrumentation:
```bash
npm install express @opentelemetry/sdk-node \
  @opentelemetry/auto-instrumentations-node \
  @opentelemetry/exporter-trace-otlp-grpc \
  @opentelemetry/exporter-metrics-otlp-grpc \
  @opentelemetry/api @opentelemetry/resources \
  @opentelemetry/semantic-conventions winston
```

### Optional: Kubernetes Cluster Setup
For full deployment testing:
```bash
# Start minikube
minikube start

# Or use Docker Desktop's built-in Kubernetes

# Verify cluster access
kubectl cluster-info
kubectl get nodes
```

### Optional: OpenTelemetry Collector
For complete observability pipeline:
```bash
# Deploy OpenTelemetry collector to your cluster
kubectl apply -f https://raw.githubusercontent.com/open-telemetry/opentelemetry-helm-charts/main/charts/opentelemetry-collector/values.yaml
```

---

## Step-by-Step Instructions

### Step 1: Understand the Demo Application

**Objective**: Review the demo app structure and deployment model

**Commands**:
```bash
# Examine the Flask app
cat demo-app/app.py

# Review the Dockerfile
cat demo-app/Dockerfile

# Check Kubernetes manifests
cat demo-app/k8s-manifests.yaml
```

**Expected Output**: Understanding of CRUD API endpoints, containerization approach, and K8s deployment strategy

**Next Step**: Step 2 (Run the app locally)

---

### Step 2: Run the Demo Application Locally

**Objective**: Verify the app works outside containers

**Command Option A - Direct Python**:
```bash
# Install Flask
pip install flask

# Run the app
python demo-app/app.py
```

**Expected Output**:
```
Starting Flask application on http://0.0.0.0:5000
```

**Command Option B - Docker**:
```bash
# Build the image
docker build -t platform-demo-app:latest demo-app/

# Run the container
docker run -p 5000:5000 platform-demo-app:latest
```

**Test the App**:
```bash
# Health check
curl http://localhost:5000/health
# Output: {"status": "healthy"}

# Create an item
curl -X POST http://localhost:5000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "My Item", "description": "Test item"}'
# Output: {"data": {"id": "abc123", "name": "My Item", ...}, "status": 201}

# List items
curl http://localhost:5000/items
# Output: {"data": [...], "status": 200}
```

**Next Step**: Step 3 (Deploy to Kubernetes) OR Step 4 (Evaluate DevEx)

---

### Step 3: Deploy to Kubernetes

**Objective**: Deploy the demo app to a Kubernetes cluster

**Prerequisites**:
- Kubernetes cluster running (minikube or cloud)
- kubectl configured to access the cluster
- Docker image pushed to registry (or use local images for minikube)

**Commands**:

**Option A - Using kubectl directly**:
```bash
# For minikube with local images
minikube image build -t platform-demo-app:latest demo-app/

# Apply manifests
kubectl apply -f demo-app/k8s-manifests.yaml

# Verify deployment
kubectl get pods -l app=platform-demo-app
kubectl get svc platform-demo-app
kubectl get hpa platform-demo-app-hpa
```

**Option B - Using the self-service script**:
```bash
# Make the script executable
chmod +x platform-deploy.sh

# Deploy (requires ArgoCD setup)
./platform-deploy.sh myapp default dev
```

**Verify Deployment**:
```bash
# Check pod status
kubectl get pods -l app=platform-demo-app

# Check service endpoints
kubectl get endpoints platform-demo-app

# Port-forward to test locally
kubectl port-forward svc/platform-demo-app 5000:80

# Test via port-forward
curl http://localhost:5000/health
```

**Monitor HPA Scaling**:
```bash
# Watch the HPA behavior (press Ctrl+C to stop watching)
kubectl get hpa platform-demo-app-hpa --watch

# Generate load to trigger scaling (in another terminal)
kubectl run -it --rm debug --image=alpine --restart=Never -- sh
# Inside the pod:
while true; do wget -q -O- http://platform-demo-app; done
```

> **Note**: Press Ctrl+C to stop the watch command after observing the scaling behavior.

**Expected Output**: Pods running (2-5 replicas depending on load), service accessible, HPA scaling up as load increases

**Next Step**: Step 4 (Evaluate DevEx)

---

### Step 4: Evaluate Developer Experience with DevEx Survey

**Objective**: Measure the developer experience of using the platform

**Command**:
```bash
python devex-survey.py
```

**Interactive Prompts** (rate 1-5):
1. How long did setup take? (1=Days, 5=Minutes)
2. How clear were onboarding instructions?
3. How easy is it to deploy changes?
4. How quickly do you get deployment feedback?
5. How complete is the documentation?
6. How clear is the documentation?
7. How satisfied are you with developer tools?
8. How intuitive is the platform API?
9. How helpful are error messages?
10. How quickly can you validate changes?

**Expected Output**:
```
======================================================================
SURVEY RESULTS
======================================================================

Overall DevEx Score: 75/100
Interpretation: Good - Room for improvement in some areas

Category Breakdown:
  Onboarding           ████████░░ 4.0/5
  Deployment           ███████░░░ 3.5/5
  Documentation        ██████░░░░ 3.0/5
  Developer Tools      █████░░░░░ 2.5/5
  Feedback Loops       ████████░░ 4.0/5

======================================================================
```

**Optional: Export Results**:
```bash
# Run survey again and export
python devex-survey.py
# Choose 'y' when prompted to export
# Enter filename: devex_baseline.json
```

**Next Step**: Step 5 (Analyze workflow friction)

---

### Step 5: Analyze Workflow Friction

**Objective**: Identify friction points in the deployment workflow

**Prepare Workflow Definition** (save as `workflow.yaml`):
```yaml
workflow:
  name: "Deploy to Production"
  steps:
    - name: "Local Development Setup"
      manual: true
      time_minutes: 30
      dependencies: []
      cognitive_load: 3
    - name: "Write Code & Tests"
      manual: true
      time_minutes: 60
      dependencies: ["Local Development Setup"]
      cognitive_load: 4
      error_prone: true
    - name: "Commit & Push"
      manual: true
      time_minutes: 5
      dependencies: ["Write Code & Tests"]
      cognitive_load: 1
    - name: "CI/CD Pipeline"
      automated: true
      time_minutes: 15
      dependencies: ["Commit & Push"]
      cognitive_load: 1
      has_feedback: true
    - name: "Deploy to Staging"
      semi_automated: true
      time_minutes: 10
      dependencies: ["CI/CD Pipeline"]
      cognitive_load: 2
    - name: "Manual Testing"
      manual: true
      time_minutes: 30
      dependencies: ["Deploy to Staging"]
      cognitive_load: 3
      error_prone: true
    - name: "Deploy to Production"
      manual: true
      time_minutes: 20
      dependencies: ["Manual Testing"]
      cognitive_load: 4
      error_prone: false
```

**Run Analysis**:
```bash
python friction-analyzer.py --workflow workflow.yaml

# With JSON export
python friction-analyzer.py --workflow workflow.yaml --export friction_report.json
```

**Expected Output**:
```
======================================================================
WORKFLOW FRICTION ANALYSIS REPORT
======================================================================

Total Steps: 7
Total Time (Serial): 170.0 minutes
Critical Path: 170.0 minutes
Parallelization Potential: 0.0%

----------------------------------------------------------------------
Friction Score: 65/100 (High)
----------------------------------------------------------------------

Step Breakdown:
Step Name                Type            Time (min)  Cognitive
----------------------------------------------------------------------
Local Development Setup  Manual          30.0        3
Write Code & Tests       Manual          60.0        4
Commit & Push            Manual          5.0         1
CI/CD Pipeline           Auto            15.0        1
Deploy to Staging        Semi-Auto       10.0        2
Manual Testing           Manual          30.0        3
Deploy to Production     Manual          20.0        4

----------------------------------------------------------------------
Friction Points:
  Step: Write Code & Tests
  Issue: Manual execution
  Impact: Could be automated
  Priority: High

  Step: Manual Testing
  Issue: Error-prone
  Impact: Frequently fails, requires rework
  Priority: High

  Step: Deploy to Production
  Issue: High cognitive load
  Impact: Complex, error-prone step
  Priority: Medium
```

**Interpretation**:
- Score 65 = High friction
- Recommendation: Automate testing, reduce manual deployment steps

**Next Step**: Step 6 (Collect Platform KPIs)

---

### Step 6: Collect Platform KPIs

**Objective**: Measure platform performance using DORA metrics

**Prerequisites**:
- Kubernetes cluster running with demo app deployed
- kubectl configured
- (Optional) git repository path

**Command**:
```bash
# Collect from Kubernetes
python platform-kpi-collector.py --namespace default

# Include git repository for lead time analysis
python platform-kpi-collector.py --namespace default --git-repo /path/to/repo

# Export results
python platform-kpi-collector.py --namespace default --export kpis.json
```

**Expected Output**:
```
======================================================================
PLATFORM KPI COLLECTION
======================================================================

Collecting deployment frequency...
Collecting lead time for changes...
Collecting MTTR...
Collecting change failure rate...

======================================================================
PLATFORM KPI RESULTS
======================================================================
Timestamp: 2025-02-20T10:30:45.123456
Namespace: default

Key Metrics:
----------------------------------------------------------------------
Metric                         Value           Unit
----------------------------------------------------------------------
deployment_frequency           2.5             deployments_per_day
lead_time_for_changes          120             minutes
mean_time_to_recovery          30              minutes
change_failure_rate            5.0             percent

----------------------------------------------------------------------
Overall Performance Level: High
======================================================================
```

**DORA Classification**:
- **Deployment Frequency**: 2.5/day = meets elite threshold (>1/day)
- **Lead Time**: 120 min (2 hours) = meets elite threshold (<1 day)
- **MTTR**: 30 min = meets elite threshold (<1 hour)
- **Change Failure Rate**: 5% = meets elite threshold (<15%)

**Result**: Elite-level platform performance

**Next Step**: Step 7 (Run tests) OR Step 8 (Full integration)

---

### Step 7: Run Tests

**Objective**: Validate all components of the Chapter 5 examples

**Command**:
```bash
# Run all tests
python test-demo-app.py

# Or with pytest for detailed output
pip install pytest
pytest test-demo-app.py -v
```

**Expected Output**:
```
======================================================================
Chapter 5: Demo App and DevEx Tests
======================================================================
test_dockerfile_exists ... ok
test_app_exists ... ok
test_k8s_manifests_exist ... ok
test_app_is_valid_python ... ok
test_survey_script_valid ... ok
test_friction_analyzer_valid ... ok
test_kpi_collector_valid ... ok

======================================================================
Ran 7 tests in 0.045s
OK
```

**Next Step**: Step 8 (Full integration)

---

### Step 8: Full Integration - Complete Workflow

**Objective**: Execute a complete developer experience evaluation loop

**Recommended Execution Order**:

```bash
# 1. Baseline survey (initial state)
echo "Step 1: Baseline DevEx Measurement"
python devex-survey.py
# (Rate all questions, export to devex_baseline.json)

# 2. Analyze current workflow friction
echo "Step 2: Analyze Current Workflow Friction"
python friction-analyzer.py --workflow workflow.yaml --export friction_baseline.json

# 3. Collect baseline KPIs
echo "Step 3: Baseline Platform KPIs"
python platform-kpi-collector.py --namespace default --export kpis_baseline.json

# 4. Deploy demo app (if not already deployed)
echo "Step 4: Deploy Demo Application"
docker build -t platform-demo-app:latest demo-app/
docker run -p 5000:5000 -d platform-demo-app:latest

# 5. Validate the deployment
echo "Step 5: Validate Deployment"
curl http://localhost:5000/health
curl -X POST http://localhost:5000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item"}'

# 6. Test all components
echo "Step 6: Run Test Suite"
python test-demo-app.py

echo "All steps completed! Review exported JSON files for trend analysis."
```

**Output Files Generated**:
- `devex_baseline.json` - DevEx metrics
- `friction_baseline.json` - Workflow friction analysis
- `kpis_baseline.json` - Platform KPIs (DORA metrics)

**Compare Over Time**: Repeat this workflow after platform improvements to measure impact.

---

## Orphan Files (Not Directly Referenced in Chapter)

The following files exist in the code directory but are not explicitly mapped to specific chapter sections:

**File**: `README.md` (old version)
- **Status**: Original README that this document replaces
- **Recommendation**: Archive or remove after confirming new README coverage

All other files are accounted for in the Code-to-Chapter Mapping section above.

---

## Companion Website Alignment

**Note**: The companion website (https://peh-packt.platformetrics.com/) was not accessible during README creation due to network restrictions. The following information is based on manuscript analysis:

### Expected Alignment

1. **Code Repository Link**: The website likely hosts or links to the complete Chapter 5 code repository
2. **Additional Resources**: May include:
   - Recorded walkthrough videos of deployment steps
   - Interactive Kubernetes cluster for testing (sandbox environment)
   - Extended examples not in the manuscript
   - Solution files for Exercise 5.1

### Exercise 5.1: Automated Security Remediation

**Manuscript Reference** (Section 5.3, after secure-deployment.yaml):
> "Exercise 5.1: Develop an automated security remediation script based on the deployment code given above that can automatically detect the issues and resolve them for:
> - Fixing any HTTP-only access
> - Adding missing network policies"

**Status**: No solution file for Exercise 5.1 is included in the code directory. This may be available on the companion website or is intended as a student exercise.

**Recommendation**: Create `security-remediation.sh` as an implementation of Exercise 5.1 using the patterns shown in `platform-deploy.sh` and `secure-deployment.yaml`.

---

## Design Principles Implemented in Code

Each code file demonstrates one or more of the key design principles:

| Principle | Files | Implementation |
|-----------|-------|-----------------|
| **Self-Service** | `platform-deploy.sh`, `app.js`, `demo-app/` | Developers deploy independently with pre-configured templates |
| **Feedback Loops** | `instrumentation.js`, `logger.js`, `devex-survey.py` | Immediate visibility via observability and surveys |
| **Minimal Cognitive Load** | `demo-app/Dockerfile`, `secure-deployment.yaml`, `platform-deploy.sh` | Security/operational concerns automated, not manual |
| **Automation First** | `demo-app/k8s-manifests.yaml` (HPA), `platform-deploy.sh` | Autoscaling, GitOps, automated deployments |
| **Observable Metrics** | `platform-kpi-collector.py`, `app.js`, `instrumentation.js` | DORA metrics, custom spans, structured logging |
| **Progressive Disclosure** | `devex-survey.py`, `friction-analyzer.py` | Simple entry point (survey), advanced analysis tools available |

---

## Common Workflows

### Workflow A: Baseline Evaluation (Day 1)
For a new platform team starting Chapter 5 exercises:

```bash
# 1. Review the demo app
cd demo-app
cat app.py
cat Dockerfile
cat k8s-manifests.yaml

# 2. Run locally to understand the app
python app.py

# 3. Assess current DevEx
python devex-survey.py

# 4. Analyze current workflow
cp workflow.yaml workflow_current.yaml
# Edit workflow_current.yaml to reflect your current deployment process
python friction-analyzer.py --workflow workflow_current.yaml --export friction_current.json

# 5. Collect baseline KPIs (if cluster available)
python platform-kpi-collector.py --namespace default --export kpis_current.json
```

**Time**: ~30 minutes
**Outputs**: DevEx score, friction score, KPI baseline

---

### Workflow B: Full Platform Evaluation (Week 1)
For teams implementing all Chapter 5 concepts:

```bash
# Day 1: Setup
./steps_1_and_2.sh  # Run app locally
./step_3.sh         # Deploy to K8s

# Day 2-4: Observability
npm install @opentelemetry/...
node --require ./instrumentation.js app.js
# Monitor logs and traces

# Day 5: Measurement
python devex-survey.py
python friction-analyzer.py --workflow workflow.yaml
python platform-kpi-collector.py --namespace default

# Analyze improvements from baseline
```

**Time**: ~5 days
**Outputs**: Full observability pipeline, complete DevEx assessment

---

### Workflow C: CI/CD Integration Testing
For teams building deployment automation:

```bash
# Build and push app
docker build -t registry.company.com/demo-app:v1.0.0 demo-app/
docker push registry.company.com/demo-app:v1.0.0

# Deploy via self-service
./platform-deploy.sh demo-app default production

# Validate deployment
kubectl get pods -n default -l app=demo-app
kubectl logs -n default -l app=demo-app

# Run tests
python test-demo-app.py

# Collect post-deployment KPIs
python platform-kpi-collector.py --namespace default
```

**Time**: ~10 minutes
**Success Criteria**: All tests pass, pods running, health checks returning 200

---

## Troubleshooting

### Problem: `kubectl: command not found`
**Solution**: Install kubectl or use `minikube kubectl` as a wrapper

### Problem: Flask app fails to start with `ModuleNotFoundError: No module named 'flask'`
**Solution**: `pip install flask`

### Problem: Docker image build fails with permission error
**Solution**: Run with sudo or add user to docker group: `sudo usermod -aG docker $USER`

### Problem: HPA not scaling (0 replicas scaling to 2-5)
**Solution**:
- Ensure metrics-server is installed: `kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml`
- Wait 30 seconds for metrics to populate

### Problem: OpenTelemetry exporter fails to connect
**Solution**:
- Verify endpoint: `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.monitoring:4317`
- Check network connectivity: `telnet otel-collector.monitoring 4317`
- Fallback: `OTEL_SDK_DISABLED=true` to disable for testing

---

## Summary of Key Concepts

### Three Pillars of DevEx (Chapter 5.2)
1. **Efficiency**: Reduction in time on repetitive tasks
2. **Satisfaction**: Reduction in friction for developers
3. **Impact**: Business value from improved developer productivity

### Four Key Metrics (DORA - Chapter 5.2)
1. **Deployment Frequency**: How often code is deployed (higher is better)
2. **Lead Time for Changes**: Time from commit to production (lower is better)
3. **Mean Time to Recovery (MTTR)**: Recovery time from failures (lower is better)
4. **Change Failure Rate**: % of deployments needing hotfixes (lower is better)

### Five Friction Reduction Principles (Chapter 5.2)
1. Self-service deployment without approvals
2. Clear feedback loops with immediate visibility
3. Minimal cognitive load on developers
4. Automation of repetitive tasks
5. Observable metrics for continuous improvement

---

## Further Reading

- [DORA: State of DevOps Reports](https://dora.dev/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [Container Security Best Practices](https://kubernetes.io/docs/concepts/security/)
- [Developer Experience: Atlassian Research](https://www.atlassian.com/developer-experience)

---

**Last Updated**: February 2025
**Chapter**: 5 - Evaluate the User Experience
**Handbook**: The Platform Engineer's Handbook (Packt Publishing)
