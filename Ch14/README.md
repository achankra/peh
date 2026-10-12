# Chapter 14: Agentic and AI-Augmented Platforms

## Overview

This chapter builds AI-augmented tooling for platform engineering — agents that triage incidents, answer documentation questions, enforce safety guardrails, and measure their own impact. Every script runs locally with mock data by default; the two LLM-backed scripts can connect to Anthropic Claude or a local Ollama model.

**What you'll build:**
- A RAG pipeline that indexes platform docs and answers questions using ChromaDB + an LLM
- An incident triage agent that correlates alerts, logs, and deployments to find root causes
- A multi-agent system (investigate → plan → execute) with human-in-the-loop approval gates
- A guardrails framework that enforces action allowlists, confidence thresholds, and audit logging
- Prometheus metrics and alerting rules for monitoring AI agent health
- An impact measurement script comparing AI-assisted vs. manual incident response

---

## Prerequisites

**Python 3.10+** and a virtual environment:

```bash
cd Ch14
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip3 install -r requirements.txt
```

> On Linux without a venv, add `--break-system-packages` to the pip command.

**LLM Configuration (optional):** Only `platform_chatbot/rag_pipeline.py` and `platform_chatbot/incident_triage.py` call an LLM; they fall back to mock responses when none is configured. The other scripts are deterministic and need no LLM. To use a real LLM:

```bash
# Option A: Anthropic Claude (recommended)
export ANTHROPIC_API_KEY="sk-ant-..."

# Option B: Local LLM with Ollama (no API key needed)
# Install from https://ollama.ai, then:
ollama pull mistral && ollama serve
export OLLAMA_MODEL="mistral"   # opt-in; used only when ANTHROPIC_API_KEY is not set
```

If you set up Bitwarden in Chapter 1, `source load-secrets.sh` pulls the keys from your vault automatically. Otherwise copy the template to a gitignored `.env`, edit it, and load it into your shell (same pattern as Chapter 10):

```bash
cp .env_example .env      # then set ANTHROPIC_API_KEY or OLLAMA_MODEL (leave the other empty)
set -a && source .env && set +a
```

**Docker Desktop + Kind cluster** (for Step 6 only — not needed for the Python scripts):

> If you are jumping into this chapter without running earlier chapters, you need Docker Desktop running and a Kind cluster with the Prometheus Operator installed. If you already have these from a prior chapter, skip ahead.

```bash
# 1. Start Docker Desktop (macOS: open from Applications or Spotlight)
open -a "Docker"
# Wait for the whale icon in the menu bar to stop animating

# 2. Create a Kind cluster (skip if you already have one)
kind get clusters                       # Check for existing clusters
kind create cluster --name platform-dev # Create one if none listed

# 3. Verify the cluster is reachable
kubectl get nodes                       # Should show node(s) in Ready state

# 4. Install Prometheus Operator (needed for ai-governance-alerts.yaml)
kubectl create namespace monitoring
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
#    The release name must be "kube-prometheus-stack": Prometheus then only loads
#    rules labelled release=kube-prometheus-stack, which Step 6 sets
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack --version 92.1.1 \
  --namespace monitoring --wait

# 5. Confirm monitoring stack is running
kubectl get pods -n monitoring          # All pods should be Running
```

---

## File Map

| File | What It Does |
|------|-------------|
| `platform_chatbot/rag_pipeline.py` | RAG system: loads docs → embeds in ChromaDB → retrieves context → generates LLM answers |
| `rag-platform-docs.py` | Lightweight TF-IDF retrieval alternative (no embeddings, no API key needed) |
| `platform_chatbot/incident_triage.py` | Correlates error spikes, deployments, and latency signals to identify root causes |
| `alert-correlator.py` | Groups related alerts by time window and metric similarity, reduces noise |
| `incident-agent.py` | Three-agent pipeline: triage → diagnosis → remediation proposal |
| `agents/multi_agent_system.py` | Supervisor pattern: Investigation → Planning → Execution with approval gates |
| `ai-guardrails.py` | Action allowlists, confidence thresholds, approval workflows, audit logging |
| `ai_governance/observability.py` | Prometheus metrics: latency, confidence, override rates, error tracking |
| `ai-governance-alerts.yaml` | PrometheusRule with 7 alerts + SLOs for AI agent health |
| `runbook-automator.py` | Parses markdown runbooks into executable steps with safety validation |
| `measure-ai-impact.py` | Compares MTTR, triage speed, and diagnosis time (AI-assisted vs. manual) |
| `backstage-ai-template.yaml` | Backstage scaffolder template for AI-generated microservice configs |
| `test-ai-agents.py` | Test suite: guardrails, correlator, agents, runbook automator, impact metrics (see Step 9) |
| `load-secrets.sh` | Loads ANTHROPIC_API_KEY from Bitwarden vault |
| `.env_example` | Template for a gitignored `.env` (`ANTHROPIC_API_KEY` or `OLLAMA_MODEL`) when you are not using Bitwarden |

---

## Step-by-Step Instructions

### Step 1: RAG Pipeline — Index and Query Platform Docs

The RAG pipeline loads documentation, creates embeddings, stores them in ChromaDB, and uses an LLM to synthesize answers from retrieved context.

```bash
python3 platform_chatbot/rag_pipeline.py
```

**What happens:** The script indexes two sample docs (a Deployment Guide and a Troubleshooting guide), embeds them into ChromaDB, then asks "How do I deploy to Kubernetes?". It keeps only chunks whose similarity is at least 0.6 (here, the Deployment Guide) and has the LLM answer from them.

**Expected output** (mock mode, no LLM configured; startup log lines omitted):
```
======================================================================
  MODE: MOCK — No LLM configured or LLM package not installed
  ...
======================================================================
Query: How do I deploy to Kubernetes?
Answer: This is a mock answer generated without API access. Based on the context provided, this would typically contain a comprehensive answer to your question.
Confidence: [0.66]
Sources: ['Deployment Guide']
Time: 9.0ms
```

With an LLM, `MODE: LIVE — Using local Ollama (mistral)` (or Anthropic Claude) is shown and `Answer:` is a real answer built from the Deployment Guide steps (build, push, `helm install`). `Confidence` is the similarity score of each retrieved chunk, `Time` includes the LLM call (seconds with Ollama), and `Sources` lists where the retrieved chunks came from: the doc title here, or the file path for documents indexed from disk with `index_documents()`.

> **First run:** The embedding model (`all-MiniLM-L6-v2`, ~90 MB) downloads once from Hugging Face, so the first run needs internet and is slower. Later runs use the local cache. If it can't be loaded, the script falls back to mock embeddings.

> **With a real LLM:** Set `ANTHROPIC_API_KEY` (or `OLLAMA_MODEL` with `ollama serve` running) and re-run. The pipeline switches from the mock to real LLM synthesis automatically. If both are set, Anthropic is used.

For a zero-dependency alternative, `rag-platform-docs.py` uses TF-IDF retrieval instead of vector embeddings:

```bash
python3 rag-platform-docs.py
```

---

### Step 2: Incident Triage — Correlate Signals and Find Root Causes

The triage agent takes an incident with multiple signals (error rate spike, recent deployment, latency increase) and identifies the most likely root cause.

```bash
python3 platform_chatbot/incident_triage.py
```

**What happens:** Processes a payment service incident with two signals — an error rate spike (25.5%, threshold 5%) and a recent deployment (revision 42). The agent correlates these signals, identifies "recent deployment caused regression" as root cause with 85% confidence, and recommends rollback steps.

**Expected output:**
```
Incident ID: INC-A7F3D2E1
Root Cause: Recent deployment caused regression
Confidence: 85%
Affected: deployment_service
Runbook: Check logs → Verify deployments → Rollback
```

> **With a real LLM** (`ANTHROPIC_API_KEY` or `OLLAMA_MODEL`): the LLM's answer replaces the root-cause text and confidence is fixed at 75%, so the output is longer, differs from run to run, and won't match the sample above. The sample shows mock mode. The incident ID is random on every run.

The alert correlator groups related alerts by time proximity and metric similarity:

```bash
python3 alert-correlator.py
```

**Expected output:** 5 raw alerts → grouped into 3 incidents (40% noise reduction): the two CPU alerts and the memory alert on the `api-server` hosts form one incident, the database connection pool alert is its own incident, and the cache alert arrives outside the 5-minute window so it is a separate incident.

---

### Step 3: Multi-Agent System — Orchestrated Remediation

Four agents work together: Investigation (read-only data gathering) → Planning (create remediation plan) → Execution (run approved steps) → Supervisor (coordinates and enforces approval gates).

```bash
python3 agents/multi_agent_system.py
```

**What happens:** The supervisor receives a `pod_crash_loop` issue. The investigation agent reports its findings (high restart count, `OOMKilled`, insufficient memory requests; confidence 0.95). The planning agent creates a two-step plan: raise the memory request (needs approval), then restart the pod. The execution agent queues step 1 for human approval and **skips step 2**, because the restart only makes sense after the memory change is approved. The workflow ends as `pending_approval`.

**Expected output** (log lines, then the workflow result and audit trail as JSON; IDs and timestamps vary):
```
... SupervisorAgent - INFO - Step 1: Investigation phase
... InvestigationAgent - INFO - investigation: Investigated pod_crash_loop - Status: success
... SupervisorAgent - INFO - Step 2: Planning phase
... PlanningAgent - INFO - planning: Created plan for pod_crash_loop - Status: success
... SupervisorAgent - INFO - Step 3: Execution phase
... ExecutionAgent - WARNING - Step 1 requires approval: update_resource_requests
... ExecutionAgent - WARNING - Step 2 skipped: restart_pod (blocked on step 1)
... SupervisorAgent - WARNING - Remediation workflow paused: waiting for human approval

=== Remediation Workflow Result ===
{ ... "steps_executed": 0, "steps_waiting_approval": 1, "steps_skipped": 1, ...
  "status": "pending_approval" }

=== Complete Audit Trail ===
{ "agent_type": "InvestigationAgent", "description": "Investigated pod_crash_loop", "status": "success", ... }
{ "agent_type": "PlanningAgent", "description": "Created plan for pod_crash_loop", "status": "success", ... }
{ "agent_type": "ExecutionAgent", "description": "Waiting for approval: update_resource_requests",
  "status": "waiting_for_approval", "approval_required": true, ... }
```

**Key pattern:** Read-only investigation runs autonomously. State-changing steps flagged `requires_approval` stop the plan: nothing after them runs until a human approves. The plan's `rollback_plan` field records how to undo the change. In this demo the approval itself is simulated; only `destructive` and `critical` steps go through the supervisor's (auto-approving) `_request_human_approval`, and the sample plans contain none.

---

### Step 4: AI Guardrails — Safety Constraints in Code

The guardrails framework enforces what each agent type can do. Guardrails are deterministic (code, not prompts) — an agent cannot talk its way past them.

```bash
python3 ai-guardrails.py
```

**What happens:** Tests five scenarios at increasing severity levels. Each action goes through two checks: the **allowlist** (is this action permitted for this agent at this severity?) and the **confidence threshold**. An action that fails either is rejected outright — no approval is even requested — and `execute_action` re-checks, so a forged approval can't bypass the guardrails. Safe medium/high/critical actions then need human approval; safe read-only/low actions are auto-approved. (Approval is simulated in the demo: the on-call engineer approves immediately.)

**Expected output** (approval IDs vary):
```
Test 1: get_metrics on api-service
  Agent: diagnosis_agent, Confidence: 50.0%, Severity: readonly
  Safety: PASS
  Approval: AUTO-APPROVED
  Execution: SUCCESS

Test 2: acknowledge_alert on alert-123
  Agent: triage_agent, Confidence: 80.0%, Severity: low
  Safety: PASS
  Approval: AUTO-APPROVED
  Execution: SUCCESS

Test 3: scale_service on api-service
  Agent: remediation_agent, Confidence: 80.0%, Severity: medium
  Safety: PASS
  Approval: REQUIRED (approval-b4222799)
  Approval: GRANTED
  Execution: SUCCESS

Test 4: deploy_version on api-service
  Agent: remediation_agent, Confidence: 90.0%, Severity: high
  Safety: FAIL
    - Action deploy_version not in allowlist for remediation_agent
  Approval: NOT REQUESTED (blocked by safety check)
  Execution: BLOCKED

Test 5: delete_data on database
  Agent: remediation_agent, Confidence: 50.0%, Severity: critical
  Safety: FAIL
    - Action delete_data not in allowlist for remediation_agent
    - Confidence 50.0% below threshold 95.0% for critical action
  Approval: NOT REQUESTED (blocked by safety check)
  Execution: BLOCKED

Framework Statistics:
  Total actions: 5
  Auto-approved: 2
  Manual approved: 1
  Rejected: 2
  Pending approvals: 0
  Audit log entries: 15
```

**Severity tiers and confidence thresholds:**

| Severity | Confidence Required | Approval |
|----------|-------------------|----------|
| READONLY | 0.0 | Autonomous |
| LOW | 0.6 | Autonomous |
| MEDIUM | 0.75 | Human required |
| HIGH | 0.85 | Human required |
| CRITICAL | 0.95 | Always human |

---

### Step 5: Incident Agent Pipeline — Triage → Diagnosis → Remediation

A three-stage pipeline where each agent has a distinct role: triage classifies severity, diagnosis identifies root cause, remediation proposes actions with risk assessment.

```bash
python3 incident-agent.py
```

**What happens:** Processes three incidents — a CPU spike (infrastructure), database connection pool exhaustion, and a security breach. Each goes through triage → diagnosis → remediation proposal. Critical and security incidents are flagged `ESCALATION REQUIRED`. The first diagnosis option becomes the proposed action. Approval is required for high-risk actions (critical severity) and whenever the diagnosis confidence is below 0.5, so a low-confidence guess is never run automatically. In the demo, the on-call engineer's approval is simulated.

**Expected output (3 incidents; IDs vary):**
```
Incident: inc-4c1f13e8
Alert: CRITICAL: API Server CPU usage 95% - requests timing out
  Triage: critical / infrastructure (confidence 95.0%, ESCALATION REQUIRED)
  Diagnosis: High CPU utilization (confidence 85.0%)
  Proposed: scale — Scale horizontally (add replicas); risk high, approval required
  Result: Scaled compute layer to 3 replicas

Incident: inc-6d256c39
Alert: WARNING: Database connection pool exhausted
  Triage: high / database (confidence 80.0%)
  Diagnosis: Database performance degradation (confidence 75.0%)
  Proposed: manual — Kill long-running queries; risk medium, no approval needed
  Result: Action manual executed successfully

Incident: inc-860d1c0f
Alert: CRITICAL: Security breach detected - unauthorized access attempt
  Triage: critical / security (confidence 95.0%, ESCALATION REQUIRED)
  Diagnosis: Unauthorized access - possible compromised credentials (confidence 80.0%)
  Proposed: manual — Block source IP and rotate credentials; risk high, approval required
  Result: Action manual executed successfully

Incident Summary: Total 3, Critical 2, Approved actions 3, Resolved 3
```
(The script prints each of these as a full multi-line block; this is condensed.)

> Triage uses simple keyword matching, so wording matters: an alert containing "app" anywhere (even inside "happened") is classified as an application incident.

---

### Step 6: Observability — Prometheus Metrics for AI Agents

Deploy Prometheus alerting rules that monitor AI agent health: confidence scores, override rates, error rates, and latency.

```bash
kubectl apply -f ai-governance-alerts.yaml
kubectl get prometheusrule -n monitoring | grep ai-governance
```

**Expected output:**
```
prometheusrule.monitoring.coreos.com/ai-governance-alerts created
prometheusrule.monitoring.coreos.com/ai-governance-slos created
configmap/ai-governance-runbooks created

ai-governance-alerts    5s
ai-governance-slos      5s
```

The file creates two PrometheusRules and a ConfigMap with runbooks. `ai-governance-alerts` holds 7 alerts (LowAIConfidence, HighHumanOverrideRate, AIAgentErrors, AILatencyHigh, etc.) plus 4 recording rules; `ai-governance-slos` holds the SLO targets: >99% success rate, <5% override rate, <1% error rate, <5s p99 latency.

**Verify Prometheus loaded the rules.** `kubectl apply` succeeding does not prove this, so ask Prometheus itself (in a second terminal, or run the port-forward in the background):

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090 &
sleep 40   # rules are evaluated every 30s; health is "unknown" until the first run
curl -s localhost:9090/api/v1/rules | python3 -c '
import sys, json
for g in json.load(sys.stdin)["data"]["groups"]:
    if g["name"] in ("ai_agent_governance", "ai_agent_slos"):
        print(g["name"], sorted({r["health"] for r in g["rules"]}), len(g["rules"]), "rules")'
kill %1   # stop the port-forward
```

**Expected output:**
```
ai_agent_governance ['ok'] 11 rules
ai_agent_slos ['ok'] 5 rules
```

No output means Prometheus did not load the rules (see the label note below); `['err']` means a rule expression failed. You can also open <http://localhost:9090/rules> while the port-forward runs.

> **The `release` label matters.** Prometheus only loads rules labelled `release: kube-prometheus-stack` (the Helm release name used in the prerequisites and by the Chapter 2 Flux install). Without that label `kubectl apply` still succeeds, but Prometheus silently ignores the rules. If you installed the chart under another release name, change the label in `ai-governance-alerts.yaml` to match. Check what yours selects with `kubectl get prometheus -n monitoring -o jsonpath='{.items[0].spec.ruleSelector}'`.

To see the Python metrics instrumentation:

```bash
python3 ai_governance/observability.py
```

**Expected output** (the tracked call, then the statistics for it; timings vary):
```
Result: {'confidence': 0.87, 'result': 'Task completed', 'status': 'success'}

Agent Statistics:
{
  "agent_type": "example",
  "total_calls": 1,
  "successful_calls": 1,
  "success_rate": 1.0,
  "average_confidence": 0.87,
  "average_duration_seconds": 0.50,
  ...
}
```

This demonstrates the `@track_agent_call` decorator that automatically records latency, confidence, and error rates to Prometheus counters and histograms. The decorator takes `agent_type` and `action_type` from the call's keyword arguments, so pass them on every call.

> **Limit of this demo:** the script records metrics in-process only. Nothing serves `/metrics` or has a ServiceMonitor, so the loaded alerts have no data to fire on until a real agent exposes its metrics to Prometheus.

---

### Step 7: Measure AI Impact — Before/After Comparison

Quantify the business impact of AI-augmented operations by comparing MTTR, triage speed, and diagnosis time.

```bash
python3 measure-ai-impact.py
```

**Expected output** (deterministic — the script generates fixed demo data):
```
============================================================
  AI IMPACT ON PLATFORM METRICS
============================================================

--- Mean Time to Resolution (MTTR) ---
  Manual:      135.0 min (n=10)
  AI-Assisted: 52.5 min (n=10)
  Improvement: 61.1%

--- Alert-to-Acknowledgment ---
  Manual:      21.0 min
  AI-Assisted: 7.5 min
  Improvement: 64.3%

--- Diagnosis Speed ---
  Manual:      46.5 min
  AI-Assisted: 13.5 min
  Improvement: 71.0%

============================================================
```

> **The data is synthetic.** The script generates 10 "manual" and 10 "AI-assisted" sample incidents, so the improvements illustrate the calculation, not a real result. To measure your own platform, build `Incident` objects from your incident-management data and pass them to `print_report()`. Diagnosis speed is measured from acknowledgment to root cause.

---

### Step 8: Runbook Automation — Safe Execution with Approval Gates

The runbook automator parses markdown runbooks into executable steps and validates each one for safety before running it. Each step is checked for destructive keywords (`kill`, `rm`, `delete`, `drop`, `restart`, ...) matched as whole words, whatever type the runbook declares for it — a step labelled `Diagnostic` (or with no `Type:` line at all) that runs `rm -rf` is still blocked. A step that needs approval pauses the run until a human approves it.

```bash
python3 runbook-automator.py
```

**What happens:** The script parses a 7-step database recovery runbook and prints each step with its safety status:

| Step | Type | Result |
|---|---|---|
| 1–2 Check status / disk | diagnostic | `OK` — runs automatically |
| 3 Stop Database | action, `ApprovalRequired: true` | `OK` — waits for approval |
| 4 Run Recovery | action, `ApprovalRequired: true` | `OK` — waits for approval |
| 5 Start Database | action, `ApprovalRequired: false` | `BLOCKED` — "Non-readonly action should require approval". This step is deliberately mis-declared to show the validator; set `ApprovalRequired: true` to fix it |
| 6 Verify Integrity | diagnostic | `OK` |
| 7 Notify Team | notification | `OK` |

It then executes the runbook:

```
Execution ID: exec-67ee005c        (varies)
Status: pending_approval
Approval Required: True
Successful steps: 2/3

✓ step-1: Step 1: Check Database Status
   Output: Service is running (OK)

✓ step-2: Step 2: Check Disk Space
   Output: Executed: df -h /var/lib/postgresql

⏸ step-3: Step 3: Stop Database
   Error: Awaiting approval
```

Steps 1–2 run, then the run stops at step 3 with status `pending_approval` — a pause, not a failure. This demo stops there: `approve_step()` removes a step from the approval queue but does not resume the run, and steps 4–7 are not executed.

---

### Step 9: Run Tests

```bash
python3 test-ai-agents.py -v
```

**Expected output** (one line per test, abridged; the exact order is alphabetical by test class):
```
test_guardrails_module_exists ... ok
test_unsafe_actions_cannot_execute_even_if_marked_approved ... ok
test_correlator_groups_same_host_and_reports_noise_reduction ... ok
test_demo_metrics_match_hand_calculation ... ok
test_security_breach_is_diagnosed_escalated_and_needs_approval ... ok
test_nothing_runs_past_an_unapproved_step ... ok
test_dangerous_command_blocked_whatever_type_it_declares ... ok
test_waiting_for_approval_is_pending_not_failed ... ok
...

----------------------------------------------------------------------
Ran 27 tests in 0.03s

OK
```

The suite needs no cluster, LLM or API key. Most tests run the code against the demo data (grouping, approval gates, the safety validator, the impact maths); a few only check that a script exists and compiles. To run one group, for example the runbook tests:

```bash
python3 -m unittest test-ai-agents.TestRunbookAutomatorBehavior -v
```

---

## Architecture Patterns

**Pattern 1 — RAG Pipeline:**
Query → Embed → Vector similarity search → Retrieved context → LLM + context → Grounded answer. Use for documentation, runbook selection, knowledge-based responses.

**Pattern 2 — Multi-Agent Supervision:**
Task → Investigation (read-only) → Planning → Risk check → Low risk: execute autonomously / High risk: request human approval → Audit log. Use for incident remediation, infrastructure automation.

**Pattern 3 — Guardrails in Code:**
Action request → Check allowlist → Check confidence threshold → Auto-approve or queue for human. Guardrails are deterministic code, not LLM prompts — an agent cannot bypass them.

---

## Troubleshooting

**"ModuleNotFoundError: No module named ..."** — Activate your venv (`source venv/bin/activate`) and install dependencies (`pip3 install -r requirements.txt`).

**Scripts show "mock mode" output** — This is expected without an LLM configured. Set `ANTHROPIC_API_KEY`, or `OLLAMA_MODEL` with `ollama serve` running and `langchain-ollama` installed, to use a real LLM. If you set `OLLAMA_MODEL` and still see mock mode, `langchain-ollama` is missing from the venv.

**RAG answers ignore your question, or the log says "HuggingFace embeddings unavailable. Using mock embeddings."** — `chromadb`, `langchain-huggingface` or `sentence-transformers` is missing, or the embedding model could not be downloaded, so the pipeline fell back to mock retrieval. Install the requirements (`pip3 install chromadb`, or `--break-system-packages` on Linux) and check your internet connection on the first run.

**PrometheusRule not created** — Ensure the monitoring stack is running: `kubectl get pods -n monitoring`.

**PrometheusRule created but the alerts are missing in Prometheus** — The rule's `release` label doesn't match what your Prometheus selects. Compare `kubectl get prometheus -n monitoring -o jsonpath='{.items[0].spec.ruleSelector}'` with the label in `ai-governance-alerts.yaml` (see Step 6).

---

**Author:** Ajay Chankramath (ajay@platformetrics.com)
**Book:** The Platform Engineer's Handbook (Packt Publishing)
**Last Updated**: October 2026
