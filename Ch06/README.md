# Chapter 6: Accelerating DevEx - Deploying and Curating Your First Developer Portal

## Overview

This chapter demonstrates how to deploy and curate a **developer portal** as the single pane of glass for your organization's technical capabilities. The portal is NOT the platform itself, but rather the **discovery and interaction layer** that enables developers to understand, access, and operate available services, APIs, and tools.

A developer portal powered by Backstage serves as:
- **Service Catalog**: Central registry of all services, APIs, and data products
- **Documentation Hub**: Integrated TechDocs for architectural decisions and runbooks
- **Access Control**: OAuth/Keycloak SSO integration for seamless authentication
- **Scaffolder**: Templates for creating new services with predefined best practices
- **Golden Path**: Guided experience from idea to production deployment
- **Infrastructure Visibility**: Integration with ArgoCD and GitOps for deployment status

### Portal vs Platform

| Aspect | Portal | Platform |
|--------|--------|----------|
| **Purpose** | Discovery & interaction | Operational infrastructure |
| **Users** | Developers, teams, operators | Infrastructure teams, automation |
| **Integration** | Service catalog, APIs, docs | Kubernetes, CI/CD, monitoring |
| **Update Cadence** | Frequent (content-driven) | Stable (infrastructure-driven) |

## Code-to-Chapter Mapping

This directory contains all code listings and configuration examples referenced in Chapter 6:

| File | Chapter Section | Purpose |
|------|-----------------|---------|
| `app-config.yaml` | 6.2 Role-based navigation | Base Backstage configuration template |
| `app-config.production.yaml` | 6.2 Role-based navigation | Production Backstage config with Keycloak SSO, GitHub discovery, and proxy settings |
| `backstage-helm-values.yaml` | 6.1 Backstage Architecture | Kubernetes Helm chart values for production Backstage deployment with PostgreSQL |
| `catalog-info.yaml` | 6.3 Service catalog examples | Backstage catalog entity definitions (Component, API, Resource, User, Group, System, Domain) |
| `api-spec.yaml` | 6.3 Service catalog examples | OpenAPI 3.0 specification for demo-app API registration |
| `register-catalog-entities.py` | 6.4 Publishing deployed services | Script to discover and register catalog entities from GitHub into Backstage |
| `test-portal-health.py` | Validation & health checks | Unit tests for portal configuration and setup |

### Orphan Files

The following files in the code directory are **not directly referenced** in Chapter 6 content:
- `__pycache__/` directory - Python bytecode cache (auto-generated, can be safely ignored)

## Prerequisites

### Required Components

1. **Backstage**: Developer Portal framework
   - Version: 1.20+
   - Deployment: Kubernetes or Docker
   - Database: PostgreSQL for production (recommended over SQLite)

2. **Keycloak**: Identity and Access Management
   - Version: 20+
   - OAuth 2.0 provider for SSO
   - Integration with GitHub for user sync
   - Pre-requisite: Completed Chapter 3 (Identity Management)

3. **GitHub**: Source control and catalog discovery
   - Organizations enabled
   - Personal access tokens for automation
   - Repository topics for catalog classification

4. **ArgoCD** (Optional): GitOps deployment visibility
   - Backstage ArgoCD plugin integration
   - Service-to-deployment mapping
   - Pre-requisite: Completed Chapter 4 (GitOps)

5. **PostgreSQL**: Persistent database for Backstage
   - Version: 12+
   - Separate instance from application databases
   - Connection credentials stored in Kubernetes secrets

### Python Dependencies

For running the included Python scripts, ensure you have:
```bash
python3 --version  # 3.8 or higher
```

The scripts use only Python standard library modules (no external dependencies), making them portable and easy to integrate.

### Docker/Kubernetes Requirements

For production Backstage deployment:
- Kubernetes cluster (1.24+)
- Helm 3.10+
- `kubectl` configured with cluster access
- cert-manager for TLS (see Chapter 4)
- Ingress controller (nginx recommended)

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           Developer Portal (Backstage)               │
├─────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────────────┐ │
│  │  Service Catalog │  │ TechDocs & Documentation │ │
│  │  (catalog-info)  │  │ (Markdown in repos)      │ │
│  └──────────────────┘  └──────────────────────────┘ │
│  ┌──────────────────┐  ┌──────────────────────────┐ │
│  │  API Registry    │  │ Scaffolder Templates     │ │
│  │  (api-spec.yaml) │  │ (Golden Paths)           │ │
│  └──────────────────┘  └──────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│  Auth: Keycloak/OAuth  |  Backend: PostgreSQL        │
├─────────────────────────────────────────────────────┤
│  Integrations: GitHub, ArgoCD, Kubernetes           │
└─────────────────────────────────────────────────────┘
```

### Key Configuration Files

- **app-config.yaml**: Base Backstage configuration template
- **app-config.production.yaml**: Production overrides with environment-specific settings
- **backstage-helm-values.yaml**: Kubernetes deployment specification
- **catalog-info.yaml**: Service catalog entity definitions
- **api-spec.yaml**: OpenAPI specification for API discovery

## Step-by-Step Instructions

### 1. Verify Prerequisites

Before deploying Backstage, ensure you have:
- A running Kind cluster (`kubectl cluster-info`)
- Helm installed (`helm version`)
- A GitHub Personal Access Token with `repo` scope (see Environment Setup in the CIA guide)

### 2. Prepare Configuration

Review and customize the configuration files for your environment:

**Edit app-config.production.yaml:**
- Replace `platform.company.com` with your domain
- Set `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD` environment variables
- Configure Keycloak OAuth with your realm details
- Update GitHub organization name and token

```bash
# Example configuration with environment variables
export POSTGRES_HOST=postgres.platform.svc.cluster.local
export POSTGRES_PORT=5432
export POSTGRES_USER=backstage
export POSTGRES_PASSWORD=$(kubectl get secret postgres-secret -o jsonpath='{.data.password}' | base64 -d)
export KEYCLOAK_METADATA_URL=https://keycloak.company.com/realms/backstage/.well-known/openid-configuration
export KEYCLOAK_CLIENT_ID=backstage
export KEYCLOAK_CLIENT_SECRET=$(kubectl get secret backstage-oauth -o jsonpath='{.data.client-secret}' | base64 -d)
export GITHUB_TOKEN=ghp_XXXXX
```

**Next steps**: Verify all environment variables are correctly set before deployment.

### 3. Deploy with Helm

Install or upgrade Backstage on your Kubernetes cluster:

```bash
# Create namespace and GitHub token secret (required for catalog registration from GitHub)
# Create a GitHub Personal Access Token (classic) with 'repo' scope at:
# https://github.com/settings/tokens/new
kubectl create namespace backstage
kubectl create secret generic backstage-secrets \
  --namespace backstage \
  --from-literal=GITHUB_TOKEN=$GITHUB_TOKEN

# Add Backstage Helm repository
helm repo add backstage https://backstage.github.io/charts
helm repo update

# Install Backstage with custom values (namespace already created above)
helm install backstage backstage/backstage \
  --namespace backstage \
  -f backstage-helm-values.yaml

# Verify deployment
kubectl get pods -n backstage
kubectl logs -n backstage -l app=backstage --tail=50
```

> **How config loading works:** By default, the Helm chart generates a ConfigMap (`app-config-from-configmap.yaml`) from `backstage.appConfig` and loads ONLY that file — skipping the image's built-in `app-config.yaml`. The built-in config contains guest auth and GitHub integration defaults. Our values file uses `backstage.args` to load the built-in config first, then our ConfigMap overrides on top. This ensures guest auth and `${GITHUB_TOKEN}` integration work without duplicating them in the values file. If you see "401 Unauthorized" or "Missing credentials", verify the `args` section is present in `backstage-helm-values.yaml`.

> **How the GitHub token reaches the container:** The Helm chart's `extraEnvVarsSecrets` injects every key from the `backstage-secrets` Kubernetes Secret as a container env var. The built-in `app-config.yaml` references `${GITHUB_TOKEN}` for GitHub integration, so the secret key name must be exactly `GITHUB_TOKEN`.

> **How auth works:** The built-in `app-config.yaml` enables guest auth (`auth.environment: development`, `auth.providers.guest: {}`). Our ConfigMap adds `backend.auth.dangerouslyDisableDefaultAuthPolicy: true` to allow unauthenticated API access (required for guest mode). In production, replace guest auth with OAuth/OIDC (e.g., Keycloak from Chapter 3).

**Expected output**:
- 1 Backstage pod running
- PostgreSQL pod running (Bitnami subchart)
- No ingress (using port-forward for Kind)

**Next steps**: Wait 60 seconds for services to stabilize, then test connectivity via port-forward: `kubectl port-forward -n backstage svc/backstage 7007:7007 &`

### 4. Verify Portal Health

Run health checks to ensure all components are functioning correctly:

```bash
python3 test-portal-health.py
```

This validates:
- Configuration files exist (`app-config.production.yaml`, `backstage-helm-values.yaml`, `catalog-info.yaml`)
- Authentication settings are configured in app-config
- Catalog has required API version field
- Python scripts compile without syntax errors

Expected output: All tests pass (✓)

**Next steps**: If any tests fail, review the error messages and check configuration files.

### 5. Register Catalog Entities

Register your services in the Backstage catalog. The recommended approach for local Kind clusters is to use the Backstage UI directly.

**Option A — Via the Backstage UI (recommended for local/Kind):**

1. Open `http://localhost:7007` in your browser
2. Click **Create** in the left sidebar → **Register Existing Component**
3. Paste the catalog-info.yaml URL and click **Analyze**:
   ```
   https://github.com/achankra/peh/blob/main/Ch06/catalog-info.yaml
   ```
4. Backstage will parse the YAML and discover all entities (Component, API, Resource, User, Group, System, Domain)
5. Click **Import** to register them
6. Navigate to **Catalog** to see the registered entities

> **Note:** The vanilla Backstage Helm image does not have API authentication configured, so the `register-catalog-entities.py` script (which sends an `Authorization: Bearer` header) will receive 401 errors. Use the UI approach for local Kind clusters.

**Option B — Via the script (requires Backstage API auth configured):**

```bash
python3 register-catalog-entities.py \
  --backstage-url $BACKSTAGE_URL \
  --token $BACKSTAGE_API_TOKEN \
  --entity-url https://github.com/achankra/peh/blob/main/Ch06/catalog-info.yaml
```

**Next steps**: Verify entities appear in Backstage UI by navigating to /catalog.

### 6. Access the Portal

Open your browser and navigate to Backstage:

```
http://localhost:7007
```

> **Note:** For local Kind clusters, we use `kubectl port-forward -n backstage svc/backstage 7007:7007 &` instead of ingress. For production deployments, configure ingress with your domain and TLS.

**Expected experience**:
1. See Backstage home page
2. Navigate to /catalog to see registered services
3. View service details, APIs, and dependencies
4. Click on a component to see ownership, relationships, and API specs

**Troubleshooting**:
- Blank catalog: Register entities via the UI (step 5 above)
- Connection refused: Ensure port-forward is running (`kubectl port-forward -n backstage svc/backstage 7007:7007 &`)

### 7. Explore Entity Relationships

After importing entities, explore how Backstage connects services, APIs, teams, and infrastructure:

1. **Component detail page**: Click on `api-gateway` in the Catalog. The Overview tab shows ownership (`platform-team`) and system (`platform-services`). The Relations tab shows the dependency graph — `api-gateway` provides `gateway-api` and depends on `postgres-primary`.

2. **API definition**: Click on `gateway-api` to see the API entity. The Definition tab renders the OpenAPI spec defined in `catalog-info.yaml`.

3. **Team ownership**: Click on `platform-team` (the Group entity) to see all components owned by the team.

4. **System view**: Click on `platform-services` (the System entity) to see all components, APIs, and resources grouped under this system.

> **Tip:** Use the Kind dropdown on the Catalog page to filter by entity type (Component, API, Resource, Group, User, System, Domain).

## Key Concepts

### Portal-of-Peril Warning

Common pitfalls when implementing a developer portal:

1. **Portal as a Project**: Treating it as one-time initiative rather than continuous investment
2. **Content Decay**: Outdated documentation and catalog entries
3. **Insufficient Integration**: Portal disconnected from actual platform and deployment systems
4. **Overengineering**: Too much customization; start simple and iterate
5. **Adoption Friction**: Poor UX or unclear value proposition leads to low adoption
6. **Fragmented Ownership**: No clear ownership of catalog entities and documentation

**Recovery Strategy**:
- Feature culling: Disable unused features, however cool they seem
- Catalog cleanup: Verify ownership, archive orphaned entries
- Developer listening sessions: Understand actual needs
- Prioritize top 3 complaints and measure success
- Iterate and communicate progress

### Success Metrics

Measure portal adoption and value:
- Do you have active contributors adding/updating catalog entries weekly?
- Is catalog completeness growing?
- Receiving positive feedback formally and informally?
- Is Portal the first place developers go for service discovery (not Slack/Confluence)?
- Are you receiving new feature requests from the platform team?

## Topics Covered

- Portal decision-making framework (6.1)
- Build vs buy vs hybrid analysis (6.1)
- Portal selection flow and organizational readiness assessment (6.1)
- Backstage architecture and deployment (6.1)
- Service catalog configuration patterns (6.2-6.3)
- Role-based navigation and permissions (6.2)
- SSO integration with OAuth/Keycloak (6.2)
- Catalog entity types and relationships (6.3)
- Auto-discovery of services from GitHub (6.4)
- API specification and publishing (6.3-6.4)
- Portal validation and health checks (6.4)
- Portal plugins and customization (6.5)

## References

- **Backstage**: https://backstage.io
- **Backstage Documentation**: https://backstage.io/docs
- **OpenAPI Specification**: https://openapis.org
- **Keycloak**: https://www.keycloak.org
- **ArgoCD**: https://argoproj.github.io/cd/
- **Kubernetes Ingress**: https://kubernetes.io/docs/concepts/services-networking/ingress/
- **The Platform Engineer's Handbook**: https://peh-packt.platformetrics.com/

## Related Chapters

This chapter builds on concepts from previous chapters:

- **Chapter 1-2**: Platform engineering fundamentals and GitOps workflows
- **Chapter 3**: OAuth/Keycloak identity provider (used for portal SSO)
- **Chapter 4**: Kubernetes deployment and cert-manager for TLS
- **Chapter 5**: Demo application deployment (becomes first catalog entry)

Subsequent chapters may reference portal capabilities for discovery and integration.

## Troubleshooting

### Common Issues

**Backstage pod stuck at 0/1 Running or CrashLoopBackOff**
- This is usually a race condition: Backstage started before PostgreSQL was ready
- Check logs: `kubectl logs deploy/backstage -n backstage --tail=30`
- If you see "the database system is shutting down" or "Knex: Timeout acquiring a connection", wait for PostgreSQL to be `1/1 Running`, then restart Backstage:
  ```bash
  kubectl rollout restart deployment/backstage -n backstage
  ```

**"401 Unauthorized" or "Failed to load entity kinds" on Catalog page**
- The built-in `app-config.yaml` isn't being loaded (guest auth missing)
- Verify the `args` section in the deployment includes both config files:
  ```bash
  kubectl get deployment backstage -n backstage -o jsonpath='{.spec.template.spec.containers[0].args}'
  ```
- You should see: `["--config","/app/app-config.yaml","--config","/app/app-config-from-configmap.yaml"]`

**"Missing credentials" on the Register Component page**
- The GITHUB_TOKEN env var is missing or contains a placeholder
- Verify: `kubectl get secret backstage-secrets -n backstage -o jsonpath='{.data.GITHUB_TOKEN}' | base64 -d; echo`
- If wrong, delete and recreate: `kubectl delete secret backstage-secrets -n backstage` then recreate with your real token

**"PASSWORDS ERROR: secret backstage-postgresql does not contain key user-password" on helm upgrade**
- Stale PostgreSQL secret from a previous install
- Fix: `kubectl delete secret backstage-postgresql -n backstage` then re-run helm install/upgrade

**Catalog entities not registering**
- Ensure catalog-info.yaml entities have all required fields (e.g., Group needs `spec.type` and `spec.children`)
- Check GitHub token has `repo` scope
- Verify the catalog URL points to a raw-accessible file on GitHub

### Getting Help

- Review Backstage documentation: https://backstage.io/docs
- Check Keycloak documentation: https://www.keycloak.org/documentation
- Search GitHub issues for similar problems
- Join Backstage community Discord for real-time support

## License

These code examples are provided as part of "The Platform Engineer's Handbook" and are available under the book's license terms.
