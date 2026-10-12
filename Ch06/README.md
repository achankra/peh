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
| `app-config.yaml` | 6.2 Role-based navigation | Base Backstage configuration with OIDC auth provider, session config, and PagerDuty proxy |
| `app-config.production.yaml` | 6.2 Role-based navigation | Production overrides: S3 TechDocs storage, Elasticsearch search, environment variable references |
| `backstage-helm-values.yaml` | 6.1 Backstage Architecture | Kubernetes Helm chart values for production Backstage deployment with PostgreSQL |
| `catalog-info.yaml` | 6.3 Service catalog examples | Catalog entity definitions: `demo-app` (Component), `demo-api` (API), `pilot-team-alpha` (Group) and `maria.garcia` (User), with PagerDuty, ArgoCD, Prometheus, and Grafana annotations on the Component |
| `api-spec.yaml` | 6.3 Service catalog examples | OpenAPI 3.0 specification for demo-app API registration |
| `keycloak-oidc-module.ts` | 6.2 SSO integration | TypeScript backend module that registers the Keycloak OIDC auth provider using `createBackendModule` and `authProvidersExtensionPoint` |
| `custom-homepage.tsx` | 6.5 Portal customisation | Backstage homepage built with `PageBlueprint.make()` (replaces deprecated `createPageExtension`); includes `KubernetesStatusCard` and `ServiceHealthCard` widgets |
| `templates/onboard-service/template.yaml` | 6.4 Golden Path / Scaffolder | Backstage Scaffolder template for onboarding new services; includes `output.links` block that surfaces the PR URL after execution |
| `create-backstage-plugin.py` | 6.5 Portal customisation | Helper script for scaffolding a new custom Backstage plugin directory with boilerplate |
| `register-catalog-entities.py` | 6.4 Publishing deployed services | Script to discover and register catalog entities from GitHub into Backstage |
| `test-portal-health.py` | Validation & health checks | Unit tests for portal configuration and setup |
| `load-secrets.sh` | Secrets management (cross-chapter) | Loads `GITHUB_TOKEN` from Bitwarden vault; requires `bw-helper.sh` from Ch1. |
| `.env_example` | Secrets management (fallback) | Template for a gitignored `.env` holding `GITHUB_TOKEN` when you are not using Bitwarden. |

## Prerequisites

### Running This Chapter Standalone

> If you are jumping into this chapter without completing earlier chapters, use these commands to set up the infrastructure dependencies. If you already have them running, skip this section.

> **Note:** The local Kind deployment in this chapter uses guest auth and a bundled PostgreSQL, so it needs only a cluster and a GitHub token. Keycloak (Chapter 3) is only needed when you move to the production SSO setup (see [Production Hardening](#production-hardening)).

```bash
# 1. Start Docker Desktop (macOS: open from Applications or Spotlight)
open -a "Docker"
# Wait for the Docker engine to start before continuing

# 2. Create a Kind cluster (skip if you already have one)
kind get clusters                       # Check for existing clusters
kind create cluster --name platform-dev # Create one if none listed
kubectl get nodes                       # Verify node(s) are Ready
```

Backstage itself is installed in [Step 4](#4-deploy-with-helm), after your secrets are loaded and the config is validated.

### Required Components

Needed for the local Kind flow in the Step-by-Step Instructions:

1. **Backstage**: Developer Portal framework
   - Pinned versions (tested): Helm chart `backstage/backstage` **2.10.2**, image `ghcr.io/backstage/backstage` **1.55.2** (pinned in `backstage-helm-values.yaml`; `latest` is avoided because the install relies on the image's built-in `app-config.yaml`)
   - Deployment: Kubernetes (Kind) via Helm

2. **PostgreSQL**: Persistent database for Backstage
   - Installed automatically by the Helm chart (Bitnami subchart) with demo credentials set in `backstage-helm-values.yaml`

3. **GitHub**: Source control and catalog discovery
   - Personal access token in `GITHUB_TOKEN`: fine-grained with **Contents: Read-only** on the repos holding your catalog files (recommended), or classic with `repo` scope (broader than needed). See [Step 1](#1-verify-prerequisites).

Needed only for the production setup (see [Production Hardening](#production-hardening)):

4. **Keycloak** (Chapter 3): OIDC identity provider. Backstage uses the generic `oidc` auth provider pointed at Keycloak's realm discovery URL (`/realms/{realm}/.well-known/openid-configuration`).

5. **ArgoCD** (optional): GitOps deployment visibility via the Backstage ArgoCD plugin. Note that Chapter 2 uses Flux, so ArgoCD must be installed separately.

### Python Dependencies

For running the included Python scripts, ensure you have:
```bash
python3 --version  # 3.8 or higher
```

The scripts use only Python standard library modules (no external dependencies), making them portable and easy to integrate.

### Docker/Kubernetes Requirements

For the local Kind deployment:
- Kubernetes cluster (1.24+)
- Helm 4.3.0
- `kubectl` configured with cluster access

Additionally, for a production deployment:
- cert-manager for TLS (see Chapter 3)
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
│  Auth: Keycloak (OIDC) |  Backend: PostgreSQL        │
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
- A GitHub Personal Access Token. Recommended: a **fine-grained** token (https://github.com/settings/personal-access-tokens/new) with these settings:
  - Resource owner: the account or org that owns the repo containing `catalog-info.yaml` (an org must allow fine-grained tokens)
  - Repository access: only select repositories, choosing the repo(s) holding your catalog files
  - Repository permissions: **Contents: Read-only** (Metadata: Read-only is added automatically)

  This is enough to register catalog entities in Step 6. The upstream `achankra/peh` catalog URL is a public repo, so it works without repo permissions, but a token raises the API rate limit. If you register a fork, the token must be owned by the fork's owner and include that repo. Fallback: a classic token with `repo` scope (https://github.com/settings/tokens/new), which is broader than needed.
  
  The Scaffolder template `templates/onboard-service/template.yaml` opens a pull request, so running it needs more: Contents and Pull requests set to Read and write (plus Administration if it creates a repo). That is outside this chapter's install flow.

### 2. Load Secrets

The only secret this flow needs is `GITHUB_TOKEN`. Never paste a real token into a tracked file or a placeholder into the cluster — load it from one of these sources:

**Option A — Bitwarden (matches the other chapters):** store the token as the password of a vault item named `peh-github`, then:

```bash
source load-secrets.sh    # needs Ch01/.env credentials; see Chapter 1
```

**Option B — `.env` file (no Bitwarden):** same pattern as Chapter 1. The `.env` file is gitignored.

```bash
cp .env_example .env      # then edit .env and set your real GITHUB_TOKEN
set -a && source .env && set +a
```

Verify the token is set before continuing (this fails fast instead of creating an empty or placeholder secret):

```bash
: "${GITHUB_TOKEN:?GITHUB_TOKEN is not set - complete Step 2 first}"
```

### 3. Validate Configuration

Run the static configuration checks **before** deploying:

```bash
python3 test-portal-health.py
```

This validates:
- Configuration files exist (`app-config.production.yaml`, `backstage-helm-values.yaml`, `catalog-info.yaml`)
- Authentication settings are configured in app-config
- Catalog has required API version field
- Python scripts compile without syntax errors

Expected output: All tests pass (✓). These are file-level checks only; they do not contact the running portal (that check is in Step 4).

**Next steps**: If any tests fail, review the error messages and check configuration files.

### 4. Deploy with Helm

Install or upgrade Backstage on your Kubernetes cluster. The chart and image versions are pinned (chart `2.10.2`, image `1.55.2` in `backstage-helm-values.yaml`) so every reader gets the same behaviour:

```bash
# Create the labeled namespace and GitHub token secret (required for catalog registration from GitHub)
# Idempotent: safe to re-run, and re-running replaces the secret with the current $GITHUB_TOKEN
# The labels are required by the Chapter 3 Gatekeeper policy (namespace-must-have-team)
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: backstage
  labels:
    team: platform
    environment: dev
    cost-center: "10001"
EOF
kubectl create secret generic backstage-secrets \
  --namespace backstage \
  --from-literal=GITHUB_TOKEN="${GITHUB_TOKEN:?GITHUB_TOKEN is not set - complete Step 2 first}" \
  --dry-run=client -o yaml | kubectl apply -f -

# Add Backstage Helm repository
helm repo add backstage https://backstage.github.io/charts
helm repo update

# Install (or upgrade) Backstage with the pinned chart version and custom values
helm upgrade --install backstage backstage/backstage \
  --version 2.10.2 \
  --namespace backstage \
  -f backstage-helm-values.yaml

# Wait until Backstage is ready, then inspect
kubectl rollout status deployment/backstage -n backstage --timeout=300s
kubectl get pods -n backstage
kubectl logs deploy/backstage -n backstage --tail=50
```

> **Why the labels:** if you completed Chapter 3, Gatekeeper's `namespace-must-have-team` constraint rejects any namespace without `team` (`^[a-z]{2,20}$`), `environment` (`dev|staging|prod`) and `cost-center` (4-6 digits) labels. Without them, `kubectl create namespace backstage` fails with `admission webhook "validation.gatekeeper.sh" denied the request ... Missing required label(s)`. The values above match the other platform namespaces; change them to suit your team.

> **PostgreSQL resource limits:** the same Chapter 3 Gatekeeper policy also has a `require-limits` constraint. The Bitnami PostgreSQL subchart sets only CPU/memory *requests* by default, so without limits the `backstage-postgresql-0` pod is never created (the Helm install still reports success). `backstage-helm-values.yaml` sets `postgresql.primary.resources` with limits for this reason.

> Because the namespace and secret are applied rather than created, re-running this block is safe. To rotate the token, load the new value (Step 2), re-run it, then `kubectl rollout restart deployment/backstage -n backstage` so the pod picks up the new env var.

> **How config loading works:** By default, the Helm chart generates a ConfigMap (`app-config-from-configmap.yaml`) from `backstage.appConfig` and loads ONLY that file — skipping the image's built-in `app-config.yaml`. The built-in config contains guest auth and GitHub integration defaults. Our values file uses `backstage.args` to load the built-in config first, then our ConfigMap overrides on top. This ensures guest auth and `${GITHUB_TOKEN}` integration work without duplicating them in the values file. If you see "401 Unauthorized" or "Missing credentials", verify the `args` section is present in `backstage-helm-values.yaml`.

> **How the GitHub token reaches the container:** The Helm chart's `extraEnvVarsSecrets` injects every key from the `backstage-secrets` Kubernetes Secret as a container env var. The built-in `app-config.yaml` references `${GITHUB_TOKEN}` for GitHub integration, so the secret key name must be exactly `GITHUB_TOKEN`.

> **How auth works:** The built-in `app-config.yaml` enables guest auth (`auth.environment: development`, `auth.providers.guest: {}`). Our ConfigMap adds `backend.auth.dangerouslyDisableDefaultAuthPolicy: true` to allow unauthenticated API access (required for guest mode). In production, replace guest auth with OAuth/OIDC (e.g., Keycloak from Chapter 3).

**Expected output**:
- 1 Backstage pod running
- PostgreSQL pod running (Bitnami subchart)
- No ingress (using port-forward for Kind)

**Next steps**: `kubectl rollout status` already waited for readiness; continue to Step 5 to reach the portal.

### 5. Access the Portal

For local Kind clusters we use `kubectl port-forward` instead of ingress. Start it in the background and check that the portal answers:

```bash
kubectl port-forward -n backstage svc/backstage 7007:7007 &
curl -sf -o /dev/null -w "%{http_code}\n" http://localhost:7007   # expect 200
```

Then open `http://localhost:7007` in your browser. For production deployments, configure ingress with your domain and TLS.

**Expected experience**:
1. See Backstage home page
2. The catalog is empty until you register entities in Step 6

### 6. Register Catalog Entities

Register your services in the Backstage catalog. The recommended approach for local Kind clusters is to use the Backstage UI directly.

**Option A — Via the Backstage UI (recommended for local/Kind):**

1. Open `http://localhost:7007` in your browser
2. Click **Create** in the left sidebar → **Register Existing Component**
3. Paste the catalog-info.yaml URL and click **Analyze**:
   ```
   https://github.com/achankra/peh/blob/main/Ch06/catalog-info.yaml
   ```
4. Backstage will parse the YAML and discover four entities: `demo-app` (Component), `demo-api` (API), `pilot-team-alpha` (Group) and `maria.garcia` (User), plus the Location that tracks the file
5. Click **Import** to register them
6. Navigate to **Catalog** to see the registered entities

> **Note:** The vanilla Backstage Helm image does not have API authentication configured, so the `register-catalog-entities.py` script (which sends an `Authorization: Bearer` header) will receive 401 errors. Use the UI approach for local Kind clusters.

**Option B — Via the script (requires Backstage API auth configured; skip on the default Kind setup):**

```bash
export BACKSTAGE_URL=http://localhost:7007
export BACKSTAGE_API_TOKEN=<your-backstage-api-token>
python3 register-catalog-entities.py \
  --backstage-url $BACKSTAGE_URL \
  --token $BACKSTAGE_API_TOKEN \
  --entity-url https://github.com/achankra/peh/blob/main/Ch06/catalog-info.yaml
```

**Expected experience**:
1. Navigate to /catalog to see registered services
2. View service details, APIs, and dependencies
3. Click on a component to see ownership, relationships, and API specs

**Troubleshooting**:
- Blank catalog: Register entities via the UI (Step 6 above)
- Connection refused: Ensure port-forward is running (`kubectl port-forward -n backstage svc/backstage 7007:7007 &`)

### 7. Explore Entity Relationships

After importing entities, explore how Backstage connects services, APIs, teams, and infrastructure:

1. **Component detail page**: Click on `demo-app` in the Catalog. The Overview tab shows ownership (`pilot-team-alpha`). The Relations tab shows the dependency graph — `demo-app` provides `demo-api`. The Component also carries annotations for PagerDuty, ArgoCD, Prometheus, and Grafana; this chapter's install does not add the matching plugins, so treat them as metadata here.

2. **API definition**: Click on `demo-api` to see the API entity. The Definition tab renders the OpenAPI spec from `api-spec.yaml`.

3. **Team ownership**: Click on `pilot-team-alpha` (the Group entity) to see its members (`maria.garcia`) and the entities it owns (`demo-app` and `demo-api`).

4. **User view**: Click on `maria.garcia` (the User entity) to see her profile and her membership of `pilot-team-alpha`.

> **Note:** `catalog-info.yaml` also references `system: pilot-program` and `resource:default/postgresql`, but defines neither. Those references do not resolve to entity pages. Add System and Resource entities if you want them to.

> **Tip:** Use the Kind dropdown on the Catalog page to filter by entity type (Component, API, Group, User, Location).

## Production Hardening

The Kind flow above uses guest auth and demo database credentials hardcoded in `backstage-helm-values.yaml` (`backstage`/`backstage`). That is acceptable for a local demo only. For a real deployment, `app-config.production.yaml` replaces those defaults; it is **not** used by the Kind install above.

1. Replace `platform.company.com` with your domain
2. Provide database and SSO settings via environment variables or Kubernetes secrets instead of hardcoded values
3. Configure Keycloak OIDC (Chapter 3) with your realm details
4. Update the GitHub organization name; keep `GITHUB_TOKEN` in a secret, never in a file

```bash
# Example: values referenced by app-config.production.yaml
export POSTGRES_HOST=postgres.platform.svc.cluster.local
export POSTGRES_PORT=5432
export POSTGRES_USER=backstage
export POSTGRES_PASSWORD=$(kubectl get secret postgres-secret -n platform -o jsonpath='{.data.password}' | base64 -d)
export KEYCLOAK_METADATA_URL=https://keycloak.company.com/realms/backstage/.well-known/openid-configuration
export KEYCLOAK_CLIENT_ID=backstage
export KEYCLOAK_CLIENT_SECRET=$(kubectl get secret backstage-oauth -n backstage -o jsonpath='{.data.client-secret}' | base64 -d)
# GITHUB_TOKEN is already loaded from Step 2
```

> `keycloak-oidc-module.ts` and `custom-homepage.tsx` are Backstage source files. They take effect only in a **custom-built** Backstage image that includes them; the stock `ghcr.io/backstage/backstage` image used in the Kind flow does not.

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

- **Chapter 1**: Workstation setup and the Bitwarden secrets helper (`bw-helper.sh`)
- **Chapter 2**: Kind cluster (`platform-dev`) and Flux GitOps
- **Chapter 3**: Keycloak identity provider (used for portal SSO) and cert-manager for TLS
- **Chapter 4**: Observability stack (Prometheus/Grafana), linked from catalog annotations
- **Chapter 5**: Demo application (becomes first catalog entry)

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
- If wrong, load your real token (Step 2), re-run the secret command from Step 4, then `kubectl rollout restart deployment/backstage -n backstage`

**`admission webhook "validation.gatekeeper.sh" denied the request: [namespace-must-have-team] Missing required label(s)`**
- The Chapter 3 Gatekeeper policy requires `team`, `environment` and `cost-center` labels on namespaces
- Use the labeled namespace manifest from Step 4; for an existing namespace: `kubectl label namespace backstage team=platform environment=dev cost-center=10001`

**Helm install succeeds but `backstage-postgresql-0` never appears (Backstage pod stays `0/1`)**
- Gatekeeper's `require-limits` is rejecting the PostgreSQL pod; Helm does not report admission denials
- Confirm: `kubectl describe sts backstage-postgresql -n backstage | tail` shows `[require-limits] Container postgresql is missing required cpu limit`
- Fix: ensure `postgresql.primary.resources.limits` is set in `backstage-helm-values.yaml`, then `helm uninstall backstage -n backstage` and re-run the Step 4 install

**"PASSWORDS ERROR: secret backstage-postgresql does not contain key user-password" on helm upgrade**
- Stale PostgreSQL secret from a previous install
- Fix: `kubectl delete secret backstage-postgresql -n backstage` then re-run helm install/upgrade

**Catalog entities not registering**
- Ensure catalog-info.yaml entities have all required fields (e.g., Group needs `spec.type` and `spec.children`)
- Check the GitHub token can read the repo: fine-grained needs Contents: Read-only on that repo (and the right resource owner); classic needs `repo` scope
- Verify the catalog URL points to a raw-accessible file on GitHub

### Getting Help

- Review Backstage documentation: https://backstage.io/docs
- Check Keycloak documentation: https://www.keycloak.org/documentation
- Search GitHub issues for similar problems
- Join Backstage community Discord for real-time support

## License

These code examples are provided as part of "The Platform Engineer's Handbook" and are available under the book's license terms.

---

**Author:** Ajay Chankramath (ajay@platformetrics.com)
**Book:** The Platform Engineer's Handbook (Packt Publishing)
**Last Updated**: March 2026
