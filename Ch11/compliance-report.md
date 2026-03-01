# Platform Compliance Report

**Generated:** 2026-02-28 16:42:44 UTC
**Total Violations:** 102

## Summary by Severity

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 40 |
| MEDIUM | 62 |
| LOW | 0 |

## Violations by Policy

| Policy | Count |
|--------|-------|
| K8sRequiredResources/require-resources | 20 |
| K8sRequireLabels/require-compliance-labels | 20 |
| K8sRequireLabels/require-labels | 20 |
| K8sRestrictImageRegistries/restrict-image-registries | 20 |
| K8sRequireResourceLimits/require-resource-limits | 18 |
| K8sDenyPrivilegedContainers/deny-privileged-containers | 4 |

## Violations by Namespace

| Namespace | Count |
|-----------|-------|
| crossplane-system | 40 |
| monitoring | 31 |
| backstage | 10 |
| istio-system | 5 |
| production | 4 |
| local-path-storage | 4 |
| databases | 3 |
| observability | 3 |
| default | 2 |

## Detailed Violations

| Severity | Policy | Namespace | Resource | Message |
|----------|--------|-----------|----------|---------|
| HIGH | K8sRequiredResources/require-resources | monitoring | Pod/monitoring-kube-prometheus-operator-77b866bdbb-2gxsn | Container kube-prometheus-stack is missing resource limits |
| HIGH | K8sRequiredResources/require-resources | monitoring | Pod/monitoring-grafana-58f5bc6ff-vglf7 | Container grafana-sc-datasources is missing resource requests |
| HIGH | K8sRequiredResources/require-resources | monitoring | Pod/monitoring-grafana-58f5bc6ff-vglf7 | Container grafana-sc-datasources is missing resource limits |
| HIGH | K8sRequiredResources/require-resources | monitoring | Pod/monitoring-grafana-58f5bc6ff-vglf7 | Container grafana-sc-dashboard is missing resource requests |
| HIGH | K8sRequiredResources/require-resources | monitoring | Pod/monitoring-grafana-58f5bc6ff-vglf7 | Container grafana-sc-dashboard is missing resource limits |
| HIGH | K8sRequiredResources/require-resources | monitoring | Pod/monitoring-grafana-58f5bc6ff-vglf7 | Container grafana is missing resource requests |
| HIGH | K8sRequiredResources/require-resources | monitoring | Pod/monitoring-grafana-58f5bc6ff-vglf7 | Container grafana is missing resource limits |
| HIGH | K8sRequiredResources/require-resources | monitoring | Pod/alertmanager-monitoring-kube-prometheus-alertmanager-0 | Container config-reloader is missing resource requests |
| HIGH | K8sRequiredResources/require-resources | monitoring | Pod/alertmanager-monitoring-kube-prometheus-alertmanager-0 | Container config-reloader is missing resource limits |
| HIGH | K8sRequiredResources/require-resources | monitoring | Pod/alertmanager-monitoring-kube-prometheus-alertmanager-0 | Container alertmanager is missing resource limits |
| HIGH | K8sRequiredResources/require-resources | local-path-storage | Pod/local-path-provisioner-67b8995b4b-t7sj2 | Container local-path-provisioner is missing resource requests |
| HIGH | K8sRequiredResources/require-resources | local-path-storage | Pod/local-path-provisioner-67b8995b4b-t7sj2 | Container local-path-provisioner is missing resource limits |
| HIGH | K8sRequiredResources/require-resources | istio-system | Pod/istiod-7c4fbc86db-6jpps | Container discovery is missing resource limits |
| HIGH | K8sRequiredResources/require-resources | crossplane-system | Pod/provider-kubernetes-a3cbbe355fa7-5746645dcc-zqsxj | Container package-runtime is missing resource requests |
| HIGH | K8sRequiredResources/require-resources | crossplane-system | Pod/provider-kubernetes-a3cbbe355fa7-5746645dcc-zqsxj | Container package-runtime is missing resource limits |
| HIGH | K8sRequiredResources/require-resources | crossplane-system | Pod/provider-helm-4d90a08b9ede-7bdc97cd54-qvftm | Container package-runtime is missing resource requests |
| HIGH | K8sRequiredResources/require-resources | crossplane-system | Pod/provider-helm-4d90a08b9ede-7bdc97cd54-qvftm | Container package-runtime is missing resource limits |
| HIGH | K8sRequiredResources/require-resources | crossplane-system | Pod/function-patch-and-transform-6a1ab24d2512-75d54b5957-ctdxj | Container package-runtime is missing resource requests |
| HIGH | K8sRequiredResources/require-resources | crossplane-system | Pod/function-patch-and-transform-6a1ab24d2512-75d54b5957-ctdxj | Container package-runtime is missing resource limits |
| HIGH | K8sRequiredResources/require-resources | backstage | Pod/backstage-postgresql-0 | Container postgresql is missing resource limits |
| HIGH | K8sRequireLabels/require-compliance-labels | databases | Deployment/postgresql | Resource missing required label 'cost-center'. Required labels: ["team", "cost-c... |
| HIGH | K8sRequireLabels/require-compliance-labels | databases | Deployment/postgresql | Resource missing required label 'compliance-level'. Required labels: ["team", "c... |
| HIGH | K8sRequireLabels/require-compliance-labels | crossplane-system | Deployment/provider-kubernetes-a3cbbe355fa7 | Resource missing required label 'team'. Required labels: ["team", "cost-center",... |
| HIGH | K8sRequireLabels/require-compliance-labels | crossplane-system | Deployment/provider-kubernetes-a3cbbe355fa7 | Resource missing required label 'cost-center'. Required labels: ["team", "cost-c... |
| HIGH | K8sRequireLabels/require-compliance-labels | crossplane-system | Deployment/provider-kubernetes-a3cbbe355fa7 | Resource missing required label 'compliance-level'. Required labels: ["team", "c... |
| HIGH | K8sRequireLabels/require-compliance-labels | crossplane-system | Deployment/provider-helm-4d90a08b9ede | Resource missing required label 'team'. Required labels: ["team", "cost-center",... |
| HIGH | K8sRequireLabels/require-compliance-labels | crossplane-system | Deployment/provider-helm-4d90a08b9ede | Resource missing required label 'cost-center'. Required labels: ["team", "cost-c... |
| HIGH | K8sRequireLabels/require-compliance-labels | crossplane-system | Deployment/provider-helm-4d90a08b9ede | Resource missing required label 'compliance-level'. Required labels: ["team", "c... |
| HIGH | K8sRequireLabels/require-compliance-labels | crossplane-system | Deployment/function-patch-and-transform-6a1ab24d2512 | Resource missing required label 'team'. Required labels: ["team", "cost-center",... |
| HIGH | K8sRequireLabels/require-compliance-labels | crossplane-system | Deployment/function-patch-and-transform-6a1ab24d2512 | Resource missing required label 'cost-center'. Required labels: ["team", "cost-c... |
| HIGH | K8sRequireLabels/require-compliance-labels | crossplane-system | Deployment/function-patch-and-transform-6a1ab24d2512 | Resource missing required label 'compliance-level'. Required labels: ["team", "c... |
| HIGH | K8sRequireLabels/require-compliance-labels | crossplane-system | Deployment/crossplane-rbac-manager | Resource missing required label 'team'. Required labels: ["team", "cost-center",... |
| HIGH | K8sRequireLabels/require-compliance-labels | crossplane-system | Deployment/crossplane-rbac-manager | Resource missing required label 'cost-center'. Required labels: ["team", "cost-c... |
| HIGH | K8sRequireLabels/require-compliance-labels | crossplane-system | Deployment/crossplane-rbac-manager | Resource missing required label 'compliance-level'. Required labels: ["team", "c... |
| HIGH | K8sRequireLabels/require-compliance-labels | crossplane-system | Deployment/crossplane | Resource missing required label 'team'. Required labels: ["team", "cost-center",... |
| HIGH | K8sRequireLabels/require-compliance-labels | crossplane-system | Deployment/crossplane | Resource missing required label 'cost-center'. Required labels: ["team", "cost-c... |
| HIGH | K8sRequireLabels/require-compliance-labels | crossplane-system | Deployment/crossplane | Resource missing required label 'compliance-level'. Required labels: ["team", "c... |
| HIGH | K8sRequireLabels/require-compliance-labels | backstage | Deployment/backstage | Resource missing required label 'team'. Required labels: ["team", "cost-center",... |
| HIGH | K8sRequireLabels/require-compliance-labels | backstage | Deployment/backstage | Resource missing required label 'cost-center'. Required labels: ["team", "cost-c... |
| HIGH | K8sRequireLabels/require-compliance-labels | backstage | Deployment/backstage | Resource missing required label 'compliance-level'. Required labels: ["team", "c... |
| MEDIUM | K8sDenyPrivilegedContainers/deny-privileged-containers | production | Pod/app-stable-75f6849556-wh4bf | Container 'istio-init' must not run as root (UID 0) |
| MEDIUM | K8sDenyPrivilegedContainers/deny-privileged-containers | production | Pod/app-stable-75f6849556-m99dd | Container 'istio-init' must not run as root (UID 0) |
| MEDIUM | K8sDenyPrivilegedContainers/deny-privileged-containers | production | Pod/app-stable-75f6849556-48fjn | Container 'istio-init' must not run as root (UID 0) |
| MEDIUM | K8sDenyPrivilegedContainers/deny-privileged-containers | production | Pod/app-canary-6cc6b969cf-zvlzb | Container 'istio-init' must not run as root (UID 0) |
| MEDIUM | K8sRequireLabels/require-labels | crossplane-system | Deployment/provider-helm-4d90a08b9ede | Resource missing required label 'owner'. Required labels: ["team", "owner", "cos... |
| MEDIUM | K8sRequireLabels/require-labels | crossplane-system | Deployment/provider-helm-4d90a08b9ede | Resource missing required label 'cost-center'. Required labels: ["team", "owner"... |
| MEDIUM | K8sRequireLabels/require-labels | crossplane-system | Deployment/function-patch-and-transform-6a1ab24d2512 | Resource missing required label 'team'. Required labels: ["team", "owner", "cost... |
| MEDIUM | K8sRequireLabels/require-labels | crossplane-system | Deployment/function-patch-and-transform-6a1ab24d2512 | Resource missing required label 'owner'. Required labels: ["team", "owner", "cos... |
| MEDIUM | K8sRequireLabels/require-labels | crossplane-system | Deployment/function-patch-and-transform-6a1ab24d2512 | Resource missing required label 'cost-center'. Required labels: ["team", "owner"... |
| MEDIUM | K8sRequireLabels/require-labels | crossplane-system | Deployment/crossplane-rbac-manager | Resource missing required label 'team'. Required labels: ["team", "owner", "cost... |
| MEDIUM | K8sRequireLabels/require-labels | crossplane-system | Deployment/crossplane-rbac-manager | Resource missing required label 'owner'. Required labels: ["team", "owner", "cos... |
| MEDIUM | K8sRequireLabels/require-labels | crossplane-system | Deployment/crossplane-rbac-manager | Resource missing required label 'cost-center'. Required labels: ["team", "owner"... |
| MEDIUM | K8sRequireLabels/require-labels | crossplane-system | Deployment/crossplane | Resource missing required label 'team'. Required labels: ["team", "owner", "cost... |
| MEDIUM | K8sRequireLabels/require-labels | crossplane-system | Deployment/crossplane | Resource missing required label 'owner'. Required labels: ["team", "owner", "cos... |
| MEDIUM | K8sRequireLabels/require-labels | crossplane-system | Deployment/crossplane | Resource missing required label 'cost-center'. Required labels: ["team", "owner"... |
| MEDIUM | K8sRequireLabels/require-labels | backstage | Deployment/backstage | Resource missing required label 'team'. Required labels: ["team", "owner", "cost... |
| MEDIUM | K8sRequireLabels/require-labels | backstage | Deployment/backstage | Resource missing required label 'owner'. Required labels: ["team", "owner", "cos... |
| MEDIUM | K8sRequireLabels/require-labels | backstage | Deployment/backstage | Resource missing required label 'cost-center'. Required labels: ["team", "owner"... |
| MEDIUM | K8sRequireLabels/require-labels | observability | DaemonSet/otel-collector | Resource missing required label 'team'. Required labels: ["team", "owner", "cost... |
| MEDIUM | K8sRequireLabels/require-labels | observability | DaemonSet/otel-collector | Resource missing required label 'owner'. Required labels: ["team", "owner", "cos... |
| MEDIUM | K8sRequireLabels/require-labels | observability | DaemonSet/otel-collector | Resource missing required label 'cost-center'. Required labels: ["team", "owner"... |
| MEDIUM | K8sRequireLabels/require-labels | monitoring | DaemonSet/monitoring-prometheus-node-exporter | Resource missing required label 'team'. Required labels: ["team", "owner", "cost... |
| MEDIUM | K8sRequireLabels/require-labels | monitoring | DaemonSet/monitoring-prometheus-node-exporter | Resource missing required label 'owner'. Required labels: ["team", "owner", "cos... |
| MEDIUM | K8sRequireLabels/require-labels | monitoring | DaemonSet/monitoring-prometheus-node-exporter | Resource missing required label 'cost-center'. Required labels: ["team", "owner"... |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | monitoring | Pod/prometheus-monitoring-kube-prometheus-prometheus-0 | Container 'prometheus' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | monitoring | Pod/prometheus-monitoring-kube-prometheus-prometheus-0 | Container 'init-config-reloader' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | monitoring | Pod/prometheus-monitoring-kube-prometheus-prometheus-0 | Container 'config-reloader' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | monitoring | Pod/monitoring-prometheus-node-exporter-6hb28 | Container 'node-exporter' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | monitoring | Pod/monitoring-kube-state-metrics-7458844c7c-xdcw6 | Container 'kube-state-metrics' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | monitoring | Pod/monitoring-kube-prometheus-operator-77b866bdbb-2gxsn | Container 'kube-prometheus-stack' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | monitoring | Pod/monitoring-grafana-58f5bc6ff-vglf7 | Container 'grafana-sc-datasources' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | monitoring | Pod/monitoring-grafana-58f5bc6ff-vglf7 | Container 'grafana-sc-dashboard' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | monitoring | Pod/monitoring-grafana-58f5bc6ff-vglf7 | Container 'grafana' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | monitoring | Pod/alertmanager-monitoring-kube-prometheus-alertmanager-0 | Container 'init-config-reloader' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | monitoring | Pod/alertmanager-monitoring-kube-prometheus-alertmanager-0 | Container 'config-reloader' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | monitoring | Pod/alertmanager-monitoring-kube-prometheus-alertmanager-0 | Container 'alertmanager' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | local-path-storage | Pod/local-path-provisioner-67b8995b4b-t7sj2 | Container 'local-path-provisioner' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | istio-system | Pod/istiod-7c4fbc86db-6jpps | Container 'discovery' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | crossplane-system | Pod/provider-kubernetes-a3cbbe355fa7-5746645dcc-zqsxj | Container 'package-runtime' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | crossplane-system | Pod/provider-helm-4d90a08b9ede-7bdc97cd54-qvftm | Container 'package-runtime' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | crossplane-system | Pod/function-patch-and-transform-6a1ab24d2512-75d54b5957-ctdxj | Container 'package-runtime' must define CPU and memory requests/limits |
| MEDIUM | K8sRequireResourceLimits/require-resource-limits | backstage | Pod/backstage-postgresql-0 | Container 'postgresql' must define CPU and memory requests/limits |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | monitoring | Pod/monitoring-kube-state-metrics-7458844c7c-xdcw6 | Image 'registry.k8s.io/kube-state-metrics/kube-state-metrics:v2.18.0' is from un... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | monitoring | Pod/monitoring-kube-prometheus-operator-77b866bdbb-2gxsn | Image 'quay.io/prometheus-operator/prometheus-operator:v0.89.0' is from unauthor... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | monitoring | Pod/monitoring-grafana-58f5bc6ff-vglf7 | Image 'quay.io/kiwigrid/k8s-sidecar:2.5.0' is from unauthorized registry. Allowe... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | monitoring | Pod/monitoring-grafana-58f5bc6ff-vglf7 | Image 'docker.io/grafana/grafana:12.4.0' is from unauthorized registry. Allowed:... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | monitoring | Pod/alertmanager-monitoring-kube-prometheus-alertmanager-0 | Image 'quay.io/prometheus/alertmanager:v0.31.1' is from unauthorized registry. A... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | monitoring | Pod/alertmanager-monitoring-kube-prometheus-alertmanager-0 | Image 'quay.io/prometheus-operator/prometheus-config-reloader:v0.89.0' is from u... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | local-path-storage | Pod/local-path-provisioner-67b8995b4b-t7sj2 | Image 'docker.io/kindest/local-path-provisioner:v20251212-v0.29.0-alpha-105-g20c... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | istio-system | Pod/istiod-7c4fbc86db-6jpps | Image 'docker.io/istio/pilot:1.29.0' is from unauthorized registry. Allowed: ["g... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | istio-system | Pod/istio-ingressgateway-8d7447659-dnv9k | Image 'docker.io/istio/proxyv2:1.29.0' is from unauthorized registry. Allowed: [... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | istio-system | Pod/istio-egressgateway-f7fc5b56c-6sg6q | Image 'docker.io/istio/proxyv2:1.29.0' is from unauthorized registry. Allowed: [... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | default | Pod/platform-demo-app-5748c74749-m52kx | Image 'platform-demo-app:latest' is from unauthorized registry. Allowed: ["gcr.i... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | default | Pod/platform-demo-app-5748c74749-7s6gw | Image 'platform-demo-app:latest' is from unauthorized registry. Allowed: ["gcr.i... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | databases | Pod/postgresql-59b69f6b66-tc8jg | Image 'postgres:15-alpine' is from unauthorized registry. Allowed: ["gcr.io/", "... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | crossplane-system | Pod/provider-kubernetes-a3cbbe355fa7-5746645dcc-zqsxj | Image 'xpkg.upbound.io/crossplane-contrib/provider-kubernetes:v0.13.0' is from u... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | crossplane-system | Pod/provider-helm-4d90a08b9ede-7bdc97cd54-qvftm | Image 'xpkg.upbound.io/crossplane-contrib/provider-helm:v0.18.1' is from unautho... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | crossplane-system | Pod/function-patch-and-transform-6a1ab24d2512-75d54b5957-ctdxj | Image 'xpkg.upbound.io/crossplane-contrib/function-patch-and-transform:v0.7.0' i... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | crossplane-system | Pod/crossplane-rbac-manager-74494cb9bf-xqz79 | Image 'xpkg.crossplane.io/crossplane/crossplane:v2.2.0' is from unauthorized reg... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | crossplane-system | Pod/crossplane-5cb76b766d-8q5zs | Image 'xpkg.crossplane.io/crossplane/crossplane:v2.2.0' is from unauthorized reg... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | backstage | Pod/backstage-postgresql-0 | Image 'docker.io/bitnamilegacy/postgresql:15.4.0-debian-11-r10' is from unauthor... |
| MEDIUM | K8sRestrictImageRegistries/restrict-image-registries | backstage | Pod/backstage-7cc8476cdc-dfhkw | Image 'ghcr.io/backstage/backstage:latest' is from unauthorized registry. Allowe... |