# Chapter 7: Self-Service Platform Onboarding

## Overview

This directory contains production-ready code examples for implementing a self-service platform onboarding system as described in "The Platform Engineer's Handbook" Chapter 7. The implementation demonstrates how to transform platform onboarding from a multi-day, ticket-driven obstacle into a fully automated experience completed in minutes.

By implementing these patterns, teams can:
- Provision complete Kubernetes namespaces with automatic RBAC and resource quotas
- Enable team leads to manage members and permissions independently
- Bootstrap new projects with Git repositories, CI/CD pipelines, and deployment manifests
- Maintain comprehensive audit trails for compliance and troubleshooting
- Operate all onboarding operations idempotently, enabling safe re-runs

## Chapter 7 Key Concepts

**API-First Architecture**: Decouples onboarding logic from any single interface (portal, CLI, chatbots, pipelines).

**Self-Service Team Management**: Empowers team leads to manage membership and delegate permissions without platform intervention.

**Project Bootstrapping**: Provisions a complete development environment (repo, namespaces, CI/CD, catalog entry) with a single API call.

**Tiered Resource Quotas**: Implements starter, standard, and enterprise tiers with appropriate CPU/memory/storage limits.

**Idempotent Operations**: All provisioning operations are safe to re-run without side effects.

## Code-to-Chapter Mapping

### Core API Components

| File | Purpose | Chapter Section | Key Concepts |
|------|---------|-----------------|--------------|
| **openapi-spec.yaml** | OpenAPI 3.0 specification | Creating an onboarding API | RESTful design, versioning, error handling |
| **onboarding-api.py** | Flask REST API implementation | Creating an onboarding API | Team/member management, namespace provisioning, RBAC setup |
| **services/teamService.js** | Node.js team service reference | Controller-Service-Repository pattern | Demonstrates service layer for team creation |

### Infrastructure & Templates

| File | Purpose | Chapter Section | Key Concepts |
|------|---------|-----------------|--------------|
| **namespace-bootstrap.yaml** | Kubernetes manifests template | RBAC, namespace, and quota automation | Complete namespace setup with quotas, network policies, RBAC |
| **templates/namespace-template.yaml** | Namespace creation template | Naming conventions & labels | Template variables, label metadata for team identification |
| **templates/team-rbac.yaml** | RBAC Role/RoleBinding templates | RBAC hierarchy (Figure 7-2) | team-admin, team-developer, team-viewer roles |
| **templates/resource-quota.yaml** | Tiered quota templates | Tiered quota system | Starter, standard, enterprise quota definitions |

### Automation & Delegation

| File | Purpose | Chapter Section | Key Concepts |
|------|---------|-----------------|--------------|
| **permission-delegation.py** | Permission delegation module | Enable self-service team management | Hierarchical permissions, role-based access, delegation validation |
| **project-bootstrapper.py** | Project initialization automation | Bootstrapping new projects | Template libraries by archetype, language variants, atomic provisioning |
| **audit-logger.py** | Audit logging module | Observability & compliance | Structured event logging, query interface, statistics |

### Testing & Validation

| File | Purpose | Chapter Section | Key Concepts |
|------|---------|-----------------|--------------|
| **test-onboarding.py** | Test suite | Quality assurance | Validates API, scripts, and manifest structure |

### Secrets Management (Bitwarden Integration)

| File | Purpose | Chapter Section | Key Concepts |
|------|---------|-----------------|--------------|
| **load-secrets.sh** | Load GitHub token from Bitwarden | Secrets Management (cross-chapter) | Retrieves `GITHUB_TOKEN` and `GITHUB_ORG` from vault. Sources `bw-helper.sh` from Ch1. |

## Orphan Files

**None identified.** All code files map to specific chapter concepts and are actively used in the implementation.

## Prerequisites

### System Requirements
- Python 3.8+ (for API and automation scripts)
- Node.js 14+ and npm (for teamService.js reference)
- Kubernetes cluster (v1.20+)
- kubectl configured and accessible to the API container
- Docker (for containerized deployment)

### Python Dependencies
```bash
pip install flask pyyaml kubernetes
```

### Node.js Dependencies
```bash
npm install @kubernetes/client-node @octokit/rest
npm install --save-dev jest supertest
```

### Kubernetes Requirements
- API server accessible from the API container
- Service account with permissions to create/manage namespaces, RBAC, and resource quotas
- Persistent volume for audit logs (optional but recommended for production)

### Environment Variables
```bash
export ONBOARDING_API_HOST=0.0.0.0
export ONBOARDING_API_PORT=5000
export ONBOARDING_API_DEBUG=False              # Set to True for development
export ONBOARDING_AUDIT_LOG_PATH=./audit.log
export ONBOARDING_DB_PATH=./onboarding.db
export PERMISSIONS_DB_PATH=./permissions.json
export KUBERNETES_NAMESPACE=platform-onboarding
export KUBERNETES_CLUSTER=default
export GITHUB_TOKEN=<your-github-token>       # For Git operations (or use: source load-secrets.sh)
```

## Step-by-Step Instructions

### Phase 1: API Setup and Team Provisioning

#### Step 1: Review the OpenAPI Specification
The API specification defines all endpoints and their contracts. Review it to understand the available operations:

```bash
cat openapi-spec.yaml
```

Expected output: YAML document defining `/teams` (POST, GET, DELETE) and `/teams/{teamId}/members` (POST, GET, DELETE) endpoints.

**Next step**: Proceed to Step 2.

#### Step 2: Start the Onboarding API
Launch the Flask-based REST API. This server will handle all team provisioning requests:

```bash
python onboarding-api.py
```

Expected output:
```
2024-01-15 10:30:00 - __main__ - INFO - Starting Onboarding API on 0.0.0.0:5000
 * Running on http://0.0.0.0:5000
```

The API is now ready to accept requests. Verify it's running by checking the health in another terminal:

```bash
curl http://localhost:5000/teams
```

Expected output: `{"teams": [], "total": 0, "offset": 0, "limit": 20}` (empty initially)

**Next step**: Proceed to Step 3.

#### Step 3: Create Your First Team
Create a team called "platform-team" with Alice as the lead. This operation triggers automatic namespace creation and RBAC setup:

```bash
curl -X POST http://localhost:5000/teams \
  -H "Content-Type: application/json" \
  -d '{
    "name": "platform-team",
    "display_name": "Platform Engineering Team",
    "lead": "alice@example.com",
    "description": "Core platform infrastructure",
    "resource_quota": {
      "cpu": "20",
      "memory": "100Gi",
      "pods": 200,
      "storage": "200Gi"
    }
  }'
```

Expected output:
```json
{
  "id": "platform-team",
  "name": "platform-team",
  "display_name": "Platform Engineering Team",
  "lead": "alice@example.com",
  "created_at": "2024-01-15T10:35:00Z",
  "namespace": {
    "name": "team-platform-team",
    "status": "active",
    "resource_quota": {...}
  },
  "status": "active",
  "member_count": 1
}
```

Verify the Kubernetes namespace was created:

```bash
kubectl get ns team-platform-team
kubectl get resourcequota -n team-platform-team
kubectl get rolebindings -n team-platform-team
```

Expected output: Namespace exists with ResourceQuota and RoleBindings for team-lead, team-developer, and team-viewer groups.

**Next step**: Proceed to Step 4.

#### Step 4: Add Team Members
Add developers to the team. Team leads can later manage additional members:

```bash
curl -X POST http://localhost:5000/teams/platform-team/members \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@example.com",
    "name": "Bob Smith",
    "role": "developer"
  }'

curl -X POST http://localhost:5000/teams/platform-team/members \
  -H "Content-Type: application/json" \
  -d '{
    "email": "carol@example.com",
    "name": "Carol Jones",
    "role": "viewer"
  }'
```

Expected output: For each member, a 201 response with member details including joined_at timestamp.

List team members to verify:

```bash
curl http://localhost:5000/teams/platform-team/members
```

Expected output:
```json
{
  "members": [
    {"email": "alice@example.com", "role": "lead", ...},
    {"email": "bob@example.com", "role": "developer", ...},
    {"email": "carol@example.com", "role": "viewer", ...}
  ],
  "total": 3
}
```

**Next step**: Proceed to Step 5.

### Phase 2: Permission Delegation & Self-Service

#### Step 5: Set Up Permission Delegation
Enable team leads to grant permissions to members without platform intervention:

```bash
python permission-delegation.py grant-role platform-team bob@example.com developer
```

Expected output: `Granted developer role to bob@example.com`

This grants all permissions associated with the developer role:
- create-projects
- manage-projects
- manage-ci-cd
- manage-deployments
- manage-secrets
- view-projects
- view-audit-logs (limited)

View available roles and permissions:

```bash
python permission-delegation.py list-roles
```

Expected output: Lists all permissions for lead, developer, and viewer roles.

Check a member's specific permissions:

```bash
python permission-delegation.py list-member platform-team bob@example.com
```

Expected output:
```
Permissions for bob@example.com in platform-team:
  - create-projects
  - manage-ci-cd
  - manage-deployments
  - manage-projects
  - manage-secrets
  - view-audit-logs
  - view-projects
```

**Next step**: Proceed to Step 6.

#### Step 6: Verify Permission Delegation
Check if a user has a specific permission:

```bash
python permission-delegation.py check platform-team bob@example.com create-projects
```

Expected output: `bob@example.com has create-projects: True`

Revoke a permission if needed:

```bash
python permission-delegation.py revoke platform-team bob@example.com manage-ci-cd alice@example.com
```

Expected output: `Revoked manage-ci-cd from bob@example.com`

**Next step**: Proceed to Step 7.

### Phase 3: Project Bootstrapping

#### Step 7: Bootstrap a New Project
Create a complete project with repository, CI/CD pipeline, Kubernetes manifests, and Backstage catalog entry:

```bash
python project-bootstrapper.py bootstrap platform-team my-api python "RESTful API service"
```

Expected output:
```
Project my-api bootstrapped successfully!
Repository: git@github.com:platform-team/my-api.git
Files created: 15
```

This creates:
- README.md with getting started instructions
- Dockerfile with multi-stage build
- .github/workflows/ci.yml for GitHub Actions CI/CD
- k8s/deployment.yaml, service.yaml, ingress.yaml, configmap.yaml
- catalog-info.yaml for Backstage registration
- Language-specific files (main.py, requirements.txt, etc.)

View available templates:

```bash
python project-bootstrapper.py templates
```

Expected output:
```
Available templates:
  python          - Python web service
  golang          - Go microservice
  nodejs          - Node.js application
  generic         - Generic project template
```

**Next step**: Proceed to Step 8.

#### Step 8: Review Bootstrapped Project Structure
Examine the files created for your project. The bootstrapper generates:

```
my-api/
├── k8s/                 # Kubernetes manifests
│   ├── deployment.yaml  # 2 replicas, health checks, resource limits
│   ├── service.yaml     # ClusterIP service on port 80->8080
│   ├── ingress.yaml     # TLS-enabled with cert-manager integration
│   └── configmap.yaml   # Application configuration
├── .github/workflows/   # CI/CD pipeline
│   └── ci.yml           # Build, test, and deploy on main branch
├── main.py              # Application entry point with health/ready/metrics endpoints
├── requirements.txt     # Python dependencies (Flask, Gunicorn, etc.)
├── Dockerfile           # Non-root user, health checks, multi-stage build
├── README.md            # Getting started guide
├── .gitignore           # Language-specific ignores
└── catalog-info.yaml    # Backstage component definition
```

Key features of bootstrapped projects:
- **Health checks**: /health and /ready endpoints for Kubernetes probes
- **Metrics**: Prometheus /metrics endpoint for monitoring
- **Security**: Non-root containers, read-only filesystems, no privilege escalation
- **CI/CD**: Automated build, test, and deploy on push to main branch
- **Documentation**: Comprehensive README with deployment instructions

**Next step**: Proceed to Step 9.

### Phase 4: Audit & Monitoring

#### Step 9: Review Audit Logs
All onboarding actions are logged for compliance and troubleshooting:

```bash
python audit-logger.py show
```

Expected output:
```
Showing N audit events (max 50):

[2024-01-15T10:35:00Z] 20240115103500-1
  Action: team_created
  Actor: system
  Resource: team/platform-team
  Status: success
  Details: {"display_name": "Platform Engineering Team", "lead": "alice@example.com"}

[2024-01-15T10:36:15Z] 20240115103615-2
  Action: member_added
  Actor: system
  Resource: team_member/platform-team/bob@example.com
  Status: success
  Details: {"role": "developer"}

[2024-01-15T10:37:30Z] 20240115103730-3
  Action: project_bootstrapped
  Actor: system
  Resource: project/platform-team/my-api
  Status: success
  Details: {"language": "python", "files_count": 15}
```

Get audit statistics:

```bash
python audit-logger.py stats
```

Expected output:
```
Audit Log Statistics:
Total Events: N

Actions: {
  "team_created": 1,
  "member_added": 2,
  "project_bootstrapped": 1,
  "permission_granted": N,
  ...
}

Actors: {
  "system": M,
  "alice@example.com": N,
  ...
}

Resource Types: {
  "team": 1,
  "team_member": 2,
  "project": 1,
  "permission": N,
  ...
}

Statuses: {
  "success": M,
  "failure": N
}
```

View failed operations for troubleshooting:

```bash
python audit-logger.py failures
```

Get history for a specific team:

```bash
python -c "from audit_logger import AuditLogger, print_audit_events; \
logger = AuditLogger(); \
events = logger.get_team_history('platform-team'); \
print_audit_events(events)"
```

**Next step**: Proceed to Step 10.

#### Step 10: Run Test Suite
Validate the implementation:

```bash
python test-onboarding.py
```

Expected output:
```
============================================================
Chapter 7: Onboarding API Tests
============================================================
test_api_script_valid (__main__.TestOnboardingAPI) ... ok
test_bootstrap_has_resource_quota (__main__.TestOnboardingAPI) ... ok
test_bootstrap_yaml_exists (__main__.TestOnboardingAPI) ... ok
test_openapi_has_team_endpoints (__main__.TestOnboardingAPI) ... ok
test_openapi_spec_exists (__main__.TestOnboardingAPI) ... ok
test_audit_logger_valid (__main__.TestSupportScripts) ... ok
test_permission_delegation_valid (__main__.TestSupportScripts) ... ok
test_project_bootstrapper_valid (__main__.TestSupportScripts) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.0XXs

OK
```

All tests should pass.

**Congratulations!** You've successfully implemented a complete self-service onboarding platform.

## Idempotent Operations

All provisioning operations are designed to be safe to re-run:

**Team Creation**: Creating a team that already exists returns success without modification:
```bash
curl -X POST http://localhost:5000/teams \
  -H "Content-Type: application/json" \
  -d '{"name": "platform-team", "display_name": "Platform Engineering Team", "lead": "alice@example.com"}'

# Second call returns the same result without errors
```

**Member Addition**: Adding a member that's already in a team returns success:
```bash
python permission-delegation.py grant platform-team bob@example.com create-projects alice@example.com
# Safe to run multiple times - permission is only granted once
```

**Project Bootstrapping**: Re-running updates existing configurations:
```bash
python project-bootstrapper.py bootstrap platform-team my-api python "Updated description"
# Updates catalog entry and manifests without corruption
```

## RBAC Hierarchy

The implementation follows a three-tier RBAC model (Figure 7-2 in chapter):

```
Platform Admin
    └── Creates team
         └── Assigns Team Admin
              ├── Team Admin (full control)
              │   ├── Invites members
              │   ├── Assigns team-developer role
              │   └── Assigns team-viewer role
              ├── Team Developer
              │   ├── Create/manage projects
              │   ├── Deploy applications
              │   └── Configure CI/CD
              └── Team Viewer
                  └── Read-only access to resources
```

Each team gets its own namespace with RoleBindings:
- **team-{name}-lead**: Full admin access (Kubernetes admin role)
- **team-{name}-developer**: Create and manage resources (Kubernetes edit role)
- **team-{name}-viewer**: Read-only access (Kubernetes view role)

## Tiered Resource Quotas

The system provides three resource tiers:

| Tier | CPU | Memory | Pods | Use Case |
|------|-----|--------|------|----------|
| **Starter** | 2 | 4Gi | 10 | Testing, small prototypes |
| **Standard** | 8 | 16Gi | 50 | Production microservices |
| **Enterprise** | 32 | 64Gi | 200 | Large-scale applications |

Quotas are enforced at the Kubernetes ResourceQuota level. Teams can request quota increases via the API without platform intervention.

## Security Considerations

1. **API Authentication**: Implement OAuth2/OpenID Connect in production using Keycloak (referenced in chapter)
2. **RBAC**: Use strong RBAC policies to limit API access to authenticated users
3. **Audit Logging**: Store audit logs in immutable storage (S3, Google Cloud Storage) for compliance
4. **Namespace Isolation**: NetworkPolicies restrict traffic between namespaces; Pod Security Standards enforced
5. **Secret Management**: Use sealed-secrets or external secret management (not inline in ConfigMaps)
6. **Image Security**: Scan container images for vulnerabilities; use private registries
7. **Resource Limits**: Enforce LimitRanges to prevent resource exhaustion attacks
8. **API Rate Limiting**: Implement rate limiting to prevent abuse

## Extending the Platform

### Adding New Project Templates
Edit `project-bootstrapper.py` to add language support:

```python
TEMPLATES = {
    'rust': {
        'description': 'Rust microservice',
        'main_file': 'main.rs',
        'ci_config': '.github/workflows/ci.yml'
    },
    # ... existing templates
}
```

Then update the `_generate_*` methods to create Rust-specific files.

### Custom Permission Scopes
Extend `permission-delegation.py` with additional permissions:

```python
ROLE_PERMISSIONS = {
    'developer': {
        # ... existing permissions
        'manage-infrastructure': 'Provision infrastructure resources',
        'manage-networking': 'Configure network policies',
    }
}
```

### Integration with Backstage
The `project-bootstrapper.py` creates Backstage catalog entries. Customize the template:

```python
def _generate_backstage_catalog(self, name: str, team: str, description: str) -> str:
    """Generate Backstage catalog entry with custom metadata."""
    # Add team tags, owner references, dependency declarations, etc.
```

### Integration with Keycloak
Extend `onboarding-api.py` to automatically create Keycloak groups:

```python
def create_keycloak_groups(team_id: str, members: List[str]):
    """Create Keycloak groups for team members."""
    # Call Keycloak API to create:
    # - team-{team_id}-admins
    # - team-{team_id}-developers
    # - team-{team_id}-viewers
```

### Webhook Notifications
Add webhooks to notify Slack, email, or other systems:

```python
@app.route('/teams', methods=['POST'])
def create_team():
    # ... existing logic
    notify_slack(f"Team {team_id} created by {actor}")
    notify_email(team_lead, "Welcome to the platform!")
```

## Performance Considerations

- **Namespace provisioning**: 2-5 seconds per team
- **Project bootstrapping**: 10-30 seconds depending on template complexity
- **API response times**:
  - Metadata operations (GET): <200ms
  - Provisioning operations (POST): <5s
- **Audit log queries**: Scale to millions of events with proper indexing
- **Permission checks**: O(1) for has_permission(), O(n) for list_member_permissions()

Optimize for production:
- Use persistent database (PostgreSQL) instead of in-memory storage
- Implement caching for frequently accessed data (Redis)
- Run API in multiple instances behind load balancer
- Store audit logs in time-series database (InfluxDB, CloudWatch, etc.)
- Use async operations for long-running provisioning tasks

## Troubleshooting

### API fails to start
```bash
# Check Flask installation
python -c "import flask; print(flask.__version__)"

# Verify port 5000 is available
lsof -i :5000

# Check detailed error logs
ONBOARDING_API_DEBUG=True python onboarding-api.py
```

### Namespace creation fails
```bash
# Verify kubectl is configured
kubectl cluster-info

# Check service account permissions
kubectl auth can-i create namespaces \
  --as=system:serviceaccount:platform-onboarding:onboarding-api

# View API error logs
curl -X POST http://localhost:5000/teams \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "display_name": "Test", "lead": "test@example.com"}' -v
```

### Permission delegation not working
```bash
# Verify team exists
curl http://localhost:5000/teams/platform-team

# Check audit logs for errors
python audit-logger.py failures

# Verify member is in team
curl http://localhost:5000/teams/platform-team/members

# Debug permission check
python -c "from permission_delegation import PermissionManager; \
m = PermissionManager(); \
print(m.has_permission('platform-team', 'bob@example.com', 'create-projects'))"
```

### Project bootstrap creates unexpected files
```bash
# Verify template is correct
python project-bootstrapper.py templates

# Check project info structure
python -c "from project_bootstrapper import ProjectBootstrapper; \
pb = ProjectBootstrapper(); \
success, error, info = pb.bootstrap('platform-team', 'test-project', 'python'); \
print(f'Files: {list(info[\"files\"].keys())}')"
```

## Companion Website Alignment

The companion website at https://peh-packt.platformetrics.com/ provides additional resources for Chapter 7:

- **Video Walkthroughs**: Step-by-step demonstrations of running the code
- **Interactive API Documentation**: Live Swagger UI for the onboarding API
- **Sample Datasets**: Pre-populated teams and projects for testing
- **Deployment Guides**: Kubernetes manifests for production deployment
- **Architecture Diagrams**: High-resolution versions of Figures 7-1 through 7-4
- **Common Patterns**: Additional onboarding scenarios and customizations
- **Discussion Forum**: Community-driven Q&A about the patterns

**Note**: The companion website content is supplementary and focuses on extending the patterns shown in the handbook. The code in this directory is self-contained and fully functional without the website.

## Contributing

When adding new features:

1. **Update OpenAPI Spec**: Add new endpoints to `openapi-spec.yaml`
2. **Implement API Endpoints**: Add Flask routes to `onboarding-api.py`
3. **Add Audit Logging**: Log all operations using `audit_logger.log_event()`
4. **Write Tests**: Add test cases to `test-onboarding.py`
5. **Update This README**: Document new capabilities and expected outputs
6. **Follow Conventions**:
   - Team IDs: lowercase alphanumeric with hyphens (team-{name})
   - API responses: Consistent JSON schemas from openapi-spec.yaml
   - Errors: Structured error objects with code and message
   - Timestamps: ISO 8601 format with Z suffix (2024-01-15T10:30:00Z)

## License

These examples are provided as part of "The Platform Engineer's Handbook" by Packt Publishing.

## References

**Chapter 7 Topics**:
- Creating an onboarding API (Listing 7-1)
- RBAC, namespace, and quota automation (Listings 7-2, 7-3)
- Enable self-service team management (Figure 7-3, 7-4)
- Bootstrapping new projects (Listing 7-4 from Backstage scaffolder)

**External Resources**:
- Kubernetes API: https://kubernetes.io/docs/reference/generated/kubernetes-api/
- OpenAPI 3.0 Specification: https://spec.openapis.org/oas/v3.0.0
- Flask Documentation: https://flask.palletsprojects.com/
- Backstage Software Catalog: https://backstage.io/docs/features/software-catalog
