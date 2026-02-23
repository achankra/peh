"""
Chapter 2: Scalable Platform Runtime - Pulumi Kind Cluster
==========================================================
Deploys a local Kind (Kubernetes in Docker) cluster with namespaces,
resource quotas, and limit ranges using Pulumi.

Usage:
    pulumi stack init dev
    pulumi up

Prerequisites:
    - Kind installed (brew install kind / go install sigs.k8s.io/kind)
    - Docker running
    - Pulumi CLI installed (curl -fsSL https://get.pulumi.com | sh)
    - Python 3.8+
"""

import pulumi
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
# Kind Cluster
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
)

# Deploy cluster and namespaces
outputs = manager.deploy_cluster()

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
pulumi.export("cluster_name", cluster_name)
pulumi.export("kubernetes_version", kubernetes_version)
pulumi.export("worker_nodes", num_worker_nodes)
pulumi.export("environment", environment)
pulumi.export(
    "next_steps",
    f"Run: kind create cluster --name {cluster_name} --config kind-config.yaml",
)
