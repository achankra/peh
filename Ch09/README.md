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
| `composition-postgresql.yaml` | Listing 9.3 | "Designing Composite Resources" | Crossplane composition that implements the PostgreSQL XRD interface. Deploys PostgreSQL as a Deployment inside the Kind cluster using the Kubernetes provider, with tier-specific resource settings and patch sets. |
| `xrd-gpu-nodepool.yaml` | Listing 9.6 | "Enabling Innovation Beyond the Platform" | XRD for GPU node pools enabling ML teams to request GPU resources with governance controls. Defines GPU types, node count, spot instance options, and scheduling windows. |

### Governance & Enforcement

| File | Listing | Section | Purpose |
|------|---------|---------|---------|
| `guardrail-validator.py` | Listing 9.4 | "Governance with Guardrails and Tagging" | Admission webhook that validates PostgreSQL claims against organizational policies. Enforces namespace restrictions: production-tier resources only in production namespaces, staging-tier in staging/production, development anywhere. |
| `tagging-patchset.yaml` | — | "Governance with Guardrails and Tagging" | Crossplane PatchSet manifests that apply standard governance tags to all composed resources. Defines three reusable patchsets: `required-tags` (team, cost-center, environment, managed-by), `lifecycle-labels` (Crossplane ownership tracking), and `common-metadata` (label propagation from claims). Referenced by compositions to ensure every cloud resource carries organizational metadata for cost allocation, auditing, and ownership tracking. |

### Environment-Specific Configuration

| File | Exercise | Section | Purpose |
|------|----------|---------|---------|
| `generate-env-defaults.py` | Exercise 9.1 | "Governance with Guardrails and Tagging" | Script that generates environment-specific Crossplane compositions (development, staging, production) with appropriate defaults for instance class, storage, backup retention, multi-AZ configuration, deletion protection, and performance insights. |

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

## Prerequisites

### System Requirements
- Kubernetes 1.20 or later (with sufficient RBAC permissions for Crossplane installation)
- kubectl configured to access your cluster
- Helm 3.0+ (for Crossplane installation)
- **Crossplane** v1.14+ (installed via Helm to cluster)
- **Crossplane CLI** v1.14+ (for building and pushing Crossplane packages)
  ```bash
  # macOS: brew install crossplane/tap/crossplane
  # Linux: curl -sL https://raw.githubusercontent.com/crossplane/crossplane/master/install.sh | sh
  ```
- Python 3.8+ (for Python scripts)

### Required Python Dependencies

Install the following packages before running Python scripts:
```bash
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
  # Load DB password from vault and create the Kubernetes secret
  ./load-secrets.sh --create-k8s
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

#### Step 1.2: Install Crossplane with Helm
```bash
helm install crossplane crossplane-stable/crossplane \
  --namespace crossplane-system \
  --create-namespace \
  --set args='{"--enable-composition-functions"}' \
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

#### Step 1.3: Verify Crossplane Installation
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

#### Step 2.1: Apply Provider Configuration
```bash
kubectl apply -f crossplane-providers.yaml
```

**Expected Output:**
```
provider.pkg.crossplane.io/provider-kubernetes created
providerconfig.kubernetes.crossplane.io/default created
provider.pkg.crossplane.io/provider-helm created
providerconfig.helm.crossplane.io/default created
```

#### Step 2.2: Verify Providers are Installed
```bash
# Check providers
kubectl get providers -n crossplane-system

# Check provider controller pods (may take 30-60 seconds to start)
kubectl get pods -n crossplane-system | grep provider
```

**Expected Output:**
Providers should show `INSTALLED=true` and `HEALTHY=true`:
```
NAME                      INSTALLED   HEALTHY
provider-kubernetes       true        true
provider-helm             true        true
```

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

#### Step 3.4: Verify the Custom Resource API is available
```bash
# List available custom resources
kubectl api-resources | grep database.platform.io

# Try creating a test claim (optional verification)
cat <<EOF | kubectl apply -f -
apiVersion: database.platform.io/v1alpha1
kind: PostgreSQLClaim
metadata:
  name: test-claim
  namespace: default
spec:
  parameters:
    tier: development
    storageGB: 20
    version: "15"
    enableBackups: false
EOF
```

**Expected Output:**
```
postgresqlclaim                 database.platform.io         true       PostgreSQLClaim
postgresqlclaims                database.platform.io         true       PostgreSQLClaim

postgresqlclaim.database.platform.io/test-claim created
```

Check the claim status:
```bash
kubectl get postgresqlclaim test-claim -o yaml
```

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
python generate-env-defaults.py
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

**Expected Output:** YAML file showing:
- `instanceClass: db.r6g.large` (production instance type)
- `allocatedStorage: 100` (production storage)
- `backupRetentionPeriod: 30` (30-day backups)
- `multiAz: true` (multi-availability zone)
- `deletionProtection: true` (deletion protection enabled)
- `performanceInsightsEnabled: true`

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

These patchsets are referenced inside compositions (e.g., `composition-postgresql.yaml`) using `patchSets[].name`. Every composed resource automatically inherits team, cost-center, environment, and ownership tags — enabling cost allocation, auditing, and lifecycle tracking without developer effort.

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
```bash
kubectl create namespace team-alpha
```

**Expected Output:**
```
namespace/team-alpha created
```

#### Step 6.2: Apply PostgreSQL Claim for Demo Application
```bash
kubectl apply -f demo-app-database.yaml
```

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
NAME           READY   SYNCED   AGE
demo-app-db    false   false    10s
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
NAME           READY   SYNCED   AGE
demo-app-db    true    true     45s
```

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
python test-infrastructure.py
```

**Expected Output:**
```
Testing infrastructure provisioning...
Waiting for claim demo-app-db to be ready...
✓ Claim is ready
✓ Connection secret exists
✓ Application connected to database successfully

✓ All infrastructure tests passed!
```

#### Step 7.3: Verify Complete Workflow
```bash
# Check all resources in team-alpha namespace
kubectl get all,secrets,postgresqlclaim -n team-alpha

# View connection secret details
kubectl get secret demo-app-db-connection -n team-alpha -o jsonpath='{.data.endpoint}' | base64 -d
```

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

For production deployment, create a Kubernetes deployment:

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
        image: python:3.10-slim
        command: ["python", "/controller/lifecycle-controller.py"]
        volumeMounts:
        - name: controller-code
          mountPath: /controller
      volumes:
      - name: controller-code
        configMap:
          name: lifecycle-controller-code
EOF
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

**Solution:** Wait 2-3 minutes for provider controllers to start, check network connectivity to xpkg.upbound.io

### Issue: PostgreSQL claim not becoming ready
**Diagnosis:**
```bash
kubectl describe postgresqlclaim demo-app-db -n team-alpha
```

**Common causes:**
- Crossplane providers not healthy (check `kubectl get providers`)
- Database credentials secret not created (run `./load-secrets.sh --create-k8s`)
- Insufficient RBAC permissions for the Kubernetes provider

**Solution:** Verify providers are healthy and the `db-credentials` secret exists in `crossplane-system`

### Issue: Python script import errors
```bash
# Reinstall dependencies
pip install --upgrade flask pyyaml kubernetes
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
- **Prerequisites Assessment:** Verify cluster access and Python/pip installation before starting
- **Stopping Point:** Phase 3 (Infrastructure Blueprints) provides a good checkpoint for intermediate students
- **Extension Activity:** Have students modify the GPU NodePool XRD to add resource quotas and affinity rules
- **Real-World Scenario:** Challenge students to write a composition for Redis cluster (cache) following the PostgreSQL pattern

