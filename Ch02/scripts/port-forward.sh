#!/bin/bash
# =============================================================================
# scripts/port-forward.sh - kubectl port-forward manager for local access
# =============================================================================
# Starts a background `kubectl port-forward` per platform UI so Grafana,
# Prometheus, and Alertmanager are reachable in the browser without editing
# /etc/hosts or touching the Istio ingress gateway. PIDs are written to a
# gitignored file so a later `stop` can find and kill exactly the processes
# this script started.
#
# Service names default to the ones platform-services.yaml's Flux HelmRelease
# produces (release name "monitoring-kube-prometheus-stack" in the
# "monitoring" namespace). If you installed the stack manually with a
# different Helm release name, override the matching env var, e.g.:
#   GRAFANA_SVC=svc/monitoring-grafana \
#   PROMETHEUS_SVC=svc/monitoring-kube-prometheus-prometheus \
#   ALERTMANAGER_SVC=svc/monitoring-kube-prometheus-alertmanager \
#     scripts/port-forward.sh start
#
# Usage:
#   scripts/port-forward.sh start    # forward all services in the background
#   scripts/port-forward.sh stop     # kill the forwards started above
#   scripts/port-forward.sh status   # show which forwards are still running
#
# Flux and Istio have no bundled web UI in this chapter's deployment, so
# they aren't forwarded here.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/.port-forward.pids"

GRAFANA_SVC="${GRAFANA_SVC:-svc/monitoring-kube-prometheus-stack-grafana}"
PROMETHEUS_SVC="${PROMETHEUS_SVC:-svc/monitoring-kube-prometheus-prometheus}"
ALERTMANAGER_SVC="${ALERTMANAGER_SVC:-svc/monitoring-kube-prometheus-alertmanager}"

# name:namespace:svc:local_port:remote_port
FORWARDS=(
  "grafana:monitoring:${GRAFANA_SVC}:3000:80"
  "prometheus:monitoring:${PROMETHEUS_SVC}:9090:9090"
  "alertmanager:monitoring:${ALERTMANAGER_SVC}:9093:9093"
)

start() {
  if [ -f "${PID_FILE}" ]; then
    echo "Port-forwards already tracked in ${PID_FILE} - run 'stop' first." >&2
    exit 1
  fi

  : > "${PID_FILE}"
  for entry in "${FORWARDS[@]}"; do
    IFS=':' read -r name namespace svc local_port remote_port <<< "${entry}"
    kubectl port-forward -n "${namespace}" "${svc}" "${local_port}:${remote_port}" \
      > "${SCRIPT_DIR}/.port-forward-${name}.log" 2>&1 &
    pid=$!
    echo "${name} ${pid}" >> "${PID_FILE}"
    echo "Forwarding ${name}: http://localhost:${local_port} (pid ${pid})"
  done
}

stop() {
  if [ ! -f "${PID_FILE}" ]; then
    echo "No tracked port-forwards (${PID_FILE} not found)." >&2
    exit 0
  fi

  while read -r name pid; do
    if kill "${pid}" 2>/dev/null; then
      echo "Stopped ${name} (pid ${pid})"
    else
      echo "${name} (pid ${pid}) was not running"
    fi
  done < "${PID_FILE}"

  rm -f "${PID_FILE}"
}

status() {
  if [ ! -f "${PID_FILE}" ]; then
    echo "No tracked port-forwards."
    exit 0
  fi

  while read -r name pid; do
    if kill -0 "${pid}" 2>/dev/null; then
      echo "${name}: running (pid ${pid})"
    else
      echo "${name}: not running (stale pid ${pid})"
    fi
  done < "${PID_FILE}"
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  status) status ;;
  *)
    echo "Usage: $0 {start|stop|status}" >&2
    exit 1
    ;;
esac
