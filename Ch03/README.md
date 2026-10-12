# Chapter 3: Securing Platform Access

## Overview

This directory contains comprehensive examples and tools for implementing security best practices in Kubernetes-based platforms. The chapter covers securing platform access through multiple layers: OAuth/OIDC-based identity and access management with Keycloak, role-based access control (RBAC), policy-as-code enforcement with Open Policy Agent (OPA), network policies for zero-trust networking, and automated TLS certificate management. These examples enable platform teams to balance developer autonomy with protecting platform system components from accidental damage while implementing the principle of least privilege.

## Code-to-Chapter Mapping

### Security Auditing & Assessment

| File | Section | Purpose |
|------|---------|---------|
| `security-audit.sh` | "Understanding platform security requirements" | Bash script for quick security auditing and vulnerability scanning. Identifies overly permissive RoleBindings, service accounts with excessive permissions, pods running as root, missing resource limits, and pods with privileged mode enabled. Supports namespace-scoped and cluster-wide auditing. |

### RBAC Configuration

| File | Section | Purpose |
|------|---------|---------|
| `rbac-platform-admin.yaml` | "Implementing Role-Based Access Control (RBAC)" | Kubernetes manifests defining ClusterRole and ClusterRoleBinding for platform administrators. Includes four personas: `platform-admin` (elevated permissions), `platform-admin-restricted` (limited admin with safety checks), `platform-audit-viewer` (read-only for security auditors), and `platform-operator` (workload management without administrative access). Demonstrates the principle of least privilege for platform team members. |
| `rbac-developer-role.yaml` | "Implementing Role-Based Access Control (RBAC)" | Kubernetes Role and RoleBinding resources for platform developers. Defines `developer-role` (namespace-scoped management of deployments, services, and pods) and `developer-readonly-role` (view-only access). ServiceAccount `developer-user` is provided for automation/CI-CD integration. Implements namespace isolation preventing cross-team access. |
| `service-account.yaml` | "Securing CI/CD with service accounts" and "Principle of least privilege in practice" | Kubernetes ServiceAccount `ci-cd-deployer` in the `staging` namespace for CI/CD pipelines. It intentionally has no permissions by itself: they are granted separately by `role-minimal-deployer.yaml` (a namespace-scoped `minimal-deployer` Role) and `rolebinding.yaml`, which keeps the permission grant explicit and auditable. Includes guidance on using short-lived tokens (`kubectl create token`) instead of long-lived secrets. Demonstrates scoped service account permissions for high-risk deployment pipelines. |
| `role-minimal-deployer.yaml` | "Securing CI/CD with service accounts" and "Principle of least privilege in practice" | Namespace-scoped Role `minimal-deployer` in `staging` (Step 2 of the CI/CD set). Grants only what a rolling deploy needs: read deployments and replica sets, update/patch deployments (including `scale` and `status`) but not create or delete them, get/list/delete pods for rollout monitoring, read pod logs, and read-only access to ConfigMaps and Secrets so the pipeline cannot write secrets into build logs. |
| `rolebinding.yaml` | "Securing CI/CD with service accounts" and "Principle of least privilege in practice" | RoleBinding `ci-cd-deployer-binding` (Step 3) that binds the `ci-cd-deployer` ServiceAccount to the `minimal-deployer` Role in `staging`, so the grant applies to that one namespace only. The file's comments include `kubectl auth can-i` checks (update deployments: yes; create deployments or read pods in `production`: no). Apply `service-account.yaml` and `role-minimal-deployer.yaml` first. |
| `clusterrole-image-reader.yaml` | "Principle of least privilege in practice" | ClusterRole `image-registry-reader` (Step 4) for pipelines that must read image metadata or a registry pull secret outside their own namespace. It allows get/list on `images` and `imagestreams` (OpenShift API group) and on the single Secret `registry-credentials`. A ClusterRole is needed for the cluster-scoped resources, but bind it with a RoleBinding, not a ClusterRoleBinding, so the permission stays inside the target namespace (the file's comments show the `kubectl create rolebinding` command). |

### TLS Certificate Management

| File | Section | Purpose |
|------|---------|---------|
| `cert-manager-config.yaml` | "Automated TLS certificate management" | cert-manager ClusterIssuer and Certificate configurations for automatic TLS certificate generation and renewal. Includes Let's Encrypt staging/production issuers, internal CA setup for mTLS, and certificate resources for platform API, demo app, and Keycloak. Eliminates manual certificate management friction that causes teams to deploy without encryption. |

### Demo Application & Network Security

| File | Section | Purpose |
|------|---------|---------|
| `demo-app-deployment.yaml` | "Building the demo application experience" and "Zero-Trust networking and network policies" | Complete Kubernetes Deployment demonstrating secure application practices that pilot teams will face. Includes: ServiceAccount with minimal privileges, ConfigMap/Secret management, security context (non-root user, read-only filesystem, dropped capabilities), resource requests/limits, health checks (`/healthz`, `/readyz` on the podinfo demo app), affinity rules for HA, and NetworkPolicy restricting ingress/egress traffic. Istio Gateway and VirtualService with a cert-manager Certificate for TLS, PodDisruptionBudget for availability, and HorizontalPodAutoscaler for auto-scaling. Simulates complete developer experience from code to running application. |

### Policy-as-Code Enforcement

| File | Section | Purpose |
|------|---------|---------|
| `template-resource-limits.yaml` | "Policy-as-code guardrails with OPA" | OPA Gatekeeper ConstraintTemplate enforcing that all containers specify CPU and memory resource limits. Prevents unbounded resource consumption and ensures fair scheduling. Used to reject deployment attempts that violate resource limit policies. |
| `constraint-namespace-labels.yaml` | "Policy-as-code guardrails with OPA" | OPA Gatekeeper Constraint enforcing required labels on namespaces (team ownership, cost-center allocation, environment classification). Demonstrates how policy-as-code works alongside RBAC to prevent configuration drift and enforce compliance regardless of who creates resources. |

### Testing & Validation

| File | Section | Purpose |
|------|---------|---------|
| `test-rbac-permissions.py` | "Implementing Role-Based Access Control (RBAC)" | Python test suite validating RBAC configuration files. Tests verify developer roles don't grant cluster-admin access, platform admin roles manage namespaces, demo app has resource limits and security context, and cert-manager configuration is properly defined. Supports test-driven validation of security posture. |
| `keycloak-realm-config.py` | "Installing and configuring Keycloak" and "OIDC configuration and creating platform identities" | Python script to automate Keycloak realm configuration for platform SSO integration. Creates Keycloak realm, OAuth2/OIDC client, roles (platform-admins, platform-users), user groups and mappings, and realm policies. Supports authentication, realm/client creation, user/group management, and verification workflows. Enables teams to have centralized identity management with short-lived tokens. |

### Secrets Management (Bitwarden Integration)

| File | Section | Purpose |
|------|---------|---------|
| `load-secrets.sh` | Secrets Management (cross-chapter) | Retrieves Keycloak admin credentials from Bitwarden vault. Exports `KEYCLOAK_ADMIN`, `KEYCLOAK_PASSWORD`, and `KEYCLOAK_URL` so you don't need to hardcode or manually export them. Sources the shared `bw-helper.sh` from Ch1. |

## Prerequisites

### Running This Chapter Standalone

> If you are jumping into this chapter without completing earlier chapters, use these commands to set up the infrastructure dependencies. If you already have them running, skip this section.

> **Note:** If you completed Chapter 2, your Kind cluster is already running and the `platform-system` namespace already exists (Chapter 2 creates it with Pulumi). `rbac-platform-admin.yaml` places its ServiceAccounts there. Otherwise, create the cluster and namespace first.

```bash
# 1. Start Docker Desktop (macOS: open from Applications or Spotlight)
open -a "Docker"
# Wait for the Docker engine to start before continuing

# 2. Create a Kind cluster (skip if you already have one)
kind get clusters                       # Check for existing clusters
kind create cluster --name platform-dev # Create one if none listed
kubectl get nodes                       # Verify node(s) are Ready

# Create the platform-system namespace (Chapter 2 creates it; safe to re-run)
kubectl create namespace platform-system --dry-run=client -o yaml | kubectl apply -f -

# Install cert-manager
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set crds.enabled=true --version v1.21.1

# Install OPA Gatekeeper
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.23.1/deploy/gatekeeper.yaml

```

### System Requirements
- Kubernetes cluster 1.21+ or local Kind cluster for testing
- kubectl configured and authenticated to cluster
- Bash 4.0+ for shell scripts
- Python 3.7+ for Python scripts

### Kubernetes Components
- **cert-manager**: `helm repo add jetstack https://charts.jetstack.io && helm install cert-manager jetstack/cert-manager --version v1.21.1 --set crds.enabled=true`
- **Keycloak**: Deployed as StatefulSet in platform-services namespace with persistent storage (PostgreSQL backend recommended)
- **Ingress Controller**: nginx-ingress or compatible controller for Ingress resources
- **OPA Gatekeeper**: installed by Chapter 2 (Flux `HelmRelease`); standalone, use the `kubectl apply -f .../gatekeeper/v3.23.1/deploy/gatekeeper.yaml` command under Prerequisites above

### Python Dependencies
```bash
python3 -m venv venv && source venv/bin/activate
pip install requests
```

### Kubernetes RBAC & Audit Logging
- Kubernetes audit logging enabled for compliance tracking
- API server configured with OIDC flags for Keycloak integration:
  - `--oidc-issuer-url=https://keycloak.example.com/realms/platform-engineering`
  - `--oidc-client-id=kubernetes-cli`
  - `--oidc-username-claim=preferred_username`
  - `--oidc-groups-claim=groups`

## Step-by-Step Instructions

### Phase 1: Security Audit & Assessment

**Step 1.1: Audit Current Cluster Security**
```bash
# Run comprehensive security audit
bash security-audit.sh

# Audit specific namespace
bash security-audit.sh --namespace kube-system

# Verbose output for detailed findings
bash security-audit.sh --verbose
```

**Expected Output:**
```
=== Kubernetes Security Audit ===
Timestamp: [current date/time]

=== Cluster Access Check ===
[OK] Cluster is accessible - Version: v1.XX.X

=== RBAC Permissions Audit ===
[WARNING] Found N cluster-admin role bindings
...

=== Audit Summary ===
Found X potential security issues
```

**Next Steps:** Review findings and prioritize critical issues. Proceed to Phase 2 to implement remediation.

### Phase 2: Identity & Access Management Setup

**Step 2.0: Start Keycloak**

Start a local Keycloak instance for development. We use port 8180 because port 8080 is already used by the Kind cluster's control-plane port mapping from Chapter 2:
```bash
docker run -d -p 8180:8080 -p 9000:9000 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  -e KC_HEALTH_ENABLED=true \
  quay.io/keycloak/keycloak:26.7.4 start-dev
```

Verify Keycloak is running (may take 30–60 seconds to start). Health endpoints are served on the management port 9000, not 8180:
```bash
curl -s http://localhost:9000/health/ready
```

**Step 2.1: Store Keycloak Credentials in Bitwarden**

If using Bitwarden for secrets management (recommended), create the vault item so `load-secrets.sh` can retrieve credentials automatically:
```bash
# If you are logged out use 
export BW_SESSION=$(bw unlock --passwordenv BW_PASSWORD --raw)

# Create the peh-keycloak vault item
echo '{"type":1,"name":"peh-keycloak","login":{"username":"admin","password":"admin","uris":[{"uri":"http://localhost:8180"}]}}' \
  | bw encode | bw create item --session "$BW_SESSION"

# Sync to make the item available
bw sync --session "$BW_SESSION"
```

**Step 2.2: Configure Keycloak Realm**
```bash
# Option A: Load credentials from Bitwarden (recommended)
source load-secrets.sh

# Option B: Set environment variables manually
export KEYCLOAK_URL="http://localhost:8180"
export KEYCLOAK_ADMIN="admin"
export KEYCLOAK_PASSWORD="admin"

# Run configuration script
python keycloak-realm-config.py

# Verify configuration
python keycloak-realm-config.py --verify
```

**Expected Output:**
```
INFO - Authenticating with Keycloak...
INFO - Successfully authenticated
INFO - Creating realm: platform-engineering
INFO - Creating OAuth client: kubernetes-cli
INFO - Creating groups: platform-admins, platform-users
INFO - Configuration complete!
```

**Keycloak Setup Details:**
- Creates dedicated "platform-engineering" realm
- OAuth client "kubernetes-cli" configured for Kubernetes API
- Groups: "platform-admins" (cluster-admin), "platform-users" (namespace-scoped)
- Token lifetime: 15 minutes (configurable)
- Realm policies enable group inheritance to Kubernetes RBAC

**Next Steps:** Configure API server with OIDC parameters. Move to Phase 3 for RBAC.

### Phase 3: RBAC Configuration & Role Binding

**Step 3.1: Apply Platform Admin RBAC**
```bash
# Create platform-engineering namespace
kubectl create namespace platform-engineering

# Apply platform admin roles
kubectl apply -f rbac-platform-admin.yaml

# Verify roles created
kubectl get clusterrole platform-admin -o yaml | head -20
kubectl get clusterrolebinding platform-admin-binding -o yaml
```

**Expected Output:**
```
clusterrole.rbac.authorization.k8s.io/platform-admin created
clusterrolebinding.rbac.authorization.k8s.io/platform-admin-binding created
clusterrole.rbac.authorization.k8s.io/platform-audit-viewer created
...
```

**Step 3.2: Apply Developer RBAC**
```bash
# Apply developer roles to dev namespace
kubectl apply -f rbac-developer-role.yaml

# Verify developer role (namespace-scoped)
kubectl get role -n dev developer-role -o yaml

# Verify service account
kubectl get serviceaccount -n dev developer-user
```

**Expected Output:**
```
namespace/dev created
role.rbac.authorization.k8s.io/developer-role created
rolebinding.rbac.authorization.k8s.io/developer-binding created
...
```

**Step 3.3: Apply CI/CD Service Account**
```bash
# Create the staging namespace the CI/CD files target
kubectl create namespace staging

# Apply the service account, then grant it a minimal Role via a RoleBinding
kubectl apply -f service-account.yaml
kubectl apply -f role-minimal-deployer.yaml
kubectl apply -f rolebinding.yaml

# Verify service account
kubectl get serviceaccount -n staging ci-cd-deployer

# Test permissions
kubectl auth can-i update deployments \
  --as=system:serviceaccount:staging:ci-cd-deployer \
  -n staging
# Expected: yes

kubectl auth can-i create deployments \
  --as=system:serviceaccount:staging:ci-cd-deployer \
  -n staging
# Expected: no (can update, not create)

kubectl auth can-i get pods \
  --as=system:serviceaccount:staging:ci-cd-deployer \
  -n production
# Expected: no (cannot access other namespaces)
```

**Expected Output:**
```
namespace/staging created
serviceaccount/ci-cd-deployer created
role.rbac.authorization.k8s.io/minimal-deployer created
rolebinding.rbac.authorization.k8s.io/ci-cd-deployer-binding created
yes
no
no
```

**Next Steps:** Verify RBAC with test suite, then move to Phase 4 for TLS.

### Phase 4: TLS Certificate Management

**Step 4.1: Verify cert-manager Installation**
```bash
# Check cert-manager namespace
kubectl get deployment -n cert-manager

# Verify cert-manager CRDs
kubectl get crd | grep cert-manager
```

**Step 4.2: Apply Certificate Issuers**
```bash
# Apply cert-manager configuration
kubectl apply -f cert-manager-config.yaml

# Verify cluster issuers
kubectl get clusterissuer
```

**Expected Output:**
```
NAME                     READY   AGE
internal-ca-issuer       True    1m
letsencrypt-production   True    1m
letsencrypt-staging      True    1m
selfsigned-ca            True    1m
selfsigned-issuer        True    1m
```

`internal-ca-issuer` may show `False` for a few seconds until the `internal-ca` certificate (in the `cert-manager` namespace) issues its CA secret. If your cluster has other issuers from earlier work (for example a leftover `letsencrypt-prod`), they appear in this list too.

**Step 4.3: Create Demo App Namespace & Certificates**
```bash
# Apply demo app with certificate
kubectl apply -f demo-app-deployment.yaml

# Watch certificate issuance
kubectl get certificate -n istio-system -w

# Check certificate status
kubectl describe certificate demo-app-cert -n istio-system
```

**Expected Output:**
```
NAME              READY   SECRET        AGE
demo-app-cert     False   demo-app-tls  2m
```

> **Note:** On a local Kind cluster, certificates will show `Ready=False` because Let's Encrypt issuers require real DNS and the self-signed CA needs time to propagate. This is expected — the resources are created correctly and the pattern is what matters. Press `Ctrl+C` after a few seconds to stop the watch and move on.

> **Why is `demo-app-cert` in `istio-system` and not in `demo-app`?** The manifest places it there so the Istio Gateway can use it:
> 1. cert-manager writes the issued certificate into the Secret named by `secretName` (here `demo-app-tls`), and always creates that Secret in the Certificate's own namespace.
> 2. TLS terminates at the Istio ingress gateway, not in the app. The Gateway's `credentialName: demo-app-tls` tells the gateway to load its server certificate from that Secret.
> 3. The ingress gateway pod runs in `istio-system`, and by default it only reads Secrets from its own namespace. The Secret (and so the Certificate) therefore has to be there. The `Gateway` resource lives in `istio-system` for the same reason.
>
> If the Certificate were in `demo-app`, the Secret would be created there and the gateway would not see it, so HTTPS on the Gateway would have no usable certificate. The app pods never need the Secret, because TLS ends at the gateway.

**Next Steps:** Proceed to Phase 5 for policy enforcement.

### Phase 5: Policy-as-Code with OPA/Gatekeeper

**Step 5.1: Verify OPA Gatekeeper**

Gatekeeper is already installed: Chapter 2 deploys it with Flux (a `HelmRelease` in `gatekeeper-system`), and the standalone setup under Prerequisites installs it too. Do not apply the upstream `gatekeeper.yaml` again here; on a Flux/Helm-managed install it overwrites the Helm-owned Deployments.
```bash
# Wait for gatekeeper webhook deployment
kubectl wait --for=condition=Ready pod \
  -l gatekeeper.sh/system=yes \
  -n gatekeeper-system \
  --timeout=300s

# Verify installation
kubectl get deployment -n gatekeeper-system
```

**Step 5.2: Apply Resource Limits Policy**
```bash
# Apply ConstraintTemplate for resource limits
kubectl apply -f template-resource-limits.yaml

# Wait for Gatekeeper to generate the CRD from the template
sleep 10

# Apply the Constraint that activates the policy
kubectl apply -f constraint-resource-limits.yaml

# Verify constraint
kubectl get constraints
```

**Expected Output:**
```
NAME                                                                ENFORCEMENT-ACTION   TOTAL-VIOLATIONS
k8sallowedregistries.constraints.gatekeeper.sh/allowed-registries   deny                 3

NAME                                                         ENFORCEMENT-ACTION   TOTAL-VIOLATIONS
k8srequiredlimits.constraints.gatekeeper.sh/require-limits   deny                 2

NAME                                                               ENFORCEMENT-ACTION   TOTAL-VIOLATIONS
resourcelimits.constraints.gatekeeper.sh/require-resource-limits   deny     
```

**Step 5.3: Apply Namespace Labels Policy**
```bash
# Apply ConstraintTemplate for required labels
kubectl apply -f template-required-labels.yaml

# Wait for CRD generation
sleep 10

# Apply the Constraint
kubectl apply -f constraint-namespace-labels.yaml

# Verify both constraints
kubectl get constraints
```

**Step 5.4: Test Policy Violations**
```bash
# This should FAIL - no resource limits
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: bad-pod
  namespace: demo-app
spec:
  containers:
  - name: nginx
    image: docker.io/library/nginx:latest
EOF

# Expected error:
# Error from server ([denied by require-resource-limits]
# Container 'nginx' must have CPU limits set
# Container 'nginx' must have memory limits set)

# This should SUCCEED - has resource limits
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: good-pod
  namespace: demo-app
spec:
  containers:
  - name: nginx
    image: docker.io/library/nginx:1.24-alpine
    resources:
      limits:
        cpu: 500m
        memory: 512Mi
EOF

# Expected: pod/good-pod created
```

**Next Steps:** Move to Phase 6 for demo application testing.

### Phase 6: Demo Application Deployment & Testing

**Step 6.1: Verify Demo App Deployment**
```bash
# Check deployment status
kubectl get deployment -n demo-app
kubectl get pods -n demo-app

# Check Istio routing (the Gateway lives in istio-system, the VirtualService in demo-app)
kubectl get gateway -n istio-system
kubectl get virtualservice -n demo-app

# Verify certificate issued
kubectl get certificate -n istio-system
```

**Expected Output:**
```
NAME       READY   UP-TO-DATE   AVAILABLE   AGE
demo-app   3/3     3            3           2m

NAME                         READY   STATUS    RESTARTS   AGE
demo-app-xxxxx-xxxxx         2/2     Running   0          2m
demo-app-xxxxx-xxxxx         2/2     Running   0          2m
demo-app-xxxxx-xxxxx         2/2     Running   0          2m

NAME               AGE
demo-app-gateway   2m

NAME       GATEWAYS                            HOSTS                                                 AGE
demo-app   ["istio-system/demo-app-gateway"]   ["demo-app.example.com","www.demo-app.example.com"]   2m

NAME              READY   SECRET         AGE
demo-app-cert     False   demo-app-tls   3m
```

Each pod shows `2/2` because Istio injects an `istio-proxy` sidecar next to the app container. `demo-app-cert` stays `False` on a local Kind cluster (see the note in Step 4.3).

The demo app is [podinfo](https://github.com/stefanprodan/podinfo), a small Go service that behaves like a real application: it serves HTTP and Prometheus metrics on port `9898`, and has `/healthz` and `/readyz` endpoints that the liveness, readiness and startup probes use. The Service maps port `80` to `9898`. To try it:
```bash
kubectl port-forward -n demo-app svc/demo-app 8081:80
curl -s localhost:8081/readyz     # readiness probe endpoint
curl -s localhost:8081/           # JSON with the pod hostname and version
curl -s localhost:8081/metrics    # Prometheus metrics
```

The manifest also creates an `AuthorizationPolicy` (`demo-app-allow-gateway` in `istio-system`). Chapter 2's `allow-external` policy only admits `/health`, `/ready` and `/api/*` through the ingress gateway, so without it every request to `demo-app.example.com` would get `403`. The extra policy admits only the demo-app hosts and leaves the Chapter 2 rules in place for everything else.

**Step 6.2: Test Pod Disruption Budget**
```bash
# Verify PDB allows graceful disruptions
kubectl get pdb -n demo-app

# Expected: minAvailable: 2, meaning at least 2 pods must be running

# Simulate pod eviction (controlled test)
kubectl delete pod -n demo-app <pod-name>

# Observe: deployment controller will recreate pod while maintaining minAvailable
kubectl get pods -n demo-app -w
```

**Step 6.3: Test Network Policies**
```bash
# Verify network policy
kubectl get networkpolicy -n demo-app

# Description shows:
# - Ingress: allowed from the istio-system namespace on port 9898 (podinfo)
# - Egress: allowed to DNS (port 53), HTTPS (port 443) and istiod (port 15012,
#   so the Istio sidecar can fetch its config and workload certificate)
kubectl describe networkpolicy demo-app-network-policy -n demo-app
```

**Expected Output:**
```
NAME                        POD-SELECTOR   AGE
demo-app-network-policy     app=demo-app   5m

Policy Types: Ingress, Egress
Ingress:
  From:
    Namespace Selector: kubernetes.io/metadata.name=istio-system
  Ports:
    TCP port 9898
Egress:
  To:
    Namespace Selector: (all)
  Ports:
    UDP port 53 (DNS)
    TCP port 443 (HTTPS)
  To:
    Namespace Selector: kubernetes.io/metadata.name=istio-system
  Ports:
    TCP port 15012 (istiod)
```

**Next Steps:** Proceed to Phase 7 for security validation.

### Phase 7: RBAC Testing & Validation

**Step 7.1: Run RBAC Test Suite**
```bash
# Run comprehensive RBAC validation tests
python test-rbac-permissions.py -v

# Expected output shows all tests passing
```

**Expected Output:**
```
============================================================
Chapter 3: RBAC Permission Tests
============================================================
test_cert_config_exists (TestCertManager) ... ok
test_cert_config_has_issuer (TestCertManager) ... ok
test_demo_app_exists (TestDemoApp) ... ok
test_demo_app_has_resource_limits (TestDemoApp) ... ok
test_demo_app_runs_as_non_root (TestDemoApp) ... ok
test_developer_role_exists (TestRBACConfigs) ... ok
test_developer_role_restricts_system_namespaces (TestRBACConfigs) ... ok
test_platform_admin_has_namespace_management (TestRBACConfigs) ... ok
test_platform_admin_role_exists (TestRBACConfigs) ... ok

Ran 9 tests in 0.02s
OK
```

**Step 7.2: Manual RBAC Verification**

The roles are bound to **groups** (`platform-admins`, `platform-users`), not to individual users. In a real cluster Keycloak supplies the group through `--oidc-groups-claim`; when impersonating with `kubectl`, pass both `--as` and `--as-group`. With `--as` alone the user has no groups, so no binding applies and every check returns `no`.

```bash
# Test platform-admin permissions
kubectl auth can-i get pods \
  --as=admin \
  --as-group=platform-admins \
  -n kube-system
# Expected: yes (admin can see system pods)

# Test developer permissions
kubectl auth can-i get pods \
  --as=developer \
  --as-group=platform-users \
  -n dev
# Expected: yes (developer can see own namespace)

kubectl auth can-i get pods \
  --as=developer \
  --as-group=platform-users \
  -n kube-system
# Expected: no (developer cannot see system namespace)

kubectl auth can-i create namespaces \
  --as=developer \
  --as-group=platform-users
# Expected: no (developer cannot create namespaces)
```

### Phase 8: Security Verification & Audit Compliance

**Step 8.1: Re-run Security Audit**
```bash
# Verify all security configurations
bash security-audit.sh

# Expected: the pod, service-account and network-policy checks are [OK]
```

**Expected Output** (counts and names vary by cluster):
```
=== Kubernetes Security Audit ===
[INFO] Auditing all namespaces

=== Cluster Access Check ===
[OK] Cluster is accessible - Version: v1.XX.X
=== RBAC Permissions Audit ===
[WARNING] Found 3 cluster-admin role bindings
[INFO]   - cluster-admin
[INFO]   - cluster-reconciler-flux-system
[INFO]   - kubeadm:cluster-admins
=== Service Account Audit ===
[OK] Found X service accounts with token secrets
=== Pod Security Audit ===
[OK] No privileged pods found
[OK] No pods running as root found
[OK] All pods have resource limits
=== Network Policy Audit ===
[OK] Found X network policies
=== Secrets Audit ===
[INFO] Found X secrets across namespaces
[WARNING] Ensure secrets are encrypted at rest and rotation policy is in place
=== RBAC Binding Audit ===
[OK] Found X role bindings

=== Audit Summary ===
[WARNING] Found 2 potential security issues
```

> **Note:** A clean cluster still reports these two warnings, so "Found 0 issues" is not the goal. The cluster-admin bindings above are normal: `cluster-admin` (`system:masters`) and `kubeadm:cluster-admins` come with the cluster, and `cluster-reconciler-flux-system` is Flux from Chapter 2. Review the list and investigate any binding you do not recognise. The secrets warning is a standing reminder to enable encryption at rest and rotation, and it always appears.

**Step 8.2: Verify Audit Logging**
```bash
# Check Kubernetes audit logs (if configured)
# Logs should show all API server access with identity information

# Example API audit log entry should include:
# - user: kubernetes-admin (or Keycloak user)
# - requestObject: the resource being accessed
# - verb: get/create/update/delete
# - namespace: the namespace (or cluster-wide)

# Verify no service account tokens in logs
grep -r "system:serviceaccount" /var/log/kubernetes/audit.log \
  | grep -v "system:serviceaccount:kube-" \
  | head -5
```

## Companion Website

The companion website at https://peh-packt.platformetrics.com/ provides:

- **Chapter 3: Securing Platform Access** with interactive explanations
- Code snippets with syntax highlighting and "Explain Code" walkthroughs
- Video demonstrations of concepts
- Hands-on exercises for implementation
- Exercise solutions for validation

### Website Alignment & Discrepancies

**Note:** The companion website displays Chapter 2 and Chapter 3 content alongside the manuscript chapters. The website provides:

1. **Tools & Technologies Coverage**: The website lists the tools used in Chapter 3 (Keycloak, kubectl, Kubernetes, cert-manager, OPA/Rego, etc.) which align with the code in this directory.

2. **Code Example Correlation**:
   - Website references specific code files like `security-audit.sh`, RBAC manifests, and deployment examples
   - All code files in this directory are referenced and explained on the website
   - Website provides additional context on why each tool is necessary

3. **Potential Discrepancies**:
   - The website may show code in "Explain Code" sections that differs slightly in formatting or comments from the files in this directory (this is expected)
   - Some website exercises may reference code not in this directory (those would be in the main book repository)
   - The website's "Show Code" buttons display the same code as these files

4. **Exercise Alignment**:
   - Chapter 3 Exercise at the end of the manuscript requires: Keycloak setup (covered by `keycloak-realm-config.py`), RBAC configuration (covered by RBAC YAML files), OPA policies (covered by template and constraint files), network security (covered by `demo-app-deployment.yaml`), certificate/mTLS setup (covered by `cert-manager-config.yaml`), testing (covered by `test-rbac-permissions.py`), and incident response (described in security audit script).

### How to Use with the Companion Website

Users should follow along with the chapter while executing code from this directory:

1. Read the chapter section in the book or on the website
2. Review the corresponding code file(s) in this directory
3. Follow the "Step-by-Step Instructions" above to implement each concept
4. Use the companion website's "Explain Code" sections for deeper understanding
5. Complete exercises from the manuscript using the code provided here
6. Validate your implementation using the test suite and audit scripts

## Best Practices Implemented

### Security

1. **Principle of Least Privilege**: Every role (admin, developer, CI/CD) has only necessary permissions
2. **Zero-Trust Architecture**: Network policies, mTLS, and RBAC enforce explicit allow-list (no implicit trust)
3. **Automated Certificate Management**: TLS certificates auto-renewed 30 days before expiration
4. **Identity Centralization**: OAuth/OIDC with Keycloak eliminates separate credential management
5. **Policy-as-Code**: OPA ensures compliance regardless of who creates resources
6. **Comprehensive Auditing**: All API server actions logged with identity for compliance
7. **Short-Lived Tokens**: Keycloak tokens expire in 15 minutes; service account tokens auto-rotated

### Operational Excellence

1. **Namespace Isolation**: Developer workloads confined to their namespace
2. **Resource Governance**: CPU/memory limits prevent noisy neighbor issues
3. **High Availability**: PodDisruptionBudget and HPA ensure resilience
4. **Observability**: Security events captured in Keycloak and Kubernetes audit logs
5. **Scalability**: Keycloak HA with StatefulSet, Kubernetes cluster auto-scales with HPA

### Developer Experience

1. **Self-Service**: Developers deploy without security friction (automatic TLS, OAuth login)
2. **Clear Boundaries**: Namespace-scoped RBAC prevents accidental cross-team damage
3. **Gradual Privilege Escalation**: Platform provides escape hatches with logging, not broad admin access
4. **Documentation**: Security audit reports help developers understand what's forbidden and why

## Cleanup (Reset for Re-Recording)

To reset all Chapter 3 resources and start from scratch:
```bash
# Stop and remove Keycloak container
docker rm -f $(docker ps -aq --filter ancestor=quay.io/keycloak/keycloak) 2>/dev/null

# Delete namespaces (removes all namespace-scoped resources within them)
kubectl delete namespace demo-app dev platform-engineering platform --ignore-not-found

# Delete cluster-scoped RBAC
kubectl delete clusterrole platform-admin platform-admin-restricted platform-audit-viewer platform-operator --ignore-not-found
kubectl delete clusterrolebinding platform-admin-binding platform-admin-sa-binding platform-audit-viewer-binding platform-operator-binding --ignore-not-found

# Delete the internal CA certificate and its secret (they live in cert-manager, not platform-engineering)
kubectl delete certificate internal-ca -n cert-manager --ignore-not-found
kubectl delete secret internal-ca-secret -n cert-manager --ignore-not-found

# Delete cert-manager ClusterIssuers (including internal CA issuer)
kubectl delete clusterissuer letsencrypt-staging letsencrypt-production selfsigned-issuer selfsigned-ca internal-ca-issuer --ignore-not-found

# Delete Gatekeeper constraints and templates
kubectl delete k8srequireresourcelimits require-resource-limits --ignore-not-found
kubectl delete k8srequiredlabels require-namespace-labels --ignore-not-found
kubectl delete constrainttemplate k8srequireresourcelimits k8srequiredlabels --ignore-not-found

# Delete any leftover test pods
kubectl delete pod test-compliant test-noncompliant good-pod bad-pod -n demo-app --ignore-not-found 2>/dev/null
```

## Troubleshooting

### Common Issues

**Certificate Not Issuing**
```bash
# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager

# Describe certificate for status
kubectl describe certificate demo-app-cert -n istio-system

# Check ClusterIssuer status
kubectl describe clusterissuer letsencrypt-production
```

**RBAC Permissions Denied**
```bash
# Test permissions as a service account (full system:serviceaccount:<ns>:<name> form)
kubectl auth can-i get pods --as=system:serviceaccount:dev:developer-user -n dev

# Test permissions as a user in a group (roles are bound to groups, so pass --as-group)
kubectl auth can-i get pods --as=developer --as-group=platform-users -n dev

# List all role bindings in namespace
kubectl get rolebindings -n dev -o yaml

# Check service account has binding
kubectl get rolebinding -n dev -o jsonpath='{.items[*].subjects[?(@.kind=="ServiceAccount")]}'
```

**Keycloak Connection Failed**
```bash
# Verify Keycloak is accessible
curl -k https://keycloak.example.com/auth/admin/

# Check OAuth client configuration
python keycloak-realm-config.py --verify

# Verify Kubernetes API server has OIDC flags
kubectl get configmap -n kube-system kube-apiserver -o yaml | grep oidc
```

**Policy Violation Rejection**
```bash
# Get OPA Gatekeeper pod to check logs
# Gatekeeper pods may be in gatekeeper-system or flux-system depending on install method
kubectl logs -n gatekeeper-system -l gatekeeper.sh/system=yes 2>/dev/null || \
  kubectl logs -n flux-system -l control-plane=controller-manager

# Describe constraint to see current status
kubectl describe K8sRequireResourceLimits require-resource-limits

# Test policy manually
kubectl apply -f - --dry-run=client -f test-pod.yaml
```

**Pod Network Policy Blocking Traffic**
```bash
# Verify network policy rules
kubectl describe networkpolicy demo-app-network-policy -n demo-app

# Check pod IP addresses for debugging
kubectl get pods -n demo-app -o wide

# Test connectivity between pods (if ingress-nginx is running)
kubectl run test-pod --image=curl:latest -it -- sh
# Then from inside: curl http://demo-app.demo-app.svc.cluster.local
```

## Security Considerations for Production

- Change all default passwords (Keycloak, API keys in demo app)
- Use real Let's Encrypt certificates (not staging) for production
- Implement secrets encryption at rest using KMS
- Enable Kubernetes audit logging with external retention (Splunk, CloudWatch, etc.)
- Implement SIEM integration for security monitoring
- Use network policies on all namespaces (not just demo-app)
- Enable Pod Security Policies or Pod Security Standards
- Implement image scanning for container vulnerabilities
- Use network segmentation between environments
- Rotate service account tokens regularly
- Implement Falco or similar runtime security monitoring
- Enable cluster autoscaling with node security hardening

## Additional Resources

- [Kubernetes RBAC Documentation](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [Keycloak Documentation](https://www.keycloak.org/documentation.html)
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)
- [OPA/Gatekeeper Documentation](https://open-policy-agent.github.io/gatekeeper/)
- [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

## License

Example code for educational purposes in "The Platform Engineer's Handbook" published by Packt Publishing.

---

**Author:** Ajay Chankramath (ajay@platformetrics.com)
**Book:** The Platform Engineer's Handbook (Packt Publishing)
**Last Updated**: October 2026
