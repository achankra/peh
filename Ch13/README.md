# Chapter 13: Resilience Automation

## Chapter Overview

This chapter demonstrates production-ready patterns for implementing resilience automation through three interconnected pillars:

1. **SLO-as-Code**: Define, measure, and enforce Service Level Objectives using Sloth and Prometheus
2. **Chaos Engineering**: Proactively test system resilience with controlled failure injection
3. **Disaster Recovery**: Automate backup, restore, and DR validation procedures

The code in this directory implements a complete resilience automation platform enabling:
- Quantifying reliability requirements through SLIs and error budgets
- Validating system behavior under failure conditions
- Automating disaster recovery procedures and RTO/RPO compliance
- Making data-driven deployment decisions based on error budget consumption

## Code-to-Chapter Mapping

### SLO Configuration Files

| File | Chapter Reference | Purpose |
|------|-------------------|---------|
| **sloth-auth-service-slo.yaml** | Listing 13.1 | Auth service SLO specification matching manuscript example (99.95% availability, 95th percentile latency) |
| **sloth-slo-spec.yaml** | Section 13.2 | Extended Sloth SLO spec demonstrating availability, latency, and throughput SLO definitions with error budget alerting |
| **slo-definitions.yaml** | Section 13.2 | ConfigMap containing Prometheus recording rules and alerting rules for SLI calculations and error budget tracking |
| **generate-slo-rules.sh** | Section 13.2 | Bash script to generate Prometheus recording/alerting rules from Sloth SLO specifications |
| **slo-dashboard.json** | Section 13.2 | Grafana dashboard JSON for visualizing SLO compliance, error budget consumption, and burn rates |

### Backup and Disaster Recovery Files

| File | Chapter Reference | Purpose |
|------|-------------------|---------|
| **velero-schedule.yaml** | Listing 13.2 | Kubernetes Schedule resources defining daily (2 AM) and hourly (production) automated backups with 7-day and 3-day retention |
| **velero-storage-location.yaml** | Section 13.3 | Backup storage configuration using MinIO (S3-compatible) running inside the Kind cluster, including MinIO deployment, credential secret, and bucket setup job |
| **backup-config-annotation.yaml** | Listing 13.2 | Deployment example with Velero backup hooks (pre/post-backup) demonstrating database quiescing and graceful backup preparation |
| **backup-automation.py** | Section 13.3 | Python orchestration script for Velero backup management: create backups, validate integrity, check freshness, cleanup old backups |
| **velero-dr-commands.sh** | Section 13.3 | Automated DR drill script that creates backup, simulates disaster (deletes namespaces), restores from backup, and measures actual RTO |
| **disaster-recovery-plan.py** | Section 13.3 | DR validation framework checking backup freshness, RTO/RPO compliance, and readiness for disaster scenarios |
| **restore-validation.sh** | Section 13.3 | Automated restore validation script: performs test restore to a temporary namespace, verifies pod health and service availability, measures actual RTO, and cleans up. Suitable for weekly automated DR validation runs. |
| **backup-self-service.yaml** | Section 13.3 | Self-service backup labeling pattern enabling development teams to opt into backup automation through simple Kubernetes labels |
| **platform-backup-config/values.yaml** | Section 13.3 | Helm values file for production Velero deployment: MinIO as S3-compatible local storage, daily + hourly backup schedules, retention policies, pre/post-backup hooks, Prometheus monitoring, and alert rules |

### Chaos Engineering Files

| File | Chapter Reference | Purpose |
|------|-------------------|---------|
| **chaos-network-delay.yaml** | Listing 13.3 | NetworkChaos experiment injecting 100ms latency with 10ms jitter (runs Mondays 9 AM for 5 minutes) |
| **chaos-mesh-pod-failure.yaml** | Section 13.4 | Comprehensive PodChaos experiments: single pod kill, 25% pod failure, all replicas, container kill, and scheduled pod failure |
| **chaos-experiment-pod-kill.yaml** | Section 13.4 | Extended pod kill experiments compatible with both Chaos Mesh and LitmusChaos, including advanced configurations |
| **chaos-experiment-network.yaml** | Section 13.4 | Network chaos experiments: latency injection, packet loss, bandwidth limiting, packet corruption, duplication with port-specific targeting |
| **chaos-workflow.yaml** | Section 13.4 | Multi-stage chaos workflows: resilience-test (pod failure → network delay → recovery check), cascading failures, comprehensive resilience testing |
| **chaos-runner.py** | Section 13.4 | Python orchestrator for chaos experiments: create/run/monitor experiments, collect Prometheus metrics, generate resilience reports |
| **test-resilience.py** | Section 13.5 | Test suite validating SLO specs, chaos experiments, backup configurations, and dashboard JSON structure |

## Prerequisites

### Running This Chapter Standalone

> If you are jumping into this chapter without completing earlier chapters, use these commands to set up the infrastructure dependencies. If you already have them running, skip this section.

> **Note:** The resilience tools (Velero, Chaos Mesh) and monitoring stack are all deployed inside the Kind cluster. No cloud credentials needed.

```bash
# 1. Start Docker Desktop (macOS: open from Applications or Spotlight)
open -a "Docker"
# Wait for the Docker engine to start before continuing

# 2. Create a Kind cluster (skip if you already have one)
kind get clusters                       # Check for existing clusters
kind create cluster --name platform-dev # Create one if none listed
kubectl get nodes                       # Verify node(s) are Ready

# Install Prometheus + Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack --version 92.1.1 --namespace monitoring --create-namespace --wait

# Install Velero + MinIO
helm repo add vmware-tanzu https://vmware-tanzu.github.io/helm-charts
helm repo update
helm install velero vmware-tanzu/velero --version 12.2.1 --namespace velero --create-namespace

# Install Chaos Mesh
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm repo update
helm install chaos-mesh chaos-mesh/chaos-mesh --version 2.8.4 --namespace chaos-mesh --create-namespace

```

### Required Tools

1. **Go** (1.21+) - Required to install Sloth
   ```bash
   # macOS
   brew install go

   # Linux
   # See https://go.dev/doc/install
   ```
   After installing Go, add its bin directory to your PATH:
   ```bash
   export PATH=$PATH:$(go env GOPATH)/bin
   ```
   Add this line to your `~/.zshrc` or `~/.bashrc` to make it permanent.

2. **Sloth** - SLO-as-Code Prometheus rule generator
   ```bash
   go install github.com/slok/sloth/cmd/sloth@v0.11.0
   ```
   > **Important:** The `go install` command places the binary in `~/go/bin/`. If `which sloth` returns "not found" after install, your Go bin directory is not in your PATH. Run `export PATH=$PATH:~/go/bin` (and add it to your shell profile).

   **Alternative (no Go required) — download the binary directly:**
   ```bash
   # macOS (Apple Silicon)
   curl -L https://github.com/slok/sloth/releases/download/v0.11.0/sloth-darwin-arm64 -o /usr/local/bin/sloth && chmod +x /usr/local/bin/sloth

   # macOS (Intel)
   curl -L https://github.com/slok/sloth/releases/download/v0.11.0/sloth-darwin-amd64 -o /usr/local/bin/sloth && chmod +x /usr/local/bin/sloth

   # Linux
   curl -L https://github.com/slok/sloth/releases/download/v0.11.0/sloth-linux-amd64 -o /usr/local/bin/sloth && chmod +x /usr/local/bin/sloth
   ```
   Verify: `sloth version`
   - Documentation: https://slok.github.io/sloth/

3. **Velero** - Kubernetes backup and disaster recovery
   ```bash
   # macOS
   brew install velero

   # Linux
   curl -L -o velero.tar.gz https://github.com/vmware-tanzu/velero/releases/download/v1.18.2/velero-v1.18.2-linux-amd64.tar.gz
   tar xzf velero.tar.gz
   sudo mv velero-*/velero /usr/local/bin/
   ```
   Verify: `velero version`
   - Uses MinIO (S3-compatible) running inside the Kind cluster — no cloud credentials required
   - Documentation: https://velero.io/docs/

4. **Chaos Mesh** - Kubernetes native chaos engineering platform
   ```bash
   helm repo add chaos-mesh https://charts.chaos-mesh.org
   helm repo update
   helm install chaos-mesh chaos-mesh/chaos-mesh --version 2.8.4 \
     --namespace chaos-mesh --create-namespace \
     --set chaosDaemon.runtime=containerd \
     --set chaosDaemon.socketPath=/run/containerd/containerd.sock
   ```
   > **Kind cluster note:** Chaos Mesh defaults to 3 controller manager replicas, which can exhaust memory on a single-node Kind cluster. If pods stay `Pending` with `Insufficient memory`, scale down:
   > ```bash
   > kubectl scale deployment chaos-controller-manager -n chaos-mesh --replicas=1
   > ```
   > Also consider deleting namespaces from previous chapters to free memory.

   Verify: `kubectl get pods -n chaos-mesh`
   - Documentation: https://chaos-mesh.org/docs/

5. **Prometheus** (from earlier chapters) - Metrics collection and alerting
   ```bash
   # If not already installed from Chapter 4/11/12:
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo update
   helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack --version 92.1.1 \
     --namespace monitoring --create-namespace
   ```
   If already installed, the `helm install` will error with "cannot re-use a name" — that's fine.
   - Port-forward: `kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090 &`
   - Required for SLI queries and chaos experiment metrics

6. **Python 3** (3.8+) - For automation scripts
   ```bash
   python3 --version
   python3 -m venv venv && source venv/bin/activate
   pip3 install pyyaml
   ```

### Cluster Requirements

- Kubernetes 1.20+ with RBAC enabled (Kind cluster from Chapter 2 works)
- Network policies allowing pod-to-pod communication for chaos tests
- Sufficient CPU/memory — on Kind, free up resources by deleting unused namespaces from prior chapters
- No cloud credentials needed — MinIO provides S3-compatible storage inside the cluster

### Storage Backend

MinIO is used as an S3-compatible local object store — it runs inside the Kind cluster alongside Velero. No cloud provider credentials are needed. The `velero-storage-location.yaml` manifest deploys MinIO, creates the backup bucket, and configures the Velero credentials secret automatically.

## Step-by-Step Instructions

### Phase 1: Set Up SLOs and Observability

#### Step 1.1: Verify or Deploy Prometheus Stack
```bash
# Check if Prometheus is already installed (from Chapter 4/11/12):
helm list -n monitoring 2>/dev/null | grep monitoring

# If no output, install it:
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack --version 92.1.1 \
  --namespace monitoring --create-namespace

# Verify deployment
kubectl get pods -n monitoring

# Port-forward Prometheus and Grafana
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090 &
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80 &

# Retrieve Grafana admin password
kubectl get secret kube-prometheus-stack-grafana -n monitoring -o jsonpath='{.data.admin-password}' | base64 -d; echo
```
**Expected Output:** Prometheus accessible at http://localhost:9090, Grafana at http://localhost:3000 (login: admin / password from above)

**Next Steps:** Proceed to Step 1.2

#### Step 1.2: Generate SLO Prometheus Rules
```bash
# Edit sloth-slo-spec.yaml to match your service metrics
# Key metrics required: http_requests_total, http_request_duration_seconds_bucket

# Generate Prometheus rules from Sloth spec
bash generate-slo-rules.sh sloth-slo-spec.yaml prometheus-slo-rules.yaml

# Verify PrometheusRule created
kubectl get prometheusrule -A | grep -i slo
```
**Expected Output:** `demo-app-slos` PrometheusRule created in monitoring namespace

**Next Steps:** Verify metrics in Prometheus UI at localhost:9090

#### Step 1.3: Deploy SLO Dashboard
```bash
# Get Grafana admin password (if you haven't already)
GRAFANA_PASS=$(kubectl get secret  kube-prometheus-stack-grafana -n monitoring -o jsonpath='{.data.admin-password}' | base64 -d)

# Import via API:
curl -X POST http://admin:${GRAFANA_PASS}@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d "{\"dashboard\": $(cat slo-dashboard.json), \"overwrite\": true}"

# Or import via Grafana UI:
# 1. Open http://localhost:3000 and log in (admin / password from above)
# 2. Click + (left sidebar) → Import → Upload JSON file
# 3. Select slo-dashboard.json → click Import
```
> **Troubleshooting:** If the API returns `401 Invalid username or password`, Grafana's stored admin password has drifted from the secret (it only reads the secret on first start). Reset it to the secret's value, then re-run the import:
> `kubectl exec -n monitoring deploy/kube-prometheus-stack-grafana -c grafana -- grafana cli admin reset-admin-password "$GRAFANA_PASS"`

**Expected Output:** SLO Dashboard visible in Grafana showing availability, latency SLIs and error budget

> **Note:** Dashboard panels will show "No data" until a workload is generating `http_requests_total` metrics matching `job="demo-app"`. The demo-app deployed in Step 3.2 provides this. If you just want to verify the dashboard imports correctly, the panels structure is sufficient.

**Next Steps:** Proceed to Phase 2 (backup setup) or Phase 3 (chaos engineering)

### Phase 2: Set Up Backup and Disaster Recovery

#### Step 2.1: Install Velero
```bash
# Install Velero (creates the velero namespace, CRDs, and controller pods)
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.8.0 \
  --bucket velero-backups \
  --secret-file <(echo -e "[default]\naws_access_key_id=minioadmin\naws_secret_access_key=minioadmin") \
  --backup-location-config region=us-east-1,s3ForcePathStyle=true,s3Url=http://minio.velero.svc.cluster.local:9000 \
  --namespace velero \
  --use-node-agent \
  --wait

# Verify Velero pods are running
kubectl get pods -n velero
```
**Expected Output:** Velero deployment and node-agent pods running in the `velero` namespace

> **Note:** `velero install` creates the namespace, installs CRDs, deploys the controller, and configures the default BackupStorageLocation. The `--use-node-agent` flag enables file-system-level backups (replaces the deprecated `--use-restic`). This is the recommended approach for modern Kubernetes clusters.

> **Troubleshooting (Ch03/Ch11 Gatekeeper policies active):** `velero install` fails with `namespace-must-have-team` because it creates an unlabelled namespace, and its pods are rejected for short image names and missing resource limits. Create the namespace first with `kubectl create namespace velero` plus the `team`, `environment` and `cost-center` labels in one manifest (see the existing namespaces for values). Then render the install with `velero install ... --dry-run -o json`, drop the `Namespace` item, prefix the Velero images with `docker.io/`, add CPU/memory requests and limits to the `velero` Deployment, its plugin init container and the `node-agent` DaemonSet, and `kubectl apply` the result. If pods stay Pending with `Insufficient cpu`, lower those CPU requests (for example to `10m`) or free CPU on the workers.

#### Step 2.2: Deploy MinIO (Local S3 Storage)
```bash
# Deploy MinIO into the velero namespace (S3-compatible object store)
kubectl apply -f velero-storage-location.yaml

# Wait for MinIO to be ready
kubectl wait --for=condition=available deployment/minio -n velero --timeout=120s

# Verify backup location is available
velero backup-location get
```
**Expected Output:** MinIO pods running, `default` backup location phase is `Available`

> **Note:** MinIO no longer publishes community images to Docker Hub or Quay, so `velero-storage-location.yaml` uses the pinned `docker.io/bitnamilegacy/minio` build (it also provides `mc` for the bucket-setup job). The backup location can show `Unavailable` for up to a minute until MinIO is ready; Velero revalidates it automatically.

**Next Steps:** Proceed to Step 2.3

#### Step 2.3: Create Backup Schedules
```bash
# Apply backup schedules (daily + hourly)
kubectl apply -f velero-schedule.yaml

# Verify schedules created
velero schedule get
```
**Expected Output:** Two schedules (`daily-backup`, `hourly-backup`) active

**Next Steps:** Proceed to Step 2.4

#### Step 2.4: Enable Self-Service Backup Labels
```bash
# Apply backup configuration with self-service pattern
kubectl apply -f backup-self-service.yaml

# Apply deployment with backup hooks (demonstrates pre/post-backup quiescing)
kubectl apply -f backup-config-annotation.yaml

# Verify backup annotation applied
kubectl get deploy demo-app -o yaml | grep -A 5 "backup.velero"

# Create backup to test hooks
velero backup create hook-test-backup --wait

# Check backup included hooks
velero backup describe hook-test-backup | grep -i "hook"
```
**Expected Output:** Deployment with backup hooks ready, backup captures pre-backup quiesce state (`HooksAttempted: 2`, `HooksFailed: 0` in the describe output)

> **Note:** `backup-config-annotation.yaml` uses a placeholder `nginx` container for the app and a `redis` sidecar (both with `docker.io/` prefixes), requests the `standard` StorageClass, and sets CPU requests of at least `50m` per container, so the pods pass the Gatekeeper and `default`-namespace LimitRange policies. The hooks run `redis-cli` commands that exist in the sidecar. `backup-self-service.yaml` keeps the Helm values as comments so `kubectl apply` accepts the file. Run `velero backup describe` without `--details`: the CLI cannot resolve the in-cluster MinIO address from your workstation, so the warnings/errors sections print `<error getting ...>` even when the backup succeeded.

**Next Steps:** Test disaster recovery in Step 2.5

#### Step 2.5: Run Automated DR Drill
```bash
# Execute full DR drill script
# Script will: backup → simulate disaster → restore → measure RTO
bash velero-dr-commands.sh

# Monitor restoration
watch "velero restore get"

# Verify restored namespace
kubectl get namespaces | grep dr-drill-demo

# Validate restored pods
kubectl get pods -n dr-drill-demo -o wide

# Cleanup backups from drill
velero backup get | awk '/^dr-drill-backup-/{print $1}' | xargs -n1 velero backup delete --confirm
velero restore get | awk '/^dr-drill-restore-/{print $1}' | xargs -n1 velero restore delete --confirm
```
**Expected Output:** DR drill completes with RTO measured (e.g., "Actual Recovery Time: 45s"), namespace and pods restored

> **Note:** With the Ch11 Gatekeeper policies active, the script creates the drill namespace with `team`/`environment`/`cost-center` labels, uses a `docker.io/` image with resource limits, and recreates the labelled namespace before the restore, because Velero would otherwise recreate it without labels and the `namespace-must-have-team` policy rejects it (the restore then ends `PartiallyFailed` with nothing restored). The reported RTO covers the Velero restore only; the script then waits for the Deployment to become available. The cleanup commands look up the drill backup names because Velero does not expand wildcards.

**Validation Checks:**
- RTO meets target (script configurable, default 600s)
- Restored namespace exists
- Pods are running and ready

**Next Steps:** Proceed to Phase 3 (chaos engineering)

#### Step 2.6: Automate Backup Validation
```bash
# Run Python backup automation script
python3 backup-automation.py --generate-report

# Check backup freshness (must be < 24 hours old)
python3 backup-automation.py --check-freshness 1

# Validate backup integrity
python3 backup-automation.py --validate-backups

# Schedule regular cleanup (keep 30 days)
python3 backup-automation.py --cleanup 30

# Run DR validation framework
python3 disaster-recovery-plan.py
```
**Expected Output:** All backups VALID and FRESH, RTO/RPO compliance confirmed

#### Step 2.7: Run Restore Validation (Weekly Recommended)

The `restore-validation.sh` script performs a non-destructive test restore to validate your backup pipeline:

```bash
chmod +x restore-validation.sh

# Run restore validation with default settings (uses latest backup, 10-minute RTO target)
./restore-validation.sh

# Specify a particular backup and RTO target
./restore-validation.sh --backup-name daily-backup-20260221020000 --rto-target 300

# Restore a source namespace into the temporary test namespace and validate it
# (without --namespaces, Velero restores into the original namespaces, where the
# objects already exist and are skipped, so the temporary namespace stays empty)
velero backup create demo-app-backup --include-namespaces default --selector app=demo-app --wait
./restore-validation.sh --backup-name demo-app-backup --namespaces default

# Output the validation report to a file
./restore-validation.sh --output /tmp/dr-validation-report.txt

# Dry run (shows what would happen without executing)
./restore-validation.sh --dry-run
```

**Expected Output:** Restore completes successfully, RTO measured and compared to target, test namespace cleaned up automatically.

> **Note:** The script fails (exit 1, test namespace kept for investigation) if the Velero restore ends in any phase other than `Completed`, including `PartiallyFailed`. The test namespace is created with the `team`/`environment`/`cost-center` labels the Ch11 Gatekeeper policy requires. The backup must contain everything the workload needs (ServiceAccounts, ConfigMaps): a selector-based backup only includes objects carrying that label, which is why `backup-config-annotation.yaml` labels them `app: demo-app`. On Kind, `local-path` volumes are hostPath-backed, so Velero skips their data (`hostPath volume which is not supported for pod volume backup`) and restores the PVC definition only.

**Recommended Schedule:** Run weekly via cron or CI/CD pipeline to ensure backup recoverability.

#### Step 2.8: Review Helm Values for Production Deployment (Reference)

The `platform-backup-config/values.yaml` provides a complete Helm values file for deploying Velero in production:

```bash
# Review the configuration
cat platform-backup-config/values.yaml

# Render the chart with these values to check them without installing anything
# (--api-versions lets the chart emit the ServiceMonitor and PrometheusRule)
helm template velero vmware-tanzu/velero --version 12.2.1 -n velero \
  -f platform-backup-config/values.yaml --api-versions monitoring.coreos.com/v1

# Deploy Velero using these values (after customizing for your environment)
helm install velero vmware-tanzu/velero --version 12.2.1 \
  --namespace velero --create-namespace \
  -f platform-backup-config/values.yaml
```

Key configuration areas: MinIO as S3-compatible local storage, daily + hourly backup schedules, 30-day retention, pre/post-backup hooks for database quiescing, Prometheus monitoring, and alert rules.

> **Note:** The values follow the `vmware-tanzu/velero` chart 12.x schema (`image`, `configuration.backupStorageLocation` as a list, `metrics`, `nodeAgent`); keys the chart does not define are ignored silently. Do not run `helm install` on top of the Velero from Steps 2.1-2.2: the chart's Deployment selector differs from the one `velero install` created, so Helm cannot take it over. With the Gatekeeper policies active, create the labelled `velero` namespace first (see the Step 2.1 troubleshooting note) rather than using `--create-namespace`. The schedules and hooks name the book's example namespaces (`team-alpha`, `team-beta`, `production`); namespaces that do not exist in your cluster are reported as backup errors.

### Phase 3: Chaos Engineering and Resilience Testing

#### Step 3.1: Install Chaos Mesh
```bash
# Add Chaos Mesh Helm repository
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm repo update

# Install Chaos Mesh in namespace (settings: containerd runtime, privileged daemon, webhook)
helm install chaos-mesh chaos-mesh/chaos-mesh --version 2.8.4 \
  --namespace chaos-mesh --create-namespace \
  -f chaos-mesh-values.yaml

# Verify installation
kubectl get pods -n chaos-mesh
kubectl api-resources | grep -i chaos
```
**Expected Output:** Chaos Mesh pods running (chaos-controller-manager, chaos-daemon on each node)

> **Note:** `chaos-mesh-values.yaml` carries the same settings as the usual `--set` flags (`chaosDaemon.privileged=true`, `controllerManager.enableWebhook=true`, `chaosDaemon.runtime=containerd`, `chaosDaemon.socketPath=/run/containerd/containerd.sock`), plus resource limits and a single controller replica so the pods fit on the Kind workers.
>
> **Troubleshooting (Ch03/Ch11 Gatekeeper policies active):** `--create-namespace` fails with `namespace-must-have-team`, and pods without resource limits are rejected. Create the namespace first with the `team`, `environment` and `cost-center` labels (the same manifest as in Step 2.1), then run `helm install` without `--create-namespace`; the values file already sets the limits. The `ghcr.io` images are large: the first install can take 5-10 minutes on a slow connection and exceed `--wait`. If Helm reports a timeout while the pods are still pulling, wait for them to become ready and re-run the command as `helm upgrade chaos-mesh chaos-mesh/chaos-mesh -n chaos-mesh -f chaos-mesh-values.yaml` to mark the release deployed.

**Next Steps:** Proceed to Step 3.2

#### Step 3.2: Deploy Demo Application (Target for Chaos Tests)
```bash
# Create the chaos-testing namespace and deploy the demo application
# (nginx, 3 replicas, container `nginx`, label app=demo-app)
kubectl apply -f chaos-demo-app.yaml

# Wait for pods to be ready
kubectl wait --for=condition=available deployment/demo-app -n chaos-testing --timeout=180s

# Verify application running
kubectl get pods -n chaos-testing
```
**Expected Output:** 3 demo-app pods running in chaos-testing namespace

> **Note:** `chaos-demo-app.yaml` replaces `kubectl create deployment demo-app --image=nginx:alpine`: with the Gatekeeper policies active that command is rejected (unlabelled namespace, short image name, no resource limits). The manifest sets the namespace labels, a `docker.io/` image and limits, and keeps the container name `nginx` and the `app=demo-app` label that the chaos experiments select on.

**Next Steps:** Run chaos experiments in Step 3.3

#### Step 3.3: Run Basic Chaos Experiments

**Experiment 1: Pod Failure**
```bash
# Apply pod failure chaos (kills 30% of matching pods)
kubectl apply -f chaos-mesh-pod-failure.yaml

# Monitor pod termination and recovery
kubectl get events -n chaos-testing | head -20

# Watch deployment recovery
watch "kubectl get pods -n chaos-testing"

# Measure recovery time (should auto-restart due to deployment replica count)
kubectl get pods -n chaos-testing -l app=demo-app
```
**Expected Output:** Some pods killed and immediately restarted by deployment controller

**Experiment 2: Extended Network Chaos**
```bash
# Apply comprehensive network experiments (delay, loss, bandwidth, corruption)
kubectl apply -f chaos-experiment-network.yaml

# Verify multiple chaos resources created
kubectl get networkchaos -n chaos-testing

# Monitor application behavior: time a request from one demo-app pod to another
# (the chaos applies to traffic leaving the pods, so a request to localhost is not affected)
PODS=($(kubectl get pod -n chaos-testing -l app=demo-app -o jsonpath='{.items[*].metadata.name}'))
TARGET_IP=$(kubectl get pod "${PODS[@]: -1}" -n chaos-testing -o jsonpath='{.status.podIP}')
kubectl exec "${PODS[@]:0:1}" -n chaos-testing -- \
  curl -s -o /dev/null -w "http=%{http_code} total=%{time_total}s\n" http://$TARGET_IP/
```
**Expected Output:** Application handles network degradation gracefully, responds despite latency/loss (`http=200`, with a total time of several hundred milliseconds while the experiments run, instead of a few milliseconds)

> **Note:** The demo application is nginx, which listens on port 80 and has no `/health` endpoint, so the request goes to `/` on port 80. The commands use bash array syntax; in zsh, arrays start at index 1 (use `${PODS[1]}` and `${PODS[-1]}`). Both chaos files also create a `Schedule` (`pod-kill-schedule` every 5 minutes, `network-chaos-schedule`) that keeps injecting faults until deleted: `kubectl delete schedule --all -n chaos-testing`.

#### Step 3.4: Run Multi-Stage Chaos Workflows
```bash
# Deploy workflow that chains multiple experiments
kubectl apply -f chaos-workflow.yaml

# Monitor workflow execution
kubectl get workflows -n chaos-testing
kubectl describe workflow resilience-test-workflow -n chaos-testing

# Watch pods during workflow
watch "kubectl get pods -n chaos-testing"

# View workflow logs
kubectl logs -n chaos-mesh -l app.kubernetes.io/component=controller-manager --tail=50

# Verify recovery after workflow completes
kubectl get deployment demo-app -n chaos-testing -o jsonpath='{.status.replicas}'
```
**Expected Output:** Workflow completes successfully, all pods recovered, recovery verification passes

#### Step 3.5: Generate Resilience Report with Chaos Runner
```bash
# The chaos-testing namespace was created in Step 3.2
kubectl get namespace chaos-testing

# Run chaos experiment and collect metrics
# (waits for every experiment in the file; delete earlier runs first, because
# applying unchanged experiments again does not inject anything:
#   kubectl delete podchaos --all -n chaos-testing)
python3 chaos-runner.py --experiment chaos-mesh-pod-failure.yaml

# Expected output:
# - Experiment created and running
# - Metrics collected (error rate, latency percentiles, pod restarts)
# - Resilience assessment generated
# - Recommendations provided

# List all chaos experiments with their phase (Pending / Running / Completed)
python3 chaos-runner.py --list-experiments

# Get detailed status of a specific experiment (names come from the YAML files)
python3 chaos-runner.py --get-status pod-kill-single

# Generate report from metrics
python3 chaos-runner.py --generate-report pod-kill-single

# Delete experiment after testing
python3 chaos-runner.py --delete pod-kill-single
```
**Expected Output:** Resilience report showing:
- Error rate stayed below threshold
- Latency p99 within SLO
- Pod restarts within normal parameters
- System resilience assessment "PASSED"

> **Note:** The metrics come from Prometheus at `localhost:9090` (port-forward it first: `kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090`) and look for `http_requests_total` and `request_duration_seconds_bucket`. If Prometheus is unreachable or returns no series for any of the queries, the report starts with a "No Prometheus data returned" warning instead of a real assessment. The nginx placeholder from Step 3.2 does not export these application metrics, so the error-rate and latency values are zero. Chaos Mesh 2.x has no single phase field, so the runner derives the phase from the `AllInjected`/`AllRecovered` conditions; `pod-kill` and `container-kill` are one-shot and count as completed once injected. The `Schedule` objects in the chaos YAML files keep injecting faults until deleted (`kubectl delete schedule --all -n chaos-testing`).

### Phase 4: Validation and Testing

#### Step 4.1: Run Complete Test Suite
```bash
# Execute all validation tests
python3 test-resilience.py

# Tests include:
# - SLO file structure and targets validation
# - Chaos experiment YAML validity
# - Chaos experiments have selectors and duration
# - Backup automation script syntax and behavior (kubectl/velero mocked)
# - Chaos runner phase detection and report handling (kubectl mocked)
# - SLO dashboard JSON validity

# Expected output: All tests pass (OK)
# Sample: test_pod_kill_experiment_exists ... ok
# Sample: test_chaos_experiments_have_selectors ... ok
```

**Expected Output:**
```
TestSLODefinitions: 3 tests PASSED
TestChaosExperiments: 4 tests PASSED
TestBackupAutomation: 5 tests PASSED
TestChaosRunner: 7 tests PASSED
TestSLODashboard: 2 tests PASSED

Ran 21 tests in 0.041s - OK
```

**Next Steps:** Proceed to validation checks in Step 4.2

#### Step 4.2: Validate SLO Compliance
```bash
# Query SLO metrics in Prometheus (port-forward first:
#   kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090)
PROM_URL="http://localhost:9090"
query() { curl -s -G "$PROM_URL/api/v1/query" --data-urlencode "query=$1" | jq -c '.data.result[] | {slo: .metric.sloth_slo, value: .value[1]}'; }

# SLO targets and error budgets loaded from the Sloth-generated rules
query 'slo:objective:ratio{sloth_service="demo-app"}'
query 'slo:error_budget:ratio{sloth_service="demo-app"}'

# Availability SLI over 5m (1 - error ratio); needs demo-app traffic
query '1 - slo:sli_error:ratio_rate5m{sloth_service="demo-app",sloth_slo="availability"}'

# Error budget remaining over the SLO period; needs demo-app traffic
query 'slo:period_error_budget_remaining:ratio{sloth_service="demo-app",sloth_slo="availability"}'

# Latency SLI: share of requests slower than 500ms over 5m; needs demo-app traffic
query 'slo:sli_error:ratio_rate5m{sloth_service="demo-app",sloth_slo="latency"}'

# Expected: objectives 0.999 (availability), 0.99 (latency, throughput). With traffic:
# availability > 0.999, error budget remaining > 0 (not exhausted), slow-request ratio < 0.01
```

> **Note:** The SLIs are computed from `http_requests_total{job="demo-app"}` and `http_request_duration_seconds_bucket{job="demo-app"}`. Until an instrumented demo-app is scraped (a ServiceMonitor with `job="demo-app"`), only the objectives and error budgets return values and the SLI queries return an empty result. The Sloth `PrometheusRule` must carry Prometheus's `ruleSelector` label (`release=kube-prometheus-stack`); `generate-slo-rules.sh` adds it, otherwise Prometheus silently ignores the rules. The `slo:api:*` rules in `slo-definitions.yaml` (used by `slo-dashboard.json`) are stored in a `ConfigMap`, which the Prometheus Operator does not load as rules.

#### Step 4.3: Validate DR Readiness
```bash
# Run disaster recovery validation
python3 disaster-recovery-plan.py

# Expected checks:
# - Latest backup is fresh (< 24 hours)
# - Backup status is "Completed"
# - RTO target achievable (< 30 minutes)
# - RPO met (< 60 minutes)
# - Required namespaces included in backups

# For demo/test mode (no cluster needed)
python3 disaster-recovery-plan.py --demo
```

#### Step 4.4: Verify Chaos Test Coverage
```bash
# Confirm all chaos experiments are valid
kubectl apply --dry-run=client -f chaos-mesh-pod-failure.yaml
kubectl apply --dry-run=client -f chaos-experiment-network.yaml
kubectl apply --dry-run=client -f chaos-workflow.yaml

# Expected: All files pass validation

# Also valid: a single NetworkChaos experiment
kubectl apply --dry-run=client -f chaos-network-delay.yaml

# List all experiment templates in directory
# (also matches chaos-demo-app.yaml and chaos-mesh-values.yaml, which are not experiments)
find . -name "chaos-*.yaml" -o -name "*-pod-kill.yaml" -o -name "*-workflow.yaml" | grep -v '^./venv' | sort
```

> **Note:** `chaos-experiment-pod-kill.yaml` also contains a LitmusChaos `ChaosEngine`, so `kubectl apply --dry-run=client -f chaos-experiment-pod-kill.yaml` reports `no matches for kind "ChaosEngine"` unless the LitmusChaos CRDs are installed (this chapter only installs Chaos Mesh). Its Chaos Mesh objects are valid. It also defines a `Schedule` named `pod-kill-schedule`, the same name as the one in `chaos-mesh-pod-failure.yaml`; applying both files replaces one with the other.

## Monitoring and Alerts

### Key SLO Metrics to Monitor

#### Availability SLI
```promql
# Ratio of successful requests (2xx/3xx) to total requests
sum(rate(http_requests_total{status=~"2.."}[5m])) / sum(rate(http_requests_total[5m]))

# Target: > 0.999 (99.9%)
```

#### Latency SLI (p99)
```promql
# 99th percentile response time
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Target: < 0.5 seconds (500ms)
```

#### Error Budget Burn Rate
```promql
# How fast error budget is consumed (4-week window)
slo:api:availability:burn_rate:4w

# Alert if > 0.1 (consuming 10% of monthly budget per day)
```

#### Error Budget Remaining
```promql
# Percentage of monthly error budget not yet consumed
slo:api:availability:error_budget_ratio

# Alert if > 0.8 (less than 20% remaining)
```

### Alert Rules (From slo-definitions.yaml)

| Alert | Condition | Action |
|-------|-----------|--------|
| SLOErrorBudgetBurnRateHigh | Burn rate > 10%/day | Warning, review deployments |
| SLOErrorBudgetLow | Budget < 20% remaining | Critical, freeze new deployments |
| SLOAvailabilityViolation | Availability < 99.9% | Critical, page on-call |
| SLOLatencyViolation | p99 latency > 500ms | Warning, investigate |

### Chaos Experiment Metrics

```promql
# Pod restart rate during experiments
rate(kube_pod_container_status_restarts_total[5m])

# Network latency during network chaos
histogram_quantile(0.99, rate(request_duration_seconds_bucket[5m]))

# Packet loss detection
rate(network_packets_lost_total[5m])

# Error rate during pod failures
rate(http_requests_total{status=~"5.."}[5m])
```

## Best Practices

### SLO-as-Code
1. **Define SLOs Quantitatively**: Use percentiles (p99), not averages
2. **Calculate Error Budgets**: Translate SLO target to allowable failures per month
3. **Automate SLI Collection**: Use Prometheus queries, not manual tracking
4. **Alert on Burn Rate**: Monitor consumption velocity, not just current compliance
5. **Review SLOs Quarterly**: Align targets with business requirements

### Chaos Engineering
1. **Start with Small Blasts**: Begin with single pod, progress to multi-pod failures
2. **Run During Business Hours**: Ensure observability and team awareness
3. **Set Experiment Duration Bounds**: Limit blast radius with time limits
4. **Verify System Recovery**: Confirm self-healing after each experiment
5. **Document Learnings**: Capture remediation items from experiment insights

### Disaster Recovery
1. **Test Regularly**: Run DR drills at least monthly
2. **Automate Restore Validation**: Script data integrity checks
3. **Measure Actual RTO**: Use velero-dr-commands.sh for realistic metrics
4. **Multi-Region Backups**: Store backups in different regions/clouds
5. **Verify RPO Requirements**: Ensure backup frequency meets RPO targets

### Error Budget-Driven Deployments
1. **Check Budget Before Deploy**: `if error_budget > 0.1: deploy_allowed = true`
2. **Graduated Rollouts**: Use error budget to inform canary percentages
3. **Freeze on Budget Exhaustion**: No production changes when budget consumed
4. **Post-Incident Review**: Factor incident impact into future deployments

## File Organization

```
code/
├── README.md (this file)
│
├── SLO Configuration
│   ├── sloth-auth-service-slo.yaml        # Auth service SLO (Listing 13.1)
│   ├── sloth-slo-spec.yaml                # Extended SLO spec with alerting rules
│   ├── slo-definitions.yaml               # Prometheus recording/alert rules
│   ├── slo-dashboard.json                 # Grafana dashboard for SLO visualization
│   └── generate-slo-rules.sh              # Script to generate rules from Sloth spec
│
├── Backup and DR
│   ├── velero-schedule.yaml               # Automated backup schedules (daily + hourly)
│   ├── velero-storage-location.yaml       # MinIO storage config (S3-compatible, local)
│   ├── backup-config-annotation.yaml      # Deployment with backup hooks (Listing 13.2)
│   ├── backup-self-service.yaml           # Self-service backup labeling pattern
│   ├── backup-automation.py               # Python script for backup management
│   ├── velero-dr-commands.sh              # Automated DR drill with RTO measurement
│   ├── restore-validation.sh             # Automated restore validation with RTO measurement
│   ├── disaster-recovery-plan.py          # DR readiness validation framework
│   └── platform-backup-config/
│       └── values.yaml                    # Helm values for production Velero deployment
│
├── Chaos Engineering
│   ├── chaos-network-delay.yaml           # Network latency injection (Listing 13.3)
│   ├── chaos-mesh-pod-failure.yaml        # PodChaos experiments (single, multiple, all, container-kill)
│   ├── chaos-experiment-pod-kill.yaml     # Extended pod kill experiments (Chaos Mesh + LitmusChaos)
│   ├── chaos-experiment-network.yaml      # Extended network experiments (delay, loss, bandwidth, corrupt, duplicate)
│   ├── chaos-workflow.yaml                # Multi-stage workflows (resilience-test, cascading, comprehensive)
│   ├── chaos-demo-app.yaml                # chaos-testing namespace + nginx demo app (Step 3.2)
│   ├── chaos-mesh-values.yaml             # Helm values for Chaos Mesh on Kind (Step 3.1)
│   ├── chaos-runner.py                    # Python orchestrator for chaos experiments
│   └── test-resilience.py                 # Test suite for SLO, chaos, and backup configs
```

## Companion Website Alignment

This code directory supplements content on the official Platform Engineering Handbook companion site:

**Website URL:** https://peh-packt.platformetrics.com/

**Chapter 13 Resources:**
- Interactive SLO calculator: Calculate error budgets for custom SLO targets
- Video walkthroughs: Step-by-step execution of chaos experiments
- Architecture diagrams: Resilience automation system design
- Community chaos experiments: Additional experiment templates
- DR runbook generator: Create team-specific runbooks from templates

**Note:** File listings, code examples, and configuration patterns in this directory are maintained in sync with website content. Refer to website for:
- Latest Sloth/Velero/Chaos Mesh API versions
- Multi-cluster resilience patterns
- Advanced chaos scenarios (cascading failures, latency spikes)
- Integration with CI/CD for automated testing

## Orphan Files and Issues

### No Orphan Files Identified

All 26 files in this directory are referenced in the manuscript or serve support functions:
- 5 SLO configuration files (referenced in Section 13.2)
- 7 Backup/DR files (referenced in Section 13.3)
- 10 Chaos engineering files (referenced in Section 13.4; includes the Kind/Gatekeeper helpers `chaos-demo-app.yaml` and `chaos-mesh-values.yaml`)
- 1 Test suite (comprehensive validation)
- 1 README (documentation)
- 2 Python cache files (__pycache__)

### Website Discrepancies Found: None

All code examples align with manuscript listings and section references.

## Known Gaps and Ideas for Further Additions

These two gaps remain when the chapter is run end to end on the local Kind cluster. They are not implemented here; the hints below are starting points.

### 1. Backup schedules point at example namespaces that may not exist

`velero-schedule.yaml` (and `platform-backup-config/values.yaml`) back up `team-alpha`, `team-beta` and `production`. If a namespace does not exist, Velero reports `fail to get the namespace <name> specified in backup.Spec.IncludedNamespaces`, the backup ends `PartiallyFailed`, and `disaster-recovery-plan.py` shows `[!] No backup errors: N backups have errors`. The hourly schedule repeats this every hour.

Ideas:
- Change `includedNamespaces` to namespaces that exist in your cluster (check with `kubectl get ns`) and re-apply `velero-schedule.yaml`.
- Or pause a schedule while you work through the chapter: `velero schedule pause hourly-backup` (resume with `velero schedule unpause hourly-backup`).
- Add a pre-flight check to `backup-automation.py` (or `disaster-recovery-plan.py`) that compares each schedule's `includedNamespaces` with `kubectl get ns` and warns about missing ones.
- To see the cause of a failed backup: `kubectl logs -n velero deploy/velero | grep "<backup-name>"` (the `velero backup describe` output cannot be downloaded from your workstation, see Step 2.4).

### 2. The SLO dashboard and SLI queries have no data

Two things are missing for real SLO data:
- **The rules behind the dashboard are not loaded.** `slo-definitions.yaml` is a `ConfigMap`, and the Prometheus Operator does not read rules from a ConfigMap, so the `slo:api:*` series used by `slo-dashboard.json` never exist. Only the Sloth-generated rules (`demo-app-slos`) are loaded.
- **Nothing produces the metrics.** The Sloth SLOs read `http_requests_total{job="demo-app"}` and `http_request_duration_seconds_bucket{job="demo-app"}`, which the nginx placeholder does not export.

Ideas:
- Turn the `groups:` content of the `slo-definitions` `ConfigMap` into a `PrometheusRule` (`spec.groups`) labelled `release: kube-prometheus-stack` (the label Prometheus selects on), then point the dashboard panels at the rule names that exist, or keep the `slo:api:*` names in both places.
- Add a small instrumented sample app that exports `http_requests_total` (with a `code` label) and `http_request_duration_seconds_bucket`, with a `Service` and a `ServiceMonitor` that results in `job="demo-app"`. Give it a `docker.io/` image and resource limits so it passes the Gatekeeper policies.
- Add a traffic generator (a small `Job` or `CronJob` calling the app, including some failing and slow requests) so the availability, latency and error-budget queries in Step 4.2, the dashboard and the burn-rate alerts show real values.
- Re-run the chaos experiments from Phase 3 against that app and watch the SLIs and `chaos-runner.py --generate-report` change, which turns the report from the "No Prometheus data" warning into a real assessment.

## Recommendations

### For Production Deployment

1. **Customize SLO Targets**: Edit `sloth-slo-spec.yaml` with actual service metrics and SLO targets
2. **Configure Cloud Storage**: Update `velero-storage-location.yaml` with your cloud bucket names and credentials
3. **Set Backup Schedules**: Modify cron expressions in `velero-schedule.yaml` for your timezone
4. **Target Correct Namespaces**: Update `chaos-*.yaml` selectors to match your application labels
5. **Review Alerts**: Adjust threshold values in `slo-definitions.yaml` for your operational needs

### For First-Time Users

1. **Start with Phase 1**: Deploy observability (Prometheus, SLO rules, dashboard)
2. **Progress to Phase 2**: Set up backup schedules and test restore procedure
3. **Then Phase 3**: Run chaos experiments in isolated namespace first
4. **Finally Phase 4**: Implement error budget-driven deployment policy

### For Scaling Beyond Single-Cluster

1. **Multi-Region Backups**: Create separate `velero-schedule.yaml` for each region
2. **Centralized SLO Metrics**: Run Prometheus federation to aggregate multi-cluster SLIs
3. **Cross-Cluster Chaos**: Coordinate experiments via shared scheduler
4. **Distributed DR Drills**: Orchestrate simultaneous restores across regions

### Maintenance Tasks

- **Weekly**: Review chaos experiment reports, verify SLO compliance
- **Monthly**: Run full DR drill, validate backup restore procedures
- **Quarterly**: Review SLO targets, update based on business changes
- **Annually**: Audit disaster recovery procedures, test multi-region failover

## Troubleshooting

### SLO Rules Not Generating

```bash
# Verify Sloth installation
sloth version

# Check SLO spec syntax
sloth generate -i sloth-slo-spec.yaml -o /dev/null

# View Prometheus rule group
kubectl get prometheusrule -o yaml
```

### Backups Not Running

```bash
# Check Velero status
velero backup-location get
velero schedule get

# View Velero logs
kubectl logs -n velero -l component=velero

# Manually trigger backup for testing
velero backup create test-backup --wait
```

### Chaos Experiments Not Triggering

```bash
# Verify Chaos Mesh pods running
kubectl get pods -n chaos-mesh

# Check experiment status
kubectl get podchaos -A
kubectl describe podchaos <name> -n chaos-testing

# View chaos daemon logs
kubectl logs -n chaos-mesh -l app=chaos-daemon
```

## Support and Contributing

- **Sloth Issues**: https://github.com/slok/sloth/issues
- **Velero Issues**: https://github.com/vmware-tanzu/velero/issues
- **Chaos Mesh Issues**: https://github.com/chaos-mesh/chaos-mesh/issues
- **Platform Engineering Handbook**: Contact publisher or visit companion website

## License and Attribution

Code examples from "The Platform Engineer's Handbook" (Packt Publishing)
- Author: Ajay Chankramath (ajay@platformetrics.com)
- Last Updated: February 2026
- License: [As specified in handbook]

All tool configurations are compatible with open-source versions of Sloth, Velero, and Chaos Mesh.

---

**Quick Start Checklist:**
- [ ] Install prerequisites (Sloth, Velero, Chaos Mesh, Prometheus, kubectl)
- [ ] Deploy Prometheus and generate SLO rules (Phase 1)
- [ ] Run first backup and validate restore (Phase 2)
- [ ] Run network latency chaos experiment (Phase 3)
- [ ] Execute full DR drill and validate RTO (Phase 2.5)
- [ ] Run complete test suite (Phase 4)
- [ ] Customize SLO targets and alert thresholds for your environment
- [ ] Integrate chaos experiments into CI/CD pipeline
- [ ] Schedule recurring DR drills (monthly minimum)

