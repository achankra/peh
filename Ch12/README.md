# Chapter 12: Optimize Cost, Performance, and Scalability

## Chapter Overview

This chapter addresses one of the most critical challenges in platform engineering: understanding and optimizing the cost of running Kubernetes infrastructure without sacrificing performance or scalability. You'll learn how to make the tradeoffs between these three concerns explicit and defensible through FinOps practices, cost observability, autoscaling strategies, and cost governance.

**Key Learning Objectives:**
- Understand the architectural tradeoffs between cost, performance, and scalability
- Instrument your platform with cost observability using OpenCost (CNCF)
- Implement autoscaling with Horizontal Pod Autoscaler (HPA) and Vertical Pod Autoscaler (VPA)
- Rightsize workloads, leverage spot instances, and use Karpenter for intelligent node selection
- Set up cost governance guardrails with ResourceQuotas, LimitRanges, and Kyverno policies
- Implement cost allocation by team and alerting on cost anomalies

---

## Code-to-Chapter Mapping

This section maps each file in the code directory to specific chapter sections and manuscript listings.

### Cost Allocation and Labeling

| File | Section | Purpose |
|------|---------|---------|
| `cost-labeling-examples.yaml` | 12.2 FinOps Observability | **Listings 12.1-12.2:** Demonstrates cost allocation labels at namespace and deployment level. Shows how to tag workloads with `team`, `cost-center`, and `business-unit` labels for OpenCost cost attribution. |
| `opencost-cost-allocation.yaml` | 12.2 FinOps Observability | **Listing 12.8 extended:** ConfigMap for OpenCost cost allocation configuration. Defines how OpenCost should map labels to cost allocation dimensions. |

### Autoscaling Configurations

| File | Section | Purpose |
|------|---------|---------|
| `checkout-api-hpa.yaml` | 12.3 Autoscaling Strategies | **Listing 12.3:** HPA configuration for the checkout-api deployment. Scales between 2-10 replicas based on CPU (70%) and memory (80%) utilization with conservative scale-down and aggressive scale-up behaviors. |
| `checkout-api-vpa.yaml` | 12.3 Autoscaling Strategies | **Listing 12.4:** VPA configuration for checkout-api with Auto mode. Adjusts CPU/memory requests based on observed usage with configurable bounds to prevent under/over-provisioning. |
| `hpa-config.yaml` | 12.3 Autoscaling Strategies | Extended HPA examples demonstrating CPU-based and custom metrics-based autoscaling with full namespace and deployment setup for a demo application. |
| `vpa-config.yaml` | 12.3 Autoscaling Strategies | Extended VPA examples showing all three VPA modes: Off (recommendations only), Auto (automatic adjustment), and Recreate (requires pod recreation). Includes RBAC and policy configurations. |

### Node and Instance Strategies

| File | Section | Purpose |
|------|---------|---------|
| `karpenter-provisioner.yaml` | 12.4 Rightsizing and Spot Instances | **Listing 12.5:** Karpenter provisioner configuration for intelligent node selection. Automatically selects the cheapest instance type from a pool of options, with preference for spot instances but fallback to on-demand. |
| `spot-instance-handler.yaml` | 12.4 Rightsizing and Spot Instances | Extended examples demonstrating pod affinity/anti-affinity for spot instances, PodDisruptionBudgets for safe eviction, and graceful termination handling. |
| `node-pool-strategy.yaml` | 12.4 Rightsizing and Spot Instances | Configuration demonstrating on-demand vs spot node pools using taints and tolerations. Shows how to isolate workload types to specific node categories. |
| `pod-disruption-budget.yaml` | 12.4 Rightsizing and Spot Instances | PodDisruptionBudget configurations for maintaining service availability when spot instances are interrupted. Ensures minimum replicas stay available during disruptions. |

### Cost Governance and Guardrails

| File | Section | Purpose |
|------|---------|---------|
| `budget-guardrails.yaml` | 12.5 Cost Governance and Alerting | ResourceQuotas and LimitRanges for dev, staging, and production environments. Implements tiered resource budgets to prevent cost overruns and ensure teams operate within their allocations. |
| `kyverno-require-resources.yaml` | 12.5 Cost Governance and Alerting | **Listing 12.11:** Kyverno ClusterPolicy requiring CPU and memory requests on all pods. Enforces cost observability by preventing "unlimited" resource consumption and enabling accurate HPA operation. |
| `cost-alerts.yaml` | 12.5 Cost Governance and Alerting | **Listing 12.8:** PrometheusRule for cost anomaly detection. Detects unusual cost spikes by comparing current rates against 7-day baselines, with configurable thresholds and alert severity. |

### Installation and Utilities

| File | Section | Purpose |
|------|---------|---------|
| `install-opencost.sh` | 12.2 FinOps Observability | Bash script to install OpenCost (CNCF) via Helm with proper Prometheus integration. Sets up OpenCost UI and API endpoints for cost analysis. |
| **`install-kubecost.sh`** | Alternative approach | **[LEGACY/ALTERNATIVE]** KubeCost installation script. KubeCost is a commercial alternative to OpenCost with additional features. The manuscript uses OpenCost (CNCF, free) as the primary tool. |

### Python Tools and Analysis

| File | Section | Purpose |
|------|---------|---------|
| `cost-analyzer.py` | 12.2 FinOps Observability | **Tool:** Analyzes pod resource requests/limits vs actual usage. Identifies over/under-provisioned resources, calculates waste, and provides right-sizing recommendations. Uses kubectl and Metrics Server data. |
| `cost-allocation-labels.py` | 12.2 FinOps Observability | **Tool:** Validates cost allocation labels across all workloads. Generates reports on cost distribution by team, cost-center, and environment. Identifies non-compliant workloads missing required labels. |
| `cost-anomaly-detector.py` | 12.5 Cost Governance and Alerting | **Tool:** Statistical anomaly detection for cost metrics. Uses z-score and spike detection to identify unusual cost patterns. Can generate test data or integrate with real Prometheus metrics. |
| `test-cost-optimization.py` | Testing | Integration tests validating HPA configurations, cost allocation labels, budget guardrails, and anomaly detection rules. Ensures cost optimization features function correctly. |

---

## Orphan Files

### Identified Legacy/Alternative Files

| File | Status | Notes |
|------|--------|-------|
| `install-kubecost.sh` | Legacy/Alternative | KubeCost is a commercial tool; the chapter uses **OpenCost (CNCF)** as the primary solution. KubeCost can coexist as an alternative for organizations with multi-cloud infrastructure. |
| `kubecost-cost-allocation.yaml` | Legacy/Alternative | ConfigMap for KubeCost cost allocation. Redundant if using OpenCost. Keep only if deploying KubeCost as alternative tool. |

**Recommendation:** Remove or deprecate these files in the main chapter flow. They can be provided as appendix materials for teams choosing KubeCost instead of OpenCost.

---

## Prerequisites

Before deploying the code in this chapter, ensure you have the following prerequisites installed and configured:

### Kubernetes and Core Tools
- **Kubernetes cluster** (v1.20+): The examples target modern Kubernetes versions with autoscaling support
- **kubectl** (v1.20+): Configured and authenticated to your cluster
- **Helm 3**: Required for installing OpenCost, Karpenter, and VPA

### Observability and Metrics
- **Prometheus**: Deployed in your cluster (from Chapter 11). OpenCost scrapes Prometheus for cost metrics
- **Metrics Server**: Required for HPA to function. The examples reference CPU and memory utilization metrics
  ```bash
  # Install if not present:
  kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
  ```

### Cost Observability
- **OpenCost**: CNCF sandbox project for Kubernetes cost allocation (installed via `install-opencost.sh`)
- **Cloud provider credentials** (for cost attribution):
  - AWS: IAM user/role with permissions for EC2, EBS pricing APIs
  - GCP: Service account with compute.instances.list, compute.disks.list permissions
  - Azure: Service principal with relevant compute permissions

### Optional but Recommended
- **Karpenter**: For intelligent node provisioning and spot instance management
- **VPA (Vertical Pod Autoscaler)**: For right-sizing recommendations
- **Kyverno**: For policy-based cost governance and admission control
- **Python 3.8+**: For running analysis and testing scripts (cost-analyzer.py, cost-allocation-labels.py, etc.)
  ```bash
  pip install pyyaml
  ```

---

## Installation & Setup Instructions

This section provides step-by-step instructions to deploy and test the cost optimization features described in the chapter.

### Step 1: Verify Prerequisites

```bash
# Verify Kubernetes cluster
kubectl cluster-info
kubectl get nodes

# Verify Metrics Server
kubectl get deployment metrics-server -n kube-system

# Verify Prometheus (from Chapter 11)
kubectl get prometheus -n monitoring
```

### Step 2: Install and Configure OpenCost

```bash
# Make the installation script executable
chmod +x install-opencost.sh

# Run the OpenCost installation
./install-opencost.sh

# Expected output:
# - opencost namespace created
# - OpenCost Helm chart installed
# - opencost pods running
```

**Verify Installation:**
```bash
kubectl get pods -n opencost
kubectl logs -n opencost deployment/opencost

# Access OpenCost UI (in another terminal)
kubectl port-forward -n opencost svc/opencost 9003:9003
# Then open http://localhost:9003 in your browser
```

### Step 3: Apply Cost Allocation Labels to Namespaces

```bash
# Deploy namespaces with cost allocation labels
kubectl apply -f cost-labeling-examples.yaml

# Expected resources created:
# - Namespace: team-checkout (with labels: team=checkout, cost-center=4521)
# - Deployment: checkout-api (with matching labels)
# - ResourceQuota: team-checkout-quota
# - LimitRange: team-checkout-limits
```

**Verify Labels:**
```bash
kubectl get ns team-checkout --show-labels
kubectl get deployment -n team-checkout checkout-api --show-labels
```

### Step 4: Deploy Horizontal Pod Autoscaler (HPA)

```bash
# Apply HPA configuration
kubectl apply -f checkout-api-hpa.yaml

# Verify HPA creation
kubectl get hpa -n team-checkout

# Check HPA status (note: metrics may take a few minutes to become available)
kubectl describe hpa checkout-api-hpa -n team-checkout

# Expected output:
# - HPA: checkout-api-hpa
# - Target: checkout-api Deployment
# - Min Replicas: 2, Max Replicas: 10
# - Metrics: CPU (70%), Memory (80%)
```

### Step 5: Deploy Vertical Pod Autoscaler Configuration (Optional)

```bash
# Install VPA (requires separate VPA controller installation)
# See vpa-config.yaml for detailed configuration

# For now, we'll use VPA in "Off" mode to get recommendations without automatic updates
kubectl apply -f checkout-api-vpa.yaml

# Verify VPA
kubectl get vpa -n team-checkout
kubectl describe vpa checkout-api-vpa -n team-checkout

# Expected output after 8+ hours of running:
# - VPA recommendations for CPU and memory
# - Shows lower bound, target, and upper bound values
```

### Step 6: Apply Budget Guardrails (ResourceQuotas and LimitRanges)

```bash
# Deploy ResourceQuotas and LimitRanges for different environments
kubectl apply -f budget-guardrails.yaml

# Verify quotas are in place
kubectl get resourcequota --all-namespaces
kubectl get limitrange --all-namespaces

# Check quota usage
kubectl describe resourcequota -n team-checkout

# Expected output:
# - Limits on CPU, memory, and pod count per environment
# - Default resource requests/limits for containers
```

### Step 7: Enforce Cost Governance with Kyverno Policy

```bash
# Apply Kyverno policy requiring resource requests
kubectl apply -f kyverno-require-resources.yaml

# Verify policy installation
kubectl get clusterpolicy require-resource-requests

# Test the policy (this should fail without resource requests)
kubectl run test-pod --image=nginx --dry-run=server -o yaml | kubectl apply -f -

# Expected: Policy violation error if pod has no resource requests
```

### Step 8: Set Up Cost Anomaly Detection

```bash
# Apply Prometheus alerting rules for cost anomalies
kubectl apply -f cost-alerts.yaml

# Verify PrometheusRule is created
kubectl get prometheusrule -n monitoring

# Check rule details
kubectl get prometheusrule cost-anomalies -n monitoring -o yaml
```

### Step 9: Spot Instance Configuration (Optional)

```bash
# Deploy spot instance handler with pod disruption budgets
kubectl apply -f spot-instance-handler.yaml
kubectl apply -f pod-disruption-budget.yaml

# Verify PodDisruptionBudgets
kubectl get pdb --all-namespaces
kubectl describe pdb critical-service-pdb -n default
```

### Step 10: Run Analysis and Validation Scripts

```bash
# Analyze current resource usage
python3 cost-analyzer.py --namespace team-checkout --output-format json

# Validate cost allocation labels
python3 cost-allocation-labels.py --report-by team

# Run cost optimization tests
python3 test-cost-optimization.py -v

# Simulate and detect cost anomalies
python3 cost-anomaly-detector.py --generate-data --threshold 2.0
```

---

## Step-by-Step Workflow with Expected Output

### Workflow Overview

1. **Establish Baseline**: Measure current resource usage and waste
2. **Configure Autoscaling**: Set up HPA and VPA based on workload characteristics
3. **Implement Cost Governance**: Apply ResourceQuotas and admission policies
4. **Enable Cost Allocation**: Tag workloads and validate with reports
5. **Monitor and Alert**: Set up cost anomaly detection
6. **Review and Iterate**: Analyze results and adjust configurations

### Example Workflow Execution

```bash
# 1. BASELINE ANALYSIS
# Analyze current resource usage and identify waste
python3 cost-analyzer.py --namespace team-checkout --show-waste

# Expected output:
# Pod: checkout-api-xyz
# - CPU Requested: 100m, Used: 25m (25% utilization)
# - Memory Requested: 256Mi, Used: 128Mi (50% utilization)
# - Status: OVER_PROVISIONED
# - Recommendation: Reduce CPU request to 50m, Memory to 128Mi

# 2. DEPLOY HPA
# Configure horizontal scaling
kubectl apply -f checkout-api-hpa.yaml

# Wait 2-3 minutes for metrics collection
sleep 180

# Generate load to trigger autoscaling
kubectl run -it load-generator --image=busybox /bin/sh -- -c "while sleep 1; do wget -q -O- http://checkout-api.team-checkout; done"

# Monitor HPA in another terminal
kubectl get hpa -n team-checkout -w

# Expected output (after ~2 min of load):
# NAME                REFERENCE                     TARGETS       MINPODS  MAXPODS  REPLICAS  AGE
# checkout-api-hpa    Deployment/checkout-api       75%/70%, 60%  2        10       3         5m
# (CPU crosses 70%, HPA creates additional replicas)

# 3. COST ALLOCATION LABELS
# Validate cost labels
python3 cost-allocation-labels.py --report-by team

# Expected output:
# Team: checkout
# - Namespace: team-checkout
# - Cost Center: 4521
# - Deployments: 1 (checkout-api)
# - Total Resources: 2-8 CPU, 512Mi-4Gi Memory
# - All workloads labeled: COMPLIANT

# 4. BUDGET GUARDRAILS
# Apply resource quotas
kubectl apply -f budget-guardrails.yaml

# Test quota enforcement
kubectl run test-pod -n team-checkout --image=nginx --requests='cpu=1,memory=1Gi' --dry-run=server -o yaml | kubectl apply -f -

# Expected output (if quota exceeded):
# Error: pods "test-pod" is forbidden: exceeded quota: team-checkout-quota

# 5. ANOMALY DETECTION
# Monitor for cost spikes
python3 cost-anomaly-detector.py --monitor --threshold 2.0

# Expected output (after 1 hour of monitoring):
# Monitoring cost anomalies...
# [Normal] Namespace: team-checkout, Cost: $12.50/hour
# [Normal] Namespace: team-checkout, Cost: $12.45/hour
# (No anomalies detected; trend is stable)

# 6. REVIEW RESULTS
# Generate cost report
python3 cost-allocation-labels.py --report-by cost-center

# Expected output:
# Cost Center: 4521
# - Namespace: team-checkout
# - Monthly Cost: ~$8,000
# - Trend: Stable (no spike detected)
# - Recommendation: HPA and rightsizing reduced waste by 25%
```

---

## Key Metrics to Monitor

### Resource Utilization Metrics

Monitor these metrics via Prometheus/Grafana to understand resource efficiency:

```promql
# Pod CPU utilization vs requests (should be 50-80% for optimal cost)
(rate(container_cpu_usage_seconds_total[5m]) / on(pod) kube_pod_container_resource_requests_cpu_cores) * 100

# Pod memory utilization vs requests (should be 50-80%)
(container_memory_working_set_bytes / on(pod) kube_pod_container_resource_requests_memory_bytes) * 100

# HPA target metrics (what HPA uses to scale)
rate(container_cpu_usage_seconds_total[1m])
container_memory_working_set_bytes
```

### Cost Metrics (OpenCost)

```promql
# Total cluster cost per hour
sum(rate(container_cpu_cost[1h])) + sum(rate(container_memory_cost[1h]))

# Cost by namespace
sum(rate(container_cpu_cost[1h]) + rate(container_memory_cost[1h])) by (namespace)

# Cost by team
sum(rate(container_cpu_cost[1h]) + rate(container_memory_cost[1h])) by (label_team)

# Top 10 most expensive deployments
topk(10, sum(rate(container_cpu_cost[1h]) + rate(container_memory_cost[1h])) by (deployment))
```

### Autoscaling Metrics

```bash
# View HPA current metrics
kubectl describe hpa checkout-api-hpa -n team-checkout

# Current replicas vs desired replicas
kubectl get hpa -n team-checkout -o jsonpath='{.items[*].status.currentReplicas},{.items[*].status.desiredReplicas}'

# Pod count over time (indicates scaling activity)
kubectl get pods -n team-checkout --sort-by=.metadata.creationTimestamp
```

### Cost Anomaly Metrics

```promql
# Cost deviation from baseline (7-day average)
abs(rate(container_cost_total[1h]) - avg_over_time(rate(container_cost_total[1h])[7d]))

# Cost trend (hour-over-hour change)
(rate(container_cost_total[1h]) - rate(container_cost_total[1h] offset 1h)) / rate(container_cost_total[1h] offset 1h) * 100
```

---

## Best Practices and Recommendations

### 1. Define Clear SLOs Before Optimizing

Don't optimize for cost in isolation. Define Service Level Objectives (SLOs) first:
- **Uptime SLO**: 99.9% vs 99.99% (affects cost significantly)
- **Latency SLO**: p99 latency target (determines resource provisioning)
- **Scalability SLO**: Peak load handling requirements

Cost optimization then becomes: "What's the cheapest way to meet our SLOs?"

### 2. Start with HPA, Add VPA for Fine-Tuning

- **HPA First**: Deploy HPA to handle traffic spikes. Scales replicas automatically based on load
- **VPA Second**: After HPA stabilizes, use VPA (in "Off" mode) to get right-sizing recommendations
- **Combined**: Together, HPA handles capacity needs while VPA ensures each pod is right-sized

### 3. Right-Size Requests and Limits Carefully

- **Requests** (used by scheduler and HPA): Should match typical usage
- **Limits** (hard cap): Set 2-3x requests to handle spikes; don't set too high
- **Formula**: requests = p50 usage, limits = p99 usage

### 4. Use Spot Instances Strategically

**Good for spot:**
- Stateless workloads (web servers, APIs, batch jobs)
- Horizontally scalable services (HPA handles node loss)
- Non-latency-sensitive batch processing

**Avoid spot for:**
- Databases (unless using replicated setups)
- Long-running jobs without checkpointing
- Single-replica critical services

### 5. Enforce Cost Governance Gradually

- **Start with audit mode**: `validationFailureAction: audit` in Kyverno policies
- **Review violations**: See what existing workloads would violate the policy
- **Enforce**: Move to `validationFailureAction: enforce` after teams remediate

### 6. Label Everything for Cost Attribution

- **Required labels**: `team`, `cost-center`, `environment` (used for chargeback/showback)
- **Enforce via admission control**: Kyverno policy prevents unlabeled workloads
- **Review monthly**: Generate team reports showing their cost and trends

### 7. Monitor Anomalies Continuously

- **Set anomaly thresholds**: Start conservative (50% deviation from baseline)
- **Alert on multiple signals**: Sudden spike AND sustained increase
- **Automate investigation**: Script should pull logs, event traces, and resource metrics
- **Create runbooks**: Document how to respond to common cost anomalies

### 8. Combine Cost Optimization with FinOps Culture

Cost optimization is not just a technical problem—it's a cultural practice:
- **Transparency**: Show teams their costs monthly
- **Accountability**: Make cost a metric engineers care about (like latency)
- **Incentives**: Reward teams that optimize costs without sacrificing SLOs
- **Education**: Help teams understand the cost implications of their design choices

---

## Companion Website Alignment

The companion resource site at https://peh-packt.platformetrics.com/ provides:

### Chapter 12 Content on Companion Site

- **Chapter Overview**: Introduction to FinOps and cost optimization principles
- **Interactive Dashboards**: Example Grafana dashboards for cost visualization
- **Exercises**: Hands-on labs for deploying HPA, VPA, and cost governance
- **Tools & Technologies**: Links to OpenCost, Karpenter, VPA documentation
- **Case Studies**: Real-world examples of cost optimization (from the "NewTech" scenario in the chapter)

### Discrepancies and Notes

1. **OpenCost vs KubeCost**: The website and chapter materials consistently recommend **OpenCost (CNCF)** as the primary cost observability tool. KubeCost files are provided as alternatives for organizations already using KubeCost.

2. **Installation Scripts**: The `install-opencost.sh` script in this directory matches the companion website's OpenCost setup instructions. The script assumes Prometheus from Chapter 11 is already installed.

3. **Code Examples**: All code files (YAML, Python) are synchronized with the chapter manuscript. File references in the manuscript use "Listing X.X" format, which maps to specific code files.

4. **Exercises**: The companion website's Chapter 12 exercises reference these files:
   - `cost-analyzer.py` for analyzing current resource usage
   - `cost-allocation-labels.py` for validating team cost allocation
   - `test-cost-optimization.py` for integration testing

### How to Use the Companion Website

1. **Read the chapter**: Start with the manuscript for concepts and theory
2. **Reference the companion site**: View dashboards and case studies to understand practical application
3. **Run the code**: Execute the scripts and configurations from this directory
4. **Do the exercises**: Complete the hands-on labs on the companion website
5. **Review results**: Verify your setup against the expected outputs documented here

---

## Troubleshooting Guide

### HPA Not Scaling

**Symptom**: HPA created but replicas remain at minReplicas despite high CPU

**Root Causes & Solutions**:

```bash
# 1. Verify Metrics Server is running
kubectl get deployment metrics-server -n kube-system
# Expected: 1 replica running

# 2. Check if metrics are available
kubectl get --raw /apis/metrics.k8s.io/v1beta1/namespaces/team-checkout/pods
# Expected: JSON output with CPU and memory metrics

# 3. Verify pod has resource requests (required for HPA)
kubectl get deployment checkout-api -n team-checkout -o yaml | grep -A 5 requests:
# Expected: cpu: 100m, memory: 256Mi (or similar)

# 4. Check HPA status and events
kubectl describe hpa checkout-api-hpa -n team-checkout
# Look for "unknown" metrics or recent warnings

# Solution: If metrics unknown, wait 1-2 minutes for metrics to populate
# If requests missing, add to deployment:
# resources:
#   requests:
#     cpu: 100m
#     memory: 256Mi
```

### VPA Not Providing Recommendations

**Symptom**: VPA created but `kubectl describe vpa` shows no recommendations

**Root Causes & Solutions**:

```bash
# 1. Verify VPA controller is installed
kubectl get deployment vpa-recommender -n kube-system
# If not found, VPA is not installed (optional component)

# 2. Check if pod has run long enough (needs 8+ hours of metrics)
kubectl logs -n kube-system -l app=vpa-recommender | grep checkout-api
# Look for: "recommendations calculated"

# 3. Verify pod has CPU/memory metrics available
kubectl top pod -n team-checkout
# Expected: CPU and memory values shown

# Solution: Wait 8+ hours of pod runtime before expecting recommendations
# For testing, you can generate load to collect metrics faster
```

### Cost Allocation Labels Not Appearing in Reports

**Symptom**: `python3 cost-allocation-labels.py` reports workloads without team labels

**Root Causes & Solutions**:

```bash
# 1. Verify labels are applied to namespace
kubectl get ns team-checkout --show-labels
# Expected: team=checkout, cost-center=4521

# 2. Verify labels are applied to deployments
kubectl get deployment -n team-checkout -o jsonpath='{.items[*].spec.selector.matchLabels}'
# Expected: app: checkout-api, team: checkout

# 3. Run label validation script
python3 cost-allocation-labels.py --namespace team-checkout

# Solution: Apply labels manually or update manifests
# kubectl label namespace team-checkout team=checkout cost-center=4521
```

### ResourceQuota Rejecting Valid Pods

**Symptom**: Pod creation fails with "exceeded quota" error even though not all quota used

**Root Causes & Solutions**:

```bash
# 1. Check current quota usage
kubectl describe resourcequota -n team-checkout
# Look at "Used" vs "Hard" limits

# 2. Check for pending pods consuming quota
kubectl get pods -n team-checkout --all-namespaces | grep Pending

# 3. Check requested resources of the pod being rejected
kubectl get pod -n team-checkout <pod-name> -o yaml | grep -A 5 resources:

# Solution: Either increase quota or reduce resource requests
# kubectl edit resourcequota team-checkout-quota -n team-checkout
# Increase the hard limits as needed
```

### Cost Anomaly Alerts Firing Constantly

**Symptom**: `CostAnomalyDetected` alert fires frequently with legitimate traffic spikes

**Root Causes & Solutions**:

```bash
# 1. Check alert threshold (default is 50% deviation from 7-day baseline)
kubectl get prometheusrule cost-anomalies -n monitoring -o yaml | grep -A 5 expr:

# 2. Check for legitimate scaling events in events log
kubectl get events -n team-checkout --sort-by='.lastTimestamp' | grep -i scaling

# Solution: Adjust alert threshold in cost-alerts.yaml
# Change threshold from 0.5 (50%) to 0.7 (70%) for less sensitive alerting
# Or exclude scheduled scaling events by time of day
```

### Spot Instance Pods Being Evicted Immediately

**Symptom**: Pods scheduled on spot nodes are evicted after seconds/minutes

**Root Causes & Solutions**:

```bash
# 1. Check if pods have appropriate PodDisruptionBudget
kubectl get pdb -n team-checkout
# Expected: minAvailable: 1 or other acceptable value

# 2. Check if pod has graceful termination period
kubectl get pod -n team-checkout <pod-name> -o yaml | grep terminationGracePeriodSeconds

# 3. Check if pod can handle SIGTERM
# Verify application logs: "Received signal, shutting down gracefully"

# Solution:
# - Add PodDisruptionBudget: minAvailable: 1 (keep at least 1 replica up)
# - Add graceful shutdown: terminationGracePeriodSeconds: 30
# - Ensure app handlers SIGTERM and stops accepting new requests
```

---

## Additional Resources and References

### Official Documentation
- **OpenCost Documentation**: https://www.opencost.io/docs
- **Kubernetes HPA**: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- **Kubernetes VPA**: https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler
- **Karpenter**: https://karpenter.sh/docs/
- **Kyverno**: https://kyverno.io/docs/

### FinOps Resources
- **FinOps Foundation**: https://www.finops.org/
- **FinOps Principles**: https://www.finops.org/framework/principles/
- **Cloud Cost Management**: https://www.finops.org/framework/phases/

### Kubernetes Cluster Inspection Commands

```bash
# View pod metrics
kubectl top pods -n team-checkout --containers
kubectl top nodes

# Check HPA metrics and history
kubectl get hpa -n team-checkout -w
kubectl get hpa -n team-checkout -o jsonpath='{.items[*].status.currentMetrics}'

# View node resource allocation
kubectl describe nodes | grep -A 5 "Allocated resources"

# Check resource requests vs usage cluster-wide
kubectl get pods --all-namespaces -o json | jq '.items[] | {name: .metadata.name, namespace: .metadata.namespace, requests: .spec.containers[].resources.requests}'

# Monitor cost allocation (if OpenCost installed)
kubectl port-forward -n opencost svc/opencost 9003:9003
# Then: curl http://localhost:9003/allocation/compute?window=24h&aggregate=namespace
```

### Python Script Usage

```bash
# Analyze specific namespace
python3 cost-analyzer.py --namespace team-checkout --show-waste

# Generate JSON output for integration
python3 cost-analyzer.py --all-namespaces --output-format json > resource-analysis.json

# Validate cost labels and generate CSV report
python3 cost-allocation-labels.py --report-by team --output csv > cost-allocation.csv

# Run full test suite
python3 test-cost-optimization.py -v

# Detect anomalies with custom threshold
python3 cost-anomaly-detector.py --monitor --threshold 3.0 --lookback-hours 24
```

---

## Summary

This directory contains all the code, configurations, and tools needed to implement cost optimization practices in your Kubernetes platform. The files are organized by topic and cross-referenced to the chapter manuscript.

**Key takeaways:**
1. **Define SLOs first**, then optimize cost within those constraints
2. **Use OpenCost** (CNCF) for Kubernetes-native cost visibility
3. **Combine HPA + VPA** for comprehensive autoscaling
4. **Enforce governance** with ResourceQuotas and admission policies
5. **Allocate costs by team** for transparency and accountability
6. **Monitor anomalies** to catch unexpected increases early

For questions or issues, refer to the troubleshooting guide above, consult the companion website, or review the manuscript sections referenced in the "Code-to-Chapter Mapping" table.
