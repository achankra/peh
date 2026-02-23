"""
Chapter 2: Scalable Platform Runtime - Pulumi Kind Cluster
==========================================================
Provisions namespaces, resource quotas, and limit ranges on an existing
Kind cluster using Pulumi.

Usage:
    1. Create the Kind cluster first:
       kind create cluster --name platform-dev --config kind-config.yaml
    2. Then run Pulumi:
       pulumi stack init dev
       pulumi up

Prerequisites:
    - A running Kind cluster (kind create cluster ...)
    - Docker running
    - Pulumi CLI installed (curl -fsSL https://get.pulumi.com | sh)
    - Python 3.8+ with venv:
        python3 -m venv venv && source venv/bin/activate
        pip install -r requirements.txt
"""

import subprocess
import pulumi
import pulumi_kubernetes as k8s
from modules.cluster import KindClusterConfig, KindClusterManager
from modules.network import create_development_network

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
config = pulumi.Config()
cluster_config_pulumi = pulumi.Config("cluster")

cluster_name = cluster_config_pulumi.get("name") or "platform-dev"
kubernetes_version = cluster_config_pulumi.get("kubernetesVersion") or "1.28"
num_worker_nodes = cluster_config_pulumi.get_int("numWorkerNodes") or 2
environment = cluster_config_pulumi.get("environment") or "dev"

# ---------------------------------------------------------------------------
# Connect to the existing Kind cluster
# ---------------------------------------------------------------------------
# Fetch the kubeconfig from the running Kind cluster so Pulumi knows
# where to create resources.  This fails fast with a clear error if
# the Kind cluster hasn't been created yet.
try:
    kubeconfig = subprocess.check_output(
        ["kind", "get", "kubeconfig", "--name", cluster_name],
        stderr=subprocess.PIPE,
    ).decode()
except (subprocess.CalledProcessError, FileNotFoundError) as exc:
    pulumi.log.error(
        f"Could not get kubeconfig for Kind cluster '{cluster_name}'. "
        f"Make sure the cluster exists:\n"
        f"  kind create cluster --name {cluster_name} --config kind-config.yaml\n"
        f"Error: {exc}"
    )
    raise

k8s_provider = k8s.Provider("kind-provider", kubeconfig=kubeconfig)

# ---------------------------------------------------------------------------
# Kind Cluster Config & Namespace Provisioning
# ---------------------------------------------------------------------------
kind_config = KindClusterConfig(
    cluster_name=cluster_name,
    kubernetes_version=kubernetes_version,
    num_worker_nodes=num_worker_nodes,
    enable_ingress=True,
    enable_metrics_server=True,
    labels={"environment": environment},
)

network_config = create_development_network()

manager = KindClusterManager(
    cluster_config=kind_config,
    network_config=network_config,
    stack_name=environment,
    provider=k8s_provider,
)

# Deploy namespaces, quotas, and limits onto the existing cluster
outputs = manager.deploy_cluster()

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
pulumi.export("cluster_name", cluster_name)
pulumi.export("kubernetes_version", kubernetes_version)
pulumi.export("worker_nodes", num_worker_nodes)
pulumi.export("environment", environment)
pulumi.export("kind_config_yaml", outputs["kind_config_yaml"])
pulumi.export("namespaces", outputs["namespaces"])
