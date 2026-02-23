# Chapter 2: Scalable Platform Runtime with Kubernetes and Service Mesh

## Overview

This chapter teaches you how to configure production-ready Kubernetes platform clusters across environments using declarative Infrastructure as Code (Pulumi), GitOps principles (Flux), service mesh technology (Istio), and policy enforcement (OPA/Gatekeeper). The code demonstrates building secure, observable, and resilient container orchestration platforms that serve as the foundation for developer-focused engineering platforms.

## Key Concepts

- **Kind Clusters**: Local Kubernetes clusters for development and testing
- **Pulumi Infrastructure as Code**: Declarative cluster and networking provisioning
- **Istio Service Mesh**: Traffic management, security policies, and observability
- **Flux GitOps**: Declarative continuous deployment and reconciliation using the App of Apps pattern
- **OPA/Gatekeeper**: Policy enforcement for resource quotas, image registries, and pod security
- **Network Policies**: Zero-trust ingress/egress traffic control
- **Namespace Provisioning**: Automated onboarding with RBAC, quotas, and labels
- **Infrastructure Testing**: Automated validation using BATS and Python

## Code-to-Chapter Mapping

This section maps each file to its specific chapter section and learning objectives.

### 2.1: Why Kubernetes for Platform Runtime

Foundational concepts explaining Kubernetes' role in platform engineering. No direct code in this section, but all subsequent code demonstrates these principles:
- Platform vs. Application distinction
- Declarative infrastructure management
- Multi-tenancy patterns with namespace isolation

### 2.2: Network Configuration with DataClasses

**Primary File:** `modules/network.py`

Configuration module defining network infrastructure using Python DataClasses for type-safe configuration management.

**Key Classes:**
- `SubnetConfig`: Individual subnet configuration with CIDR and availability zone
- `ServiceMeshConfig`: Istio service mesh settings (version, namespace, traffic policies, observability)
- `FirewallRule`: Network policy rules (ingress/egress, protocol, CIDR blocks)
- `OPAConfig`: OPA/Gatekeeper policy engine settings
- `NetworkConfig`: Root configuration aggregating all network topology
- `TrafficPolicy` Enum: Network traffic policies (ALLOW_ALL, DENY_ALL, ISTIO_MUTUAL_TLS, STRICT)
- `LoggingLevel` Enum: Network debugging verbosity levels

**Learning Objectives:**
- Use Python DataClasses for configuration management
- Define subnet topology with validation
- Configure service mesh with mTLS policies
- Set up OPA policy constraints
- Create network policies for zero-trust security

**Helper Functions:**
- `create_development_network()`: Development cluster with 2 subnets, 1 NAT gateway
- `create_production_network()`: Production cluster with 3 subnets, 3 NAT gateways, stricter policies

### 2.3: Deploying the Core Platform

**Primary File:** `modules/cluster.py`

Kubernetes cluster provisioning module for Kind (Kubernetes in Docker) using Pulumi.

**Key Classes:**
- `KindClusterConfig`: Configuration dataclass for Kind cluster (name, version, node count, port mappings, labels, mounts)
- `KindClusterManager`: Manages cluster lifecycle with Pulumi
  - `create_kind_cluster()`: Generate Kind cluster configuration with kubeadm and containerd settings
  - `create_provider()`: Initialize Kubernetes provider for resource management
  - `setup_namespaces()`: Create system namespaces (flux-system, istio-system, cert-manager, monitoring, application)
  - `deploy_cluster()`: Orchestrate complete cluster deployment

**Learning Objectives:**
- Provision local Kubernetes clusters using Kind
- Create essential namespaces with proper labels
- Configure resource quotas and limit ranges
- Manage cluster lifecycle with Pulumi
- Implement proper dependency ordering

**Helper Functions:**
- `create_dev_cluster()`: 1 control plane + 2 worker nodes for development
- `create_prod_cluster()`: 1 control plane + 3 worker nodes for production-like testing

### 2.4: Deployment Validation Testing

**Primary Files:**
- `test/infrastructure.bats` - BATS shell-based infrastructure tests
- `test-cluster-health.py` - Python unittest framework

#### infrastructure.bats

BATS (Bash Automated Testing System) tests for infrastructure validation.

**Test Cases:**
- `cluster_is_running`: Verify kubectl connectivity and cluster availability
- `namespaces_exist`: Validate platform-system and monitoring namespaces
- `flux_is_ready`: Check Flux GitOps controller health
- `istio_injection_enabled`: Verify sidecar injection in application namespaces

**Learning Objectives:**
- Write shell-based infrastructure tests with BATS
- Validate Kubernetes cluster configuration
- Test GitOps and service mesh deployment
- Implement health checks for critical components

#### test-cluster-health.py

Python unittest framework for cluster health validation.

**Test Classes:**
- `TestClusterHealth`: Validate node readiness, system pods running, ArgoCD namespace
- `TestPulumiConfig`: Verify Pulumi configuration files exist
- `TestServiceMeshConfig`: Validate Istio mTLS configuration

**Learning Objectives:**
- Use Python unittest for infrastructure testing
- Parse kubectl JSON output
- Validate YAML configurations
- Create reusable test patterns

### 2.5: GitOps Architecture with Flux

**Primary Files:**
- `modules/flux.py` - Flux configuration module
- `platform-services.yaml` - Platform services kustomization
- `istio-mesh-config.yaml` - Istio service mesh configuration

#### modules/flux.py

Flux GitOps controller configuration using App of Apps pattern.

**Key Classes:**
- `FluxSourceConfig`: Git repository source configuration
  - `to_kubernetes_resource()`: Convert to GitRepository manifest
- `FluxKustomizationConfig`: Kustomization configuration for reconciliation
  - `to_kubernetes_resource()`: Convert to Kustomization manifest
- `FluxAppOfAppsManager`: Manages hierarchical application structure
  - `add_source()`: Register Git source
  - `add_kustomization()`: Register Kustomization
  - `create_root_application()`: Create root App of Apps entry point
  - `create_platform_services_app()`: Create platform services application
  - `create_workload_app()`: Create user workload applications
  - `deploy_flux()`: Install Flux via Helm
  - `generate_manifests()`: Generate YAML manifests for declarative application

**App of Apps Hierarchy:**
```
root-app (entry point)
├── platform-services-app (Istio, cert-manager, monitoring, OPA)
└── workload-apps (api-backend, frontend, etc.)
```

**Learning Objectives:**
- Implement App of Apps pattern for GitOps
- Define Git sources and Kustomizations
- Configure dependency management
- Use Flux for continuous deployment
- Validate resource health checks

#### platform-services.yaml

Kustomization manifest defining cluster-wide platform services via Flux.

**Resources Deployed:**
- **Istio Service Mesh**: istiod (control plane), ingress gateway, base
  - Namespace: istio-system
  - Replicas: 2 (istiod), 2 (ingress gateway)
  - Auto-scaling: 2-5 replicas with resource requests/limits

- **cert-manager**: TLS certificate management
  - Namespace: cert-manager
  - ClusterIssuers: letsencrypt-prod, letsencrypt-staging
  - ACME solver for HTTP-01 challenges

- **Monitoring Stack**: Prometheus, Grafana, Alertmanager
  - Namespace: monitoring (with istio-injection enabled)
  - Prometheus: 2 replicas, 7-day retention
  - Grafana: Pre-configured datasources
  - Alertmanager: Multi-channel routing

- **OPA/Gatekeeper**: Policy enforcement
  - Namespace: gatekeeper-system
  - ConstraintTemplates:
    - `K8sRequiredLimits`: Enforce CPU/memory limits on containers
    - `K8sAllowedRegistries`: Whitelist image registries
  - Constraints: require-limits, allowed-registries

- **Network Policies**:
  - Default deny ingress in application namespace
  - Allow same-namespace traffic
  - Allow from Istio ingress gateway

**Learning Objectives:**
- Use Kustomize for resource organization
- Deploy Helm charts via Flux
- Configure Istio service mesh
- Implement OPA policies
- Set up monitoring and observability
- Use HelmRepository sources

#### istio-mesh-config.yaml

Istio service mesh configuration resources.

**Security Policies:**
- `PeerAuthentication`: Enforce strict mTLS mode
- `RequestAuthentication`: JWT token validation
- `AuthorizationPolicy`: RBAC with deny-all default

**Traffic Management:**
- `VirtualService`: Canary deployments (90% v1, 10% v2)
  - Timeout: 10s, Retries: 3 attempts × 2s
- `DestinationRule`: Load balancing and circuit breaking
  - Connection pooling: 100 max connections
  - Outlier detection: eject after 5 consecutive errors

**Ingress:**
- `Gateway`: Multi-host HTTPS/HTTP configuration
  - HTTPS with TLS secrets
  - HTTP to HTTPS redirect

**Observability:**
- `Telemetry`: Metrics and tracing configuration
  - Prometheus metrics with custom dimensions
  - Jaeger tracing with 10% sampling

**Learning Objectives:**
- Implement mTLS with Istio
- Configure traffic policies for canary deployments
- Set up circuit breaking and outlier detection
- Define authorization policies
- Configure observability with metrics and tracing

### 2.6: Pulumi Kind Cluster

**Primary File:** `pulumi-cluster/__main__.py`

Kind cluster deployment using Pulumi for infrastructure-as-code patterns.

**Resources Created:**
- Kind cluster with configurable worker nodes
- Docker network for cluster communication
- Port mappings for ingress (80, 443) and NodePorts (30000-30100)
- Kubeconfig export for kubectl access

**Configuration (via Pulumi.yaml):**
```yaml
cluster:name: platform-dev
cluster:kubernetesVersion: "1.28"
cluster:numWorkerNodes: 2
cluster:environment: dev
```

**Learning Objectives:**
- Provision Kind clusters with Pulumi
- Configure cluster networking and port mappings
- Manage cluster lifecycle with IaC
- Export kubeconfig for kubectl access

### Supplementary Files

#### namespace-provisioner.py

Standalone Python script for automating namespace provisioning in existing clusters.

**Features:**
- Create namespaces with custom labels
- Apply resource quotas (CPU, memory, pod count)
- Implement network policies (deny-all ingress, allow same-namespace, allow monitoring)
- Create service accounts and RBAC bindings
- Environment-aware configuration (dev/staging/prod)

**Usage:**
```bash
python namespace-provisioner.py --namespace app-team --env prod --team backend
```

**Learning Objectives:**
- Automate namespace onboarding
- Implement resource governance
- Configure network policies programmatically
- Create repeatable infrastructure workflows

#### multi-env-config.yaml

Configuration comparison for production vs. non-production environments.

**Production Configuration:**
- 18 nodes (3 system + 10 app + 5 batch)
- t3.xlarge/2xlarge and m6i.xlarge instances
- 30-day metrics retention
- Pod security policies enabled
- Daily backups with 30-day retention

**Non-Production Configuration:**
- 6 nodes (2 system + 3 app + 1 batch)
- t3.large/xlarge instances
- 7-day metrics retention
- Relaxed security for development velocity
- Weekly backups with 7-day retention

**Learning Objectives:**
- Design environment-specific cluster configurations
- Understand production security requirements
- Configure autoscaling for different workloads
- Plan monitoring and backup strategies

#### argocd-platform-app.yaml

Alternative GitOps tool configuration (ArgoCD vs. Flux).

**Applications:**
- platform-core: Core platform services
- platform-observability: Monitoring stack (Prometheus, Grafana, Jaeger)
- platform-ingress: Ingress controller configuration

**Project Configuration:**
- Source restrictions (approved Git repositories and Helm charts)
- Destination namespaces (platform-*, monitoring, ingress-*)
- RBAC and audit controls
- Signature verification for Git commits

**Learning Objectives:**
- Compare Flux and ArgoCD approaches
- Configure GitOps automation
- Implement source and destination policies
- Enable multi-environment deployments

#### Pulumi.yaml

Pulumi project configuration file.

**Defines:**
- Project name: platform-cluster
- Runtime: Python
- Configuration parameters for cluster name, Kubernetes version, node count, environment, region
- VirtualEnv setup for dependency isolation

### pulumi-cluster/ Directory

Pulumi project for Kind cluster deployment.

**Files:**
- `__main__.py`: Kind cluster with configurable workers, networking, port mappings
- `Pulumi.yaml`: Project configuration and stacks
- `requirements.txt`: Python dependencies (pulumi, pulumi-kubernetes, pyyaml)

### test/ Directory

Test automation for infrastructure validation.

**Files:**
- `infrastructure.bats`: BATS shell tests for cluster validation
- Related Python tests: `test-cluster-health.py` (in root directory)

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Kind Cluster                      │
├─────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────┐ │
│  │  Flux GitOps Controller (flux-system NS)       │ │
│  │  ├─ Root Application (App of Apps)             │ │
│  │  ├─ Platform Services Application              │ │
│  │  └─ Workload Applications                      │ │
│  └────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────┐ │
│  │  Istio Service Mesh (istio-system NS)          │ │
│  │  ├─ Ingress Gateway (north-south)              │ │
│  │  ├─ Sidecar Proxies (east-west)                │ │
│  │  ├─ VirtualServices & DestinationRules         │ │
│  │  └─ mTLS & Authorization Policies              │ │
│  └────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────┐ │
│  │  Platform Services                              │ │
│  │  ├─ cert-manager (TLS/SSL certificates)        │ │
│  │  ├─ Prometheus & Grafana (monitoring)          │ │
│  │  ├─ Alertmanager (alerting)                    │ │
│  │  ├─ OPA/Gatekeeper (policy enforcement)        │ │
│  │  └─ Network Policies (zero-trust)              │ │
│  └────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────┐ │
│  │  Application Namespace                          │ │
│  │  ├─ User workloads (Istio-injected)            │ │
│  │  ├─ Resource quotas enforced                   │ │
│  │  └─ Network policies enabled                   │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## Orphan Files and Notes

### Potential Orphan/Alternative Files

The following files are complementary but not directly tied to chapter sections:

1. **argocd-platform-app.yaml** - Alternative GitOps tool (Chapter 2 focuses on Flux, not ArgoCD)
   - Recommendation: Keep for reference; note in README that Flux is primary pattern

2. **pulumi-cluster/__main__.py** - Kind cluster via Pulumi (IaC approach)
   - Recommendation: Use alongside the Kind CLI approach for comparing IaC vs imperative workflows

3. **multi-env-config.yaml** - Standalone configuration comparison (informational, not executable)
   - Recommendation: Keep for learning environment design principles

All other files are core to the chapter content and should be retained.

## Prerequisites

### Docker Runtime (Required)

Kind runs Kubernetes nodes as Docker containers, so a Docker-compatible runtime must be running **before** you create a cluster.

- **Docker Desktop** (macOS / Windows): Open Docker Desktop and wait for the engine to start.
- **Colima** (macOS, lightweight alternative): `colima start`
- **Docker Engine** (Linux): `sudo systemctl start docker`

Verify Docker is reachable:
```bash
docker info --format '{{.ServerVersion}}'
# Should print a version like 24.0.7 — if you see a connection error, start your runtime first.
```

### Required Tools

1. **Kind** (v0.20+) - Kubernetes in Docker
   ```bash
   # macOS: brew install kind
   # Linux:
   curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
   chmod +x ./kind && sudo mv ./kind /usr/local/bin
   ```

2. **kubectl** (v1.26+) - Kubernetes CLI
   ```bash
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   chmod +x kubectl && sudo mv kubectl /usr/local/bin
   ```

3. **Pulumi** (v3.0+) - Infrastructure as Code framework
   ```bash
   curl -fsSL https://get.pulumi.com | sh
   ```

4. **Flux CLI** (v2.0+) - GitOps controller
   ```bash
   curl -s https://fluxcd.io/install.sh | sudo bash
   ```

5. **Helm** (v3.0+) - Kubernetes package manager
   ```bash
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
   ```

6. **Kustomize** (v5.0+) - Kubernetes configuration management
   ```bash
   # macOS: brew install kustomize
   # Linux: curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
   ```

7. **bats** (v1.0+) - Bash Automated Testing System
   ```bash
   sudo apt-get install -y bats
   ```

8. **Python** (v3.8+) with pip packages (installed via virtual environment in Step 2a):
   ```bash
   cd pulumi-cluster
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt   # pulumi, pulumi-kubernetes, pyyaml
   ```

## Step-by-Step Instructions

### Phase 1: Understanding Configuration (Read-Only)

**Step 1a: Review Network Configuration**
```bash
# Read modules/network.py to understand network topology
cat modules/network.py
# Key takeaway: NetworkConfig is root dataclass aggregating SubnetConfig,
# ServiceMeshConfig, OPAConfig, and FirewallRule definitions
```

**Expected Output:**
- Network configuration structure with DataClasses
- Development and production network factory functions
- Subnet CIDR validation and service mesh settings

**Step 1b: Review Cluster Configuration**
```bash
# Read modules/cluster.py to understand Kind cluster provisioning
cat modules/cluster.py
# Key takeaway: KindClusterManager orchestrates cluster creation with
# kubeadm, containerd, and Pulumi resource management
```

**Expected Output:**
- Kind cluster configuration with node definitions
- Namespace creation with resource quotas and limit ranges
- Provider initialization for Kubernetes resource management

### Phase 2: Environment Setup

**Step 2a: Create a Python Virtual Environment and Install Dependencies**
```bash
cd pulumi-cluster
python3 -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

The `requirements.txt` installs `pulumi`, `pulumi-kubernetes`, and `pyyaml`. Pulumi expects the virtual environment in a `venv/` directory (configured in `Pulumi.yaml`).

**Expected Output:**
```
Successfully installed pulumi-3.x.x pulumi-kubernetes-4.x.x pyyaml-6.x
```

**Step 2b: Initialize Pulumi Stack**
```bash
pulumi stack init dev
# Or select existing stack: pulumi stack select dev
```

**Expected Output:**
```
Created stack 'dev'
Setting organization to 'personal'
Default runtime language python
```

**Step 2c: Configure Pulumi Settings**
```bash
# For Kind cluster (local development):
pulumi config set cluster:name platform-dev
pulumi config set cluster:kubernetesVersion 1.27

pulumi config set cluster:numWorkerNodes 2
```

**Expected Output:**
```
Set 'cluster:name' to 'platform-dev'
Set 'cluster:kubernetesVersion' to '1.27'
```

### Phase 3: Cluster Deployment

**Step 3a: Create the Kind Cluster**

The Kind cluster must exist **before** running Pulumi. Pulumi provisions namespaces and quotas on an already-running cluster.

```bash
kind create cluster --name platform-dev --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 80
        hostPort: 8080
      - containerPort: 443
        hostPort: 8443
  - role: worker
  - role: worker
EOF
```

**Expected Output:**
```
Creating cluster "platform-dev" ...
 ✓ Ensuring node image (kindest/node:v1.28.0) 🖼
 ✓ Preparing nodes 📦 📦 📦
 ✓ Writing configuration 📜
 ✓ Starting control-plane 🕹️
 ✓ Installing CNI 🔌
 ✓ Installing StorageClass 💾
 ✓ Joining worker nodes 🚜
Set kubectl context to "kind-platform-dev"
```

**Step 3b: Verify the Cluster is Running**
```bash
kubectl get nodes
```

**Expected Output:**
```
NAME                         STATUS   ROLES           AGE   VERSION
platform-dev-control-plane   Ready    control-plane   1m    v1.28.0
platform-dev-worker          Ready    <none>          1m    v1.28.0
platform-dev-worker2         Ready    <none>          1m    v1.28.0
```

**Step 3c: Run Pulumi to Provision Namespaces and Quotas**

Pulumi fetches the kubeconfig from the running Kind cluster automatically and creates namespaces, resource quotas, and limit ranges.

```bash
pulumi up --yes
```

**Expected Output:**
```
Updating (dev)
     Type                              Name                  Status
 +   pulumi:pulumi:Stack               platform-cluster-dev  created
 +   ├─ pulumi:providers:kubernetes     kind-provider         created
 +   ├─ kubernetes:core/v1:Namespace    platform-system       created
 +   ├─ kubernetes:core/v1:Namespace    monitoring            created
 +   ├─ kubernetes:core/v1:Namespace    ingress               created
 +   ├─ kubernetes:core/v1:Namespace    databases             created
 +   ├─ kubernetes:core/v1:Namespace    apps                  created
 +   └─ ... (ResourceQuotas and LimitRanges for each namespace)

Resources:
    + 16 created
```

**Step 3d: Verify Namespaces**
```bash
kubectl get namespaces --show-labels | grep pulumi
```

**Expected Output:**
```
apps              Active   10s   environment=dev,managed-by=pulumi
databases         Active   10s   environment=dev,managed-by=pulumi
ingress           Active   10s   environment=dev,managed-by=pulumi
monitoring        Active   10s   environment=dev,managed-by=pulumi
platform-system   Active   10s   environment=dev,managed-by=pulumi
```

### Phase 4: Platform Services Deployment (GitOps)

**Important:** Flux must be installed **before** applying `platform-services.yaml`. The manifest contains Flux CRDs (HelmRelease, Kustomization, HelmRepository) that only exist after Flux is running. It also contains cert-manager and Gatekeeper CRDs that only exist after those tools are deployed by Flux.

**Step 4a: Install Flux GitOps Controller**
```bash
# Option 1: Using Flux CLI (recommended)
flux install --namespace flux-system

# Option 2: Using Helm (alternative)
helm repo add fluxcd-community https://fluxcd-community.github.io/helm-charts
helm install flux2 fluxcd-community/flux2 --namespace flux-system --create-namespace
```

**Expected Output:**
```
✓ install completed in 45s
✓ components are healthy
```

**Step 4b: Verify Flux Is Ready**
```bash
flux check
```

**Expected Output:**
```
► checking prerequisites
✓ kubernetes 1.28.0 >= 1.20.6
✓ kustomize 5.x.x >= 3.1.0
...
all checks passed
```

**Step 4c: Apply Platform Services and Create the Application Namespace**

Apply the manifest. Namespaces, HelmRepositories, and HelmReleases will be created. Flux will start reconciling and install Istio, cert-manager, Prometheus, and Gatekeeper automatically. Some CRD-dependent resources (ClusterIssuers, Constraints) will warn on this first apply — that's expected.

```bash
kubectl create namespace application
kubectl apply -f platform-services.yaml
```

**Expected Output:**
```
namespace/istio-system created
helmrepository.source.toolkit.fluxcd.io/istio created
helmrelease.helm.toolkit.fluxcd.io/istio-base created
...
# Warnings about ClusterIssuer, ConstraintTemplate — expected on first run
```

**Step 4d: Wait for Flux to Reconcile, Then Re-Apply**

Flux needs 1–2 minutes to install the Helm charts (cert-manager, Gatekeeper, etc.) which register the CRDs that the remaining resources depend on. Wait, then re-apply:

```bash
# Monitor progress — wait until cert-manager and gatekeeper show Ready
flux get helmrelease -A

# Wait 60s for CRDs to fully register, then re-apply
sleep 60 && kubectl apply -f platform-services.yaml
```

**Expected Output:**
```
clusterissuer.cert-manager.io/letsencrypt-prod created
clusterissuer.cert-manager.io/letsencrypt-staging created
constrainttemplate.templates.gatekeeper.sh/k8srequiredlimits unchanged
k8srequiredlimits.constraints.gatekeeper.sh/require-limits created
constrainttemplate.templates.gatekeeper.sh/k8sallowedregistries unchanged
# K8sAllowedRegistries Constraint may still warn — Gatekeeper needs ~10s more
```

**Step 4e: Final Re-Apply for Gatekeeper Constraints**

Gatekeeper generates Constraint CRDs from ConstraintTemplates asynchronously. A short wait and one more apply picks up any remaining Constraints:

```bash
sleep 10 && kubectl apply -f platform-services.yaml
```

**Expected Output (clean — no warnings):**
```
k8sallowedregistries.constraints.gatekeeper.sh/allowed-registries created
# Everything else shows 'unchanged'
```

### Phase 5: Service Mesh Configuration

**Step 5a: Verify Istio Deployment**
```bash
# Istio is deployed via Flux HelmRelease — monitor deployment status
kubectl rollout status deployment/istiod -n istio-system --timeout=5m
```

**Expected Output:**
```
deployment "istiod" successfully rolled out
```

**Step 5b: Enable Sidecar Injection**
```bash
kubectl label namespace application istio-injection=enabled
```

**Expected Output:**
```
namespace/application labeled
```

**Step 5c: Apply Service Mesh Configuration**
```bash
kubectl apply -f istio-mesh-config.yaml
```

**Expected Output:**
```
peerauthentication.security.istio.io/default created
virtualservice.networking.istio.io/platform-api created
destinationrule.networking.istio.io/platform-api created
...
```

**Step 5d: Verify Istio Configuration**
```bash
kubectl get gateway -A
kubectl get virtualservice -A
kubectl get destinationrule -A
```

**Expected Output:**
```
NAMESPACE        NAME                AGE
platform-apps    platform-gateway    2m
platform-apps    platform-ingress    2m
```

### Phase 6: Namespace Provisioning

**Step 6a: Provision Application Namespace**
```bash
python namespace-provisioner.py \
  --namespace app-team-1 \
  --env staging \
  --team backend \
  --cpu 10 \
  --memory 20Gi \
  --pods 100
```

**Expected Output:**
```
--- Provisioning namespace: app-team-1 ---
Creating namespace 'app-team-1'...
Applying labels to namespace 'app-team-1': {'environment': 'staging', 'team': 'backend', ...}
Creating ResourceQuota for namespace 'app-team-1'...
Creating NetworkPolicy for namespace 'app-team-1'...
Creating service accounts for namespace 'app-team-1'...

Namespace 'app-team-1' provisioned successfully!
```

**Step 6b: Verify Namespace Configuration**
```bash
kubectl get namespace app-team-1 -o yaml
kubectl get resourcequota,limitrange,networkpolicy -n app-team-1
```

**Expected Output:**
```
apiVersion: v1
kind: Namespace
metadata:
  labels:
    environment: staging
    team: backend
  name: app-team-1
...
```

### Phase 7: Infrastructure Testing

**Step 7a: Run BATS Tests**
```bash
# From the root code directory
bats test/infrastructure.bats -v
```

**Expected Output:**
```
 ✓ cluster_is_running
 ✓ namespaces_exist
 ✓ flux_is_ready
 ✓ istio_injection_enabled

4 tests, 0 failures
```

**Step 7b: Run Python Health Checks**
```bash
python test-cluster-health.py -v
```

**Expected Output:**
```
======================================================
Chapter 2: Cluster Health Tests
======================================================
test_argocd_namespace_exists (TestClusterHealth) ... skipped
test_nodes_ready (TestClusterHealth) ... ok
test_system_pods_running (TestClusterHealth) ... ok
test_main_py_exists (TestPulumiConfig) ... ok
test_pulumi_yaml_exists (TestPulumiConfig) ... ok
test_requirements_exists (TestPulumiConfig) ... ok
test_istio_config_exists (TestServiceMeshConfig) ... ok
test_istio_config_has_mtls (TestServiceMeshConfig) ... ok

------------------------------------------------------
Ran 8 tests in 0.5s

OK
```

### Phase 8: Verification and Cleanup

**Step 8a: Verify All Components**
```bash
# Check cluster status
kubectl get nodes -o wide
kubectl get namespaces

# Check Flux
flux get all

# Check Istio
kubectl get pods -n istio-system
kubectl get virtualservice -A

# Check monitoring
kubectl get pods -n monitoring

# Check OPA/Gatekeeper
kubectl get pods -n gatekeeper-system
```

**Expected Output:**
```
NAME                          STATUS   ROLES           AGE
platform-cluster-node-1       Ready    control-plane   2h
platform-cluster-node-2       Ready    <none>          2h
platform-cluster-node-3       Ready    <none>          2h

NAMESPACE              STATUS   AGE
flux-system            Active   1h
istio-system           Active   1h
cert-manager           Active   50m
monitoring             Active   45m
gatekeeper-system      Active   45m
application            Active   30m
```

**Step 8b: Clean Up (Optional)**
```bash
# Destroy Pulumi stack
cd pulumi-cluster
pulumi destroy
pulumi stack rm dev

# Or delete Kind cluster
kind delete cluster --name platform-dev
```

**Expected Output:**
```
Deleting cluster "platform-dev" ...
Deleted nodes: ["platform-dev-control-plane" "platform-dev-worker" "platform-dev-worker2"]
Stack 'dev' has been removed!
```

## Key Configuration Points

### Network Configuration (modules/network.py)

Edit configuration for your environment:

```python
# Development: 2 subnets, 1 NAT gateway
dev_network = create_development_network()

# Production: 3 subnets, 3 NAT gateways, strict mTLS
prod_network = create_production_network()

# Custom configuration
custom_network = NetworkConfig(
    vpc_cidr="10.1.0.0/16",
    cluster_name="my-cluster",
    subnets=[
        SubnetConfig(cidr_block="10.1.1.0/24", name="subnet-1", availability_zone="us-east-1a"),
        SubnetConfig(cidr_block="10.1.2.0/24", name="subnet-2", availability_zone="us-east-1b"),
    ],
    service_mesh=ServiceMeshConfig(
        enabled=True,
        version="1.17.1",
        traffic_policy=TrafficPolicy.STRICT,
        pilot_replicas=3,
    ),
    opa=OPAConfig(
        enabled=True,
        enable_audit_logging=True,
    ),
)
```

### Cluster Configuration (modules/cluster.py)

Customize cluster parameters:

```python
# Development cluster
dev_cluster = KindClusterConfig(
    cluster_name="platform-dev",
    kubernetes_version="1.27.0",
    num_worker_nodes=2,
    enable_ingress=True,
    enable_metrics_server=True,
)

# Production-like cluster
prod_cluster = KindClusterConfig(
    cluster_name="platform-prod",
    kubernetes_version="1.27.0",
    num_worker_nodes=3,
    api_server_port=6443,
    extra_port_mappings=[
        {"containerPort": 443, "hostPort": 8443, "protocol": "tcp"},
    ],
)
```

### Istio Configuration (istio-mesh-config.yaml)

Key customization points:

```yaml
# mTLS enforcement mode
PeerAuthentication:
  mtls:
    mode: STRICT  # Options: PERMISSIVE, STRICT, DISABLE

# Canary deployment traffic split
VirtualService:
  http:
  - route:
    - destination:
        subset: v1
      weight: 90  # 90% traffic to v1
    - destination:
        subset: v2
      weight: 10  # 10% traffic to v2

# Circuit breaking thresholds
DestinationRule:
  outlierDetection:
    consecutive5xxErrors: 5
    interval: 30s
    baseEjectionTime: 30s
    maxEjectionPercent: 50
```

### OPA/Gatekeeper Policies (platform-services.yaml)

Custom constraints example:

```yaml
# Require resource limits on all containers
ConstraintTemplate:
  rego: |
    violation[{"msg": msg}] {
      container := input.review.object.spec.containers[_]
      not container.resources.limits
      msg := sprintf("Container %v missing limits", [container.name])
    }

# Apply to all namespaces except system
Constraint:
  match:
    excludedNamespaces:
      - kube-system
      - kube-public
      - istio-system
```

## Companion Website Alignment

The companion website at https://peh-packt.platformetrics.com/ displays Chapter 2 content with the following sections:

| Website Section | Code File(s) | Notes |
|-----------------|--------------|-------|
| 2.1: Why Kubernetes for Platform Runtime | N/A | Foundational concepts |
| 2.2: Network Configuration with DataClasses | modules/network.py | Full DataClass implementation |
| 2.3: Deploying the Core Platform | modules/cluster.py | Kind cluster provisioning |
| 2.4: Deployment Validation Testing | test/infrastructure.bats, test-cluster-health.py | BATS and Python tests |
| 2.5: GitOps Architecture with Flux | modules/flux.py, platform-services.yaml | App of Apps pattern |
| Service Mesh Configuration | istio-mesh-config.yaml | mTLS, traffic policies, observability |

**Alignment Status:** Excellent alignment between code and website content. Website demonstrates code examples and explanations that correspond to actual files in the repository.

**Code File References on Website:**
- `modules/network.py` - Shown in 2.2 section
- `modules/cluster.py` - Shown in 2.3 section
- `test/infrastructure.bats` - Shown in 2.4 section
- `modules/flux.py` - Shown in 2.5 section
- `platform-services.yaml` - Shown in 2.5 section
- `istio-mesh-config.yaml` - Shown in service mesh section

**Exercise Alignment:**
Website Chapter 2 Exercises section lists:
1. Create Flux Validation Check - Use flux.py and infrastructure.bats
2. Create App-Dev and App-Production Configuration - Use modules/network.py and multi-env-config.yaml
3. Policy to Deny Unpinned Helm Versions - Implement in platform-services.yaml

## Troubleshooting

### Docker / Colima Issues

**`kind create cluster` fails with "failed to get docker info" or "docker.sock: connect: no such file or directory":**

Your Docker runtime isn't running. Start it first:
```bash
# Colima (macOS):
colima start

# Docker Desktop (macOS / Windows):
# Open Docker Desktop from your Applications and wait for the engine icon to turn green.

# Docker Engine (Linux):
sudo systemctl start docker
```

Then verify Docker is reachable before retrying:
```bash
docker info --format '{{.ServerVersion}}'
```

### Pulumi / Kubeconfig Issues

**`pulumi up` fails with "no configuration has been provided" or "Kubernetes cluster is unreachable":**

The Kind cluster must exist before running Pulumi. Create it first:
```bash
kind create cluster --name platform-dev --config kind-config.yaml
```

Then verify kubectl can reach the cluster:
```bash
kubectl get nodes
```

If the cluster exists but kubectl can't connect, set the context:
```bash
kubectl cluster-info --context kind-platform-dev
```

### CRD / Platform-Services Ordering Issues

**`kubectl apply -f platform-services.yaml` fails with "no matches for kind HelmRelease" or "ensure CRDs are installed first":**

Two possible causes:

1. **Flux not installed yet.** Flux must be installed before applying `platform-services.yaml`:
```bash
flux install --namespace flux-system
kubectl apply -f platform-services.yaml
```

2. **Deprecated API versions.** If Flux is installed but HelmRelease/HelmRepository still fail, the manifest may use old API versions (`v2beta1`, `v1beta2`) that have been removed in newer Flux releases. Update them:
   - `helm.toolkit.fluxcd.io/v2beta1` → `helm.toolkit.fluxcd.io/v2`
   - `source.toolkit.fluxcd.io/v1beta2` → `source.toolkit.fluxcd.io/v1`

**ClusterIssuer or ConstraintTemplate resources fail on first apply:**

These depend on CRDs from cert-manager and Gatekeeper, which are deployed by Flux HelmReleases. Wait for Flux to finish reconciling, then re-apply:
```bash
# Check HelmRelease status
flux get helmrelease -A

# Once cert-manager and gatekeeper show Ready, re-apply
kubectl apply -f platform-services.yaml
```

**Constraint fails with "strict decoding error: unknown field spec.parameters":**

When you update a ConstraintTemplate (e.g. to add a `parameters` schema), Gatekeeper needs a few seconds to regenerate the Constraint CRD. Wait and re-apply:
```bash
sleep 10 && kubectl apply -f platform-services.yaml
```

**ClusterIssuers still fail even after cert-manager HelmRelease shows Ready:**

cert-manager CRDs can take 30–60 seconds to fully register after the HelmRelease succeeds. Verify the CRDs exist, then re-apply:
```bash
# Check if cert-manager CRDs are registered
kubectl get crd | grep cert-manager

# If clusterissuers.cert-manager.io is listed, re-apply
kubectl apply -f platform-services.yaml
```

**K8sAllowedRegistries Constraint fails with "ensure CRDs are installed first":**

ConstraintTemplate CRDs are generated by Gatekeeper after the template is applied. The matching Constraint can only be created after Gatekeeper has processed the template. Wait and re-apply:
```bash
# Verify the CRD was generated from the ConstraintTemplate
kubectl get crd | grep k8sallowedregistries

# Once listed, re-apply
kubectl apply -f platform-services.yaml
```

**General tip — multiple re-applies are normal:**

Because platform-services.yaml bundles everything into one file, resources with CRD dependencies will fail until their parent CRDs are installed by Flux. The expected workflow is: apply → wait for Flux → re-apply → wait for CRD propagation → re-apply. After 2–3 applies, everything will be created.

**"namespaces 'application' not found" error:**

The `application` namespace must exist before applying NetworkPolicies that target it:
```bash
kubectl create namespace application
kubectl apply -f platform-services.yaml
```

**`kubectl apply` fails with "TLS handshake timeout" or "failed to download openapi":**

The API server is temporarily overloaded (common right after installing Flux on a resource-constrained Kind cluster). Retry with validation disabled:
```bash
kubectl apply -f platform-services.yaml --validate=false
```

If timeouts persist, give Colima more resources:
```bash
colima stop
colima start --cpu 4 --memory 6
```

### Gatekeeper Webhook Timeout

**`kubectl label namespace` or `kubectl apply` fails with "failed calling webhook check-ignore-label.gatekeeper.sh: context deadline exceeded":**

Gatekeeper's validating webhook isn't ready yet or is timing out. This commonly happens right after Flux installs Gatekeeper. Note that Flux installs Gatekeeper into `flux-system` (not `gatekeeper-system`), so check pods there:
```bash
# Check if Gatekeeper pods are running (they're in flux-system, not gatekeeper-system)
kubectl get pods -n flux-system | grep gatekeeper
```

If the pods are running but the webhook still times out, delete the webhook configuration to unblock yourself — Gatekeeper will re-create it automatically:
```bash
kubectl delete validatingwebhookconfiguration gatekeeper-validating-webhook-configuration
kubectl label namespace application istio-injection=enabled --overwrite
```

If pods aren't running, check the HelmRelease:
```bash
flux get helmrelease gatekeeper -n flux-system
```

### Istio Mesh Config Issues

**`kubectl apply -f istio-mesh-config.yaml` fails with "namespaces 'platform-apps' not found":**

The Istio mesh config expects the `application` namespace (not `platform-apps`). Make sure you're using the updated `istio-mesh-config.yaml` and that the namespace exists:
```bash
kubectl create namespace application
kubectl label namespace application istio-injection=enabled --overwrite
kubectl apply -f istio-mesh-config.yaml
```

**DestinationRule fails with "unknown field minRequestVolume" or Telemetry fails with "unknown field dimensions":**

These fields were removed or renamed in newer Istio versions (1.22+). The updated `istio-mesh-config.yaml` uses the correct field names for Istio 1.22+:
- `outlierDetection.minRequestVolume` has been removed — delete it
- `Telemetry` uses `telemetry.istio.io/v1` with `overrides`/`tagOverrides` instead of `v1alpha1` with `dimensions`

### Cluster Issues

**Cluster stuck pending:**
```bash
kind get clusters
kind delete cluster --name platform-dev
pulumi destroy && pulumi up
```

**Nodes not ready:**
```bash
kubectl describe node <node-name>
kubectl logs -n kube-system -l component=kubelet
```

**DNS not resolving:**
```bash
kubectl run -it --rm debug --image=ubuntu:latest --restart=Never -- bash
apt-get update && apt-get install -y dnsutils
nslookup kubernetes.default
```

### Flux Issues

**Flux not syncing:**
```bash
flux get source git
flux get kustomization
flux logs --all-namespaces --follow
kubectl describe kustomization -n flux-system
```

**Helm release failing:**
```bash
kubectl describe helmrelease <release> -n flux-system
kubectl logs deployment/helm-controller -n flux-system
```

### Istio Issues

**Sidecar not injecting:**
```bash
# Verify webhook is working
kubectl get mutatingwebhookconfigurations | grep istio

# Manually label namespace
kubectl label namespace default istio-injection=enabled --overwrite

# Restart pods to trigger injection
kubectl rollout restart deployment -n default
```

**mTLS handshake failures:**
```bash
# Check PeerAuthentication mode
kubectl get peerauthentication -A

# Verify sidecar proxies are running
kubectl get pods -A --field-selector status.phase=Running
```

### Test Failures

**BATS tests failing:**
```bash
# Run single test with verbose output
bats test/infrastructure.bats -f "cluster_is_running"

# Check kubectl availability
which kubectl
kubectl version
```

**Python tests failing:**
```bash
# Check Python and packages
python --version
pip list | grep -i pulumi

# Run with detailed output
python test-cluster-health.py -v
```

## References

- [Kind Documentation](https://kind.sigs.k8s.io/)
- [Pulumi Kubernetes Provider](https://www.pulumi.com/docs/reference/pkg/kubernetes/)
- [Pulumi Command Provider](https://www.pulumi.com/registry/packages/command/)
- [Flux Documentation](https://fluxcd.io/docs/)
- [Istio Documentation](https://istio.io/latest/docs/)
- [OPA/Gatekeeper](https://open-policy-agent.github.io/gatekeeper/)
- [cert-manager Documentation](https://cert-manager.io/)
- [Kustomize Documentation](https://kustomize.io/)
- [BATS Documentation](https://bats-core.readthedocs.io/)
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)
- [GitOps Principles](https://opengitops.dev/)

## License

All code in this chapter is provided as educational material for "The Platform Engineer's Handbook" published by Packt Publishing.
