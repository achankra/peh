# The Platform Engineer's Handbook — Companion Code

This repository contains the companion code for all 14 chapters plus Appendix A of *The Platform Engineer's Handbook* (Packt Publishing). Each chapter lives in its own `ChNN/` folder with a dedicated `README.md` covering step-by-step instructions, prerequisites, and code-to-chapter mappings.

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
| VPA | Latest | `git clone https://github.com/kubernetes/autoscaler.git && kubectl apply -f autoscaler/vertical-pod-autoscaler/deploy/` | Ch12 |
| Metrics Server | Latest | `kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml` | Ch12 |

> **Kind cluster note:** Metrics Server requires a TLS patch on Kind clusters:
> ```bash
> kubectl patch deployment metrics-server -n kube-system \
>   --type='json' -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
> ```

### AI & ML (Chapter 14)

| Tool | Version | Install | Used In |
|------|---------|---------|---------|
| LangChain | 0.1+ | `pip3 install langchain` | Ch14 |
| ChromaDB | 0.3.21+ | `pip3 install chromadb` | Ch14 |
| Ollama (optional) | Latest | [ollama.ai](https://ollama.ai/) | Ch14 |

---

## Tools That Thread Across Chapters

Several tools are introduced in an early chapter and then quietly expected in later ones. If you skip a chapter or forget to install something, you may hit missing-dependency errors further down the line. This section calls out those cross-cutting tools so you can keep track of them.

### Bitwarden CLI — Secrets Management

**Introduced:** Chapter 1 (setup + `upload-secrets.sh`)
**Shared helper:** `Ch01/scripts/bw-helper.sh`

Bitwarden is the book's secrets manager. Chapter 1 walks you through account creation and the CLI install, then each chapter below has a `load-secrets.sh` script that pulls credentials from your vault instead of requiring manual `export` commands.

| Chapter | Script | Vault Item | Secrets Loaded |
|---------|--------|------------|----------------|
| Ch3 | `load-secrets.sh` | `peh-keycloak` | `KEYCLOAK_ADMIN`, `KEYCLOAK_PASSWORD`, `KEYCLOAK_URL` |
| Ch7 | `load-secrets.sh` | `peh-github` | `GITHUB_TOKEN`, `GITHUB_ORG` |
| Ch9 | `load-secrets.sh` | `peh-db` | `POSTGRES_PASSWORD` |
| Ch10 | `load-secrets.sh` | `peh-backstage` | `BACKSTAGE_URL`, `BACKSTAGE_TOKEN` |
| Ch14 | `load-secrets.sh` | `peh-openai` | `OPENAI_API_KEY`, `PINECONE_API_KEY` |

Every `load-secrets.sh` sources the shared `bw-helper.sh` from Chapter 1. If you chose not to use Bitwarden, each chapter README also shows the manual `export` commands.

**Getting your Bitwarden API credentials for the `.env` file:**

1. Log in at [vault.bitwarden.com](https://vault.bitwarden.com)
2. Click your profile icon (top-right) → **Account Settings**
3. Scroll to **Keys** → **API Key** → click **View API Key**
4. Copy `client_id` and `client_secret` into `Ch01/.env`

```
BW_CLIENTID=user.a1b2c3d4-e5f6-7890-abcd-ef1234567890   ← your client_id
BW_CLIENTSECRET=K4xQz9LmN8pR2wY6vT0sA3bF7hJ5dG1c       ← your client_secret
BW_PASSWORD=YourActualMasterPassword                      ← same password you use to log in
```

The `BW_CLIENTID` always starts with `user.` followed by a UUID. The `BW_CLIENTSECRET` is a random alphanumeric string generated by Bitwarden. `BW_PASSWORD` is your master password.

### Pulumi — Infrastructure as Code

**Introduced:** Chapter 1 (CircleCI workflow references it)
**Hands-on use:** Chapter 2 (Kind cluster provisioning)

Pulumi is set up early as the book's IaC engine. Chapter 2 is where you first run `pulumi up` to provision a cluster. After Chapter 2, infrastructure work shifts to Kubernetes-native tools (Helm, Kustomize, Crossplane), but the Pulumi concepts carry through whenever you need to stand up or tear down cloud resources.

### CI/CD Tools — CircleCI and GitHub Actions

**CircleCI:** Chapter 1 (infrastructure deployment pipelines with Pulumi)
**GitHub Actions:** Chapter 8 (application CI/CD — reusable workflows, progressive delivery, rollback)

The book intentionally uses both to demonstrate that a platform team should be CI-tool-agnostic. Chapter 1's CircleCI config shows infrastructure pipeline patterns (preview/approve/apply), while Chapter 8's GitHub Actions shows application delivery patterns (build/test/scan/deploy with blue-green and canary strategies). The underlying patterns — reusable workflows, approval gates, progressive delivery — translate across any CI/CD system.

### OPA / Gatekeeper — Policy Enforcement

**Introduced:** Chapter 3 (cluster admission policies)
**Returns in:** Chapter 11 (full policy-as-code framework with conftest, Rego testing, CI integration)

Chapter 3 deploys Gatekeeper as part of cluster security. Chapter 11 goes much deeper with constraint templates, conftest for shift-left validation, and Prometheus-based compliance dashboards. If you skipped Chapter 3's Gatekeeper install, Chapter 11 provides its own Helm-based setup.

> **Important for Chapter 12:** Chapter 12 exercises (OpenCost, VPA) deploy workloads via Helm. The Gatekeeper constraints from Chapter 11 must use `enforcementAction: dryrun` (the default in the companion code) to avoid blocking those Helm installs. If you switched any constraints to `deny` for testing in Chapter 11, switch them back to `dryrun` before starting Chapter 12.

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

## Surviving Docker & Kind Restarts

Kind clusters run as Docker containers, so they **do not survive Docker Desktop restarts**. If you reboot your Mac, quit Docker, or Docker crashes, you will need to recreate your cluster and redeploy any in-cluster services. Here's how to get back up and running quickly.

### 1. Start Docker Desktop

```bash
open -a Docker          # macOS
# On Linux: sudo systemctl start docker
# On Windows: launch Docker Desktop from Start Menu
```

Wait 30–60 seconds for Docker to fully initialize, then verify:

```bash
docker ps               # Should return an empty table (no error)
```

### 2. Check If Your Kind Cluster Survived

```bash
kind get clusters
```

**If your cluster is listed** (e.g., `peh`), the container may just be stopped. Try restarting it:

```bash
docker start peh-control-plane    # Replace "peh" with your cluster name
kubectl cluster-info               # Verify the API server is reachable
```

**If no clusters are listed**, you need to recreate:

```bash
kind create cluster --name peh --config Ch02/kind-config.yaml
```

> **Note:** If you don't have a `kind-config.yaml`, create one with ingress port mappings:
> ```yaml
> kind: Cluster
> apiVersion: kind.x-k8s.io/v1alpha4
> nodes:
> - role: control-plane
>   kubeadmConfigPatches:
>   - |
>     kind: InitConfiguration
>     nodeRegistration:
>       kubeletExtraArgs:
>         node-labels: "ingress-ready=true"
>   extraPortMappings:
>   - containerPort: 80
>     hostPort: 8080
>     protocol: TCP
>   - containerPort: 443
>     hostPort: 8443
>     protocol: TCP
> ```

### 3. Redeploy In-Cluster Services

After recreating a cluster, all Helm releases and deployed workloads are gone. Redeploy what you need for your current chapter:

```bash
# Monitoring stack (Ch4+) — needed by Ch4, Ch8, Ch11, Ch12, Ch13
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

# Gatekeeper (Ch3, Ch11)
helm repo add gatekeeper https://open-policy-agent.github.io/gatekeeper/charts
helm install gatekeeper gatekeeper/gatekeeper \
  --namespace gatekeeper-system --create-namespace

# cert-manager (Ch3, Ch6)
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace --set installCRDs=true

# Crossplane (Ch9)
helm repo add crossplane-stable https://charts.crossplane.io/stable
helm install crossplane crossplane-stable/crossplane \
  --namespace crossplane-system --create-namespace

# Keycloak (Ch3, Ch6) — use port 8180 to avoid Kind port conflict
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install keycloak bitnami/keycloak \
  --namespace keycloak --create-namespace \
  --set auth.adminUser=admin --set auth.adminPassword=admin
```

Only install what your current chapter requires — you don't need everything at once.

### 4. Verify and Resume

```bash
kubectl get pods -A              # Check all pods are Running
kubectl get nodes                # Should show one Ready node
```

Then re-run any `kubectl port-forward` commands from your chapter's README. For example, for Chapter 4:

```bash
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090 &
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80 &

# Retrieve the Grafana admin password
kubectl get secret monitoring-grafana -n monitoring -o jsonpath='{.data.admin-password}' | base64 -d; echo
```

Open [http://localhost:3000](http://localhost:3000) and log in with username `admin` and the password from the command above.

> **Tip:** If you're doing multiple recording sessions across days, consider leaving Docker Desktop running between sessions to avoid full cluster recreation.

---

## Repository Layout

```
├── README.md                  ← You are here
├── Appendix-A-Installation-Instructions.docx
├── Ch01/                      ← Laying the Groundwork
├── Ch02/                      ← Scalable Platform Runtime
├── Ch03/                      ← Securing Platform Access
├── Ch04/                      ← Embedding Observability
├── Ch05/                      ← Evaluating User Experience
├── Ch06/                      ← Developer Portal (Backstage)
├── Ch07/                      ← Self-Service Onboarding
├── Ch08/                      ← CI/CD as a Platform Service
├── Ch09/                      ← Self-Service Infrastructure
├── Ch10/                      ← Publishing Starter Kits
├── Ch11/                      ← Policy-as-Code
├── Ch12/                      ← Cost, Performance & Scale
├── Ch13/                      ← Resilience Automation
└── Ch14/                      ← AI-Augmented Platforms
```

Each `ChNN/` folder contains its own `README.md` with full prerequisites, step-by-step instructions, expected outputs, and troubleshooting.

---

## Companion Website

Additional resources, videos, case studies, and interactive tools are available at:

**https://peh-packt.platformetrics.com/**
