# Chapter 9: Self-Service Infrastructure Management - Code Examples

## Chapter Overview

Chapter 9 addresses infrastructure provisioning as a self-service capability. The chapter demonstrates how to deploy Crossplane to enable declarative infrastructure management, create composable infrastructure blueprints that teams can consume through simple configurations, establish guardrails that enforce governance without blocking innovation, and integrate infrastructure provisioning with the demo application.

By the end of this chapter, you will be able to:
- Deploy and configure Crossplane for infrastructure management
- Create infrastructure blueprints using Composite Resource Definitions (XRDs)
- Implement governance through guardrails, tagging, and environment-specific defaults
- Manage infrastructure dependencies and lifecycle automation
- Add a database to the demo application using configuration-driven deployment

## Code-to-Chapter Mapping

This directory contains all code listings and exercises from Chapter 9, organized by concept area. The mapping below connects each file to specific sections and listings in the manuscript.

### Crossplane Installation & Configuration

| File | Listing | Section | Purpose |
|------|---------|---------|---------|
| `crossplane-providers.yaml` | Listing 9.1 | "Infrastructure Blueprints" | Provider configuration for Kubernetes and Helm providers. Runs entirely on the local Kind cluster — no cloud credentials required. |

### Composite Resource Definitions (XRDs) & Infrastructure Blueprints

| File | Listing | Section | Purpose |
|------|---------|---------|---------|
| `xrd-postgresql.yaml` | Listing 9.2 | "Designing Composite Resources" | PostgreSQL XRD that defines the schema developers interact with when requesting databases. Specifies parameters (storageGB, version, tier, enableBackups) with defaults and validation rules. |
| `composition-postgresql.yaml` | Listing 9.3 | "Designing Composite Resources" | Crossplane v2 pipeline-mode composition that implements the PostgreSQL XRD interface using `function-patch-and-transform`. Deploys PostgreSQL as a Deployment inside the Kind cluster using the Kubernetes provider, with tier-specific resource settings and patch sets. |
| `xrd-gpu-nodepool.yaml` | Listing 9.6 | "Enabling Innovation Beyond the Platform" | XRD for GPU node pools enabling ML teams to request GPU resources with governance controls. Defines GPU types, node count, spot instance options, and scheduling windows. |

### Governance & Enforcement

| File | Listing | Section | Purpose |
|------|---------|---------|---------|
| `guardrail-validator.py` | Listing 9.4 | "Governance with Guardrails and Tagging" | Admission webhook that validates PostgreSQL claims against organizational policies. Enforces namespace restrictions: production-tier resources only in production namespaces, staging-tier in staging/production, development anywhere. |
| `tagging-patchset.yaml` | — | "Governance with Guardrails and Tagging" | Crossplane PatchSet manifests that apply standard governance tags to all composed resources. Defines three reusable patchsets: `required-tags` (team, cost-center, environment, managed-by), `lifecycle-labels` (Crossplane ownership tracking), and `common-metadata` (label propagation from claims). Referenced by compositions to ensure every cloud resource carries organizational metadata for cost allocation, auditing, and ownership tracking. |

### Environment-Specific Configuration

| File | Exercise | Section | Purpose |
|------|----------|---------|---------|
| `generate-env-defaults.py` | Exercise 9.1 | "Governance with Guardrails and Tagging" | Script that generates environment-specific Crossplane compositions (development, staging, production) in pipeline mode. Each deploys PostgreSQL as a Deployment with environment-appropriate replica count and CPU/memory requests and limits. Storage, backup retention, deletion protection, and monitoring defaults are defined in the script's `EnvironmentConfig` but not yet rendered into the output; wiring them in is a natural extension. |

### Infrastructure Lifecycle Management

| File | Listing | Section | Purpose |
|------|---------|---------|---------|
| `lifecycle-controller.py` | Listing 9.5 | "Provisioning and Lifecycle Automation" | Infrastructure lifecycle controller that watches Crossplane claims and enforces organizational policies including maximum age limits per environment tier, required owner labels for production resources, and automatic cleanup scheduling for development resources. |

### Custom Infrastructure Requests

| File | Listing | Section | Purpose |
|------|---------|---------|---------|
| `custom-infra-request.py` | Listing 9.7 | "Enabling Innovation Beyond the Platform" | Handler for custom infrastructure requests requiring approval. Provides a governed workflow for infrastructure needs outside standard blueprints, including request submission, platform team notification, approval with cost checks, and manifest generation. |

### Demo Application Integration

| File | Listing | Section | Purpose |
|------|---------|---------|---------|
| `demo-app-database.yaml` | Listing 9.8 | "Adding Infrastructure to the Demo Application" | PostgreSQL claim for the demo application in the team-alpha namespace. Demonstrates how teams request databases through simple configuration with storage size, version, tier, and backup preferences. |

### Testing & Validation

| File | Listing | Section | Purpose |
|------|---------|---------|---------|
| `test-infrastructure.py` | Listing 9.9 | "Adding Infrastructure to the Demo Application" | Test script that validates the complete infrastructure workflow: applies PostgreSQL claim, waits for readiness, verifies connection secret creation, and confirms application database connectivity. |

### Secrets Management (Bitwarden Integration)

| File | Listing | Section | Purpose |
|------|---------|---------|---------|
| `load-secrets.sh` | N/A | Secrets Management (cross-chapter) | Retrieves database credentials from Bitwarden vault and optionally creates the `db-credentials` Kubernetes Secret for Crossplane. Exports `POSTGRES_PASSWORD`. Run with `--create-k8s` to also create the Kubernetes secret. |
| `.env_example` | N/A | Secrets Management (fallback) | Template for a gitignored `.env` holding `POSTGRES_PASSWORD` when you are not using Bitwarden. |

## Prerequisites

### Running This Chapter Standalone

> If you are jumping into this chapter without completing earlier chapters, use these commands to set up the infrastructure dependencies. If you already have them running, skip this section.

> **Note:** Crossplane runs entirely inside the Kind cluster. No cloud credentials are needed for the local Kubernetes and Helm providers.

```bash
# 1. Start Docker Desktop (macOS: open from Applications or Spotlight)
open -a "Docker"
# Wait for the Docker engine to start before continuing

# 2. Create a Kind cluster (skip if you already have one)
kind get clusters                       # Check for existing clusters
kind create cluster --name platform-dev # Create one if none listed
kubectl get nodes                       # Verify node(s) are Ready

# Install Crossplane
helm repo add crossplane-stable https://charts.crossplane.io/stable
helm repo update
helm install crossplane crossplane-stable/crossplane --version 2.4.2 --namespace crossplane-system --create-namespace --wait

```

### System Requirements
- Kubernetes 1.20 or later (with sufficient RBAC permissions for Crossplane installation)
- kubectl configured to access your cluster
- Helm 4.3.0 (for Crossplane installation)
- **Crossplane** v2.4 (installed via Helm to cluster, chart pinned to 2.4.2)
- **Crossplane CLI** v2.x (for building and pushing Crossplane packages)
  ```bash
  # macOS: brew install crossplane/tap/crossplane
  # Linux: curl -sL -o crossplane https://releases.crossplane.io/stable/v2.4.2/bin/linux_amd64/crossplane && chmod +x crossplane && sudo mv crossplane /usr/local/bin/
  ```
- Python 3.8+ (for Python scripts)

### Required Python Dependencies

Install the following packages before running Python scripts:
```bash
python3 -m venv venv && source venv/bin/activate
pip install flask pyyaml kubernetes
```

The following versions are recommended:
- flask: 2.0+
- pyyaml: 5.4+
- kubernetes: 20.0+

### Database Credentials

For Crossplane-managed PostgreSQL deployments:
- **Recommended:** Store database credentials in Bitwarden and use `load-secrets.sh`:
  ```bash
  export BW_SESSION=$(bw unlock --raw)
  source load-secrets.sh
  ```
- **Or manually:**
  ```bash
  cp .env_example .env      # then edit .env (POSTGRES_PASSWORD)
  set -a && source .env && set +a
  ```
- All providers (Kubernetes, Helm) run locally on Kind — no cloud credentials needed

### Cluster Permissions

Ensure your Kubernetes user has permissions to:
- Create CustomResourceDefinitions
- Create resources in the `crossplane-system` namespace
- Create Provider and ProviderConfig resources
- Create and manage Composite Resources

## Step-by-Step Instructions

### Phase 1: Crossplane Installation

#### Step 1.1: Add Crossplane Helm Repository
```bash
helm repo add crossplane-stable https://charts.crossplane.io/stable
helm repo update
```

**Expected Output:**
```
"crossplane-stable" has been added to your repositories
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "crossplane-stable" chart repository
```

#### Step 1.2: Allow the Crossplane Image Registry

If you completed Chapter 2, its Gatekeeper `allowed-registries` constraint denies images from registries that are not on its list. Crossplane and its providers and functions are all pulled from `xpkg.crossplane.io`, so allow it before installing:

```bash
kubectl patch k8sallowedregistries allowed-registries --type=json -p='[
  {"op":"add","path":"/spec/parameters/allowedRegistries/-","value":"xpkg.crossplane.io/"}]'
```

Skip this step if the constraint does not exist (`kubectl get k8sallowedregistries`). The repository's `Ch02/platform-services.yaml` (and Chapter 11's `restrict-image-registries.yaml`) already include this prefix, so a fresh Chapter 2 setup does not need the patch.

#### Step 1.3: Install Crossplane with Helm

If you completed Chapter 11, the `namespace-must-have-team` constraint rejects namespaces without `team`, `cost-center` and `environment` labels, and it checks them at creation time, so `--create-namespace` alone fails. Create the namespace with the labels first (harmless if you did not do Chapter 11):

```bash
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: crossplane-system
  labels:
    team: platform
    cost-center: "10001"
    environment: dev
EOF
```

The first start pulls a large image on each node and can take over 3 minutes. If `--wait` times out, the release is marked `failed` even though it keeps starting; once the pods are Running, re-run the same command as `helm upgrade` to mark it `deployed`.

```bash
helm install crossplane crossplane-stable/crossplane \
  --version 2.4.2 \
  --namespace crossplane-system \
  --create-namespace \
  --set resourcesCrossplane.limits.cpu=500m \
  --set resourcesCrossplane.limits.memory=512Mi \
  --set resourcesCrossplane.requests.cpu=100m \
  --set resourcesCrossplane.requests.memory=256Mi
```

**Expected Output:**
```
NAME: crossplane
LAST DEPLOYED: [timestamp]
NAMESPACE: crossplane-system
STATUS: deployed
REVISION: 1
```

#### Step 1.4: Verify Crossplane Installation
```bash
# Check Crossplane pods are running
kubectl get pods -n crossplane-system

# Check Crossplane CRDs are available
kubectl get crds | grep crossplane
```

**Expected Output:**
Crossplane pods should show `STATUS: Running`:
```
NAME                            READY   STATUS    RESTARTS   AGE
crossplane-6f8d4c5d9f-xyz       1/1     Running   0          30s
crossplane-rbac-manager-abc     1/1     Running   0          30s
```

CRDs should include multiple Crossplane-related CRDs:
```
compositions.apiextensions.crossplane.io
compositeresourcedefinitions.apiextensions.crossplane.io
providers.pkg.crossplane.io
...
```

**Next Step:** Proceed to Phase 2: Provider Configuration

---

### Phase 2: Provider Configuration

The providers file installs the Kubernetes provider, Helm provider, and `function-patch-and-transform` (required for the v2 Composition pipeline mode). Because the ProviderConfig CRDs are registered *by* the providers, you need to apply the file twice: once to create the Provider/Function objects, then again after they're healthy to create the ProviderConfigs.

#### Step 2.1: Apply Provider Configuration (first pass)
```bash
kubectl apply -f crossplane-providers.yaml
```

The ProviderConfig resources will fail on this first apply — that's expected because the CRDs haven't been registered yet. Wait for the providers and function to become healthy:

```bash
kubectl wait provider.pkg.crossplane.io/provider-kubernetes --for=condition=Healthy --timeout=120s
kubectl wait provider.pkg.crossplane.io/provider-helm --for=condition=Healthy --timeout=120s
kubectl wait function.pkg.crossplane.io/function-patch-and-transform --for=condition=Healthy --timeout=120s
```

#### Step 2.2: Re-apply to create ProviderConfigs
```bash
kubectl apply -f crossplane-providers.yaml
```

**Expected Output:**
```
provider.pkg.crossplane.io/provider-kubernetes unchanged
providerconfig.kubernetes.crossplane.io/default created
function.pkg.crossplane.io/function-patch-and-transform unchanged
provider.pkg.crossplane.io/provider-helm unchanged
providerconfig.helm.crossplane.io/default created
```

#### Step 2.3: Verify Providers are Installed
```bash
# Check providers and function
kubectl get providers
kubectl get functions

# Check provider controller pods
kubectl get pods -n crossplane-system | grep provider
```

**Expected Output:**
Providers should show `INSTALLED=true` and `HEALTHY=true`:
```
NAME                      INSTALLED   HEALTHY
provider-kubernetes       true        true
provider-helm             true        true
```

#### Step 2.4: Grant RBAC to the Kubernetes Provider

The Kubernetes provider needs cluster-admin permissions to create resources (Namespaces, Deployments, PVCs, Services) on behalf of Crossplane. Without this, all Object resources will fail with "forbidden" errors.

```bash
SA=$(kubectl -n crossplane-system get sa -o name \
  | grep provider-kubernetes | head -1)

kubectl create clusterrolebinding provider-kubernetes-admin \
  --clusterrole cluster-admin \
  --serviceaccount=crossplane-system:${SA##*/}
```

**Expected Output:**
```
clusterrolebinding.rbac.authorization.k8s.io/provider-kubernetes-admin created
```

> **Note:** The service account name includes a package-revision hash (for example `provider-kubernetes-d1ed189e04fc`). If you later change the provider version, Crossplane creates a new revision and a new service account, so delete and re-create this binding with the same commands.

**Next Step:** Proceed to Phase 3: Infrastructure Blueprints

---

### Phase 3: Infrastructure Blueprints

#### Step 3.1: Apply PostgreSQL XRD (Composite Resource Definition)
```bash
kubectl apply -f xrd-postgresql.yaml
```

**Expected Output:**
```
compositeresourcedefinition.apiextensions.crossplane.io/postgresqlinstances.database.platform.io created
```

#### Step 3.2: Apply PostgreSQL Composition

The composition uses the v2 pipeline mode with `function-patch-and-transform` (installed in Phase 2). It maps the XRD parameters to four Kubernetes resources: a Namespace, PersistentVolumeClaim, Deployment, and Service.

```bash
kubectl apply -f composition-postgresql.yaml
```

**Expected Output:**
```
composition.apiextensions.crossplane.io/postgresql-kubernetes created
```

#### Step 3.3: Verify XRD and Composition
```bash
# Check XRDs
kubectl get xrd | grep postgresql

# Check Compositions
kubectl get compositions | grep postgresql
```

**Expected Output:**
```
NAME                                        ESTABLISHED   OFFERED   AGE
postgresqlinstances.database.platform.io    true          true      10s

NAME                    AGE
postgresql-kubernetes    5s
```

#### Step 3.4: Create the Database Credentials Secret

The PostgreSQL Deployment references a Kubernetes Secret called `db-credentials` for the `POSTGRES_PASSWORD`. Create the `databases` namespace and the secret before submitting any claims.

```bash
# Labels are required if the Chapter 11 namespace-must-have-team constraint is active
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: databases
  labels:
    team: platform
    cost-center: "10001"
    environment: dev
EOF

# Use the password from Bitwarden (or the .env you loaded above)
kubectl create secret generic db-credentials \
  --namespace databases \
  --from-literal=password=${POSTGRES_PASSWORD:-platformdev123}
```

**Expected Output:**
```
namespace/databases created      # "configured" if it already exists
secret/db-credentials created
```

> **Note:** The composition also manages a `db-credentials` Secret in `databases` (`db-secret` in `composition-postgresql.yaml`). When the claim in Phase 6 reconciles, it replaces the Secret created here with its own static demo password (`change-me-in-production`), so the value you set in this step is only used until then.

**Next Step:** Proceed to Phase 4: Environment-Specific Configuration

---

### Phase 4: Environment-Specific Composition Generation

#### Step 4.1: Prepare the Generation Script
```bash
# Make the script executable
chmod +x generate-env-defaults.py

# (Optional) Review the script to understand environment definitions
cat generate-env-defaults.py
```

#### Step 4.2: Generate Environment-Specific Compositions
```bash
python3 generate-env-defaults.py
```

**Expected Output:**
```
Generated composition-postgresql-development.yaml
Generated composition-postgresql-staging.yaml
Generated composition-postgresql-production.yaml
```

#### Step 4.3: Review Generated Compositions
```bash
# View the production composition to verify environment-specific settings
cat composition-postgresql-production.yaml
```

**Expected Output:** A pipeline-mode Composition (`mode: Pipeline`, one `patch-and-transform` step using `function-patch-and-transform`) whose `db-deployment` resource shows the production settings:
- `replicas: 2`
- `requests: cpu: 500m, memory: 1Gi`
- `limits: cpu: 2000m, memory: 2Gi`
- `image: docker.io/library/postgres:15-alpine`

#### Step 4.4: Apply Generated Compositions
```bash
kubectl apply -f composition-postgresql-development.yaml
kubectl apply -f composition-postgresql-staging.yaml
kubectl apply -f composition-postgresql-production.yaml
```

**Expected Output:**
```
composition.apiextensions.crossplane.io/postgresql-development created
composition.apiextensions.crossplane.io/postgresql-staging created
composition.apiextensions.crossplane.io/postgresql-production created
```

#### Step 4.5: Verify All Compositions
```bash
kubectl get compositions -l provider=kubernetes
```

**Expected Output:**
```
NAME                          AGE
postgresql-kubernetes         2m
postgresql-development        30s
postgresql-staging            30s
postgresql-production         30s
```

**Next Step:** Proceed to Phase 5: Governance Setup

---

### Phase 5: Governance & Validation

#### Step 5.1: Deploy the Guardrail Validator Webhook (Optional)

The guardrail validator enforces namespace-tier policies. Note: Full webhook deployment requires certificate management and ValidatingWebhookConfiguration setup. For testing the validation logic:

```bash
# Make the script executable
chmod +x guardrail-validator.py

# Review the validation rules
cat guardrail-validator.py

# For full deployment, you would create a Kubernetes deployment, service, and webhook configuration:
# kubectl apply -f guardrail-validator-deployment.yaml
```

#### Step 5.2: Review Tagging Patchsets

The tagging patchset defines reusable governance tags that compositions apply to every cloud resource. Review how labels flow from claims to managed resources:

```bash
# Review the three patchsets: required-tags, lifecycle-labels, common-metadata
cat tagging-patchset.yaml
```

`tagging-patchset.yaml` is a reference snippet, not an applicable resource (it has no `apiVersion` or `kind`). To use it, copy the patchsets into a pipeline step's `input.patchSets` and reference them from a resource with `type: PatchSet` and `patchSetName`. `composition-postgresql.yaml` shows this mechanism with its own `common-labels` patchset. Once a composition applies the tagging patchsets, every composed resource inherits team, cost-center, environment, and ownership tags — enabling cost allocation, auditing, and lifecycle tracking without developer effort.

#### Step 5.3: Apply GPU NodePool XRD (Optional - for innovation use case)
```bash
kubectl apply -f xrd-gpu-nodepool.yaml
```

**Expected Output:**
```
compositeresourcedefinition.apiextensions.crossplane.io/gpunodepools.compute.platform.io created
```

**Next Step:** Proceed to Phase 6: Demo Application Integration

---

### Phase 6: Demo Application Integration

#### Step 6.1: Create team-alpha Namespace

The labels satisfy the Chapter 11 `namespace-must-have-team` policy if it is active (`team` letters only, so `alpha` and not `team-alpha`; `environment` one of `dev`, `staging`, `prod`; `cost-center` 4-6 digits). They are harmless otherwise.

```bash
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: team-alpha
  labels:
    team: alpha
    cost-center: "10001"
    environment: dev
EOF
```

**Expected Output:**
```
namespace/team-alpha created
```

#### Step 6.2: Apply PostgreSQL Claim for Demo Application
```bash
kubectl apply -f demo-app-database.yaml
```

The claim selects the `postgresql-kubernetes` composition with `compositionSelector` (`database: postgresql`). This matters because Phase 4 created more compositions for the same `PostgreSQLInstance` kind; without a selector Crossplane picks one of them, and the environment compositions only create a Deployment.

**Expected Output:**
```
postgresqlclaim.database.platform.io/demo-app-db created
```

#### Step 6.3: Verify Claim Creation
```bash
kubectl get postgresqlclaim -n team-alpha
```

**Expected Output:**
```
NAME          SYNCED   READY   CONNECTION-SECRET   AGE
demo-app-db                                        1s
```

#### Step 6.4: Monitor Claim Status
```bash
# Watch the claim's status in detail
kubectl describe postgresqlclaim demo-app-db -n team-alpha

# Watch for changes (Ctrl+C to exit)
kubectl get postgresqlclaim -n team-alpha -w
```

**Expected Output (after ready):**
```
NAME          SYNCED   READY   CONNECTION-SECRET   AGE
demo-app-db   True     True                        45s
```

`READY` means Crossplane has created the composed resources, not that the database is usable. Confirm the PostgreSQL pod and its volume as well:
```bash
kubectl get pods,pvc -n databases
```
The pod should be `1/1 Running` and the PVC `Bound`. If the PVC stays `Pending`, see "Claim is `READY` but the PostgreSQL pod stays `Pending`" under Troubleshooting.

#### Step 6.5: Verify Connection Secret Creation
```bash
# Check if the connection secret was created
kubectl get secret demo-app-db-connection -n team-alpha -o yaml
```

**Expected Output:** Secret should contain keys:
- `endpoint` - Database endpoint
- `port` - Database port
- `username` - Database username
- `password` - Database password

The `CONNECTION-SECRET` column of the claim stays empty. Crossplane v2 does not propagate a connection secret from the composite resource to the claim, so the composition creates this Secret itself (`app-connection-secret` in `composition-postgresql.yaml`) in the claim's namespace, named `<claim-name>-connection`.

**Next Step:** Proceed to Phase 7: Testing & Validation

---

### Phase 7: Testing & Validation

#### Step 7.1: Prepare Test Infrastructure Script
```bash
chmod +x test-infrastructure.py

# Review the test script
cat test-infrastructure.py
```

#### Step 7.2: Run Infrastructure Tests
```bash
python3 test-infrastructure.py
```

**Expected Output:**
```
Testing infrastructure provisioning...
✓ Claim is ready
✓ Connection secret exists
⊘ Skipped app connectivity check (demo-app not deployed)

✓ All infrastructure tests passed!
```

If the claim is not ready yet you also see `Waiting for claim demo-app-db to be ready...` lines. The connectivity check only runs when the Chapter 5 `demo-app` Deployment exists in `team-alpha`; otherwise it is skipped, as above.

#### Step 7.3: Verify Complete Workflow
```bash
# The claim and its connection secret are in the team-alpha namespace
kubectl get secrets,postgresqlclaim -n team-alpha

# The database itself runs in the databases namespace
kubectl get deploy,pods,svc,pvc -n databases

# View connection secret details
kubectl get secret demo-app-db-connection -n team-alpha -o jsonpath='{.data.endpoint}' | base64 -d
```

**Expected Output (last command):** `postgresql.databases.svc.cluster.local`

---

### Phase 8: Optional - Lifecycle Controller Setup

#### Step 8.1: Review Lifecycle Policy Configuration
```bash
chmod +x lifecycle-controller.py

# Review the lifecycle policies
cat lifecycle-controller.py
```

The controller enforces:
- **Development:** 30-day max age with automatic cleanup
- **Staging:** 90-day max age
- **Production:** No age limit, requires owner label

#### Step 8.2: Deploy Lifecycle Controller (Production Setup)

For production deployment, create a Kubernetes deployment. First put the controller code into the ConfigMap the Deployment mounts:

```bash
kubectl create configmap lifecycle-controller-code \
  --from-file=lifecycle-controller.py -n crossplane-system
```

Then deploy it:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: infrastructure-lifecycle-controller
  namespace: crossplane-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: lifecycle-controller
  template:
    metadata:
      labels:
        app: lifecycle-controller
    spec:
      serviceAccountName: crossplane
      containers:
      - name: controller
        # Fully qualified so the Chapter 2 allowed-registries policy accepts it
        image: docker.io/library/python:3.10-slim
        # The slim image has no Kubernetes client; install it at start-up.
        # -u keeps the log output unbuffered so kubectl logs shows it immediately.
        command: ["sh", "-c", "pip install --quiet --no-cache-dir kubernetes && python -u /controller/lifecycle-controller.py"]
        # Required by the Chapter 2 require-limits policy
        resources:
          requests:
            cpu: 50m
            memory: 128Mi
          limits:
            cpu: 250m
            memory: 256Mi
        volumeMounts:
        - name: controller-code
          mountPath: /controller
      volumes:
      - name: controller-code
        configMap:
          name: lifecycle-controller-code
EOF
```

The `crossplane` service account can already list and watch claims cluster-wide, which is all the controller needs. This demo reuses it for brevity; for real use, create a dedicated service account with read-only access to `postgresqlclaims`.

#### Step 8.3: Verify the Controller

The first start installs the Kubernetes client, which takes a few seconds. The controller only logs violations, so a compliant claim produces no output. Trigger one by removing the owner label from the demo claim, check the log, then put the label back:

```bash
kubectl get pods -n crossplane-system -l app=lifecycle-controller

kubectl label postgresqlclaim demo-app-db -n team-alpha platform.io/owner-
kubectl logs -n crossplane-system deploy/infrastructure-lifecycle-controller --tail=5
kubectl label postgresqlclaim demo-app-db -n team-alpha platform.io/owner=demo-app
```

**Expected Output (logs):**
```
Policy violations for demo-app-db: ['Missing platform.io/owner label']
```

---

## Troubleshooting Guide

### Issue: Crossplane pods not starting
**Diagnosis:**
```bash
kubectl logs -n crossplane-system deployment/crossplane
```

**Solution:** Ensure cluster has sufficient resources (2GB+ memory), check RBAC permissions

### Issue: Providers stuck in "Unpack" phase
**Diagnosis:**
```bash
kubectl describe providers -n crossplane-system
```

**Solution:** Wait 2-3 minutes for provider controllers to start, check network connectivity to xpkg.crossplane.io

### Issue: PostgreSQL claim not becoming ready
**Diagnosis:**
```bash
kubectl describe postgresqlclaim demo-app-db -n team-alpha
kubectl get objects -A
kubectl describe object <name> | tail -20
```

**Common causes:**
- **RBAC forbidden errors:** The Kubernetes provider service account needs cluster-admin. See Phase 2, Step 2.4.
- **`db-credentials` secret missing:** The PostgreSQL Deployment references this secret. Create it in the `databases` namespace — see Phase 3, Step 3.4.
- **ProviderConfig not found:** You need to apply `crossplane-providers.yaml` twice — the first time creates the Provider objects, the second time (after they're healthy) creates the ProviderConfigs. See Phase 2.
- **`function-patch-and-transform` not healthy:** The composition requires this function. Check with `kubectl get functions`.
- Crossplane providers not healthy (check `kubectl get providers`)

**Solution:** Run through the Phase 2 steps carefully, ensuring providers and functions are healthy before proceeding.

### Issue: Claim is `READY` but the PostgreSQL pod stays `Pending` (PVC `postgresql-data` is `Pending`)
A claim becomes `READY` once Crossplane has created its resources, not when the database is usable.

**Diagnosis:**
```bash
kubectl describe pvc postgresql-data -n databases
```
Look for a `ProvisioningFailed` event such as:
```
admission webhook "validation.gatekeeper.sh" denied the request: [require-limits] Container helper-pod is missing required cpu limit
```

**Cause:** The Kind `standard` StorageClass uses the local-path provisioner, which starts a short-lived `helper-pod` in the `local-path-storage` namespace to create each volume. That pod has no resource limits, so a Gatekeeper constraint that denies pods without limits (and does not exclude `local-path-storage`) blocks it. Chapter 2's `require-limits` constraint is in `deny` mode and blocks it; Chapter 11's constraints start in `dryrun` mode and would not.

**Solution:** Add resource limits to the helper pod in the provisioner's ConfigMap:
```bash
kubectl edit configmap local-path-config -n local-path-storage
```
Under `helperPod.yaml`, add a `resources` block to the `helper-pod` container, next to `image`:
```yaml
    resources:
      requests:
        cpu: 50m
        memory: 32Mi
      limits:
        cpu: 100m
        memory: 64Mi
```
The provisioner picks up the change after Kubernetes syncs the ConfigMap into its pod and retries with backoff, so the PVC can take several minutes to bind.

The provisioner pod itself also has no limits, so the same constraint blocks any *new* provisioner pod (the running one predates the policy). Restarting it would leave the rollout stuck, so give it limits first:
```bash
kubectl set resources deployment/local-path-provisioner -n local-path-storage \
  -c local-path-provisioner --requests=cpu=50m,memory=64Mi --limits=cpu=100m,memory=128Mi
```
This rolls the provisioner; a freshly started provisioner starts with an empty retry queue, so pending volumes should be retried without waiting for the backoff.

Both changes live in the cluster, so re-apply them if you recreate the Kind cluster.

### Issue: Python script import errors
```bash
# Reinstall dependencies
pip install --break-system-packages --upgrade flask pyyaml kubernetes
```

## Companion Website Alignment

The companion website (https://peh-packt.platformetrics.com/) contains supplementary materials for Chapter 9, which may include:

- Interactive Crossplane composition builder
- Example infrastructure configurations for Kind clusters
- Extended guardrail policy examples
- Kubernetes manifest templates for webhook deployment
- Video walkthroughs of the complete workflow

**Note:** The companion website could not be accessed during README generation. Check the website directly for the latest Chapter 9 resources.

## Key Concepts Summary

### Self-Service Infrastructure Model
- Developers declare infrastructure needs in configuration that travels with application code
- Platform encodes organizational standards in reusable blueprints
- Governance is applied transparently through defaults and validation rules

### Crossplane Architecture
- **Providers:** Integrations with external systems (Kubernetes, Helm, and optionally cloud providers)
- **Managed Resources:** Individual infrastructure components (Deployments, Services, Helm releases, etc.)
- **Composite Resources:** High-level abstractions that hide complexity from consumers

### Governance Pattern
- **Blueprints (XRDs):** Define valid configurations with constraints
- **Compositions:** Map claims to managed resources with organization-specific settings
- **Tagging & Labeling:** Enable cost tracking and compliance monitoring
- **Guardrails:** Validate requests against organizational policies
- **Lifecycle Controllers:** Enforce resource compliance over time

## Files Reference

```
Ch09/
├── crossplane-providers.yaml           # Provider configuration (Listing 9.1)
├── xrd-postgresql.yaml                 # PostgreSQL XRD (Listing 9.2)
├── composition-postgresql.yaml         # PostgreSQL composition (Listing 9.3)
├── guardrail-validator.py              # Policy webhook (Listing 9.4)
├── tagging-patchset.yaml              # Governance tagging patchsets (Section 9.4)
├── lifecycle-controller.py             # Lifecycle management (Listing 9.5)
├── xrd-gpu-nodepool.yaml               # GPU node pool XRD (Listing 9.6)
├── custom-infra-request.py             # Custom request handler (Listing 9.7)
├── demo-app-database.yaml              # Demo app database (Listing 9.8)
├── test-infrastructure.py              # Infrastructure tests (Listing 9.9)
├── generate-env-defaults.py            # Environment generator (Exercise 9.1)
└── README.md                           # This file
```

## Related Chapters

- **Chapter 5:** Demo Application (provides the application that uses provisioned infrastructure)
- **Chapter 8:** CI/CD as a Platform Service (provides the pipeline context for infrastructure provisioning)
- **Chapter 10:** Publishing Starter Kits (building on infrastructure blueprints for developer onboarding)

## Additional Resources

### Official Documentation
- [Crossplane Documentation](https://crossplane.io/docs/)
- [Upbound Providers](https://docs.upbound.io/providers/)
- [Kubernetes Custom Resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)

### References from Manuscript
- [1] https://crossplane.io/docs/
- [2] https://docs.upbound.io/providers/
- [3] https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/

## Exercises

### Exercise 9.1: Environment-Specific Compositions
**File:** `generate-env-defaults.py`

Generate environment-specific Crossplane compositions with appropriate defaults for development, staging, and production environments. The script automatically creates three composition files with environment-aware settings that reduce configuration burden on developers.

**Challenge Extension:** Modify the script to add a fourth "sandbox" environment with minimal resources (db.t3.nano, 10GB storage, no backups, auto-deletion after 7 days).

### Exercise 9.2: Complete Self-Service Implementation
**Covered by:** All files in sequence following this README's step-by-step instructions

Deploy Crossplane, create infrastructure blueprints, and provision a database for the demo application. Consolidates all chapter concepts into hands-on practice:

1. Install Crossplane using Helm
2. Deploy Kubernetes provider for local testing
3. Apply PostgreSQL XRD and composition
4. Create PostgreSQL claim for demo application
5. Update demo application deployment to use database
6. Run test script to verify connectivity
7. Deploy lifecycle controller and observe policy evaluation

## Notes for Instructors/Facilitators

- **Lab Duration:** 2-3 hours for complete walkthrough of all 8 phases
- **Prerequisites Assessment:** Verify cluster access and Python/installation before starting
- **Stopping Point:** Phase 3 (Infrastructure Blueprints) provides a good checkpoint for intermediate students
- **Extension Activity:** Have students modify the GPU NodePool XRD to add resource quotas and affinity rules
- **Real-World Scenario:** Challenge students to write a composition for Redis cluster (cache) following the PostgreSQL pattern

---

**Author:** Ajay Chankramath (ajay@platformetrics.com)
**Book:** The Platform Engineer's Handbook (Packt Publishing)
**Last Updated**: January 2026
