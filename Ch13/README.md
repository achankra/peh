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
| **velero-storage-location.yaml** | Section 13.3 | Multi-cloud backup storage configuration for AWS S3, Azure Blob Storage, and Google Cloud Storage with encryption and lifecycle policies |
| **backup-config-annotation.yaml** | Listing 13.2 | Deployment example with Velero backup hooks (pre/post-backup) demonstrating database quiescing and graceful backup preparation |
| **backup-automation.py** | Section 13.3 | Python orchestration script for Velero backup management: create backups, validate integrity, check freshness, cleanup old backups |
| **velero-dr-commands.sh** | Section 13.3 | Automated DR drill script that creates backup, simulates disaster (deletes namespaces), restores from backup, and measures actual RTO |
| **disaster-recovery-plan.py** | Section 13.3 | DR validation framework checking backup freshness, RTO/RPO compliance, and readiness for disaster scenarios |
| **restore-validation.sh** | Section 13.3 | Automated restore validation script: performs test restore to a temporary namespace, verifies pod health and service availability, measures actual RTO, and cleans up. Suitable for weekly automated DR validation runs. |
| **backup-self-service.yaml** | Section 13.3 | Self-service backup labeling pattern enabling development teams to opt into backup automation through simple Kubernetes labels |
| **platform-backup-config/values.yaml** | Section 13.3 | Helm values file for production Velero deployment: AWS S3 storage (with Azure/GCS alternatives), daily + hourly backup schedules, retention policies, pre/post-backup hooks, Prometheus monitoring, and alert rules |

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

### Required Tools

1. **Sloth** - SLO-as-Code Prometheus rule generator
   ```bash
   go install github.com/slok/sloth@latest
   ```
   - Documentation: https://slok.github.io/sloth/
   - Generates Prometheus recording/alerting rules from YAML SLO specs
   - Enables error budget calculations and burn rate alerting

2. **Velero** - Kubernetes backup and disaster recovery
   ```bash
   wget https://github.com/vmware-tanzu/velero/releases/download/v1.12.0/velero-v1.12.0-linux-amd64.tar.gz
   tar -xzf velero-v1.12.0-linux-amd64.tar.gz
   sudo mv velero-v1.12.0-linux-amd64/velero /usr/local/bin/
   velero version
   ```
   - Requires cloud credentials (AWS S3, Azure, or GCS)
   - Documentation: https://velero.io/docs/

3. **Chaos Mesh** - Kubernetes native chaos engineering platform
   ```bash
   helm repo add chaos-mesh https://charts.chaos-mesh.org
   helm install chaos-mesh chaos-mesh/chaos-mesh -n chaos-mesh --create-namespace
   kubectl get pods -n chaos-mesh
   ```
   - Or LitmusChaos as alternative: `helm install litmus litmuschaos/litmus`
   - Documentation: https://chaos-mesh.org/docs/

4. **Prometheus** - Metrics collection and alerting
   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm install prometheus prometheus-community/kube-prometheus-stack
   kubectl get pods -n default | grep prometheus
   ```
   - Exposed on localhost:9090 (port-forward if remote)
   - Required for SLI queries and chaos experiment metrics

5. **kubectl** - Kubernetes CLI (v1.20+)
   ```bash
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   chmod +x kubectl && sudo mv kubectl /usr/local/bin/
   kubectl version --client
   ```

6. **Python** (3.8+) - For automation scripts
   ```bash
   python3 --version
   pip install pyyaml
   ```

### Cluster Requirements

- Kubernetes 1.20+ with RBAC enabled
- Persistent storage for backups (S3 bucket, Azure Storage, or GCS)
- Network policies allowing pod-to-pod communication for chaos tests
- At least 3 worker nodes for multi-pod chaos experiments
- Sufficient CPU/memory for Prometheus and Velero components

### Access Credentials

- **AWS**: IAM credentials with S3 full access and EBS snapshot permissions
- **Azure**: Service principal with Storage and Snapshot permissions
- **GCS**: Service account with Storage Object Admin role

## Step-by-Step Instructions

### Phase 1: Set Up SLOs and Observability

#### Step 1.1: Deploy Prometheus Stack
```bash
# Install Prometheus operator and kube-prometheus components
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --values - <<EOF
prometheus:
  prometheusSpec:
    retention: 15d
    resources:
      requests:
        cpu: 500m
        memory: 2Gi
grafana:
  adminPassword: admin
EOF

# Verify deployment
kubectl get pods -n monitoring
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
```
**Expected Output:** Prometheus accessible at http://localhost:9090, Grafana at http://localhost:3000

**Next Steps:** Proceed to Step 1.2

#### Step 1.2: Generate SLO Prometheus Rules
```bash
# Edit sloth-slo-spec.yaml to match your service metrics
# Key metrics required: http_requests_total, http_request_duration_seconds_bucket

# Generate Prometheus rules from Sloth spec
bash generate-slo-rules.sh sloth-slo-spec.yaml prometheus-slo-rules.yaml

# Apply generated rules to Kubernetes
kubectl apply -f prometheus-slo-rules.yaml

# Verify PrometheusRule created
kubectl get prometheusrule -A | grep -i slo
```
**Expected Output:** `prometheus-slo-rules` PrometheusRule created in default namespace

**Next Steps:** Verify metrics in Prometheus UI at localhost:9090

#### Step 1.3: Deploy SLO Dashboard
```bash
# Create ConfigMap with dashboard JSON
kubectl create configmap slo-dashboard \
  --from-file=slo-dashboard.json \
  -n monitoring

# Import dashboard into Grafana
# UI: Home → Dashboards → Import → Upload JSON file (slo-dashboard.json)
# Or use API:
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @slo-dashboard.json
```
**Expected Output:** SLO Dashboard visible in Grafana showing availability, latency SLIs and error budget

**Next Steps:** Proceed to Phase 2 (backup setup) or Phase 3 (chaos engineering)

### Phase 2: Set Up Backup and Disaster Recovery

#### Step 2.1: Install and Configure Velero
```bash
# Create velero namespace
kubectl create namespace velero

# Configure cloud credentials (AWS example)
cat > velero-credentials <<EOF
[default]
aws_access_key_id=YOUR_ACCESS_KEY
aws_secret_access_key=YOUR_SECRET_KEY
EOF

# Install Velero
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.8.0 \
  --bucket my-cluster-backups-prod \
  --secret-file ./velero-credentials \
  --namespace velero \
  --secret-key-file ~/.ssh/id_rsa

# Verify installation
kubectl get pods -n velero
velero backup-location get
```
**Expected Output:** Velero pods running, `aws-s3` backup location accessible

**Next Steps:** Proceed to Step 2.2

#### Step 2.2: Create Backup Schedules
```bash
# Apply backup storage locations (multi-cloud)
kubectl apply -f velero-storage-location.yaml

# Apply backup schedules (daily + hourly)
kubectl apply -f velero-schedule.yaml

# Verify schedules created
velero schedule get

# Trigger first backup manually for testing
velero backup create test-backup-001 --wait

# Monitor backup progress
velero backup describe test-backup-001
velero backup logs test-backup-001
```
**Expected Output:** Two schedules (`daily-backup`, `hourly-backup`) active, first backup completes

**Next Steps:** Proceed to Step 2.3

#### Step 2.3: Enable Self-Service Backup Labels
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
**Expected Output:** Deployment with backup hooks ready, backup captures pre-backup quiesce state

**Next Steps:** Test disaster recovery in Step 2.4

#### Step 2.4: Run Automated DR Drill
```bash
# Execute full DR drill script
# Script will: backup → simulate disaster → restore → measure RTO
bash velero-dr-commands.sh

# Monitor restoration
watch "velero restore get"

# Verify restored namespaces
kubectl get namespaces | grep -E "team-alpha|team-beta"

# Validate restored pods
kubectl get pods -n team-alpha -o wide

# Cleanup backups from drill
velero backup delete dr-drill-backup-* --confirm
velero restore delete dr-drill-restore-* --confirm
```
**Expected Output:** DR drill completes with RTO measured (e.g., "Actual Recovery Time: 45s"), namespaces and pods restored

**Validation Checks:**
- RTO meets target (script configurable, default 600s)
- All restored namespaces exist
- Pods are running and ready
- Data integrity verified (pod counts match pre-disaster state)

**Next Steps:** Proceed to Phase 3 (chaos engineering)

#### Step 2.5: Automate Backup Validation
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

#### Step 2.6: Run Restore Validation (Weekly Recommended)

The `restore-validation.sh` script performs a non-destructive test restore to validate your backup pipeline:

```bash
chmod +x restore-validation.sh

# Run restore validation with default settings (uses latest backup, 10-minute RTO target)
./restore-validation.sh

# Specify a particular backup and RTO target
./restore-validation.sh --backup-name daily-backup-20260221020000 --rto-target 300

# Output the validation report to a file
./restore-validation.sh --output /tmp/dr-validation-report.txt

# Dry run (shows what would happen without executing)
./restore-validation.sh --dry-run
```

**Expected Output:** Restore completes successfully, RTO measured and compared to target, test namespace cleaned up automatically.

**Recommended Schedule:** Run weekly via cron or CI/CD pipeline to ensure backup recoverability.

#### Step 2.7: Review Helm Values for Production Deployment (Reference)

The `platform-backup-config/values.yaml` provides a complete Helm values file for deploying Velero in production:

```bash
# Review the configuration
cat platform-backup-config/values.yaml

# Deploy Velero using these values (after customizing for your environment)
helm install velero vmware-tanzu/velero \
  --namespace velero --create-namespace \
  -f platform-backup-config/values.yaml
```

Key configuration areas: AWS S3 storage (with Azure/GCS alternatives commented), daily + hourly backup schedules, 30-day retention, pre/post-backup hooks for database quiescing, Prometheus monitoring, and alert rules.

### Phase 3: Chaos Engineering and Resilience Testing

#### Step 3.1: Install Chaos Mesh
```bash
# Add Chaos Mesh Helm repository
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm repo update

# Install Chaos Mesh in namespace
helm install chaos-mesh chaos-mesh/chaos-mesh \
  --namespace chaos-mesh --create-namespace \
  --set chaosDaemon.privileged=true \
  --set controllerManager.enableWebhook=true

# Verify installation
kubectl get pods -n chaos-mesh
kubectl api-resources | grep -i chaos
```
**Expected Output:** Chaos Mesh pods running (chaos-controller-manager, chaos-daemon on each node)

**Next Steps:** Proceed to Step 3.2

#### Step 3.2: Deploy Demo Application (Target for Chaos Tests)
```bash
# Create namespace for chaos testing
kubectl create namespace team-alpha

# Apply demo application with backup hooks
kubectl apply -f backup-config-annotation.yaml -n team-alpha

# Wait for pods to be ready
kubectl rollout status deployment/demo-app -n team-alpha --timeout=300s

# Verify application running
kubectl get pods -n team-alpha -l app=demo-app
kubectl port-forward -n team-alpha svc/demo-app 8080:8080
```
**Expected Output:** 3 demo-app pods running, service accessible at localhost:8080

**Next Steps:** Run chaos experiments in Step 3.3

#### Step 3.3: Run Basic Chaos Experiments

**Experiment 1: Network Latency Injection**
```bash
# Apply network latency chaos (Listing 13.3 example)
kubectl apply -f chaos-network-delay.yaml

# Monitor impact on application
watch "kubectl get pods -n production"

# Query Prometheus for latency impact
# In Prometheus UI: histogram_quantile(0.99, request_duration_seconds_bucket)

# Experiment runs for 5 minutes (cron scheduled) or apply and wait
sleep 5m

# Verify pods recovered
kubectl get pods -n production -l app=api-service
```
**Expected Output:** Network latency injected for 5 minutes, pods remain running, latency metric increases in Prometheus

**Experiment 2: Pod Failure**
```bash
# Apply pod failure chaos (kills 30% of matching pods)
kubectl apply -f chaos-mesh-pod-failure.yaml

# Monitor pod termination and recovery
kubectl get events -n chaos-testing | head -20

# Watch deployment recovery
watch "kubectl get pods -n team-alpha"

# Measure recovery time (should auto-restart due to deployment replica count)

# Verify pods recovered after 1 minute
sleep 65
kubectl get pods -n team-alpha -l app=demo-app
```
**Expected Output:** Some pods killed and immediately restarted by deployment controller

**Experiment 3: Extended Network Chaos**
```bash
# Apply comprehensive network experiments (delay, loss, bandwidth, corruption)
kubectl apply -f chaos-experiment-network.yaml

# Verify multiple chaos resources created
kubectl get networkchaos -n chaos-testing

# Monitor application behavior
kubectl exec -it $(kubectl get pod -n team-alpha -l app=demo-app -o jsonpath='{.items[0].metadata.name}') \
  -n team-alpha -- curl -v http://localhost:8080/health
```
**Expected Output:** Application handles network degradation gracefully, responds despite latency/loss

#### Step 3.4: Run Multi-Stage Chaos Workflows
```bash
# Deploy workflow that chains multiple experiments
kubectl apply -f chaos-workflow.yaml

# Monitor workflow execution
kubectl get workflows -n chaos-testing
kubectl describe workflow resilience-test-workflow -n chaos-testing

# Watch pods during workflow
watch "kubectl get pods -n team-alpha"

# View workflow logs
kubectl logs -n chaos-mesh -l app=chaos-controller-manager --tail=50

# Verify recovery after workflow completes
kubectl get deployment demo-app -n team-alpha -o jsonpath='{.status.replicas}'
```
**Expected Output:** Workflow completes successfully, all pods recovered, recovery verification passes

#### Step 3.5: Generate Resilience Report with Chaos Runner
```bash
# Create chaos namespace if not exists
kubectl create namespace chaos-testing --dry-run=client -o yaml | kubectl apply -f -

# Run chaos experiment and collect metrics
python3 chaos-runner.py --experiment chaos-mesh-pod-failure.yaml

# Expected output:
# - Experiment created and running
# - Metrics collected (error rate, latency percentiles, pod restarts)
# - Resilience assessment generated
# - Recommendations provided

# List all active chaos experiments
python3 chaos-runner.py --list-experiments

# Get detailed status of specific experiment
python3 chaos-runner.py --get-status pod-failure-demo

# Generate report from metrics
python3 chaos-runner.py --generate-report pod-failure-demo

# Delete experiment after testing
python3 chaos-runner.py --delete pod-failure-demo
```
**Expected Output:** Resilience report showing:
- Error rate stayed below threshold
- Latency p99 within SLO
- Pod restarts within normal parameters
- System resilience assessment "PASSED"

### Phase 4: Validation and Testing

#### Step 4.1: Run Complete Test Suite
```bash
# Execute all validation tests
python3 test-resilience.py

# Tests include:
# - SLO file structure and targets validation
# - Chaos experiment YAML validity
# - Chaos experiments have selectors and duration
# - Backup automation script syntax
# - SLO dashboard JSON validity

# Expected output: All tests pass (OK)
# Sample: test_pod_kill_experiment_exists ... ok
# Sample: test_chaos_experiments_have_selectors ... ok
```

**Expected Output:**
```
TestSLODefinitions: 3 tests PASSED
TestChaosExperiments: 4 tests PASSED
TestBackupAutomation: 2 tests PASSED
TestSLODashboard: 2 tests PASSED

Ran 11 tests in 0.234s - OK
```

**Next Steps:** Proceed to validation checks in Step 4.2

#### Step 4.2: Validate SLO Compliance
```bash
# Query SLO metrics in Prometheus
PROM_URL="http://localhost:9090"

# Check availability SLI
curl -s "$PROM_URL/api/v1/query?query=slo:api:availability:ratio" | jq '.data.result[].value'

# Check error budget remaining
curl -s "$PROM_URL/api/v1/query?query=slo:api:availability:error_budget_ratio" | jq '.data.result[].value'

# Check latency SLI (p99)
curl -s "$PROM_URL/api/v1/query?query=slo:api:latency:p99" | jq '.data.result[].value'

# Expected: availability > 0.999, error_budget < 1.0 (not exhausted), latency_p99 < 0.5s
```

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

# List all experiment templates in directory
find . -name "chaos-*.yaml" -o -name "*-pod-kill.yaml" -o -name "*-workflow.yaml" | sort
```

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
│   ├── velero-storage-location.yaml       # Multi-cloud storage config (AWS, Azure, GCS)
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

All 24 files in this directory are referenced in the manuscript or serve support functions:
- 5 SLO configuration files (referenced in Section 13.2)
- 7 Backup/DR files (referenced in Section 13.3)
- 8 Chaos engineering files (referenced in Section 13.4)
- 1 Test suite (comprehensive validation)
- 1 README (documentation)
- 2 Python cache files (__pycache__)

### Website Discrepancies Found: None

All code examples align with manuscript listings and section references.

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
kubectl apply -f sloth-slo-spec.yaml --dry-run=client -o yaml

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
- Author: [Author Name]
- Updated: February 2026
- License: [As specified in handbook]

All tool configurations are compatible with open-source versions of Sloth, Velero, and Chaos Mesh.

---

**Quick Start Checklist:**
- [ ] Install prerequisites (Sloth, Velero, Chaos Mesh, Prometheus, kubectl)
- [ ] Configure cloud credentials for Velero backups
- [ ] Deploy Prometheus and generate SLO rules (Phase 1)
- [ ] Run first backup and validate restore (Phase 2)
- [ ] Run network latency chaos experiment (Phase 3)
- [ ] Execute full DR drill and validate RTO (Phase 2.4)
- [ ] Run complete test suite (Phase 4)
- [ ] Customize SLO targets and alert thresholds for your environment
- [ ] Integrate chaos experiments into CI/CD pipeline
- [ ] Schedule recurring DR drills (monthly minimum)

