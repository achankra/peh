# Chapter 4: Embedding Observability - Code Examples

## Overview

This directory contains comprehensive, production-ready examples for implementing observability in platform engineering using OpenTelemetry, Prometheus, Grafana, and Jaeger. The code demonstrates the three pillars of observability (metrics, logs, traces), integrates with the OTEL Collector, and shows how to build persona-specific dashboards and observability-driven deployment practices.

**Key Concepts Covered:**
- OpenTelemetry standardization and vendor independence
- Pull-based metrics collection (Prometheus)
- Push-based trace collection (OTLP/Jaeger)
- Single Pane of Glass (SPOG) architecture for observability
- Observability-Driven Development (ODD)
- Persona-specific dashboards (Developer, SRE, Management, Security)
- Observability-driven deployment gates
- Alert rules based on observability data

---

## Code-to-Chapter Mapping

This section maps each code file to specific sections, concepts, and listings in Chapter 4 of "The Platform Engineer's Handbook."

### Python Applications and Tools

#### `otel_setup.py`
**Maps to:** Section "Standardization with OpenTelemetry" and Chapter Listing 1
**Demonstrates:**
- TracerProvider initialization with OTLP exporter
- MeterProvider configuration for metrics collection
- Resource attributes and semantic conventions
- Service identification and deployment context
- Batch span processor for performance optimization
- Periodic metric export configuration
- Reusable setup functions for service instrumentation

**Key Functions:**
- `setup_tracing()` - Initializes distributed tracing with resource metadata
- `setup_metrics()` - Configures metrics collection with periodic export
- `initialize_observability()` - Complete one-shot initialization for both tracing and metrics

**Related Chapter Content:**
- Code Snippet 1: "Instrumenting your application with OTEL"
- Discusses vendor-neutral OpenTelemetry Protocol (OTLP)
- Semantic conventions for consistent attribute naming

---

#### `instrument-app.py`
**Maps to:** Section "Standardization with OpenTelemetry" and Chapter Listing 1
**Demonstrates:**
- Complete WSGI application with OTEL instrumentation
- Automatic trace instrumentation using decorators (`@traced`)
- Custom span attributes and events
- Structured logging with context propagation
- Metrics collection (request count, errors, latency percentiles)
- Optional OTEL SDK integration (graceful fallback if not installed)
- Error handling and exception recording in spans
- Prometheus metrics endpoint for scraping

**Key Features:**
- `StructuredLogger` class: JSON-formatted logs with context
- `MetricsCollector` class: In-memory metrics storage with percentile calculation
- `@traced` decorator: Automatic span creation for functions
- `SimpleWSGIApp` class: HTTP application with endpoints for health, data, metrics, error simulation
- Raw HTTP server implementation (no external dependencies required)

**Endpoints:**
- `/health` - Health check endpoint
- `/api/data` - Returns simulated data with optional delay parameter
- `/metrics` - Prometheus text-format metrics endpoint
- `/error` - Intentional error endpoint for testing error handling

**Related Chapter Content:**
- Demonstrates the three pillars: traces, metrics, logs
- Shows how applications instrument themselves once with OTEL
- Eliminates vendor lock-in through standardized instrumentation

---

#### `metrics_pull.py`
**Maps to:** Section "Ingestion methods (push vs pull)" and Code Snippet 2
**Demonstrates:**
- Prometheus pull-based metrics collection
- Prometheus Client Python library usage
- Metric types: Counter, Histogram, Gauge
- Prometheus text-format metrics endpoint (`/metrics`)
- Decorator-based automatic metrics tracking
- Flask web application with OTEL-instrumented endpoints

**Key Metrics:**
- `http_requests_total` - Counter with method, endpoint, status labels
- `http_request_duration_seconds` - Histogram with custom buckets (5ms to 5s)
- `http_active_connections` - Gauge for connection pool monitoring

**Pull Model Advantages:**
- Centralized control: Prometheus initiates all scrapes
- No client-side buffering: Reduces data loss points
- Service discovery: Works with Kubernetes annotations and SDKs
- Scrape interval control: Prometheus determines timing

**Flask Endpoints:**
- `/health` - Health check with metrics tracking
- `/api/items` - Data retrieval with artificial delay
- `/metrics` - Prometheus scrape endpoint (default 30s interval)

**Related Chapter Content:**
- Code Snippet 2: "Demonstrating the pull mode of ingestion"
- Shows how metrics are exposed for Prometheus scraping
- Demonstrates metric labels for categorization

---

#### `traces_push.py`
**Maps to:** Section "Ingestion methods (push vs pull)" and Code Snippet 3
**Demonstrates:**
- OTLP push-based trace collection
- Parent-child span relationships in distributed systems
- Semantic attributes for context and analysis
- Event recording in spans
- Exception handling in spans
- Batch span processor for efficient export
- Service resource attributes and metadata

**Key Functions:**
- `initialize_tracer()` - Sets up TracerProvider with OTLP exporter
- `process_user_request()` - Parent span with business logic attributes
- `validate_user_action()` - Child span for validation logic
- `perform_action()` - Child span for business processing

**Span Attributes & Events:**
- HTTP method and URL attributes
- User ID and action tracking
- Custom events: "user_request_started", "user_request_completed", "action_executed"
- Exception recording for error analysis
- Status codes for result tracking

**Push Model Advantages:**
- Immediate visibility: No waiting for scrape intervals
- Cross-network support: Works across network boundaries
- Application-initiated: Reduces load on target pods
- Buffering: OTEL Collector handles retries and batching

**Related Chapter Content:**
- Code Snippet 3: "OTLP Push-Based Trace Collection" (implicit in chapter)
- Demonstrates why traces are essential for unknown unknowns
- Shows parent-child span hierarchy for RCA (Root Cause Analysis)

---

#### `observability-personas.py`
**Maps to:** Section "Single pane of glass (SPOG) architecture"
**Demonstrates:**
- Persona-specific dashboard generation for Grafana
- Tailored metrics views for different stakeholder needs
- Grafana dashboard JSON structure and panel configuration
- PromQL queries for different personas

**Four Personas Generated:**

1. **Developer Dashboard**
   - Focus: Application performance, debugging, error tracing
   - Panels: Request latency, error rates, request counts, response size, database queries, cache hit rates
   - Questions: What's my service doing? Why is it slow? What went wrong?
   - 6 panels with application-focused metrics

2. **SRE Dashboard**
   - Focus: Infrastructure health, reliability, resource utilization
   - Panels: Pod availability, node resource utilization, error rates, SLA compliance, pod restarts, persistent volume usage
   - Questions: Is the platform healthy? Are we meeting SLAs? What's failing?
   - 6 panels with infrastructure-focused metrics

3. **Management Dashboard**
   - Focus: Business metrics, SLA compliance, user impact
   - Panels: Service availability, MTTR, request volume, critical incidents, revenue impact, customer issues
   - Questions: Are we meeting our commitments? What's the business impact?
   - 6 panels with business-focused metrics

4. **Security Dashboard**
   - Focus: CVE tracking, compliance, unauthorized access
   - Panels: Critical CVEs, vulnerability scans, 401 attempts, suspicious activity (403/404), compliance status, image scan coverage
   - Questions: Are we secure? What vulnerabilities exist? Is there suspicious activity?
   - 6 panels with security-focused metrics

**Output:**
- Generates Grafana dashboard JSON files for each persona
- Can be imported directly into Grafana UI
- All dashboards use same Prometheus datasource with different queries

**Usage:**
```bash
# Generate all dashboards
python3 observability-personas.py --output-dir ./dashboards

# Generate specific persona
python3 observability-personas.py --persona developer --output-dir ./dashboards

# Print JSON to stdout
python3 observability-personas.py --persona sre --print
```

**Related Chapter Content:**
- Demonstrates SPOG concept: single interface for multiple personas
- Shows how to serve diverse stakeholder needs from unified data
- Eliminates "shadow IT" by providing self-service dashboards
- Reduces context switching across disparate tools

---

#### `test-observability.py`
**Maps to:** Chapter's discussion of validation and testing observability infrastructure
**Demonstrates:**
- Unit tests for observability stack configuration
- File validation (configuration files exist and are valid)
- YAML syntax validation for OTEL Collector configuration
- Grafana dashboard JSON validation
- Python code compilation check
- Alert rules validation

**Test Classes:**

1. **TestOTELCollector**
   - Validates collector configuration file exists
   - Validates deployment manifest exists
   - Ensures all three pipelines (metrics, traces, logs) are configured

2. **TestGrafanaDashboard**
   - Validates dashboard JSON is syntactically correct
   - Ensures dashboard has at least one panel
   - Checks for required fields (title, panels)

3. **TestAlertRules**
   - Validates alert rules file exists
   - Ensures alert rules include severity labels

4. **TestInstrumentedApp**
   - Validates Python application code compiles without syntax errors

**Usage:**
```bash
# Run all tests with verbose output
python3 test-observability.py --verbose

# Run specific test class
python3 test-observability.py TestOTELCollector
```

**Related Chapter Content:**
- Shows the importance of validating observability configuration
- Demonstrates testing as part of platform engineering practice
- Ensures observability setup is correct before deployment

---

### Configuration Files

#### `otel-collector-config.yaml`
**Maps to:** Section "Automatic Telemetry Ingestion" and platform responsibility discussion
**Demonstrates:**
- Complete OTEL Collector configuration with all receiver types
- Receiver configuration: OTLP (gRPC + HTTP), Prometheus, Syslog, Jaeger
- Processor pipeline: Batch, Memory Limiter, Attributes, Resource Detection, Sampling
- Exporter configuration: Prometheus, Loki, Jaeger, Debug logging
- Service pipeline setup for metrics, traces, logs
- Health check and performance profiling extensions

**Receivers:**
- **OTLP**: gRPC (port 4317) and HTTP (port 4318) for application instrumentation
- **Prometheus**: Kubernetes service discovery with annotation-based scraping
- **Syslog**: RFC5424 protocol for traditional log ingestion (port 514)
- **Jaeger**: Native Jaeger protocol support (gRPC 14250, HTTP 14268)

**Processors (in order):**
- `batch`: Groups telemetry for efficient export (1024 batch size, 10s timeout)
- `memory_limiter`: Prevents OOM (512 MB limit, 128 MB spike limit)
- `attributes`: Adds environment and namespace attributes
- `resourcedetection`: Auto-detects cloud/K8s/Docker/system attributes
- `sampling`: Configurable sampling (100% for development, 1% for production)

**Exporters:**
- `prometheus`: Exposes metrics on port 8889 for scraping
- `otlp`: Sends traces/metrics to Jaeger backend
- `loki`: Ships logs to Grafana Loki for log aggregation
- `jaeger`: Sends traces to Jaeger backend (primary trace destination)
- `logging`: Debug exporter to console (remove in production)

**Pipelines:**
- `metrics`: OTLP + Prometheus → Prometheus exporter
- `traces`: OTLP + Jaeger → Jaeger exporter
- `logs`: Syslog → Loki exporter

**Related Chapter Content:**
- Shows how platform team centralizes collector configuration
- Demonstrates receiver variety for different data sources
- Shows processor flexibility for data enrichment
- Illustrates exporters for multiple backends

---

#### `otel-collector-deployment.yaml`
**Maps to:** Section "Automatic Telemetry Ingestion" and platform infrastructure responsibility
**Demonstrates:**
- Kubernetes DaemonSet for node-level collector deployment
- Complete Kubernetes RBAC (ClusterRole, ClusterRoleBinding, ServiceAccount)
- ConfigMap for configuration management
- Services for internal and external access
- Resource requests/limits for production environments
- Health checks (liveness and readiness probes)
- Network policies and security contexts
- Node affinity and tolerations for cluster-wide deployment
- Kubernetes service discovery integration

**Kubernetes Resources:**

1. **Namespace**
   - Creates dedicated `observability` namespace for isolation

2. **ConfigMap**
   - Stores OTEL Collector configuration
   - Embedded collector configuration (inline YAML)

3. **RBAC (ServiceAccount, ClusterRole, ClusterRoleBinding)**
   - Allows collector to list/watch pods, nodes, endpoints
   - Enables Kubernetes service discovery
   - Principle of least privilege

4. **Services**
   - `otel-collector`: Main service for application communication
     - OTLP gRPC (4317), OTLP HTTP (4318)
     - Jaeger gRPC (14250)
     - Metrics (8889), Health check (13133)
   - `otel-collector-metrics`: Separate metrics scrape endpoint

5. **DaemonSet**
   - Runs on all Linux nodes (node affinity)
   - Rolling update strategy (max 1 unavailable)
   - Host network and PID enabled for node-level access
   - Tolerations for all taints (NoSchedule, NoExecute)

**Container Configuration:**
- Image: `otel/opentelemetry-collector-k8s:0.88.0`
- Resource requests: 100m CPU, 256 Mi memory
- Resource limits: 500m CPU, 512 Mi memory
- Liveness probe: HTTP on health check port (30s initial delay, 30s period)
- Readiness probe: HTTP on health check port (10s initial delay, 10s period)
- Non-root user with read-only filesystem preference

**Environment Variables:**
- `GOGC`: Garbage collection tuning (80%)
- `NODE_NAME`, `NAMESPACE`, `POD_NAME`: Runtime context

**Related Chapter Content:**
- Demonstrates platform team responsibility for collector infrastructure
- Shows how to deploy collectors for automatic telemetry ingestion
- Illustrates HA setup and operational considerations
- Describes shared responsibility model between platform and applications

---

#### `alert-rules.yaml`
**Maps to:** Chapter's discussion of observability-driven deployment and incident response
**Demonstrates:**
- Alert rules for all three pillars of observability
- Multiple alert severity levels and team assignments
- Recording rules for metric pre-computation
- Context-rich annotations for incident response
- Links to dashboards, traces, and runbooks
- Alerts for platform health, application performance, and business impact
- Security and compliance-focused alerts

**Alert Groups:**

1. **http_service_alerts**
   - `HighErrorRate`: >5% error rate for 5 minutes (critical)
   - `HighP99Latency`: P99 latency >1.0s for 5 minutes (warning)
   - `HighP95Latency`: P95 latency >0.5s for 10 minutes, SRE team (warning)

2. **kubernetes_alerts**
   - `PodRestartingLoop`: Restart rate >0.1/min (critical)
   - `PodNotReady`: Pod not ready for 10 minutes (critical)
   - `NodePressure`: Memory or disk pressure for 5 minutes (critical)
   - `NodeHighCPU`: CPU >85% for 10 minutes, SRE team (warning)
   - `NodeHighMemory`: Memory >85% for 10 minutes, SRE team (warning)

3. **otel_collector_alerts**
   - `OTELCollectorDown`: Collector down for 2 minutes (critical)
   - `OTELCollectorHighMemory`: Memory >80% of limit (warning)
   - `OTELCollectorSpanDropped`: Spans dropped at rate >100/sec (warning)

4. **platform_business_alerts**
   - `SLAViolation`: Availability <99% for 10 minutes, management team (critical)
   - `ServiceDegraded`: Error rate >1% for 5 minutes, management team (warning)

5. **security_and_compliance_alerts**
   - `CVEDetected`: New CVE found in images (critical, security team)
   - `UnauthorizedAccessAttempt`: 401 rate >10/sec for 2 minutes (warning, security team)
   - `SuspiciousActivity`: 403/404 rate >50/sec for 5 minutes (warning, security team)

6. **deployment_and_rollout_alerts**
   - `DeploymentStuck`: No progress for 15 minutes (critical)
   - `CanaryDeploymentRollback`: Error rate >5% in canary (critical)

**Recording Rules:**
Pre-computed metrics for faster dashboard queries:
- `http_requests:rate5m` - Request rate over 5 minutes
- `http_errors:rate5m` - Error rate over 5 minutes
- `http_latency:p99` - 99th percentile latency
- `http_latency:p95` - 95th percentile latency

**Annotation Fields:**
- `summary`: Alert title and context
- `description`: Detailed explanation with Prometheus template variables
- `dashboard`: Link to relevant Grafana dashboard
- `trace`: Link to Jaeger traces for the service
- `runbook`: Link to incident response runbook
- `kubectl`: kubectl command for diagnosis
- `logs`: kubectl logs command for investigation
- `action`: Recommended action (auto-remediation hint)
- `escalate`: Escalation path for critical alerts
- `check`: Verification steps

**Related Chapter Content:**
- Shows integration of observability with incident response
- Demonstrates how alerts enable observability-driven deployment
- Illustrates persona-specific alert routing (SRE, management, security)
- Shows MTTR reduction through actionable alerts

---

#### `grafana-dashboard-platform.json`
**Maps to:** Section "Single pane of glass (SPOG) architecture"
**Demonstrates:**
- Complete Grafana dashboard JSON structure
- Prometheus datasource integration
- Multiple panel types for different visualizations
- Time series visualization for metrics
- Custom thresholds and color schemes
- Legend configuration and tooltips
- Multiple metrics on single dashboard

**Dashboard Features:**
- **Title**: "Platform Observability Dashboard"
- **Refresh Rate**: 30 seconds
- **Time Range**: Last 6 hours
- **Total Panels**: 8+ panels (latency, errors, availability, etc.)

**Panels Included:**
1. **Request Latency Distribution** (p50, p95, p99 percentiles)
   - Time series visualization
   - Legend with mean, max, min calculations
   - Unit: milliseconds

2. **Error Rate** (HTTP 5xx status codes)
   - Shows percentage of failed requests
   - Tracks by endpoint or job

3. **Pod Health Status**
   - Pod availability metrics
   - Restart tracking

4. **Node Resource Utilization**
   - CPU usage percentage
   - Memory usage percentage

5. **Service SLA Compliance**
   - Availability percentage
   - Threshold alerts on 99% SLA

6. **Request Volume**
   - Request rate over time
   - By endpoint or service

7. **Database Query Performance**
   - Query latency percentiles
   - Connection pool status

8. **Cache Efficiency**
   - Hit/miss rates
   - Cache utilization

**Related Chapter Content:**
- Demonstrates SPOG concept with unified dashboard
- Shows how to combine metrics from multiple services
- Illustrates dashboard serving multiple personas
- Shows Prometheus PromQL integration

---

## Prerequisites

### Software Requirements
- **Python 3.8+** - For running Python scripts
- **Kubernetes 1.20+** - For DaemonSet deployment (optional)
- **kubectl** - For Kubernetes operations
- **Docker/Container Runtime** - For running OTEL Collector in containers

### External Services
- **Prometheus 2.30+** - For metrics scraping and storage
- **Grafana 8.0+** - For dashboard visualization and alerting
- **Jaeger** - For distributed trace storage and visualization (optional but recommended)
- **Loki** - For log aggregation (optional)

### Python Dependencies

Install required packages for running Python examples:

```bash
# Core OTEL packages
pip install opentelemetry-api opentelemetry-sdk

# Exporters
pip install opentelemetry-exporter-otlp
pip install opentelemetry-exporter-jaeger  # For Jaeger backend
pip install opentelemetry-exporter-prometheus  # For Prometheus integration

# Instrumentation libraries
pip install opentelemetry-instrumentation-wsgi
pip install opentelemetry-instrumentation-flask

# Additional packages
pip install prometheus-client  # For metrics_pull.py
pip install flask  # For Flask-based applications
```

**Optional: Install all at once**

```bash
pip install \
  opentelemetry-api \
  opentelemetry-sdk \
  opentelemetry-exporter-otlp \
  opentelemetry-exporter-jaeger \
  opentelemetry-instrumentation-wsgi \
  opentelemetry-instrumentation-flask \
  prometheus-client \
  flask
```

### Environment Configuration

Set these environment variables before running applications:

```bash
# OTEL Collector endpoint
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"

# Service identification
export SERVICE_NAME="my-service"
export SERVICE_VERSION="1.0.0"

# Deployment context
export DEPLOYMENT_ENV="development"  # or "production"
export HOSTNAME="worker-1"
```

---

## Step-by-Step Instructions

This section provides detailed instructions for running each component in the recommended order.

### Phase 0: Deploy Monitoring Stack (Prometheus + Grafana)

The observability stack requires Prometheus and Grafana running in-cluster. Deploy them first if not already installed:

```bash
# Deploy kube-prometheus-stack (Prometheus + Grafana + Alertmanager)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

# Wait for pods to be ready (1-2 minutes)
kubectl get pods -n monitoring

# Port-forward Prometheus and Grafana for local access
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090 &
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80 &

# Retrieve the Grafana admin password
kubectl get secret monitoring-grafana -n monitoring -o jsonpath='{.data.admin-password}' | base64 -d; echo
```

Open [http://localhost:3000](http://localhost:3000) and log in with username `admin` and the password from the command above.

> **Note:** If the monitoring stack is already installed (e.g., from Chapter 2 via Flux), the `helm install` command will error with "cannot re-use a name that is still in use" — that's fine, it means the stack is already running. If you've recreated your Kind cluster (e.g., after a Docker restart), you will need to redeploy — see the main [README](../../README.md#surviving-docker--kind-restarts) for details.

**Expected Output:**
```
NAME                                                     READY   STATUS    RESTARTS   AGE
alertmanager-monitoring-kube-prometheus-alertmanager-0    2/2     Running   0          2m
monitoring-grafana-xxxxx                                 3/3     Running   0          2m
monitoring-kube-prometheus-operator-xxxxx                 1/1     Running   0          2m
monitoring-kube-state-metrics-xxxxx                       1/1     Running   0          2m
prometheus-monitoring-kube-prometheus-prometheus-0         2/2     Running   0          2m
```

### Phase 1: Infrastructure Setup (Kubernetes)

If running on Kubernetes, deploy the OTEL Collector first:

> **Note:** The deployment uses `otel/opentelemetry-collector-contrib:0.98.0`. The config uses the `debug` exporter (replaces the deprecated `logging` exporter) and `otlp/jaeger` (replaces the removed native `jaeger` exporter — Jaeger now accepts OTLP natively on port 4317).

```bash
# Create observability namespace and deploy OTEL Collector
kubectl apply -f otel-collector-deployment.yaml

# Wait for DaemonSet to be ready (readiness probe has a 30s initial delay)
kubectl wait --for=condition=ready pod \
  -l app=otel-collector \
  -n observability \
  --timeout=300s

# Verify deployment
kubectl get pods -n observability
kubectl logs -l app=otel-collector -n observability

# Port-forward the OTel Collector so locally-run apps can export traces
# Without this, apps running on your machine cannot reach the collector
# inside the Kind cluster and you will see "Failed to export traces to
# localhost:4317, error code: StatusCode.UNAVAILABLE" errors.
kubectl port-forward -n observability svc/otel-collector 4317:4317 &
```

**Expected Output:**
```
NAME                             READY   STATUS    RESTARTS   AGE
otel-collector-xxxxx             1/1     Running   0          2m
otel-collector-xxxxx             1/1     Running   0          2m
```

### Phase 2: Local Development Setup (Non-Kubernetes)

For local development without Kubernetes:

```bash
# 1. Start OTEL Collector in Docker
docker run -d \
  --name otel-collector \
  -v $(pwd)/otel-collector-config.yaml:/etc/otel/config.yaml \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 8889:8889 \
  otel/opentelemetry-collector-k8s:0.88.0 \
  --config=/etc/otel/config.yaml

# 2. Verify collector is running
docker logs otel-collector
curl http://localhost:13133/  # Health check endpoint
```

**Expected Output:**
```
{"status":"Server started"}
```

### Phase 3: Validate Observability Stack

Run the test suite to validate configuration:

```bash
# Run all tests
python3 test-observability.py -v

# Expected output:
# test_collector_config_exists ... ok
# test_collector_deployment_exists ... ok
# test_collector_has_all_pipelines ... ok
# test_dashboard_is_valid_json ... ok
# test_dashboard_has_panels ... ok
# test_alert_rules_exist ... ok
# test_alert_rules_have_severity ... ok
# test_app_is_valid_python ... ok
#
# Ran 8 tests in 0.234s
# OK
```

### Phase 4: Run Instrumented Application

Start the example application with OTEL instrumentation:

```bash
# Set environment for OTEL Collector
export OTEL_EXPORTER_OTLP_ENDPOINT="localhost:4317"
export SERVICE_NAME="example-app"

# Install dependencies (if not already installed)
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp

# Run the application
python3 instrument-app.py

# Expected output:
# 2025-02-21 14:23:45 - platform-app - INFO -
# {"timestamp": "2025-02-21T14:23:45.123456",
#  "level": "INFO",
#  "message": "Starting instrumented application",
#  "context": {"otel_enabled": true}}
# 2025-02-21 14:23:45 - platform-app - INFO -
# {"timestamp": "2025-02-21T14:23:45.234567",
#  "level": "INFO",
#  "message": "Server listening on http://0.0.0.0:8000"}
```

**Test the application (in a new terminal):**

```bash
# Health check
curl http://localhost:8000/health

# Simulate requests with different latencies
curl "http://localhost:8000/api/data?delay=0.1"
curl "http://localhost:8000/api/data?delay=0.5"

# View metrics
curl http://localhost:8000/metrics

# Trigger an error for trace testing
curl http://localhost:8000/error
```

### Phase 5: Run Metrics Pull Example

In another terminal, run the Flask-based metrics example:

```bash
# Install Flask and prometheus_client
pip install flask prometheus-client

# Run the application
python3 metrics_pull.py

# Expected output:
# WARNING in app.run - Running on http://0.0.0.0:5000
# Press CTRL+C to quit
```

**Test the metrics endpoint:**

```bash
# Generate requests
curl http://localhost:5000/health
curl http://localhost:5000/api/items

# View metrics in Prometheus format
curl http://localhost:5000/metrics
```

**Expected Prometheus metrics output:**
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="health",status="200"} 1.0

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="health",le="0.005"} 1.0
http_request_duration_seconds_bucket{method="GET",endpoint="health",le="0.01"} 1.0
...
```

### Phase 6: Run Traces Push Example

In another terminal, run the trace collection example:

```bash
# Run the traces example
python3 traces_push.py

# Expected output:
# 2025-02-21 14:25:30,123 - root - INFO - Request result:
# {'success': True, 'result': {'action': 'update', 'status': 'completed', 'duration_ms': 101.23}}
```

**Check OTEL Collector logs for trace receipt:**

```bash
# View collector logs (if running in Kubernetes)
kubectl logs -l app=otel-collector -n observability

# Or for Docker:
docker logs otel-collector | grep "span"
```

**Expected output:**
```
otel_collector: ResourceSpans#0
otel_collector: InstrumentationLibrarySpans#0
otel_collector: Span#0
  Trace ID: 4bf92f3577b34da6a3ce929d0e0e4736
  Parent ID:
  ID: 7a5ece4ef8e9f5f9
  Name: process_user_request
  ...
```

### Phase 7: Generate Persona Dashboards

Create Grafana dashboards for different stakeholders:

```bash
# Generate all persona dashboards
python3 observability-personas.py --output-dir ./dashboards

# Expected output:
# Generated: ./dashboards/dashboard-developer.json
# Prometheus data source: Developer Dashboard - Application Metrics
#   - Persona: developer
#   - Tags: developer, application, debug
#   - Panels: 6
#
# Generated: ./dashboards/dashboard-sre.json
# Prometheus data source: SRE Dashboard - Platform Health
#   - Persona: sre
#   - Tags: sre, infrastructure, reliability
#   - Panels: 6
# ...

# Verify generated files
ls -lh ./dashboards/
```

**Generate a specific persona dashboard:**

```bash
# Developer dashboard
python3 observability-personas.py --persona developer --output-dir ./dashboards

# Or print to stdout
python3 observability-personas.py --persona security --print | jq '.title'
# Output: "Security Dashboard - CVE & Compliance"
```

### Phase 8: Import Dashboards into Grafana

Configure Grafana with the dashboards and alerts:

```bash
# Open Grafana UI (default: http://localhost:3000)
# Default credentials: admin / admin

# Via Grafana UI:
# 1. Navigate to: Dashboards → New → Import
# 2. Click "Upload JSON file"
# 3. Select each file from ./dashboards/ directory
# 4. Choose Prometheus datasource
# 5. Import

# Via Grafana API (if automation is desired):
for dashboard in ./dashboards/*.json; do
  curl -X POST http://localhost:3000/api/dashboards/db \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_API_TOKEN" \
    -d @"$dashboard"
done
```

### Phase 9: Configure Alert Rules

Import the alert rules into Prometheus:

```bash
# Copy alert rules to Prometheus config directory
cp alert-rules.yaml /etc/prometheus/rules/

# Reload Prometheus configuration
curl -X POST http://localhost:9090/-/reload

# Or if running in Kubernetes:
kubectl create configmap prometheus-rules \
  --from-file=alert-rules.yaml \
  -n prometheus \
  --dry-run=client -o yaml | kubectl apply -f -

# Verify rules are loaded
curl http://localhost:9090/api/v1/rules | jq '.data.groups[0].rules' | head -20
```

### Phase 10: Generate Load for Testing

Create synthetic traffic to test the full observability stack:

```bash
# Simple load generation script
for i in {1..100}; do
  # Normal request
  curl -s "http://localhost:8000/api/data?delay=0.1" > /dev/null

  # Occasional slow request
  if [ $((i % 20)) -eq 0 ]; then
    curl -s "http://localhost:8000/api/data?delay=0.5" > /dev/null
  fi

  # Occasional error
  if [ $((i % 50)) -eq 0 ]; then
    curl -s "http://localhost:8000/error" > /dev/null
  fi

  sleep 0.1
done

echo "Load generation complete"
```

### Phase 11: View Results in Grafana

Navigate to your dashboards and verify data is flowing:

```
1. Open Grafana: http://localhost:3000
2. Go to: Dashboards → Platform Observability Dashboard
3. Verify panels show:
   - Request latency (p50, p95, p99)
   - Error rate trending
   - Pod health status
   - Resource utilization graphs
```

**Debugging Tips:**

If dashboards are empty:
1. Check Prometheus datasource configuration: Settings → Data Sources → Prometheus
2. Test datasource connection
3. Verify metric names match: Go to Explore → Metrics → http_requests_total
4. Check time range (should be "last 6 hours")

### Phase 12: Verify Traces in Jaeger (Optional)

If Jaeger is configured:

```bash
# Open Jaeger UI: http://localhost:16686
# 1. Select service from dropdown: "trace-demo-service"
# 2. Click "Find Traces"
# 3. Verify traces appear with spans:
#    - process_user_request (parent)
#    - validate_user_action (child)
#    - perform_action (child)
```

---

## Troubleshooting Guide

### OTEL Collector Issues

**Problem: Collector not receiving data**

```bash
# Check collector health
curl http://localhost:13133/

# Check collector logs
docker logs otel-collector | grep -i error
kubectl logs -l app=otel-collector -n observability | grep -i error

# Verify application can reach collector
python3 -c "import socket; socket.create_connection(('localhost', 4317), timeout=5)"
```

**Solution:** Verify OTEL_EXPORTER_OTLP_ENDPOINT matches collector location.

### Metrics Not Appearing in Prometheus

**Problem: Metrics endpoint not being scraped**

```bash
# Verify metrics endpoint is accessible
curl http://localhost:8889/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[]'

# Look for collector job
curl http://localhost:9090/api/v1/query?query=up | jq '.data.result'
```

**Solution:** Ensure Prometheus is configured to scrape the collector on port 8889.

### Grafana Dashboard Empty

**Problem: Dashboard panels show no data**

```bash
# Test Prometheus directly
curl "http://localhost:9090/api/v1/query?query=http_requests_total"

# Check datasource settings in Grafana
# Settings → Data Sources → Prometheus → Test Data Source

# Verify metric names in dashboard JSON
grep -o '"expr":"[^"]*' ./dashboards/dashboard-*.json
```

**Solution:** Ensure application is generating metrics and Prometheus is scraping them.

---

## Companion Website Alignment

**Note:** The companion website (peh-packt.platformetrics.com) provides additional resources, but due to network restrictions, cannot be accessed at this moment.

**Expected Website Content:**
- Interactive code examples with live Prometheus/Grafana instances
- Video walkthroughs of each deployment scenario
- Updated OTEL versions and best practices
- Community-contributed dashboard examples
- Troubleshooting forums and issue tracker

**How to Use This Repository with the Book:**

1. **Chapter Introduction**: Understand the three pillars of observability
2. **Standardization Section**: Run `otel_setup.py` and `instrument-app.py`
3. **Push vs Pull Section**: Compare `traces_push.py` (push) vs `metrics_pull.py` (pull)
4. **SPOG Architecture**: Run `observability-personas.py` to see multi-persona dashboards
5. **Deployment Section**: Deploy `otel-collector-deployment.yaml` to Kubernetes
6. **Alert & Response**: Import `alert-rules.yaml` and understand incident response workflow

**Recommended Reading Order:**
1. Chapter 4 Introduction and Concepts
2. Run `test-observability.py` to validate setup
3. Deploy infrastructure: `otel-collector-deployment.yaml`
4. Run `instrument-app.py` to see application instrumentation
5. Run `traces_push.py` and `metrics_pull.py` for protocol examples
6. Generate dashboards: `observability-personas.py`
7. Review `alert-rules.yaml` for incident detection
8. Implement observability-driven deployment practices

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Applications (Instrumented with OTEL)         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ instrument-app   │  │ metrics_pull.py  │  │ traces_push.py │ │
│  │ (WSGI + Traces)  │  │ (Pull Metrics)   │  │ (Push Traces)  │ │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬────────┘ │
│           │                      │                      │          │
│           └──────────────────────┼──────────────────────┘          │
└────────────────────────────────────┬─────────────────────────────┘
                                     │ OTLP (gRPC, HTTP)
                                     │ + Prometheus Scrape
                                     ▼
                    ┌──────────────────────────────┐
                    │ OTEL Collector (DaemonSet)   │
                    │ ┌────────────────────────┐   │
                    │ │ Receivers:             │   │
                    │ │ - OTLP (4317/4318)     │   │
                    │ │ - Prometheus           │   │
                    │ │ - Syslog (514)         │   │
                    │ │ - Jaeger               │   │
                    │ └────────────────────────┘   │
                    │ ┌────────────────────────┐   │
                    │ │ Processors:            │   │
                    │ │ - Batch, Memory Limit  │   │
                    │ │ - Attributes, Sampling │   │
                    │ │ - Resource Detection   │   │
                    │ └────────────────────────┘   │
                    │ ┌────────────────────────┐   │
                    │ │ Exporters:             │   │
                    │ │ - Prometheus (8889)    │   │
                    │ │ - Jaeger               │   │
                    │ │ - Loki                 │   │
                    │ └────────────────────────┘   │
                    └──────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
          ┌─────────┐   ┌─────────┐   ┌──────────┐
          │Prometheus   │ Jaeger  │   │Loki Logs │
          │(Metrics)    │(Traces) │   │          │
          └─────┬───┘   └────┬────┘   └──────────┘
                │             │
                └─────────────┼────────────┐
                              │            │
                              ▼            ▼
        ┌────────────────────────────────────────┐
        │        Grafana (SPOG)                  │
        │  ┌──────────┐ ┌────────┐ ┌─────────┐ │
        │  │Developer │ │  SRE   │ │Management│ │
        │  │Dashboard │ │Dashboard│ │Dashboard │ │
        │  └──────────┘ └────────┘ └─────────┘ │
        │  ┌──────────────────────────────────┐ │
        │  │   Security Dashboard (CVE, Auth) │ │
        │  └──────────────────────────────────┘ │
        │  ┌──────────────────────────────────┐ │
        │  │   Alert Rules (Severity-based)   │ │
        │  └──────────────────────────────────┘ │
        └────────────────────────────────────────┘
```

---

## File Summary

| File | Type | Purpose | Chapter Section |
|------|------|---------|-----------------|
| `otel_setup.py` | Python | OTEL SDK initialization for tracing/metrics | Standardization |
| `instrument-app.py` | Python | WSGI app with OTEL instrumentation | Standardization |
| `metrics_pull.py` | Python | Prometheus pull-based metrics | Push vs Pull |
| `traces_push.py` | Python | OTLP push-based traces | Push vs Pull |
| `observability-personas.py` | Python | Dashboard generator for personas | SPOG Architecture |
| `test-observability.py` | Python | Validation test suite | Testing |
| `otel-collector-config.yaml` | YAML | Collector configuration | Ingestion |
| `otel-collector-deployment.yaml` | YAML | Kubernetes DaemonSet deployment | Infrastructure |
| `alert-rules.yaml` | YAML | Prometheus alert rules | Incident Response |
| `grafana-dashboard-platform.json` | JSON | Sample Grafana dashboard | SPOG Visualization |

---

## Next Steps

After working through this chapter's examples:

1. **Implement Observability in Your Services**: Use the OTEL SDK setup from `otel_setup.py` as a template
2. **Deploy OTEL Collectors**: Follow the Kubernetes deployment in your cluster
3. **Create Custom Dashboards**: Extend `observability-personas.py` for your specific services
4. **Establish Alert Runbooks**: Link `alert-rules.yaml` to runbooks for your team
5. **Measure MTTR**: Track Mean Time To Recovery improvements from better observability
6. **Practice Observability-Driven Deployment**: Use observability gates in your CI/CD pipeline

---

## References

- **OpenTelemetry**: https://opentelemetry.io/
- **OTEL Python SDK**: https://opentelemetry.io/docs/instrumentation/python/
- **Prometheus**: https://prometheus.io/
- **Grafana**: https://grafana.com/
- **Jaeger**: https://www.jaegertracing.io/
- **Kubernetes**: https://kubernetes.io/
- **The Platform Engineer's Handbook**: https://peh-packt.platformetrics.com/

---

## Summary

This chapter equips platform engineers with the knowledge and tools to embed observability into their organizations' microservices architectures. Through standardized OpenTelemetry instrumentation, unified SPOG dashboards, and observability-driven deployment practices, teams can dramatically reduce MTTR, enable developer self-service, and make data-driven operational decisions. The code examples in this directory provide production-ready templates for implementing these patterns in your organization.
