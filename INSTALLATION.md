# Appendix A: Setting Up Your Organization Toolset

**The Platform Engineer's Handbook**
*Comprehensive setup guide for macOS, Linux, and Windows*

---

Before we start coding, you will need to ensure that the tooling used is set up for a mock organization that will allow us to practice engineering platform techniques at scale. For details on how to do some of these operations, we will include links to vendor and tooling documentation.

## Table of Contents

- [Account Setups](#account-setups)
  - [Pulumi Account Setup](#pulumi-account-setup)
  - [GitHub Account Setup](#github-account-setup)
  - [CircleCI Setup](#circleci-setup)
  - [Bitwarden Setup](#bitwarden-setup)
- [Foundational Tools](#foundational-tools)
  - [Package Managers](#package-managers)
  - [Git](#git)
  - [Docker](#docker)
  - [Python 3.10+ and UV](#python-310-and-uv)
  - [Node.js 18+ and npm](#nodejs-18-and-npm)
  - [kubectl](#kubectl)
  - [Kind (Kubernetes in Docker)](#kind-kubernetes-in-docker)
  - [Helm](#helm)
- [Chapter-Specific Installation Instructions](#chapter-specific-installation-instructions)
- [Troubleshooting](#troubleshooting)
- [Quick Reference: Tools by Chapter](#quick-reference-tools-by-chapter)

---

## Account Setups

### Pulumi Account Setup

1. Sign up for a free Pulumi account at [pulumi.com](https://pulumi.com).
2. Note that for the exercises in this book, an Organization account is not needed; an Individual account will be fine.
3. Using the profile link in the top right corner of the page, create a **Personal Access Token**.
4. Take note of this value for now, we will keep it in a secret store later.

> [!WARNING]
> **Common pitfalls to watch out for**
> - Forgetting to enforce a consistent state backend (local vs. cloud) leads to drift.
> - Creating multiple tokens without tracking them properly makes revocation difficult.
> - Skipping policy-as-code guardrails means unsafe infra patterns can creep in.

### GitHub Account Setup

We recommend creating a dedicated GitHub organization for practicing this book. While you can use a personal repository, it will not give you access to some of the organizational settings used, as well as the ability to add "mock" development accounts for different personas.

1. Create a new Organization using the documentation at [GitHub Docs: Creating a new organization](https://docs.github.com/en/organizations/collaborating-with-groups-in-organizations/creating-a-new-organization-from-scratch). Use an appropriate name like `<<yourname>>-peh-org`.
2. Create a Fine-Grained Personal Access Token authorized for use by the organization using the [GitHub PAT documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).
3. The following permissions are needed for the PAT to work with the exercises in this book:
   - Access to all repositories in your organization (not your personal account)
   - Administration: Read & Write
   - Commit statuses: Read & Write
   - Contents: Read & Write
   - Custom Properties: Read & Write
   - Metadata: Read-Only
4. Take note of this token for now, we will keep it in a secret store later.

> [!WARNING]
> **Common pitfalls to watch out for**
> - Not enabling SSO and 2FA creates a weak security posture and risks losing access to your files.
> - Skipping branch protections can lead to accidental merges into main.
> - Mixing personal repos with org repos fragments ownership and access.

### CircleCI Setup

1. Create a free CircleCI account using an email address at [circleci.com](https://circleci.com).
2. On the main page, create a new Organization (you can use the same name as your GitHub Organization).
3. In Organization Settings, configure a VCS connection to all repositories in your GitHub Organization account.
4. In Organization Settings → Self-hosted runners, agree to the terms and conditions for using a local runner. *We will set up the runner itself later using Kind.*

> [!WARNING]
> **Common pitfalls to watch out for**
> - Relying only on the UI for pipeline config instead of YAML in source control will lead to challenges with reproducibility.
> - Overusing the free tier without optimizing jobs more often than not will lead to hitting limits quickly.
> - Misconfigured self-hosted runners consume local resources and cause flaky builds.

### Bitwarden Setup

1. Create a free Bitwarden account at [bitwarden.com](https://bitwarden.com) using an email address.
2. Keep track of your BW master password. It will be needed later, and you will lose access to your vault without it.
3. Create an API Key via the documentation at [Bitwarden API Key docs](https://bitwarden.com/help/personal-api-key/).
4. Take note of the client ID and client secret for now; we will script using them as environment variables later.

> [!WARNING]
> **Common pitfalls to watch out for**
> - Teams continue storing secrets in configs instead of migrating to the vault.
> - Poor access scoping (all users see all secrets) creates compliance issues.
> - Secrets pulled incorrectly into pipelines show up in logs.

---

## Foundational Tools

These tools are used across multiple chapters and should be installed first. Instructions are provided for macOS, Linux (Ubuntu/Debian), and Windows. Where possible, we recommend using package managers (Homebrew for macOS, apt for Linux, and Chocolatey/winget for Windows) to simplify installation and updates.

### Package Managers

Package managers simplify installing and updating software. Set up the appropriate one for your operating system before installing other tools.

#### Homebrew (macOS)

Homebrew is the recommended package manager for macOS.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Chocolatey (Windows)

Open PowerShell as Administrator and run:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString("https://community.chocolatey.org/install.ps1"))
```

#### apt (Linux)

apt is pre-installed on Ubuntu/Debian. Keep it updated:

```bash
sudo apt update && sudo apt upgrade -y
```

### Git

Distributed version control system used throughout all chapters for source control and collaboration.

**macOS:**
```bash
brew install git
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install -y git
```

**Windows:**
```powershell
choco install git -y
# or: winget install Git.Git
```

**Verify installation:**
```bash
git --version
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Not configuring `user.name` and `user.email` globally leads to anonymous or misattributed commits.
> - Ignoring `.gitignore` best practices results in secrets, build artifacts, or IDE configs leaking into repos.
> - Working directly on main without feature branches makes collaboration difficult and rollbacks painful.

### Docker

Container runtime required for building images and running Kind clusters. Docker Desktop provides both the daemon and CLI.

**macOS:**
```bash
brew install --cask docker
# Then launch Docker Desktop from Applications
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io
sudo usermod -aG docker $USER  # Log out and back in after this
```

**Windows:**
```powershell
choco install docker-desktop -y
# Then launch Docker Desktop and enable WSL 2 backend
```

**Verify installation:**
```bash
docker --version
docker compose version
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Running Docker Desktop with default memory (2 GB) is insufficient for Kind clusters; increase to at least 4 GB.
> - Forgetting to prune unused images and volumes fills disk space quickly (use `docker system prune` regularly).
> - On Linux, skipping the `usermod -aG docker` step means every Docker command requires sudo.

### Python 3.10+ and UV

Python is the primary language for infrastructure code (Pulumi), tests (pytest), and platform scripts. UV is a fast Python package manager used throughout the book.

**macOS:**
```bash
brew install python@3.12 uv
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install -y python3 python3-pip python3-venv
pip install uv --break-system-packages
```

**Windows:**
```powershell
choco install python --version=3.12 -y
pip install uv
```

**Verify installation:**
```bash
python3 --version
uv --version
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Installing packages globally without virtual environments leads to version conflicts between chapters.
> - On Linux, forgetting `--break-system-packages` for pip causes cryptic installation failures.
> - Mixing `python` and `python3` commands across platforms causes path confusion; always use `python3` explicitly.

### Node.js 18+ and npm

Required for Backstage development, Express.js services, OpenTelemetry JS instrumentation, and template scaffolding.

**macOS:**
```bash
brew install node@18
```

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

**Windows:**
```powershell
choco install nodejs-lts -y
```

**Verify installation:**
```bash
node --version
npm --version
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Using a Node.js version that is too old (< 18) breaks Backstage and many modern npm packages.
> - Global npm installs without proper PATH configuration cause "command not found" errors.
> - Not using a version manager (nvm or fnm) makes switching between projects with different Node requirements difficult.

### kubectl

The Kubernetes command-line tool for interacting with clusters. Used in virtually every chapter.

**macOS:**
```bash
brew install kubectl
```

**Linux (Ubuntu/Debian):**
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

**Windows:**
```powershell
choco install kubernetes-cli -y
```

**Verify installation:**
```bash
kubectl version --client
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Having a kubectl version more than one minor version off from the cluster version causes subtle API incompatibilities.
> - Forgetting to switch contexts between clusters (kind vs. cloud) leads to running commands against the wrong environment.
> - Not setting a default namespace with `kubectl config set-context` means accidentally deploying to the default namespace.

### Kind (Kubernetes in Docker)

Creates local Kubernetes clusters using Docker containers. The primary local cluster tool used throughout the book.

**macOS:**
```bash
brew install kind
```

**Linux (Ubuntu/Debian):**
```bash
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind
```

**Windows:**
```powershell
choco install kind -y
```

**Verify installation:**
```bash
kind --version
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Not allocating enough Docker memory causes OOM kills when deploying multiple Helm charts to a Kind cluster.
> - Kind clusters do not survive Docker restarts; plan for recreating clusters and redeploying when Docker is restarted.
> - Port mapping must be configured at cluster creation time; you cannot add port mappings after the cluster is running.

### Helm

Kubernetes package manager for deploying charts (Istio, Backstage, Gatekeeper, OpenCost, Velero, and more).

**macOS:**
```bash
brew install helm
```

**Linux (Ubuntu/Debian):**
```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

**Windows:**
```powershell
choco install kubernetes-helm -y
```

**Verify installation:**
```bash
helm version
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Forgetting to run `helm repo update` before installing charts often installs stale or missing chart versions.
> - Not pinning chart versions in CI/CD means builds break silently when upstream charts introduce breaking changes.
> - Overriding too many default values without understanding the chart's structure leads to misconfigured deployments.

---

## Chapter-Specific Installation Instructions

The following sections detail additional tools needed for each chapter beyond the foundational tools listed above.

### Chapter 1: Laying the Groundwork

| Tool | Version | Purpose |
|------|---------|---------|
| Pulumi | ≥3.0 | Infrastructure as Code engine |
| Bitwarden CLI | ≥2024.1 | Secrets management |
| CircleCI CLI | Latest | CI/CD pipeline management |
| pre-commit | Latest | Git hook framework for code quality |
| pytest | ≥7.0 | Python unit testing |

#### Pulumi

Infrastructure as Code tool using Python. The CircleCI configuration in this chapter demonstrates Pulumi preview/apply workflows. Create a free account at [pulumi.com](https://pulumi.com) before installing the CLI.

**macOS:**
```bash
brew install pulumi/tap/pulumi
```

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://get.pulumi.com | sh
echo "export PATH=$HOME/.pulumi/bin:$PATH" >> ~/.bashrc && source ~/.bashrc
```

**Windows:**
```powershell
choco install pulumi -y
```

**Verify installation:**
```bash
pulumi version
pulumi login  # Authenticate with your Pulumi account
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Forgetting to run `pulumi login` before `pulumi up` causes the CLI to prompt interactively, breaking automation.
> - Not encrypting secrets with `pulumi config set --secret` exposes sensitive values in plain text in stack state.
> - Leaving orphaned stacks in the Pulumi console after deleting resources makes it hard to track what is actually deployed.

#### Bitwarden CLI

Command-line interface for Bitwarden password manager. Create a free account at [bitwarden.com](https://bitwarden.com) and generate an API key before use.

**macOS:**
```bash
brew install bitwarden-cli
```

**Linux (Ubuntu/Debian):**
```bash
sudo snap install bw
```

**Windows:**
```powershell
choco install bitwarden-cli -y
```

**Verify installation:**
```bash
bw --version
```

#### CircleCI CLI

Command-line tool for validating CircleCI configurations and managing pipelines. Create a free account at [circleci.com](https://circleci.com).

**macOS:**
```bash
brew install circleci
```

**Linux (Ubuntu/Debian):**
```bash
curl -fLSs https://raw.githubusercontent.com/CircleCI-CLI/circleci-cli/main/install.sh | bash
```

**Windows:**
```powershell
# Download from https://github.com/CircleCI-CLI/circleci-cli/releases
# Extract and add to PATH
```

**Verify installation:**
```bash
circleci version
circleci setup  # Configure with your API token
```

#### pre-commit

Framework for managing multi-language Git pre-commit hooks. Used to enforce commit message conventions, run linters, and validate configurations before code is committed.

**macOS:**
```bash
brew install pre-commit
```

**Linux (Ubuntu/Debian):**
```bash
pip3 install pre-commit --break-system-packages
```

**Windows:**
```powershell
pip3 install pre-commit
```

**Verify installation:**
```bash
pre-commit --version
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Not running `pre-commit install` after cloning a repo means hooks are never activated for that developer.
> - Overly strict hooks that take too long to run cause developers to bypass them with `--no-verify`.
> - Failing to pin hook versions in `.pre-commit-config.yaml` leads to inconsistent behavior across team members.

#### Python Testing and Quality Tools

Install the Python testing tools in a virtual environment or globally:

```bash
pip3 install pytest pytest-cov pyyaml
# On Linux, add --break-system-packages if installing globally
```

---

### Chapter 2: Building a Scalable Platform Runtime

| Tool | Version | Purpose |
|------|---------|---------|
| Flux CD | ≥2.0 | GitOps continuous delivery |
| Istio | ≥1.20 | Service mesh with mTLS |
| Kustomize | ≥5.0 | Kubernetes configuration management |
| bats-core | ≥1.10 | Bash Automated Testing System |

#### Flux CD

GitOps toolkit for Kubernetes. Flux continuously reconciles cluster state with Git repositories.

**macOS:**
```bash
brew install fluxcd/tap/flux
```

**Linux (Ubuntu/Debian):**
```bash
curl -s https://fluxcd.io/install.sh | sudo bash
```

**Windows:**
```powershell
choco install flux -y
# Or download from https://github.com/fluxcd/flux2/releases
```

**Verify installation:**
```bash
flux --version
flux check --pre  # Check prerequisites
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Not bootstrapping Flux with the correct GitHub token permissions causes silent sync failures.
> - Modifying resources directly with kubectl instead of through Git breaks the GitOps reconciliation loop.
> - Forgetting to set up Flux notifications means drift goes undetected for hours or days.

#### Istio (istioctl)

Service mesh providing mTLS encryption, traffic management, and observability. Install using istioctl.

**macOS:**
```bash
brew install istioctl
```

**Linux (Ubuntu/Debian):**
```bash
curl -L https://istio.io/downloadIstio | sh -
sudo mv istio-*/bin/istioctl /usr/local/bin/
```

**Windows:**
```powershell
# Download from https://github.com/istio/istio/releases
# Extract and add istioctl.exe to your PATH
```

**Verify installation:**
```bash
istioctl version
istioctl install --set profile=demo -y  # Install to cluster
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Installing Istio without resource limits can consume significant cluster memory (1-2 GB for the control plane).
> - Forgetting to label namespaces with `istio-injection=enabled` means sidecars are not injected into pods.
> - Upgrading Istio without following the canary upgrade process can cause brief traffic disruptions.

#### Kustomize

Template-free customization of Kubernetes YAML configurations.

**macOS:**
```bash
brew install kustomize
```

**Linux (Ubuntu/Debian):**
```bash
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
sudo mv kustomize /usr/local/bin/
```

**Windows:**
```powershell
choco install kustomize -y
```

**Verify installation:**
```bash
kustomize version
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Using the kubectl built-in kustomize (`kubectl apply -k`) may lag behind the standalone version and miss newer features.
> - Deeply nested overlays become hard to debug; keep the overlay hierarchy shallow (base + one or two overlays).
> - Forgetting to include new files in `kustomization.yaml` resources list means they are silently ignored.

#### bats-core

Testing framework for Bash scripts, used for infrastructure validation tests.

**macOS:**
```bash
brew install bats-core
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install -y bats
```

**Windows:**
```powershell
npm install -g bats
```

**Verify installation:**
```bash
bats --version
```

---

### Chapter 3: Securing Platform Access

| Tool | Version | Purpose |
|------|---------|---------|
| Keycloak | ≥22.0 | Identity and access management (OIDC/OAuth2) |
| OPA Gatekeeper | ≥3.14 | Kubernetes admission controller for policy enforcement |
| cert-manager | ≥1.13 | Automated TLS certificate management |

#### Keycloak

Open-source identity provider supporting OIDC, OAuth2, and SAML. Deploy to your Kind cluster using Helm.

**All platforms (Helm is cross-platform):**
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install keycloak bitnami/keycloak \
  --namespace keycloak --create-namespace \
  --set auth.adminUser=admin \
  --set auth.adminPassword=admin
```

**Verify installation:**
```bash
kubectl get pods -n keycloak
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Leaving the default admin/admin credentials in a shared environment is a critical security risk.
> - Not configuring persistent storage means Keycloak state (realms, users) is lost when the pod restarts.
> - Importing realm configurations manually via the UI instead of JSON exports makes setups non-reproducible.

#### OPA Gatekeeper

Policy controller for Kubernetes that enforces policies written in Rego at admission time.

**All platforms (Helm is cross-platform):**
```bash
helm repo add gatekeeper https://open-policy-agent.github.io/gatekeeper/charts
helm repo update
helm install gatekeeper gatekeeper/gatekeeper \
  --namespace gatekeeper-system --create-namespace \
  --set enableGenerateViolationEvents=true \
  --set constraintViolationsLimit=1000 \
  --set auditIntervalSeconds=60
```

**Verify installation:**
```bash
kubectl get pods -n gatekeeper-system
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Deploying constraints in enforce mode without testing first blocks legitimate workloads across the cluster.
> - Not using dryrun mode during initial rollout causes outages when policies unexpectedly reject valid deployments.
> - Forgetting to set `constraintViolationsLimit` high enough means Gatekeeper silently stops reporting after the default cap.

#### cert-manager

Automates TLS certificate management within Kubernetes clusters.

**All platforms (Helm is cross-platform):**
```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true
```

**Verify installation:**
```bash
kubectl get pods -n cert-manager
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Skipping `--set installCRDs=true` leaves cert-manager unable to create Certificate and Issuer resources.
> - Using the staging Let's Encrypt issuer without realizing it produces untrusted certificates in production.
> - Not monitoring certificate expiration means services silently break when certs expire.

---

### Chapter 4: Embedding Observability

| Tool | Version | Purpose |
|------|---------|---------|
| OpenTelemetry SDK | Latest | Telemetry instrumentation libraries (Python) |
| Prometheus | ≥2.45 | Metrics collection and storage |
| Grafana | ≥10.0 | Metrics visualization and dashboards |
| Jaeger | ≥1.50 | Distributed tracing backend (optional) |
| Loki | ≥2.9 | Log aggregation system (optional) |

#### Observability Stack (Helm Deployment)

The observability stack is best deployed to your Kind cluster using Helm charts.

**Prometheus and Grafana (kube-prometheus-stack):**
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - The kube-prometheus-stack chart is resource-heavy; on Kind clusters, disable components you do not need (e.g., alertmanager).
> - Default retention (15 days) fills disk quickly on small clusters; set `server.retention` to match your available storage.
> - Not creating ServiceMonitor resources means Prometheus never discovers your application metrics.

**Jaeger (optional):**
```bash
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm install jaeger jaegertracing/jaeger \
  --namespace observability --create-namespace
```

**Loki (optional):**
```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  --namespace observability --set grafana.enabled=false
```

#### Python OpenTelemetry Libraries

Install the Python OpenTelemetry SDK and exporters:

```bash
pip3 install opentelemetry-api opentelemetry-sdk \
  opentelemetry-exporter-otlp \
  opentelemetry-exporter-prometheus \
  prometheus-client flask
# On Linux, add --break-system-packages if installing globally
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Mixing OpenTelemetry SDK versions across packages causes import errors and missing attributes.
> - Not setting `OTEL_RESOURCE_ATTRIBUTES` for `service.name` means traces show up as "unknown_service" in Jaeger.
> - Forgetting to call `shutdown()` on TracerProvider in tests causes spans to be silently dropped.

---

### Chapter 5: Evaluating the User Experience

| Tool | Version | Purpose |
|------|---------|---------|
| ArgoCD | ≥2.9 | GitOps continuous deployment |
| Flask | ≥2.3 | Python web framework (demo app) |
| Express.js | ≥4.18 | Node.js web framework (instrumentation demo) |
| OpenTelemetry JS SDK | ≥1.17 | Node.js instrumentation |
| Winston | ≥3.11 | Node.js logging library |

#### ArgoCD

Declarative GitOps continuous delivery tool for Kubernetes. Used by the platform-deploy.sh script for GitOps-based deployment.

**Install ArgoCD to cluster:**
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

**Install CLI:**

**macOS:**
```bash
brew install argocd
```

**Linux (Ubuntu/Debian):**
```bash
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
```

**Windows:**
```powershell
choco install argocd-cli -y
```

**Verify installation:**
```bash
argocd version
kubectl get pods -n argocd
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Not retrieving the initial admin password (from `argocd-initial-admin-secret`) means you cannot log in after install.
> - Syncing applications with auto-sync enabled before policies are in place can deploy unreviewed changes.
> - ArgoCD's default resource tracking can conflict with Flux if both are installed in the same cluster.

#### Python Demo Application Dependencies

```bash
pip3 install flask pyyaml
# On Linux, add --break-system-packages if installing globally
```

#### Node.js Instrumentation Dependencies

```bash
npm install express winston
npm install @opentelemetry/sdk-node \
  @opentelemetry/auto-instrumentations-node \
  @opentelemetry/exporter-trace-otlp-http \
  @opentelemetry/exporter-metrics-otlp-http \
  @opentelemetry/resources \
  @opentelemetry/semantic-conventions
```

---

### Chapter 6: Accelerating Developer Experience with Backstage

| Tool | Version | Purpose |
|------|---------|---------|
| Backstage | ≥1.20 | Developer portal framework by Spotify |
| PostgreSQL | ≥14.0 | Database backend for Backstage |

#### Backstage

Internal developer portal providing a software catalog, TechDocs, and service scaffolding.

**Option 1: Deploy via Helm**
```bash
helm repo add backstage https://backstage.github.io/charts
helm install backstage backstage/backstage \
  --namespace backstage --create-namespace
```

**Option 2: Create local development instance**
```bash
npx @backstage/create-app@latest
```

**Verify installation:**
```bash
kubectl get pods -n backstage
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Backstage's `app-config.yaml` must be properly configured for your GitHub org; the default config will not discover your repos.
> - Running Backstage without PostgreSQL (using SQLite) works for development but fails under load and loses data on restart.
> - Plugin compatibility issues are common after Backstage upgrades; always check release notes before updating.

---

### Chapter 7: Self-Service Team Onboarding

| Tool | Version | Purpose |
|------|---------|---------|
| Flask | ≥2.3 | Python web framework (onboarding API) |
| @kubernetes/client-node | Latest | Kubernetes API client for Node.js |
| @octokit/rest | Latest | GitHub API client for Node.js |

Chapter 7 uses a dual-stack approach: the primary onboarding API is a Python/Flask application (`onboarding-api.py`), while the team provisioning service (`services/teamService.js`) demonstrates the Node.js equivalent.

**Python Onboarding API Dependencies:**
```bash
pip3 install flask pyyaml kubernetes
# On Linux, add --break-system-packages if installing globally
```

**Node.js Team Service Dependencies:**
```bash
npm install @kubernetes/client-node @octokit/rest
npm install --save-dev jest supertest
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - The Kubernetes Python client requires a valid kubeconfig; running inside a container needs in-cluster config setup.
> - GitHub PAT permissions must match the operations (repo creation, team management); insufficient scopes cause silent 403 errors.
> - Not making onboarding operations idempotent means retrying a failed request creates duplicate namespaces or RBAC bindings.

---

### Chapter 8: CI/CD as a Platform Service

| Tool | Version | Purpose |
|------|---------|---------|
| GitHub Actions | N/A | CI/CD workflow automation (GitHub-hosted) |
| Trivy | ≥0.48 | Container vulnerability scanner |

GitHub Actions workflows run on GitHub-hosted runners and do not require local installation. The chapter demonstrates reusable workflows and composite actions for platform-standardized CI/CD.

#### Trivy

Comprehensive security scanner for container images, file systems, and IaC configurations.

**macOS:**
```bash
brew install trivy
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install -y wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | \
  sudo tee /etc/apt/sources.list.d/trivy.list
sudo apt update && sudo apt install -y trivy
```

**Windows:**
```powershell
choco install trivy -y
```

**Verify installation:**
```bash
trivy --version
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Trivy's vulnerability database must be updated regularly; stale databases miss recently disclosed CVEs.
> - Scanning with `--severity CRITICAL` only hides important HIGH-severity findings that still need remediation.
> - Running Trivy in CI without caching the database download adds 30-60 seconds to every pipeline run.

**Python Dependencies:**
```bash
pip3 install pyyaml requests pytest
# On Linux, add --break-system-packages if installing globally
```

---

### Chapter 9: Self-Service Infrastructure with Crossplane

| Tool | Version | Purpose |
|------|---------|---------|
| Crossplane | ≥1.14 | Kubernetes-native infrastructure management |
| Crossplane CLI | ≥1.14 | CLI for building and pushing Crossplane packages |

#### Crossplane

Extends Kubernetes to manage external infrastructure resources using Custom Resource Definitions (XRDs) and Compositions.

**Install Crossplane to cluster:**
```bash
helm repo add crossplane-stable https://charts.crossplane.io/stable
helm repo update
helm install crossplane crossplane-stable/crossplane \
  --namespace crossplane-system --create-namespace
```

**Install CLI:**

**macOS:**
```bash
brew install crossplane/tap/crossplane
```

**Linux (Ubuntu/Debian):**
```bash
curl -sL https://raw.githubusercontent.com/crossplane/crossplane/master/install.sh | sh
sudo mv crossplane /usr/local/bin/
```

**Windows:**
```powershell
# Install CLI from GitHub Releases
```

**Verify installation:**
```bash
crossplane --version
kubectl get pods -n crossplane-system
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Not installing the correct cloud provider (e.g., provider-aws) before applying Compositions causes resources to hang in a pending state.
> - Crossplane provider credentials stored as plain Kubernetes Secrets without encryption at rest are a security risk.
> - XRD schema changes after initial deployment require careful migration; breaking changes invalidate existing claims.
> - Forgetting to apply PatchSets for governance tags means cloud resources are created without cost-allocation or ownership labels.

**Python Dependencies:**
```bash
pip3 install flask pyyaml kubernetes
# On Linux, add --break-system-packages if installing globally
```

---

### Chapter 10: Publishing Starter Kits

| Tool | Version | Purpose |
|------|---------|---------|
| Yeoman | Latest | Scaffolding tool for project generators |
| Renovate | Latest | Automated dependency and template upgrade management |
| Backstage CLI | Latest | Backstage template scaffolding |

#### Yeoman

Generic scaffolding system for creating project templates and generators. Used for CLI-based project generation in the scaffolding layer.

**All platforms:**
```bash
npm install -g yo
```

**Verify installation:**
```bash
yo --version
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Generators that hardcode file paths break on Windows due to path separator differences (use `path.join` instead).
> - Not supporting a non-interactive (`--no-insight`) mode makes generators unusable in CI/CD pipelines.
> - Failing to test generators with different option combinations leads to broken scaffolding for edge-case configurations.

#### Renovate

Automated dependency update tool that solves the "template drift" problem described in Section 10.5. When starter kit templates are updated, Renovate automatically opens pull requests in generated projects to pull in the latest improvements.

**Option 1: Install Renovate GitHub App (recommended)**
Visit https://github.com/apps/renovate and install on your repositories.

**Option 2: Self-hosted CLI for testing**
```bash
npm install -g renovate
```

**Verify installation:**
```bash
renovate --version  # Only needed for self-hosted option
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Not configuring a `renovate.json` in each repository means Renovate skips those repos entirely.
> - Auto-merging all Renovate PRs without tests in place can introduce breaking dependency updates silently.
> - Overly broad package rules (e.g., matching all dependencies) create PR noise that teams learn to ignore.

**Python Dependencies:**
```bash
pip3 install pyyaml requests pytest
# On Linux, add --break-system-packages if installing globally
```

---

### Chapter 11: Validating Compliance with Policy-as-Code

| Tool | Version | Purpose |
|------|---------|---------|
| OPA Gatekeeper | ≥3.14 | Kubernetes admission controller |
| conftest | ≥0.41 | Policy testing for configuration files |
| OPA CLI | ≥0.60 | Open Policy Agent for Rego testing |
| pre-commit | Latest | Git hook framework for shift-left validation |
| prometheus-client | Latest | Python library for custom Prometheus exporters |

OPA Gatekeeper installation is covered in [Chapter 3](#chapter-3-securing-platform-access). The additional tools for this chapter are:

#### conftest

Utility for testing structured data against Rego policies. Enables shift-left policy validation in development and CI pipelines.

**macOS:**
```bash
brew install conftest
```

**Linux (Ubuntu/Debian):**
```bash
wget https://github.com/open-policy-agent/conftest/releases/latest/download/conftest_Linux_x86_64.tar.gz
tar xzf conftest_Linux_x86_64.tar.gz
sudo mv conftest /usr/local/bin/
```

**Windows:**
```powershell
choco install conftest -y
# Or download from https://github.com/open-policy-agent/conftest/releases
```

**Verify installation:**
```bash
conftest --version
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Policies in the wrong directory (conftest expects `policy/` by default) cause "0 tests, 0 failures" with no actual validation.
> - Not using `--strict` mode in CI means warnings pass silently; only failures block the pipeline.
> - Rego policies that parse YAML incorrectly (e.g., missing `input.metadata`) give false positives on valid manifests.

#### OPA CLI

The Open Policy Agent command-line tool for authoring and unit-testing Rego policies.

**macOS:**
```bash
brew install opa
```

**Linux (Ubuntu/Debian):**
```bash
curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64
chmod +x opa && sudo mv opa /usr/local/bin/
```

**Windows:**
```powershell
choco install opa -y
# Or download from https://www.openpolicyagent.org/docs/latest/#running-opa
```

**Verify installation:**
```bash
opa version
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Writing Rego policies without unit tests (`opa test`) means policy logic errors are only caught at admission time in production.
> - Not using `opa fmt` to format policies leads to inconsistent style that makes code reviews harder.
> - Rego's default-deny semantics catch newcomers off guard; always start with explicit allow/deny rules.

**Python Dependencies:**
```bash
pip3 install prometheus-client kubernetes pyyaml
# On Linux, add --break-system-packages if installing globally
```

---

### Chapter 12: Optimizing Cost, Performance, and Scalability

| Tool | Version | Purpose |
|------|---------|---------|
| OpenCost | ≥1.108 | CNCF Kubernetes cost allocation (open-source) |
| Karpenter | ≥0.33 | Kubernetes-native node autoscaling and instance selection |
| VPA | Latest | Vertical Pod Autoscaler for rightsizing |
| Metrics Server | Latest | Cluster resource metrics for HPA/VPA |

> **Note:** HPA (Horizontal Pod Autoscaler) is built into every standard Kubernetes cluster and does not require separate installation. You only need the Metrics Server so HPA has data to work with.

#### OpenCost

CNCF sandbox project providing Kubernetes-native cost allocation. Requires Prometheus (installed in Chapter 4).

**All platforms (Helm is cross-platform):**
```bash
helm repo add opencost https://opencost.github.io/opencost-helm-chart
helm repo update
helm install opencost opencost/opencost \
  --namespace opencost --create-namespace \
  --set opencost.prometheus.internal.serviceName="monitoring-kube-prometheus-prometheus" \
  --set opencost.prometheus.internal.namespaceName="monitoring" \
  --set opencost.prometheus.internal.port=9090 \
  --set opencost.ui.enabled=true \
  --set opencost.exporter.defaultClusterId="platform-cluster"
```

**Verify installation:**
```bash
kubectl get pods -n opencost
# Web UI (port 9090) — open http://localhost:9090
kubectl port-forward -n opencost svc/opencost 9090:9090
# REST API (port 9003) — no web UI on this port
kubectl port-forward -n opencost svc/opencost 9003:9003
curl http://localhost:9003/allocation/compute?window=24h&aggregate=namespace
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - OpenCost requires Prometheus to be running and accessible; misconfigured Prometheus endpoints produce $0 cost reports.
> - Without custom pricing configured, OpenCost uses default on-demand AWS pricing which may not match your actual cloud costs.
> - On Kind clusters, OpenCost reports $0 for compute because there are no real cloud instances to price.

#### Karpenter

Kubernetes-native node autoscaler. Note: Karpenter is primarily designed for AWS EKS. For other cloud providers, use the Cluster Autoscaler.

```bash
helm repo add karpenter https://charts.karpenter.sh
helm repo update
helm install karpenter karpenter/karpenter \
  --namespace karpenter --create-namespace \
  --set settings.aws.clusterName=my-cluster
```

**Verify installation:**
```bash
kubectl get pods -n karpenter
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Karpenter requires specific IAM roles and instance profiles; missing permissions cause nodes to fail to launch.
> - Not setting resource limits on NodePools can lead to runaway scaling and unexpected cloud bills.
> - Karpenter does not work on Kind or local clusters; the exercises for Karpenter require an actual EKS cluster.

#### Vertical Pod Autoscaler (VPA)

VPA is not included in standard Kubernetes and must be installed separately. It provides resource request recommendations.

**All platforms (requires kubectl access to cluster):**
```bash
git clone https://github.com/kubernetes/autoscaler.git /tmp/autoscaler
kubectl apply -f /tmp/autoscaler/vertical-pod-autoscaler/deploy/
# Ignore v1beta1 CRD errors — they are harmless (old API versions)
```

**Verify installation:**
```bash
kubectl get pods -n kube-system | grep vpa
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - VPA in Auto mode restarts pods to apply new resource requests; this can disrupt stateful workloads.
> - VPA and HPA should not both target CPU on the same deployment; they will fight each other.
> - VPA recommendations take time to stabilize (24-48 hours of data); do not act on initial recommendations.

#### Metrics Server

Required for HPA and VPA functionality:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
# For Kind clusters, patch the deployment to skip TLS verification:
kubectl patch deployment metrics-server -n kube-system \
  --type='json' -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - On Kind clusters, Metrics Server fails without the `--kubelet-insecure-tls` arg; patch the deployment after install.
> - Metrics Server only stores the latest data point, not historical data; use Prometheus for historical metrics.

---

### Chapter 13: Resilience Automation

| Tool | Version | Purpose |
|------|---------|---------|
| Sloth | ≥0.11 | SLO-to-Prometheus rules generator |
| Velero | ≥1.12 | Kubernetes backup and disaster recovery |
| Chaos Mesh | ≥2.6 | Chaos engineering platform |

#### Go (required for Sloth)

Go is needed to install Sloth via `go install`. If you already have Go installed, skip this step.

**macOS:**
```bash
brew install go
```

**Linux (Ubuntu/Debian):**
```bash
# See https://go.dev/doc/install for the latest version
```

**Verify and configure PATH:**
```bash
go version
export PATH=$PATH:$(go env GOPATH)/bin
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - The `go install` command places binaries in `~/go/bin/` by default. If `which sloth` returns "not found" after installing Sloth, your Go bin directory is not in your PATH.
> - Add `export PATH=$PATH:~/go/bin` to your `~/.zshrc` or `~/.bashrc` to make it permanent.

#### Sloth

Generates Prometheus recording and alerting rules from SLO specifications.

**Option A — via Go (recommended):**
```bash
go install github.com/slok/sloth/cmd/sloth@latest
```

**Option B — direct binary download (no Go required):**

macOS (Apple Silicon):
```bash
curl -L https://github.com/slok/sloth/releases/download/v0.11.0/sloth-darwin-arm64 -o /usr/local/bin/sloth && chmod +x /usr/local/bin/sloth
```

macOS (Intel):
```bash
curl -L https://github.com/slok/sloth/releases/download/v0.11.0/sloth-darwin-amd64 -o /usr/local/bin/sloth && chmod +x /usr/local/bin/sloth
```

Linux:
```bash
curl -L https://github.com/slok/sloth/releases/download/v0.11.0/sloth-linux-amd64 -o /usr/local/bin/sloth && chmod +x /usr/local/bin/sloth
```

**Verify installation:**
```bash
sloth version
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - SLO specs with incorrect Prometheus query syntax produce rules that silently fail when loaded.
> - Not running `sloth validate` before applying rules means errors are only caught when Prometheus rejects the config.
> - Setting SLO targets too aggressively (e.g., 99.99%) on non-critical services creates unnecessary alert fatigue.

#### Velero

Backup, restore, and migrate Kubernetes resources and persistent volumes.

**macOS:**
```bash
brew install velero
```

**Linux (Ubuntu/Debian):**
```bash
curl -L -o velero.tar.gz https://github.com/vmware-tanzu/velero/releases/latest/download/velero-v1.12.0-linux-amd64.tar.gz
tar xzf velero.tar.gz
sudo mv velero-*/velero /usr/local/bin/
```

**Windows:**
```powershell
choco install velero -y
# Or download from https://github.com/vmware-tanzu/velero/releases
```

**Verify installation:**
```bash
velero version
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Velero backs up Kubernetes resources but not persistent volume data by default; you must configure volume snapshots separately.
> - Not testing restores regularly means your backup strategy is unverified and may fail when you need it most.
> - Backup schedules without retention policies fill cloud storage and increase costs over time.

#### Chaos Mesh

Cloud-native chaos engineering platform for Kubernetes with pod failure, network delay, and stress testing experiments.

**All platforms (Helm is cross-platform):**
```bash
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm repo update
helm install chaos-mesh chaos-mesh/chaos-mesh \
  --namespace chaos-mesh --create-namespace \
  --set chaosDaemon.runtime=containerd \
  --set chaosDaemon.socketPath=/run/containerd/containerd.sock
```

**Verify installation:**
```bash
kubectl get pods -n chaos-mesh
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - Running chaos experiments without namespace selectors can affect system namespaces (kube-system, monitoring) and crash the cluster.
> - Not setting experiment duration limits means a forgotten experiment keeps injecting failures indefinitely.
> - Chaos Mesh requires privileged DaemonSet access; some security-hardened clusters block its installation.
> - **Kind clusters:** Chaos Mesh defaults to 3 controller-manager replicas, which can exhaust memory on a single-node cluster. If pods stay `Pending` with `Insufficient memory`, scale down: `kubectl scale deployment chaos-controller-manager -n chaos-mesh --replicas=1`. Also delete namespaces from previous chapters to free memory.

---

### Chapter 14: AI-Augmented Platforms

| Tool | Version | Purpose |
|------|---------|---------|
| LangChain | ≥0.1 | LLM application framework |
| OpenAI API | N/A | LLM provider (requires API key) |
| ChromaDB | ≥0.4 | Vector database for embeddings |

#### Python AI/ML Libraries

Install the Python packages for the RAG pipeline, multi-agent system, and AI governance components:

```bash
pip3 install langchain langchain-openai langchain-community \
  chromadb sentence-transformers \
  openai tiktoken \
  prometheus-client kubernetes pyyaml
# On Linux, add --break-system-packages if installing globally
```

> [!WARNING]
> **Common pitfalls to watch out for**
> - LangChain's API changes frequently between minor versions; pin your version in `requirements.txt` to avoid breaking changes.
> - ChromaDB's default in-memory mode loses all embeddings on restart; configure persistent storage for anything beyond quick tests.
> - OpenAI API rate limits are easily hit when batch-processing documents for RAG; implement exponential backoff and request throttling.
> - Not setting `OPENAI_API_KEY` as an environment variable before running scripts causes immediate failures with opaque error messages.

#### OpenAI API Key

An OpenAI API key is required for the LLM components. Sign up at [platform.openai.com](https://platform.openai.com) and set the key as an environment variable:

**macOS / Linux:**
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
# Add to ~/.bashrc or ~/.zshrc for persistence
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY = "sk-your-api-key-here"
# Or set via System Properties > Environment Variables for persistence
```

---

## Troubleshooting

### Docker Desktop Not Starting

On Windows, ensure WSL 2 is enabled and the WSL 2 Linux kernel update package is installed. On macOS, ensure sufficient disk space and that Rosetta 2 is installed for Apple Silicon Macs (`softwareupdate --install-rosetta`).

### Kind Cluster Networking Issues

If pods cannot reach external networks, check your Docker network settings. On Linux, ensure iptables rules allow forwarding. On macOS/Windows, increase Docker Desktop memory allocation to at least 4 GB.

### Helm Chart Installation Failures

Always run `helm repo update` before installing charts. If a chart fails due to resource constraints, check that your Kind cluster has sufficient CPU and memory. Consider creating a multi-node Kind cluster for production-like setups.

### Python Package Conflicts

Use virtual environments to isolate dependencies per chapter. Create one with:

```bash
python3 -m venv .venv && source .venv/bin/activate
# On Windows: .venv\Scripts\activate
```

This avoids conflicts between chapters that may use different versions of the same package.

### Windows Path Issues

After installing tools via Chocolatey, you may need to restart your terminal for PATH changes to take effect. If a command is not found, verify the tool's install location is in your system PATH.

---

## Quick Reference: Tools by Chapter

The following table provides a quick lookup for which tools are needed per chapter. An asterisk (*) indicates the tool is first introduced in that chapter.

| Chapter | Tools Required (* = first introduced) |
|---------|---------------------------------------|
| 1 | Git, Docker, Python/UV, Pulumi*, Bitwarden CLI*, CircleCI CLI*, pre-commit*, pytest |
| 2 | Flux CD*, Istio*, Kustomize*, bats-core*, Kind, kubectl, Helm |
| 3 | Keycloak*, OPA Gatekeeper*, cert-manager* |
| 4 | OpenTelemetry SDK*, Prometheus*, Grafana*, Jaeger*, Loki* |
| 5 | ArgoCD*, Flask, Express.js*, Winston*, OTEL JS SDK* |
| 6 | Backstage*, PostgreSQL |
| 7 | Flask, @kubernetes/client-node*, @octokit/rest* |
| 8 | GitHub Actions, Trivy* |
| 9 | Crossplane* |
| 10 | Yeoman*, Renovate*, Backstage CLI |
| 11 | conftest*, OPA CLI*, pre-commit, prometheus-client* |
| 12 | OpenCost*, Karpenter*, VPA*, Metrics Server* |
| 13 | Go*, Sloth*, Velero*, Chaos Mesh* |
| 14 | LangChain*, OpenAI API*, ChromaDB* |

> **Note:** All chapters assume the foundational tools (Git, Docker, Python, Node.js, kubectl, Kind, and Helm) are already installed. See the [Foundational Tools](#foundational-tools) section at the beginning of this appendix.

**Companion Website:** For the latest installation scripts, version updates, and additional resources, visit https://peh-packt.platformetrics.com/
