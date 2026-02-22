# The Platform Engineer's Handbook — Companion Code

This repository contains the companion code for all 14 chapters plus Appendix A of *The Platform Engineer's Handbook* (Packt Publishing). Each chapter lives in its own `ChN/code/` folder with a dedicated `README.md` covering step-by-step instructions, prerequisites, and code-to-chapter mappings.

Before diving into individual chapters, read through this document to get your workstation ready and to understand how certain tools thread across the entire book.

---

## Foundational Tools

Chapter 1 covers Python, Git, Bitwarden CLI, Pulumi basics, and pre-commit. The tools below are **not** set up in Chapter 1 but are required by two or more later chapters. Install them once and you're covered for the rest of the book.

### Kubernetes & Container Runtime

| Tool | Version | Install | Used In |
|------|---------|---------|---------|
| Docker | 20.10+ | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) | Ch5, Ch8, Ch10, Ch13 |
| Kind | 0.20+ | `brew install kind` / `go install sigs.k8s.io/kind` | Ch2 (creates your first cluster) |
| kubectl | 1.26+ | `brew install kubectl` / [kubernetes.io/docs/tasks/tools](https://kubernetes.io/docs/tasks/tools/) | Ch2–Ch13 |
| Helm | 3.0+ | `brew install helm` / [helm.sh/docs/intro/install](https://helm.sh/docs/intro/install/) | Ch2, Ch6, Ch8, Ch9, Ch10, Ch12, Ch13 |
| Kustomize | 5.0+ | `brew install kustomize` | Ch2 |

Docker and kubectl are used in almost every chapter from Chapter 2 onwards. Install these first.

### GitOps & Deployment

| Tool | Version | Install | Used In |
|------|---------|---------|---------|
| Flux CLI | 2.0+ | `brew install fluxcd/tap/flux` / `curl -s https://fluxcd.io/install.sh \| sudo bash` | Ch2 |
| Istio (`istioctl`) | 1.10+ | [istio.io/latest/docs/setup/getting-started](https://istio.io/latest/docs/setup/getting-started/) | Ch2, Ch8 |

### Policy & Security

| Tool | Version | Install | Used In |
|------|---------|---------|---------|
| OPA Gatekeeper | 3.14+ | Installed via Helm into the cluster | Ch3, Ch11 |
| conftest | 0.41+ | `brew install conftest` | Ch11 |
| OPA CLI | Latest | `brew install opa` | Ch11 |
| cert-manager | Latest | Installed via Helm into the cluster | Ch3, Ch6 |

### Observability

| Tool | Version | Install | Used In |
|------|---------|---------|---------|
| Prometheus | 2.30+ | Installed via Helm (kube-prometheus-stack) | Ch4, Ch8, Ch11, Ch12, Ch13 |
| Grafana | 8.0+ | Bundled with kube-prometheus-stack | Ch4, Ch11, Ch12 |

### Infrastructure & Platform

| Tool | Version | Install | Used In |
|------|---------|---------|---------|
| Pulumi | 3.0+ | `brew install pulumi/tap/pulumi` / `curl -fsSL https://get.pulumi.com \| sh` | Ch1, Ch2 |
| Crossplane + CLI | 1.14+ | Installed via Helm; CLI: `curl -sL https://raw.githubusercontent.com/crossplane/crossplane/master/install.sh \| sh` | Ch9 |
| Backstage | 1.20+ | `npx @backstage/create-app@latest` | Ch6, Ch10 |
| Keycloak | 20+ | Docker image or Helm chart | Ch3, Ch6 |

### Node.js Ecosystem

| Tool | Version | Install | Used In |
|------|---------|---------|---------|
| Node.js | 20+ | [nodejs.org](https://nodejs.org/) | Ch5, Ch7, Ch10 |
| npm | 9+ | Bundled with Node.js | Ch5, Ch7, Ch10 |
| Yeoman | Latest | `npm install -g yo` | Ch10 |
| Renovate | Latest | GitHub App (recommended) or `npm install -g renovate` | Ch10 |

### Resilience & Cost (Chapters 12–13)

| Tool | Version | Install | Used In |
|------|---------|---------|---------|
| Sloth | Latest | `go install github.com/slok/sloth/cmd/sloth@latest` | Ch13 |
| Velero | 1.12+ | `brew install velero` / [velero.io/docs/install-overview](https://velero.io/docs/main/basic-install/) | Ch13 |
| Chaos Mesh | Latest | Installed via Helm | Ch13 |
| OpenCost | Latest | Installed via `install-opencost.sh` (Ch12) | Ch12 |
| Metrics Server | Latest | `kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml` | Ch12 |

### AI & ML (Chapter 14)

| Tool | Version | Install | Used In |
|------|---------|---------|---------|
| LangChain | 0.1+ | `pip install langchain` | Ch14 |
| ChromaDB | 0.3.21+ | `pip install chromadb` | Ch14 |
| Ollama (optional) | Latest | [ollama.ai](https://ollama.ai/) | Ch14 |

---

## Tools That Thread Across Chapters

Several tools are introduced in an early chapter and then quietly expected in later ones. If you skip a chapter or forget to install something, you may hit missing-dependency errors further down the line. This section calls out those cross-cutting tools so you can keep track of them.

### Bitwarden CLI — Secrets Management

**Introduced:** Chapter 1 (setup + `upload-secrets.sh`)
**Shared helper:** `Ch1/code/scripts/bw-helper.sh`

Bitwarden is the book's secrets manager. Chapter 1 walks you through account creation and the CLI install, then each chapter below has a `load-secrets.sh` script that pulls credentials from your vault instead of requiring manual `export` commands.

| Chapter | Script | Vault Item | Secrets Loaded |
|---------|--------|------------|----------------|
| Ch3 | `load-secrets.sh` | `peh-keycloak` | `KEYCLOAK_ADMIN`, `KEYCLOAK_PASSWORD`, `KEYCLOAK_URL` |
| Ch7 | `load-secrets.sh` | `peh-github` | `GITHUB_TOKEN`, `GITHUB_ORG` |
| Ch9 | `load-secrets.sh` | `peh-aws` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` |
| Ch10 | `load-secrets.sh` | `peh-backstage` | `BACKSTAGE_URL`, `BACKSTAGE_TOKEN` |
| Ch14 | `load-secrets.sh` | `peh-openai` | `OPENAI_API_KEY`, `PINECONE_API_KEY` |

Every `load-secrets.sh` sources the shared `bw-helper.sh` from Chapter 1. If you chose not to use Bitwarden, each chapter README also shows the manual `export` commands.

### Pulumi — Infrastructure as Code

**Introduced:** Chapter 1 (CircleCI workflow references it)
**Hands-on use:** Chapter 2 (Kind cluster provisioning, EKS alternative)

Pulumi is set up early as the book's IaC engine. Chapter 2 is where you first run `pulumi up` to provision a cluster. After Chapter 2, infrastructure work shifts to Kubernetes-native tools (Helm, Kustomize, Crossplane), but the Pulumi concepts carry through whenever you need to stand up or tear down cloud resources.

### OPA / Gatekeeper — Policy Enforcement

**Introduced:** Chapter 3 (cluster admission policies)
**Returns in:** Chapter 11 (full policy-as-code framework with conftest, Rego testing, CI integration)

Chapter 3 deploys Gatekeeper as part of cluster security. Chapter 11 goes much deeper with constraint templates, conftest for shift-left validation, and Prometheus-based compliance dashboards. If you skipped Chapter 3's Gatekeeper install, Chapter 11 provides its own Helm-based setup.

### Prometheus + Grafana — Observability Stack

**Introduced:** Chapter 4 (embedding observability, OpenTelemetry instrumentation)
**Used through:** Chapter 8 (CI/CD metrics), Chapter 11 (compliance dashboards), Chapter 12 (cost and scaling metrics), Chapter 13 (SLO monitoring)

The monitoring stack from Chapter 4 is assumed to be running in later chapters. If you're jumping straight to Chapter 12 or 13, make sure Prometheus is deployed in your cluster first.

### Keycloak — Identity Provider

**Introduced:** Chapter 3 (securing platform access)
**Referenced in:** Chapter 6 (Backstage SSO integration)

Chapter 3 walks through Keycloak deployment and OIDC configuration. Chapter 6 expects Keycloak to be running when setting up Backstage authentication. The `load-secrets.sh` in Chapter 3 pulls Keycloak admin credentials from Bitwarden.

### Backstage — Developer Portal

**Introduced:** Chapter 6 (full setup and configuration)
**Referenced in:** Chapter 10 (publishing starter kits to the Backstage catalog)

Chapter 6 deploys Backstage and configures the software catalog. Chapter 10 publishes Yeoman-generated starter kits into that same Backstage instance. If you're jumping to Chapter 10, you need a running Backstage from Chapter 6.

### cert-manager — TLS Certificates

**Introduced:** Chapter 3 (installed as part of cluster security)
**Referenced in:** Chapter 6 (TLS for Backstage ingress)

Installed once in Chapter 3 and assumed present when later chapters expose services through HTTPS ingresses.

---

## Recommended Install Order

If you want to set everything up before starting the book, here is a minimal workstation bootstrap. Detailed install instructions for each tool are in Appendix A.

```bash
# 1. Languages & package managers (Ch1+)
#    Python 3.8+, Node.js 20+, Go (for Sloth)

# 2. Container & Kubernetes basics (Ch2+)
brew install docker kind kubectl helm kustomize

# 3. GitOps (Ch2)
brew install fluxcd/tap/flux

# 4. IaC (Ch1–Ch2)
brew install pulumi/tap/pulumi

# 5. Policy tools (Ch11)
brew install conftest opa

# 6. Secrets management (Ch1, used in Ch3/7/9/10/14)
npm install -g @bitwarden/cli

# 7. Resilience tools (Ch13)
brew install velero
go install github.com/slok/sloth/cmd/sloth@latest
```

Everything else (Prometheus, Grafana, Gatekeeper, cert-manager, Crossplane, Chaos Mesh, OpenCost, Backstage, Keycloak) is deployed **into the cluster** via Helm or kubectl as part of the chapter walkthroughs.

---

## Repository Layout

```
├── README.md                  ← You are here
├── Ch1/code/                  ← Laying the Groundwork
├── Ch2/code/                  ← Scalable Platform Runtime
├── Ch3/code/                  ← Securing Platform Access
├── Ch4/code/                  ← Embedding Observability
├── Ch5/code/                  ← Evaluating User Experience
├── Ch6/code/                  ← Developer Portal (Backstage)
├── Ch7/code/                  ← Self-Service Onboarding
├── Ch8/code/                  ← CI/CD as a Platform Service
├── Ch9/code/                  ← Self-Service Infrastructure
├── Ch10/code/                 ← Publishing Starter Kits
├── Ch11/code/                 ← Policy-as-Code
├── Ch12/code/                 ← Cost, Performance & Scale
├── Ch13/code/                 ← Resilience Automation
└── Ch14/code/                 ← AI-Augmented Platforms
```

Each chapter folder contains its own `README.md` with full prerequisites, step-by-step instructions, expected outputs, and troubleshooting.

---

## Companion Website

Additional resources, videos, case studies, and interactive tools are available at:

**https://peh-packt.platformetrics.com/**
