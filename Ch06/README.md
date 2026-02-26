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
| `portal-evaluation-framework.py` | 6.1 Portal selection | Decision-making framework for evaluating portal solutions (Backstage, Keycloak, Gitea, commercial options) |
| `register-catalog-entities.py` | 6.4 Publishing deployed services | Script to discover and register catalog entities from GitHub into Backstage |
| `create-backstage-plugin.py` | 6.5 Extending the portal (implied) | Scaffolding tool for generating complete Backstage plugin structures |
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

Before deploying Backstage, validate that all required components are ready:

```bash
python3 portal-evaluation-framework.py --portals backstage keycloak
```

Expected output: Comparison table showing Backstage scoring highest for extensibility and community support.

**Next steps**: Ensure Keycloak (Chapter 3) is deployed and accessible at your configured URL.

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

> **How the GitHub token works:** The default Backstage image ships with `integrations.github.token: ${GITHUB_TOKEN}` in its built-in app-config. The Helm chart's `extraEnvVarsSecrets` injects every key from the `backstage-secrets` Kubernetes Secret as a container env var. The secret key name (`GITHUB_TOKEN`) must match the env var name exactly. Without this, the catalog registration page shows "Missing credentials" or "401 Unauthorized" when fetching from GitHub.

> **How auth works:** The default Backstage image ships with guest auth enabled (`auth.environment: development`, `auth.providers.guest: {}`). Our values file deliberately does NOT override the `auth` section, so guest auth works out of the box. If you override `appConfig.auth` and forget to include the guest provider, the Catalog page shows "Failed to load entity kinds" / "401 Unauthorized" on every API call. In production, replace guest auth with OAuth/OIDC (e.g., Keycloak from Chapter 3).

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

### 7. Create Custom Plugins (Optional)

Extend Backstage with custom plugins for your organization:

```bash
# Create a frontend plugin for custom dashboards
python3 create-backstage-plugin.py \
  --name company-dashboard \
  --type frontend \
  --description "Custom analytics dashboard for our platform"

# Create a backend plugin for integration
python3 create-backstage-plugin.py \
  --name internal-api-proxy \
  --type backend \
  --description "Backend plugin for internal API proxying"

# Create a full stack plugin
python3 create-backstage-plugin.py \
  --name compliance-checker \
  --type full \
  --description "Full-stack plugin for compliance validation"
  --output-dir ./plugins
```

**Expected output**:
```
Scaffolding frontend plugin: company-dashboard
============================================================
Created directory structure in ./company-dashboard
Created package.json
Created tsconfig.json
Created manifest.json
Created README.md
Created test template
Created frontend plugin files
============================================================

Successfully created company-dashboard plugin!
Plugin directory: ./company-dashboard

Next steps:
  1. cd ./company-dashboard
  2. yarn install
  3. yarn build
  4. yarn dev
```

**Next steps**: Develop plugin in the created directory, then integrate with Backstage app.

## Key Concepts

### Portal Evaluation Framework

The decision-making framework evaluates portals across multiple dimensions:

1. **Extensibility** (25% weight): Ability to extend with custom plugins and integrations
2. **Community Support** (20% weight): Active community, documentation, and ecosystem
3. **SSO/Auth Support** (20% weight): Support for OAuth, SAML, Keycloak
4. **Catalog Management** (20% weight): Service catalog features and discovery
5. **Templates & Scaffolding** (15% weight): Project templates and code generation

Run the evaluation framework to compare solutions:
```bash
python3 portal-evaluation-framework.py --output-format table
python3 portal-evaluation-framework.py --output-format json > results.json
```

### Build vs Buy vs Hybrid Decision

**Backstage (Open Source)**
- Pros: Highly customizable, strong plugin ecosystem, vendor-agnostic, integration with book stack
- Cons: Requires operational overhead, plugin maintenance
- Best for: Organizations with engineering maturity and specific integration needs

**Commercial Solutions** (Port, OpsLevel, Cortex, Harness)
- Pros: Managed service, guaranteed uptime, professional support
- Cons: Vendor lock-in, less customization, ongoing licensing costs
- Best for: Organizations prioritizing operational simplicity

**Hybrid Approach** (Recommended)
Start with open-source Backstage, evaluate managed solutions after 6-12 months of operation.

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

**Backstage pods not starting**
```bash
# Check pod logs
kubectl logs -n backstage -l app=backstage --tail=100

# Check persistent volume
kubectl get pvc -n backstage

# Verify database connectivity
kubectl exec -it -n backstage backstage-0 -- psql -U backstage -c "SELECT version();"
```

**Catalog entities not registering**
- Verify Backstage API token is correct and has permissions
- Check GitHub token has repo access for discovery
- Ensure catalog-info.yaml files are valid YAML and contain required `apiVersion` field
- Review registration output for specific error messages

**OAuth/SSO not working**
- Verify Keycloak realm and client configuration match app-config settings
- Check Keycloak metadata URL is accessible from Backstage pod
- Confirm redirect URI in Keycloak matches `https://backstage.example.com/oauth/callback`

**TLS certificate errors**
- Verify cert-manager is installed and ingress has annotations
- Check certificate status: `kubectl describe certificate -n backstage`
- Re-create ingress if certificate not issued within 5 minutes

### Getting Help

- Review Backstage documentation: https://backstage.io/docs
- Check Keycloak documentation: https://www.keycloak.org/documentation
- Search GitHub issues for similar problems
- Join Backstage community Discord for real-time support

## License

These code examples are provided as part of "The Platform Engineer's Handbook" and are available under the book's license terms.
