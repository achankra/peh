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

### 2.6 (Alternative): Pulumi EKS Cluster

**Primary File:** `pulumi-cluster/__main__.py`

Production AWS EKS cluster deployment (alternative to Kind for cloud environments).

**Resources Created:**
- VPC with public/private subnets across availability zones
- Internet gateway and route tables
- EKS cluster with managed control plane
- IAM roles for cluster and worker nodes
- Managed node groups with auto-scaling (t3.medium, 1-10 nodes)
- EKS add-ons: CoreDNS, kube-proxy
- CloudWatch logging for cluster operations

**Configuration (via Pulumi.yaml):**
```yaml
cluster:name: platform-cluster
cluster:kubernetesVersion: "1.28"
cluster:numWorkerNodes: 3
cluster:environment: dev
aws:region: us-east-1
```

**Learning Objectives:**
- Provision production-grade EKS clusters with Pulumi
- Configure AWS networking for Kubernetes
- Manage cluster add-ons
- Set up logging and monitoring
- Enable managed node groups with auto-scaling

**Note:** This file provides an AWS EKS alternative but the chapter primarily focuses on Kind clusters for learning. Both approaches use identical Pulumi patterns.

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

Complete production-ready Pulumi project for AWS EKS deployment.

**Files:**
- `__main__.py`: Complete EKS cluster with VPC, subnets, node groups, add-ons
- `Pulumi.yaml`: Project configuration and stacks
- `requirements.txt`: Python dependencies (pulumi, pulumi-aws, pulumi-eks, pulumi-kubernetes, pyyaml)

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

2. **pulumi-cluster/__main__.py** - AWS EKS alternative (Chapter focuses on Kind)
   - Recommendation: Keep as reference for production AWS deployments; document clearly as optional

3. **multi-env-config.yaml** - Standalone configuration comparison (informational, not executable)
   - Recommendation: Keep for learning environment design principles

All other files are core to the chapter content and should be retained.

## Prerequisites

### Required Tools

1. **Kind** (v0.20+) - Kubernetes in Docker
   ```bash
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

8. **Python** (v3.8+) with pip packages:
   ```bash
   pip install pulumi pulumi-kubernetes pulumi-docker pyyaml
   ```

### Optional Tools (for AWS EKS alternative)

- **AWS CLI** (v2.0+) with configured credentials
- **pulumi-aws** and **pulumi-eks** Python packages

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

**Step 2a: Initialize Pulumi Stack**
```bash
cd pulumi-cluster
pulumi stack init dev
# Or select existing stack: pulumi stack select dev
```

**Expected Output:**
```
Created stack 'dev'
Setting organization to 'personal'
Default runtime language python
```

**Step 2b: Configure Pulumi Settings**
```bash
# For Kind cluster (local development):
pulumi config set cluster:name platform-dev
pulumi config set cluster:kubernetesVersion 1.27

# For AWS EKS (optional):
pulumi config set aws:region us-east-1
pulumi config set cluster:numWorkerNodes 3
```

**Expected Output:**
```
Set 'cluster:name' to 'platform-dev'
Set 'cluster:kubernetesVersion' to '1.27'
```

### Phase 3: Cluster Deployment

**Step 3a: Deploy Infrastructure (Kind)**

**Option A: Using Python modules directly:**
```bash
cd ..
# Create a custom Pulumi program using cluster.py and network.py modules
# This approach is documented in the chapter
pulumi up
```

**Option B: Using provided EKS stack (requires AWS credentials):**
```bash
cd pulumi-cluster
pulumi up
```

**Expected Output:**
- Resource creation summary showing VPC, subnets, EKS cluster, node groups
- Cluster endpoint and kubeconfig configuration
- Duration: 15-20 minutes for full cluster provisioning

**Step 3b: Configure kubectl Access**
```bash
# For EKS:
aws eks update-kubeconfig --region us-east-1 --name platform-cluster

# For Kind (if using):
kind get kubeconfig --name platform-dev > ~/.kube/kind-config-platform-dev
export KUBECONFIG=~/.kube/kind-config-platform-dev
```

**Expected Output:**
```
Updated context arn:aws:eks:us-east-1:ACCOUNT:cluster/platform-cluster in /home/user/.kube/config
```

**Step 3c: Verify Cluster Readiness**
```bash
kubectl get nodes
kubectl get pods -A
```

**Expected Output:**
```
NAME                          STATUS   ROLES           AGE   VERSION
platform-cluster-node-1       Ready    control-plane   5m    v1.27.0
platform-cluster-node-2       Ready    <none>          5m    v1.27.0
```

### Phase 4: Platform Services Deployment (GitOps)

**Step 4a: Create Flux System Namespace**
```bash
kubectl create namespace flux-system
kubectl apply -f platform-services.yaml
```

**Expected Output:**
```
namespace/istio-system created
helmrelease.helm.toolkit.fluxcd.io/istio-base created
helmrelease.helm.toolkit.fluxcd.io/istiod created
...
```

**Step 4b: Deploy Flux GitOps Controller**
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

**Step 4c: Verify Flux Deployment**
```bash
flux check --pre
flux get source git
flux get kustomization
```

**Expected Output:**
```
► checking prerequisites
✓ kubernetes 1.27.0 >= 1.20.6
✓ kustomize 4.5.7 >= 3.1.0
...
all checks passed
```

### Phase 5: Service Mesh Configuration

**Step 5a: Deploy Istio**
```bash
# Istio is deployed via platform-services.yaml HelmRelease
# Monitor deployment status
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
Resources to delete:
 - eks:Cluster: platform-cluster
 - ec2:Instance: platform-cluster-worker-1
 ...

Do you want to perform this destroy? [yes/no]: yes
...
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
- [Pulumi AWS Provider](https://www.pulumi.com/docs/reference/pkg/aws/)
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
