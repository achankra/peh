# Chapter 11: Validating Compliance with Policy-as-Code

**The Platform Engineer's Handbook**

## Chapter Overview

This chapter demonstrates how to implement **Policy-as-Code** using **Open Policy Agent (OPA)** and its Kubernetes admission controller variant, **OPA Gatekeeper**. Rather than treating compliance as a retroactive audit activity, you will learn to enforce policies proactively at the Kubernetes API boundary, catching misconfigurations before they reach production.

### Key Concepts Covered

1. **OPA Gatekeeper** - Kubernetes admission controller for policy enforcement
2. **Rego Policy Language** - Declarative language for expressing compliance policies
3. **ConstraintTemplates & Constraints** - Infrastructure for defining and applying policies
4. **Shift-Left Testing with conftest** - Validate manifests locally before deployment
5. **Compliance Dashboards** - Monitor policy violations and track remediation progress
6. **Balancing Enforcement with Developer Experience** - Gradual rollout strategies

## Code-to-Chapter Mapping

This directory contains production-ready examples tied to specific chapter sections and listings:

### Core Gatekeeper Infrastructure

| File | Chapter Section | Purpose |
|------|-----------------|---------|
| `gatekeeper-install.yaml` | 11.1 Deploying an Admission Controller | Complete Kubernetes manifests for deploying OPA Gatekeeper (namespace, ValidatingWebhookConfiguration, MutatingWebhookConfiguration, RBAC, deployments) |
| `install-gatekeeper.sh` | 11.1 | Helm-based alternative installation script |
| `constraint-template.yaml` | 11.1, Listing 11.1 | Basic ConstraintTemplate for K8sRequiredResources policy (resource requests/limits validation) |
| `constraint-template-security-baselines.yaml` | 11.2, Listing 11.6 | Security baseline ConstraintTemplate (privileged containers, read-only filesystem, dangerous capabilities) |

### Policy Definitions (Rego + Constraints)

| File | Chapter Section | Purpose |
|------|-----------------|---------|
| `policies/require-resource-limits.yaml` | 11.1, 11.2 | ConstraintTemplate enforcing CPU/memory requests and limits on all containers, with helper functions and examples |
| `policies/deny-privileged-containers.yaml` | 11.2 | ConstraintTemplate preventing privileged containers, root execution, and privilege escalation; includes exempt images logic |
| `policies/restrict-image-registries.yaml` | 11.2 | ConstraintTemplate restricting container images to approved registries; includes registry extraction and allowlist matching |
| `policies/require-labels.yaml` | 11.2 | ConstraintTemplate mandating team, owner, and cost-center labels for accountability and chargeback |
| `policies/require-tests-passed.rego` | 11.2 (Unit Testing) | Rego policy requiring test-results="passed" annotation on Deployments (demonstrates Rego assertion patterns) |
| `policies/require-tests-passed_test.rego` | 11.2, Listing 11.8 | Unit tests for require-tests-passed.rego policy (demonstrates Rego test syntax) |

### Constraint Instances

| File | Chapter Section | Purpose |
|------|-----------------|---------|
| `constraints/require-resources.yaml` | 11.1, Listing 11.2 | Constraint instance of K8sRequiredResources ConstraintTemplate, excludes system namespaces |
| `constraints/require-resource-limits.yaml` | 11.2 | Constraint instance of K8sRequireResourceLimits, enforces CPU/memory on all containers |
| `constraints/deny-privileged-containers.yaml` | 11.2 | Constraint instance of K8sDenyPrivilegedContainers, blocks privileged pods |
| `constraints/restrict-image-registries.yaml` | 11.2 | Constraint instance of K8sRestrictImageRegistries, enforces approved registries |
| `constraints/require-labels.yaml` | 11.2 | Constraint instance of K8sRequireLabels, requires team/owner/cost-center labels |
| `constraints/require-compliance-labels.yaml` | 11.2 | Constraint instance of K8sRequireLabels, enforces team, cost-center, and compliance-level labels on Deployments |

### Policy Testing Manifests

| File | Chapter Section | Purpose |
|------|-----------------|---------|
| `test-pod-violation.yaml` | 11.1, 11.2 | Sample Kubernetes manifests with **intentional policy violations** (no resource limits, `:latest` tags, privileged containers, missing labels, running as root). Use these to test Gatekeeper enforcement and conftest validation. |

### Shift-Left Testing with conftest

| File | Chapter Section | Purpose |
|------|-----------------|---------|
| `conftest-tests/policy.rego` | 11.3, Shift-Left Policy Testing | Comprehensive conftest Rego policies for local manifest validation (resource limits, security context, labels, registries) |
| `conftest-tests/test-manifests.yaml` | 11.3 | Sample Kubernetes manifests demonstrating compliant and non-compliant deployments for conftest testing |
| `run-conftest.sh` | 11.3 | Shell script to run conftest validation against manifests with color-coded output, summary statistics, and CI/CD-friendly `--strict` mode |
| `.pre-commit-config.yaml` | 11.3 | Pre-commit framework configuration that runs conftest, YAML linting, and Dockerfile checks automatically before each commit — enforcing shift-left validation in the developer workflow |

### Compliance Monitoring & Dashboards

| File | Chapter Section | Purpose |
|------|-----------------|---------|
| `prometheus-gatekeeper-config.yaml` | 11.4, Listing 11.9 | Prometheus ConfigMap configuring a scrape target for Gatekeeper's native metrics (`gatekeeper_violations`, `gatekeeper_constraints`) for a standalone Prometheus. Prometheus Operator ignores it and uses the ServiceMonitor below |
| `gatekeeper-metrics-servicemonitor.yaml` | 11.4 | Prometheus Operator ServiceMonitor + Service for automatic metric discovery and scraping from Gatekeeper |
| `grafana-compliance-dashboard.json` | 11.4, Listing 11.11 | Grafana dashboard JSON showing Total Violations, Violations by Constraint, Violations by Namespace, and Compliance Rate |
| `compliance-dashboard.py` | 11.4, Listing 11.12 | Python script querying Kubernetes Gatekeeper events and generating compliance reports (violations by policy, namespace, severity) |
| `scripts/gatekeeper_exporter.py` | 11.4 | Custom Prometheus exporter that queries Gatekeeper audit results via the Kubernetes API and exposes 9 metrics (violations_total, by_policy, by_namespace, by_kind, by_severity, constraint_count, audit_timestamp, collection_duration, collection_errors). Runs as a standalone HTTP server for Prometheus scraping. |

### CI/CD Integration

| File | Chapter Section | Purpose |
|------|-----------------|---------|
| `.github/workflows/policy-tests.yaml` | 11.3, CI/CD Integration | GitHub Actions workflow testing Rego policies with OPA, validating syntax, running conftest on constraints, linting YAML manifests |
| `.github/workflows/validate.yml` | 11.3 | Alternative CI/CD workflow for conftest-based pre-deployment validation |

### Integration Tests

| File | Chapter Section | Purpose |
|------|-----------------|---------|
| `test-policies.py` | 11.3, 11.4 | Python unittest suite simulating policy violations and testing both offline (conftest) and live (`--live`, Gatekeeper admission via `kubectl --dry-run=server`) enforcement |

## Orphan Files Flagged

**None identified.** All files in this directory are documented and tied to specific chapter concepts.

## Prerequisites

### Running This Chapter Standalone

> If you are jumping into this chapter without completing earlier chapters, use these commands to set up the infrastructure dependencies. If you already have them running, skip this section.

> **Note:** If you completed Chapter 2, Gatekeeper is already installed by Flux (`HelmRelease/gatekeeper` in `flux-system`, pods in `gatekeeper-system`). Skip the Gatekeeper install below and go straight to Phase 1.2 to verify it. Otherwise, OPA Gatekeeper can be installed via Helm (shown below) or via raw manifests. Either method works.

```bash
# 1. Start Docker Desktop (macOS: open from Applications or Spotlight)
open -a "Docker"
# Wait for the Docker engine to start before continuing

# 2. Create a Kind cluster (skip if you already have one)
kind get clusters                       # Check for existing clusters
kind create cluster --name platform-dev # Create one if none listed
kubectl get nodes                       # Verify node(s) are Ready

# Install OPA Gatekeeper
helm repo add gatekeeper https://open-policy-agent.github.io/gatekeeper/charts
helm repo update
helm install gatekeeper gatekeeper/gatekeeper --version 3.23.1 --namespace gatekeeper-system --create-namespace

```

### Kubernetes Environment
- **Kubernetes cluster** v1.18+ (v1.24+ recommended for latest webhook API)
- **kubectl** configured with cluster admin access
- ~200MB memory allocation for Gatekeeper components (audit, controller-manager, constraint processing)

### OPA Gatekeeper Installation
- **OPA Gatekeeper** v3.23.1 (or use Helm chart: `open-policy-agent/gatekeeper`)
- ValidatingWebhookConfiguration and MutatingWebhookConfiguration supported (standard in K8s v1.18+)
- Certificate management for webhook TLS (included in gatekeeper-install.yaml)

### Shift-Left Testing
- **conftest** v0.71.1 (specified in `.pre-commit-config.yaml`; used in CI/CD workflows)
  - Installation: `brew install conftest` (macOS) or download from https://github.com/open-policy-agent/conftest/releases
- **OPA CLI** (opa test, opa parse) for policy unit testing (installed with conftest or separately)
- **pre-commit** framework (for shift-left validation hooks in `.pre-commit-config.yaml`)
  - Installation: `brew install pre-commit` (macOS) or `pip3 install pre-commit`
- **Python** 3.8+ (for test-policies.py, compliance-dashboard.py, and gatekeeper_exporter.py)
  ```bash
  pip3 install prometheus-client kubernetes pyyaml
  ```

### Compliance Monitoring
- **Prometheus** (kube-prometheus-stack chart 92.1.1; optional but recommended for compliance dashboard)
- **Grafana** (bundled with kube-prometheus-stack chart 92.1.1; optional for compliance dashboard visualization)
- **Prometheus Operator** (if using gatekeeper-metrics-servicemonitor.yaml)

### For CI/CD Integration
- **GitHub Actions** (if using .github/workflows files)
- **git pre-commit hooks** (optional, for local policy validation before commit)

## Step-by-Step Instructions

### Phase 1: Deploy OPA Gatekeeper

#### 1.1 Choose Installation Method

> **Already installed in Chapter 2?** Skip this step. Flux manages Gatekeeper there; installing it again with `helm install` or `kubectl apply` would conflict with the Flux-managed release. Confirm it is healthy and continue with 1.2:
>
> ```bash
> kubectl get helmrelease gatekeeper -n flux-system
> # Expected: READY True
> ```

**Option A: kubectl (Manual)**
```bash
# Review the manifest
cat gatekeeper-install.yaml | head -50

# Deploy Gatekeeper
kubectl apply -f gatekeeper-install.yaml

# Watch deployment progress
kubectl get pods -n gatekeeper-system -w
kubectl get validatingwebhookconfigurations,mutatingwebhookconfigurations
```

**Option B: Helm (Recommended)**
```bash
# Add Gatekeeper Helm repo
helm repo add gatekeeper https://open-policy-agent.github.io/gatekeeper/charts
helm repo update

# Install Gatekeeper
helm install gatekeeper gatekeeper/gatekeeper --version 3.23.1 -n gatekeeper-system --create-namespace

# Verify installation
helm list -n gatekeeper-system
```

#### 1.2 Verify Gatekeeper Installation

```bash
# Check if Gatekeeper pods are running
kubectl get pods -n gatekeeper-system
# Expected: gatekeeper-audit-*, gatekeeper-controller-manager-*, webhook-* pods in Running state

# Verify webhook configurations
kubectl get validatingwebhookconfigurations | grep gatekeeper
kubectl get mutatingwebhookconfigurations | grep gatekeeper

# Check webhook logs for errors
kubectl logs -n gatekeeper-system deployment/gatekeeper-audit
kubectl logs -n gatekeeper-system deployment/gatekeeper-controller-manager
```

**Expected Output:**
```
NAME                                       READY   STATUS    RESTARTS   AGE
gatekeeper-audit-5d7f4c9d7-x2k8w          1/1     Running   0          2m
gatekeeper-controller-manager-6b8d4-7p9z  1/1     Running   0          2m
gatekeeper-webhook-6b8d4-abc12            1/1     Running   0          2m
```

### Phase 2: Deploy Policies (Audit Mode)

#### 2.1 Deploy Policy Templates & Constraints

```bash
# Deploy all ConstraintTemplates (standalone + policies/)
kubectl apply -f constraint-template.yaml
kubectl apply -f constraint-template-security-baselines.yaml
kubectl apply -f policies/

# Wait for Gatekeeper to register ALL CRDs from ConstraintTemplates
echo 'Waiting for CRDs...'
until kubectl get crd \
  k8sdenyprivilegedcontainers.constraints.gatekeeper.sh \
  k8srequirelabels.constraints.gatekeeper.sh \
  k8srequireresourcelimits.constraints.gatekeeper.sh \
  k8srestrictimageregistries.constraints.gatekeeper.sh \
  k8srequiredresources.constraints.gatekeeper.sh \
  k8ssecuritybaselines.constraints.gatekeeper.sh \
  >/dev/null 2>&1; do sleep 3; done
echo 'All CRDs registered!'

# Verify ConstraintTemplates are created
kubectl get constrainttemplates
# Expected: k8srequiredresources, k8ssecuritybaselines, k8srequireresourcelimits, etc.

# Deploy Constraint instances (reference the CRDs created above)
kubectl apply -f constraints/

# Verify Constraints are instantiated
kubectl get constraints -A
```

**Expected Output:**
```
NAME                                 ENFORCEMENT-ACTION   TOTAL-VIOLATIONS
deny-privileged-containers           dryrun
require-compliance-labels            dryrun               57
require-labels                       dryrun
require-resource-limits              dryrun
require-resources                    dryrun               29
restrict-image-registries            dryrun
```

> **Coming from Chapters 2 and 3?** None of the templates above are installed yet, so apply everything as written. Your cluster already has other Gatekeeper constraints from those chapters (Ch02: `require-limits`, `allowed-registries`; Ch03: `namespace-must-have-team`, `require-resource-limits`), so `kubectl get constraints -A` will list them alongside the Ch11 ones, and the Ch03 ones are in `deny` mode rather than `dryrun`. Some names look alike but are different kinds: `K8sRequiredLabels` (Ch03) vs `K8sRequireLabels` (Ch11), and `K8sRequiredLimits` (Ch02) vs `K8sRequireResourceLimits` (Ch11).

> **Registry allowlists differ:** Ch11's `restrict-image-registries` is stricter than Ch02's `allowed-registries`. Ch11 allows `gcr.io/`, `registry.example.com/`, `quay.io/my-org/`, `docker.io/library/`, `k8s.gcr.io/` and `xpkg.crossplane.io/`, so images from `ghcr.io/`, `registry.k8s.io/` and `registry.istio.io/`, which Ch02 allows, are reported as violations. On a cluster with the earlier chapters' workloads (demo app, Istio) expect dozens of findings, for example `Image 'ghcr.io/stefanprodan/podinfo:6.15.0' is from unauthorized registry`. This is intentional for the audit demo and harmless in `dryrun`. Add your registries to `constraints/restrict-image-registries.yaml` before switching it to `deny`.

> **Note:** All constraints use `dryrun` (audit mode) so you can monitor violations without blocking deployments. This is critical — using `deny` enforcement would block Helm installs in later chapters (e.g., OpenCost in Ch12) because third-party charts typically don't include your custom labels. Violation counts appear after Gatekeeper's next audit cycle (typically 60 seconds).

#### 2.2 Check Initial Audit Results

> **Name clash with Chapter 3:** If you did Ch03, a constraint named `require-resource-limits` already exists there (kind `ResourceLimits`) next to the Ch11 one (kind `K8sRequireResourceLimits`). A bare `kubectl describe constraint require-resource-limits` can return the Ch03 one, so name the kind to see the Ch11 constraint, for example `kubectl describe k8srequireresourcelimits require-resource-limits`. The `kubectl get constraint require-resource-limits` commands below need the same change.

```bash
# View constraint status and violation counts
kubectl describe constraint require-resource-limits

# Get detailed violations
kubectl get constraint require-resource-limits -o jsonpath='{.status.violations}' | jq .

# Count violations by constraint
for constraint in $(kubectl get constraints -o jsonpath='{.items[*].metadata.name}'); do
  violations=$(kubectl get constraint $constraint -o jsonpath='{.status.totalViolations}')
  echo "$constraint: $violations violations"
done
```

**Expected Output (Audit Mode):**
```
require-resources: 29 violations
require-compliance-labels: 57 violations
```

> **Why so many violations?** Gatekeeper audits all existing resources in non-excluded namespaces. Most system workloads (CoreDNS, local-path-provisioner, Backstage, etc.) lack the required labels and resource annotations. This is expected — the high violation count demonstrates why starting in audit mode (`enforcementAction: dryrun`) is critical before enforcing.

### Phase 3: Shift-Left Testing with conftest

#### 3.1 Install conftest

```bash
# macOS
brew install conftest

# Linux
wget https://github.com/open-policy-agent/conftest/releases/download/v0.46.0/conftest_0.46.0_Linux_x86_64.tar.gz
tar xzf conftest_0.46.0_Linux_x86_64.tar.gz
sudo mv conftest /usr/local/bin/

# Verify installation
conftest --version
# Expected: conftest 0.46.0
```

#### 3.2 Validate Test Manifests

```bash
# Test the provided sample manifests (expect mixed pass/fail results)
conftest test -p conftest-tests/policy.rego conftest-tests/test-manifests.yaml
```

**Expected:** A mix of passes, warnings, and failures. The test manifests contain both compliant and intentionally non-compliant resources:

```
56 tests, 36 passed, 3 warnings, 11 failures, 0 exceptions
```

Failures include missing labels (`team`, `owner`, `cost-center`), missing resource limits, privileged containers, unauthorized registries, and running as root. These are intentional — the test manifests demonstrate what each policy catches. The 36 passing tests confirm that compliant resources are correctly allowed through.

#### 3.3 Test Against Your Own Manifests

```bash
# Create a test deployment manifest
cat > /tmp/my-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    team: backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: api
        image: gcr.io/my-project/api:v1.0
        # Missing resources - should fail conftest
EOF

# Run conftest (will fail)
conftest test -p conftest-tests/policy.rego /tmp/my-deployment.yaml

# Expected: FAIL - Container 'api' missing CPU requests
```

#### 3.4 Fix Violations and Retest

```bash
# Fix the manifest
cat > /tmp/my-deployment-fixed.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    team: backend
    owner: alice@example.com
    cost-center: "1234"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: api
        image: gcr.io/my-project/api:v1.0
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
        securityContext:
          privileged: false
          runAsNonRoot: true
          allowPrivilegeEscalation: false
EOF

# Retest (will pass)
conftest test -p conftest-tests/policy.rego /tmp/my-deployment-fixed.yaml
# Expected: 2 tests, 2 passed, 0 failed
```

#### 3.5 Use the run-conftest.sh Script

Instead of running conftest manually, use the provided script for consistent validation with summary output:

```bash
# Run against the test manifests
chmod +x run-conftest.sh
./run-conftest.sh conftest-tests/test-manifests.yaml

# Run against the intentionally non-compliant test-pod-violation.yaml
./run-conftest.sh test-pod-violation.yaml
```

**Expected:** Both commands will show `FAILED` in the validation summary. This is correct — the test manifests contain intentional violations to demonstrate the policies. The wrapper script adds colour-coded output and a summary count of passes vs failures, making it easy to use in CI/CD pipelines.

```bash
# Use --strict mode for CI/CD (returns non-zero exit code on any failure)
./run-conftest.sh test-pod-violation.yaml --strict
```

#### 3.6 Test Policy Violations with test-pod-violation.yaml

Use the provided violation manifest to confirm policies catch common mistakes:

```bash
# Review the intentional violations
cat test-pod-violation.yaml

# Run conftest against it — all should fail
conftest test -p conftest-tests/policy.rego test-pod-violation.yaml

# Expected: Multiple failures for missing resources, privileged containers, :latest tags, etc.
```

#### 3.7 Add Pre-Commit Hooks (Optional)

The `.pre-commit-config.yaml` in this directory configures automatic conftest validation before every commit:

```bash
# Install pre-commit framework (if not already installed)
pip3 install pre-commit

# Copy the config to your repo root and install hooks
cp .pre-commit-config.yaml /path/to/your/repo/
cd /path/to/your/repo
pre-commit install

# Run the conftest hook against all Ch11 files
pre-commit run conftest --all-files
```

**Expected:** The conftest hook will show FAIL for files containing intentionally non-compliant manifests (like `test-pod-violation.yaml`). Infrastructure files (ConstraintTemplates, ServiceMonitors) will also fail label checks because they are not Kubernetes Deployments — conftest applies all rules uniformly. This is normal; in a real project you would scope the hook to only validate application manifests.

### Phase 4: Test Policy Enforcement

#### 4.1 Run Integration Tests

```bash
# Run the test-policies.py suite (offline mode - no cluster required)
python3 test-policies.py
```

**Expected:** All 6 tests pass:

```
test_conftest_compliant_passes ... ok
test_compliant_deployment_passes ... ok
test_missing_labels_detected ... ok
test_no_limits_detected ... ok
test_privileged_container_detected ... ok
test_untrusted_registry_detected ... ok
Ran 6 tests in 0.2s — OK
```

The test suite validates that compliant manifests (with labels, resource limits, approved registries, and non-privileged security contexts) pass conftest, while non-compliant manifests are correctly flagged.

#### 4.2 Test Against Live Cluster

```bash
# Run the offline tests plus the live Gatekeeper tests against your cluster
python3 test-policies.py --live
```

Requires the `K8sRequiredResources` ConstraintTemplate from step 2.1 (`constraint-template.yaml`). The live tests do not change your Chapter 11 constraints. They create a scratch namespace (`peh-policy-test`) and a temporary deny-mode constraint (`peh-live-test`) scoped to that namespace, submit two pods with `kubectl apply --dry-run=server`, and delete both afterwards (nothing is ever created from the pods).

**Expected:** The 6 offline tests plus 2 live tests pass:

```
test_pod_with_resources_admitted ... ok
test_pod_without_resources_denied ... ok
Ran 8 tests in ~2s — OK
```

The pod without requests/limits is rejected with `[peh-live-test] Container app is missing resource limits`, and the pod with them is admitted. Gatekeeper takes a few seconds to start enforcing the new constraint, so the first run pauses briefly in setup.

#### 4.3 Manually Test Admission Webhook

All constraints ship in `dryrun` mode so they don't block Helm installs in later chapters (e.g., OpenCost in Ch12). To demonstrate live enforcement, temporarily switch one constraint to `deny`:

```bash
# Temporarily enable deny enforcement on require-resources
kubectl patch k8srequiredresources require-resources \
  --type merge -p '{"spec":{"enforcementAction":"deny"}}'

# Non-compliant: no resource limits → DENIED by Gatekeeper
kubectl run test-noncompliant --image=docker.io/library/nginx --dry-run=server
```

**Expected:** Gatekeeper denies the request because the pod has no resource limits:

```
Error from server (Forbidden): admission webhook "validation.gatekeeper.sh" denied the request:
[require-resources] Container test-noncompliant is missing resource limits
[require-resources] Container test-noncompliant is missing resource requests
```

> If you completed Chapter 2, its `require-limits` constraint also denies this pod, so you will additionally see `[require-limits] Container test-noncompliant is missing required cpu limit` (and `memory`). The `[require-resources]` lines confirm the Chapter 11 constraint is enforcing. The image is fully qualified because Chapter 2's `allowed-registries` rejects bare image names like `nginx`.

```bash
# Compliant: with resource limits → ACCEPTED by Gatekeeper
# The override must reuse the container name (test-compliant); a different name adds a second container
kubectl run test-compliant --image=docker.io/library/nginx --dry-run=server \
  --overrides='{"spec":{"containers":[{"name":"test-compliant","image":"docker.io/library/nginx","resources":{"limits":{"cpu":"100m","memory":"128Mi"},"requests":{"cpu":"50m","memory":"64Mi"}}}]}}'
```

**Expected:** `pod/test-compliant created (server dry run)` — Gatekeeper allows the pod because it has proper resource limits. The `--dry-run=server` flag validates against the admission webhook without actually creating the pod.

```bash
# IMPORTANT: Switch back to dryrun so later chapters are not blocked
kubectl patch k8srequiredresources require-resources \
  --type merge -p '{"spec":{"enforcementAction":"dryrun"}}'
```

### Phase 5: Set Up Compliance Monitoring

#### 5.1 Deploy Prometheus Scrape Configuration

```bash
# Create monitoring namespace (safe to re-run if it already exists)
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Deploy Prometheus ConfigMap for Gatekeeper metrics
kubectl apply -f prometheus-gatekeeper-config.yaml

# Verify ConfigMap
kubectl get configmap -n monitoring prometheus-gatekeeper -o yaml
```

> **Already running kube-prometheus-stack (Chapter 4)?** The `monitoring` namespace and Prometheus Operator already exist. Prometheus Operator does not read this ConfigMap, so applying it changes nothing on its own. The scraping that actually works for you is the ServiceMonitor in 5.2. Apply this ConfigMap only if you run a standalone Prometheus and mount it there.

#### 5.2 Deploy Prometheus Operator ServiceMonitor (Optional)

```bash
# If using Prometheus Operator (https://prometheus-operator.dev/)
kubectl apply -f gatekeeper-metrics-servicemonitor.yaml

# Verify ServiceMonitor
kubectl get servicemonitor -n gatekeeper-system

# Verify Service is created
kubectl get svc -n gatekeeper-system | grep gatekeeper

# Verify Prometheus picked up the targets (about a minute after applying)
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090 &
curl -s localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | select(.scrapePool | test("gatekeeper")) | "\(.labels.pod) \(.health)"'
kill %1
```

**Expected:** three targets (the audit pod and two controller-manager pods) with health `up`. Gatekeeper's native metrics are then queryable, for example `gatekeeper_violations` (a gauge with an `enforcement_action` label) and `gatekeeper_constraints`. Note that Gatekeeper does not expose `gatekeeper_violations_total`; that name belongs to the custom exporter in 5.5.

#### 5.3 Generate Compliance Reports

```bash
# Run the compliance dashboard generator
python3 compliance-dashboard.py

# Output: JSON report with violations by policy, namespace, severity
# Example output:
# {
#   "summary": {
#     "total_violations": 47,
#     "policies_enforcing": 3,
#     "policies_auditing": 2
#   },
#   "violations_by_policy": {
#     "require-resource-limits": 25,
#     "require-labels": 18,
#     ...
#   }
# }

# Generate markdown report
python3 compliance-dashboard.py --format markdown --output compliance-report.md
cat compliance-report.md
```

#### 5.4 Set Up Grafana Dashboard

```bash
# If Grafana is installed, import the dashboard
# 1. Navigate to Grafana: http://localhost:3000
# 2. Menu > Dashboards > Import
# 3. Upload: grafana-compliance-dashboard.json
# 4. Select Prometheus data source
# 5. Click Import

# Or use curl to import programmatically
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @grafana-compliance-dashboard.json

# Expected: Dashboard "Gatekeeper Compliance" displays:
#   - Total Violations (stat panel with color thresholds)
#   - Violations by Constraint (bar chart)
#   - Violations by Namespace (table)
#   - Compliance Rate (gauge)
```

Two panels use Gatekeeper's native metrics and work once the 5.2 ServiceMonitor is scraped:

| Panel | Query | Source |
|-------|-------|--------|
| Total Violations | `sum(gatekeeper_violations)` | native |
| Compliance Rate | share of active constraints with `enforcement_action='deny'` (`gatekeeper_constraints`) | native |
| Violations by Constraint | `topk(5, sum by (policy) (gatekeeper_violations_by_policy))` | exporter (5.5) |
| Violations by Namespace | `topk(10, gatekeeper_violations_by_namespace)` | exporter (5.5) |

The two exporter panels stay empty until the exporter from 5.5 runs as an in-cluster Deployment that Prometheus scrapes; running it on your laptop does not feed them. "Compliance Rate" is the share of constraints in `deny` mode, so it reads low (for example 40%) while you are still in audit mode.

#### 5.5 Deploy the Custom Gatekeeper Prometheus Exporter (Optional)

For richer metrics beyond what Gatekeeper exposes natively, deploy the custom exporter:

```bash
# Test locally first
pip3 install prometheus_client kubernetes
python3 scripts/gatekeeper_exporter.py --once

# Run the exporter (exposes metrics on :8000/metrics by default)
python3 scripts/gatekeeper_exporter.py --port 8000 --interval 60

# Verify metrics are available
curl http://localhost:8000/metrics | grep gatekeeper_

# Expected: 9 metric families including:
#   gatekeeper_violations_total
#   gatekeeper_violations_by_policy
#   gatekeeper_violations_by_namespace
#   gatekeeper_constraint_count
```

Gatekeeper stores at most 20 violations per constraint (`--constraint-violations-limit=20`), so the exporter's per-policy and per-namespace counts are capped and add up to less than the native `gatekeeper_violations` total (for example 89 vs 321). Use the native metric for totals and the exporter for the breakdowns.

For production, deploy as a Kubernetes Deployment and add a ServiceMonitor pointing to its `/metrics` endpoint.

### Phase 6: Transition from Audit to Enforcement

#### 6.1 Review Audit Results (Week 1-2)

```bash
# Monitor which resources violate policies
python3 compliance-dashboard.py --days 14 > week1-report.json

# Identify most problematic policies
kubectl get constraints -A -o json | \
  jq '.items[] | {name: .metadata.name, violations: .status.totalViolations}' | \
  sort -k2 -rn | head -10
```

#### 6.2 Communicate with Teams

Share compliance reports with application teams:
- Which policies they're violating
- Specific resources requiring remediation
- Remediation guidance (see "Common Tasks" section below)

#### 6.3 Transition Critical Policies to Enforcement

```bash
# After 2-4 weeks of monitoring, transition resource limits policy
kubectl patch constraint require-resource-limits --type merge \
  -p '{"spec":{"enforcementAction":"deny"}}'

# Verify enforcement is active
kubectl get constraint require-resource-limits -o jsonpath='{.spec.enforcementAction}'
# Expected: deny

# Now non-compliant deployments will be rejected
# Try deploying a non-compliant resource
kubectl apply -f /tmp/my-deployment.yaml  # Missing resources
# Expected: admission webhook denial
```

#### 6.4 Gradual Rollout Schedule (Recommended)

```
Week 1-2: All policies in AUDIT MODE
          - Monitor violations
          - Generate compliance reports
          - Communicate with teams

Week 3-4: Transition CRITICAL policies to enforcement
          - require-resource-limits (prevents resource exhaustion)
          - deny-privileged-containers (security critical)
          - Remaining policies stay in audit

Month 2:  Transition remaining policies to enforcement
          - require-labels (operational but not blocking)
          - restrict-image-registries (based on team readiness)
```

## Common Tasks

### View Policy Violations

```bash
# List all constraint violations
kubectl get constraints -A -o json | jq '.items[] | select(.status.totalViolations > 0)'

# Get detailed violation info for a specific constraint
kubectl describe constraint require-resource-limits

# Export violations to file for analysis
kubectl get constraint require-resource-limits -o json | \
  jq '.status.violations' > violations-export.json
```

### Update a Policy

```bash
# Edit policy definition directly
kubectl edit constraint require-resource-limits

# Or apply from file with changes
vim policies/require-resource-limits.yaml
kubectl apply -f policies/require-resource-limits.yaml

# Verify changes
kubectl describe constraint require-resource-limits
```

### Exempt Specific Namespaces

```bash
# Add namespace to exclusion list
kubectl patch constraint require-resource-limits --type merge \
  -p '{"spec":{"match":{"excludedNamespaces":["kube-system","kube-public","legacy-app"]}}}'

# Verify exemption
kubectl get constraint require-resource-limits -o jsonpath='{.spec.match.excludedNamespaces}'
```

### Exempt Specific Users or Service Accounts

```bash
# Exclude system:kube-controller-manager from policies
kubectl patch constraint require-resource-limits --type merge \
  -p '{"spec":{"match":{"excludedUsers":["system:kube-controller-manager","system:kubeadm"]}}}'
```

### Test Manifest Before Deployment

```bash
# Use conftest locally (fastest)
conftest test -p conftest-tests/policy.rego my-deployment.yaml

# Use kubectl dry-run with server-side evaluation (tests actual Gatekeeper)
kubectl apply -f my-deployment.yaml --dry-run=server

# Use kubectl dry-run client-side (syntax check only, no webhook validation)
kubectl apply -f my-deployment.yaml --dry-run=client
```

### Check Policy Test Coverage

```bash
# Run OPA policy unit tests
opa test policies/ -v

# Run all tests including test files ending in _test.rego
opa test policies/require-tests-passed_test.rego -v
```

## Troubleshooting

### Gatekeeper Pods Not Starting

> **Important**: If Gatekeeper was installed via Flux (Chapter 2), the `HelmRelease` lives in `flux-system` but the pods still run in `gatekeeper-system`. If they are not Ready, check the release first: `kubectl describe helmrelease gatekeeper -n flux-system`

```bash
# Check pod events and logs
kubectl describe pod -n gatekeeper-system \
  -l control-plane=controller-manager

# View controller manager logs
kubectl logs -n gatekeeper-system deployment/gatekeeper-controller-manager --tail=50

# Check webhook certificate
kubectl get secret -n gatekeeper-system | grep webhook

# Common issue: Certificate not valid
# Solution: Delete the pod to trigger recreation with new cert
kubectl delete pod -n gatekeeper-system -l gatekeeper=active
```

### Policy Not Enforcing (Audit Mode Not Catching Violations)

```bash
# Verify constraint is active
kubectl get constraint require-resource-limits -o yaml | grep -A5 spec

# Check if constraint has violations
kubectl describe constraint require-resource-limits

# If no violations: policy may be too permissive or not matching resources
# Debug: test policy Rego in isolation
opa test policies/ -v

# Check if your resources match the constraint's match rules
kubectl get deployment -A -o json | jq '.items[0].spec.template.spec.containers'
```

### conftest Showing False Positives

```bash
# Verify policy syntax is correct
conftest verify -p conftest-tests/policy.rego

# Run with verbose output to see which rules are evaluated
conftest test -p conftest-tests/policy.rego conftest-tests/test-manifests.yaml

# Test a single file with debugging
conftest test -p conftest-tests/policy.rego /tmp/deployment.yaml -d

# Compare with Gatekeeper behavior (may differ slightly)
```

### Webhook Timeouts During Deployments

```bash
# Issue: Gatekeeper webhook slow to respond or "context deadline exceeded"
# Symptoms: kubectl apply takes >30 seconds or fails with timeout

# Workaround: Delete the stale webhook (Gatekeeper will recreate it)
kubectl delete validatingwebhookconfiguration gatekeeper-validating-webhook-configuration

# Check webhook logs for slowness
kubectl logs -n gatekeeper-system deployment/gatekeeper-audit | grep -i latency

# Solution options:
# 1. Increase webhook timeout in gatekeeper-install.yaml
#    Change: spec.timeoutSeconds from 5 to 10-15
# 2. Exclude non-critical namespaces from validation
# 3. Optimize constraint complexity (fewer rules = faster evaluation)

# Temporarily disable a constraint to test performance
kubectl patch constraint require-resource-limits --type merge \
  -p '{"spec":{"match":{"excludedNamespaces":["default"]}}}'
```

## Best Practices

1. **Start with Audit Mode**: Deploy all policies with `enforcementAction: dryrun` for 2-4 weeks. Never jump directly to enforcement.

2. **Monitor Violations Continuously**: Use compliance dashboards to track violations and identify patterns before enforcing.

3. **Provide Remediation Guidance**: When policies are enforced, teams need clear documentation on:
   - Why the policy exists (security risk, operational stability, etc.)
   - How to fix violations (code examples)
   - Exceptions process (when to request exemptions)

4. **Document Exceptions Carefully**: Use `excludedNamespaces` or `excludedUsers` for legitimate special cases, but require justification.

5. **Test Policies Locally First**: Always validate manifests with conftest in your editor or pre-commit hooks before deployment.

6. **Gradual Rollout**: Enforce policies incrementally, starting with critical ones (security) before operational ones (labeling).

7. **Regular Review**: Quarterly audit of:
   - Which policies have high violation rates (may be too restrictive)
   - Whether exemptions are still justified
   - New policies needed based on incidents

8. **Version Control Policies**: Keep all policy YAML and Rego files in git; use pull requests for policy changes with automated tests.

9. **Test Policy Changes**: Use `.github/workflows/policy-tests.yaml` to validate policy syntax and logic before merging.

10. **Balance Enforcement with Developer Experience**: A policy that everyone exempts is either poorly designed or poorly explained. Iterate based on feedback.

## Companion Website Alignment

**Note:** The companion website at https://peh-packt.platformetrics.com/ provides supplementary videos, additional policy examples, and community-contributed constraint templates.

Expected sections:
- **Video 11.1**: "OPA Gatekeeper Architecture and Admission Webhooks"
- **Video 11.2**: "Writing Rego Policies: Syntax and Examples"
- **Video 11.3**: "Shift-Left Testing with conftest"
- **Policy Library**: Community policies for AWS, GCP, Azure-specific compliance
- **Case Study**: NewTech's compliance transformation (referenced in Chapter 11 narrative)

**Note:** Due to network restrictions, the companion website was not accessed for this README. Check the website for:
- Updated conftest versions and compatibility notes
- Additional policy examples beyond those in this directory
- Interactive Rego playground for policy development

## File Structure Summary

```
Ch11/
├── README.md                                    # This file
├── gatekeeper-install.yaml                      # Kubernetes manifests for Gatekeeper deployment
├── install-gatekeeper.sh                        # Helm installation script (alternative)
├── constraint-template.yaml                     # Basic ConstraintTemplate (Listing 11.1)
├── constraint-template-security-baselines.yaml  # Security ConstraintTemplate (Listing 11.6)
├── constraints/                                 # Constraint instances
│   ├── require-resources.yaml                   # Resource limits constraint (Listing 11.2)
│   ├── require-resource-limits.yaml             # CPU/memory limits constraint
│   ├── deny-privileged-containers.yaml          # Privileged container constraint
│   ├── restrict-image-registries.yaml           # Registry restriction constraint
│   ├── require-labels.yaml                      # Label requirement constraint
│   └── require-compliance-labels.yaml           # Compliance label constraint
├── policies/                                    # ConstraintTemplates (Rego policy definitions)
│   ├── require-resource-limits.yaml             # Resource limits ConstraintTemplate
│   ├── deny-privileged-containers.yaml          # Security hardening ConstraintTemplate
│   ├── restrict-image-registries.yaml           # Registry restriction ConstraintTemplate
│   ├── require-labels.yaml                      # Label requirement ConstraintTemplate
│   ├── require-tests-passed.rego                # Test result validation
│   └── require-tests-passed_test.rego           # Policy unit tests
├── test-pod-violation.yaml                      # Intentionally non-compliant manifests for testing
├── run-conftest.sh                              # Shell script to run conftest validation
├── .pre-commit-config.yaml                      # Pre-commit hooks for shift-left testing
├── conftest-tests/                              # Shift-left testing
│   ├── policy.rego                              # conftest policies for local validation
│   └── test-manifests.yaml                      # Sample compliant/non-compliant manifests
├── prometheus-gatekeeper-config.yaml            # Prometheus scrape config (Listing 11.9)
├── gatekeeper-metrics-servicemonitor.yaml       # Prometheus Operator ServiceMonitor
├── grafana-compliance-dashboard.json            # Grafana dashboard definition (Listing 11.11)
├── compliance-dashboard.py                      # Compliance report generator (Listing 11.12)
├── scripts/
│   └── gatekeeper_exporter.py                   # Custom Prometheus exporter for Gatekeeper
├── test-policies.py                             # Integration tests for policies
└── .github/workflows/
    ├── policy-tests.yaml                        # CI/CD workflow for policy testing
    └── validate.yml                             # CI/CD workflow for conftest validation
```

## Quick Reference: Command Cheat Sheet

```bash
# Installation
kubectl apply -f gatekeeper-install.yaml                    # Deploy Gatekeeper
kubectl get pods -n gatekeeper-system                       # Check status

# Policies (ConstraintTemplates first, wait for CRDs, then Constraints)
kubectl apply -f policies/
# Wait for CRDs before applying constraints:
until kubectl get crd k8sdenyprivilegedcontainers.constraints.gatekeeper.sh k8srequirelabels.constraints.gatekeeper.sh k8srequireresourcelimits.constraints.gatekeeper.sh k8srestrictimageregistries.constraints.gatekeeper.sh >/dev/null 2>&1; do sleep 3; done
kubectl apply -f constraints/
kubectl get constraints                                     # List constraints
kubectl describe constraint require-resource-limits         # View constraint details
kubectl get constraint -A -o json | jq '.items[].status.totalViolations'

# Testing
conftest test -p conftest-tests/policy.rego my-deployment.yaml  # Local validation
opa test policies/ -v                                       # Unit test policies
python3 test-policies.py                                     # Integration tests

# Monitoring
python3 compliance-dashboard.py                              # Generate compliance report
kubectl get constraints -o json | jq '.items[] | {name: .metadata.name, violations: .status.totalViolations}'

# Enforcement
kubectl patch constraint require-resource-limits --type merge -p '{"spec":{"enforcementAction":"deny"}}'  # Enable enforcement
kubectl patch constraint require-resource-limits --type merge -p '{"spec":{"match":{"excludedNamespaces":["kube-system"]}}}'  # Exclude namespace

# Debugging
kubectl logs -n gatekeeper-system deployment/gatekeeper-audit     # Check audit logs
kubectl logs -n gatekeeper-system deployment/gatekeeper-controller-manager  # Check controller
conftest test -p conftest-tests/policy.rego manifest.yaml    # Verbose policy output
```

## Additional Resources

- **OPA Gatekeeper Documentation**: https://open-policy-agent.github.io/gatekeeper/
- **Rego Language Guide**: https://www.openpolicyagent.org/docs/latest/policy-language/
- **conftest Documentation**: https://www.conftest.dev/
- **OPA Policy Library**: https://www.openpolicyagent.org/policies/
- **Kubernetes Admission Controllers**: https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/
- **Chapter 11: Policy-as-Code Enabler or Enforcer Sidebar**: Balance enforcement with developer experience

---

**Author:** Ajay Chankramath (ajay@platformetrics.com)
**Book:** The Platform Engineer's Handbook (Packt Publishing)
**Last Updated**: January 2026
