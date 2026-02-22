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
| `service-account.yaml` | "Securing CI/CD with service accounts" and "Principle of least privilege in practice" | Kubernetes ServiceAccount for CI/CD pipelines with minimal required permissions. Features `automountServiceAccountToken: false` for security, RoleBinding to `platform-deployer` role (deployment-only permissions), and guidance on using short-lived TokenRequest API instead of long-lived secrets. Demonstrates scoped service account permissions for high-risk deployment pipelines. |

### TLS Certificate Management

| File | Section | Purpose |
|------|---------|---------|
| `cert-manager-config.yaml` | "Automated TLS certificate management" | cert-manager ClusterIssuer and Certificate configurations for automatic TLS certificate generation and renewal. Includes Let's Encrypt staging/production issuers, internal CA setup for mTLS, and certificate resources for platform API, demo app, and Keycloak. Eliminates manual certificate management friction that causes teams to deploy without encryption. |

### Demo Application & Network Security

| File | Section | Purpose |
|------|---------|---------|
| `demo-app-deployment.yaml` | "Building the demo application experience" and "Zero-Trust networking and network policies" | Complete Kubernetes Deployment demonstrating secure application practices that pilot teams will face. Includes: ServiceAccount with minimal privileges, ConfigMap/Secret management, security context (non-root user, read-only filesystem, dropped capabilities), resource requests/limits, health checks, affinity rules for HA, and NetworkPolicy restricting ingress/egress traffic. Ingress with automatic TLS (cert-manager annotations), PodDisruptionBudget for availability, and HorizontalPodAutoscaler for auto-scaling. Simulates complete developer experience from code to running application. |

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

### System Requirements
- Kubernetes cluster 1.21+ or local Kind cluster for testing
- kubectl configured and authenticated to cluster
- Bash 4.0+ for shell scripts
- Python 3.7+ for Python scripts

### Kubernetes Components
- **cert-manager**: `helm repo add jetstack https://charts.jetstack.io && helm install cert-manager jetstack/cert-manager`
- **Keycloak**: Deployed as StatefulSet in platform-services namespace with persistent storage (PostgreSQL backend recommended)
- **Ingress Controller**: nginx-ingress or compatible controller for Ingress resources
- **OPA Gatekeeper**: `kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.14.0/deploy/gatekeeper.yaml`

### Python Dependencies
```bash
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

**Step 2.1: Configure Keycloak Realm**
```bash
# Option A: Load credentials from Bitwarden (recommended)
source load-secrets.sh

# Option B: Set environment variables manually
export KEYCLOAK_URL="https://keycloak.example.com"
export KEYCLOAK_ADMIN="admin"
export KEYCLOAK_PASSWORD="your-secure-password"

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
# Create platform namespace for CI/CD
kubectl create namespace platform

# Apply CI/CD service account with scoped permissions
kubectl apply -f service-account.yaml

# Verify service account
kubectl get serviceaccount -n platform cicd-deployer

# Test permissions
kubectl auth can-i update deployments \
  --as=system:serviceaccount:platform:cicd-deployer \
  -n platform
# Expected: yes

kubectl auth can-i get pods \
  --as=system:serviceaccount:platform:cicd-deployer \
  -n production
# Expected: no (cannot access other namespaces)
```

**Expected Output:**
```
serviceaccount/cicd-deployer created
rolebinding.rbac.authorization.k8s.io/cicd-deployer-binding created
yes
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
NAME                      READY   AGE
letsencrypt-staging       True    1m
letsencrypt-production    True    1m
selfsigned-issuer         True    1m
internal-ca-issuer        True    1m
```

**Step 4.3: Create Demo App Namespace & Certificates**
```bash
# Apply demo app with certificate
kubectl apply -f demo-app-deployment.yaml

# Watch certificate issuance
kubectl get certificate -n demo-app -w

# Check certificate status
kubectl describe certificate demo-app-cert -n demo-app
```

**Expected Output:**
```
NAME              READY   SECRET        AGE
demo-app-cert     True    demo-app-tls  2m

Status:
  Conditions:
    Type: Ready
    Status: True
    Reason: Issued
    Message: Certificate issued successfully
```

**Next Steps:** Proceed to Phase 5 for policy enforcement.

### Phase 5: Policy-as-Code with OPA/Gatekeeper

**Step 5.1: Deploy OPA Gatekeeper**
```bash
# Install OPA Gatekeeper
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.14.0/deploy/gatekeeper.yaml

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

# Create Constraint to enforce the policy
kubectl apply -f - <<EOF
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequireResourceLimits
metadata:
  name: require-resource-limits
spec:
  enforcementAction: deny
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    excludedNamespaces:
      - kube-system
      - kube-public
      - gatekeeper-system
EOF

# Verify constraint
kubectl get constraints
```

**Expected Output:**
```
constrainttemplate.templates.gatekeeper.sh/k8srequireresourcelimits created
constraint.constraints.gatekeeper.sh/require-resource-limits created
```

**Step 5.3: Apply Namespace Labels Policy**
```bash
# Apply namespace labels constraint
kubectl apply -f constraint-namespace-labels.yaml

# Verify constraint
kubectl get K8sRequiredLabels
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
    image: nginx:latest
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
    image: nginx:1.24-alpine
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

# Check ingress
kubectl get ingress -n demo-app

# Verify certificate issued
kubectl get certificate -n demo-app
```

**Expected Output:**
```
NAME       READY   UP-TO-DATE   AVAILABLE   AGE
demo-app   3/3     3            3           2m

NAME                         READY   STATUS    RESTARTS   AGE
demo-app-xxxxx-xxxxx         1/1     Running   0          2m
demo-app-xxxxx-xxxxx         1/1     Running   0          2m
demo-app-xxxxx-xxxxx         1/1     Running   0          2m

NAME              CLASS   HOSTS                INGRESS      TLS
demo-app-ingress  nginx   demo-app.example.com ...          demo-app-tls

NAME              READY   SECRET         AGE
demo-app-cert     True    demo-app-tls   3m
```

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
# - Ingress: allowed from nginx-ingress namespace on ports 8080, 9090
# - Egress: allowed to DNS (port 53) and HTTPS (port 443) outbound
kubectl describe networkpolicy demo-app-network-policy -n demo-app
```

**Expected Output:**
```
NAME                        POD-SELECTOR   AGE
demo-app-network-policy     app=demo-app   5m

Policy Types: Ingress, Egress
Ingress:
  From:
    Namespace Selector: name=ingress-nginx
  Ports:
    TCP port 8080
    TCP port 9090
Egress:
  To:
    Namespace Selector: (all)
  Ports:
    UDP port 53 (DNS)
    TCP port 443 (HTTPS)
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
```bash
# Test platform-admin permissions
kubectl auth can-i get pods \
  --as=admin \
  -n kube-system
# Expected: yes (admin can see system pods)

# Test developer permissions
kubectl auth can-i get pods \
  --as=developer \
  -n dev
# Expected: yes (developer can see own namespace)

kubectl auth can-i get pods \
  --as=developer \
  -n kube-system
# Expected: no (developer cannot see system namespace)

kubectl auth can-i create namespaces \
  --as=developer
# Expected: no (developer cannot create namespaces)
```

### Phase 8: Security Verification & Audit Compliance

**Step 8.1: Re-run Security Audit**
```bash
# Verify all security configurations
bash security-audit.sh

# Expected: Issues should be resolved, audit shows compliance
```

**Expected Output:**
```
=== Kubernetes Security Audit ===
[OK] Cluster is accessible
[OK] No excessive cluster-admin bindings found
[OK] Found X service accounts with token secrets
[OK] No privileged pods found
[OK] No pods running as root found
[OK] All pods have resource limits
[OK] Found X network policies
[WARNING] Ensure secrets are encrypted at rest

=== Audit Summary ===
Found 0 critical security issues
```

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

## Troubleshooting

### Common Issues

**Certificate Not Issuing**
```bash
# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager

# Describe certificate for status
kubectl describe certificate demo-app-cert -n demo-app

# Check ClusterIssuer status
kubectl describe clusterissuer letsencrypt-production
```

**RBAC Permissions Denied**
```bash
# Test permissions as specific user/service account
kubectl auth can-i get pods --as=developer-user -n dev

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
kubectl logs -n gatekeeper-system -l gatekeeper.sh/system=yes

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
