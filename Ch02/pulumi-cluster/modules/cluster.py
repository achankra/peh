"""
Kind Cluster Management Module
==============================
Provides configuration and deployment helpers for a local Kind
(Kubernetes in Docker) cluster managed through Pulumi.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pulumi
import pulumi_kubernetes as k8s
import yaml


# ---------------------------------------------------------------------------
# Configuration data-class
# ---------------------------------------------------------------------------
@dataclass
class KindClusterConfig:
    """Holds the desired-state configuration for a Kind cluster."""

    cluster_name: str = "platform-dev"
    kubernetes_version: str = "1.28"
    num_worker_nodes: int = 2
    enable_ingress: bool = True
    enable_metrics_server: bool = True
    labels: Dict[str, str] = field(default_factory=lambda: {"environment": "dev"})

    @property
    def kind_image(self) -> str:
        """Return the Kind node image tag that matches the requested K8s version."""
        return f"kindest/node:v{self.kubernetes_version}.0"


# ---------------------------------------------------------------------------
# Cluster Manager
# ---------------------------------------------------------------------------
class KindClusterManager:
    """Generates the Kind config and Pulumi resources for a local cluster."""

    # Platform namespaces that every cluster should have
    PLATFORM_NAMESPACES: List[str] = [
        "platform-system",
        "monitoring",
        "ingress",
        "databases",
        "apps",
    ]

    def __init__(
        self,
        cluster_config: KindClusterConfig,
        network_config: Optional[dict] = None,
        stack_name: str = "dev",
        provider: Optional[k8s.Provider] = None,
    ):
        self.config = cluster_config
        self.network = network_config or {}
        self.stack_name = stack_name
        self.provider = provider

    # ------------------------------------------------------------------
    # Kind config YAML
    # ------------------------------------------------------------------
    def _build_kind_config(self) -> str:
        """Build the Kind cluster configuration YAML."""
        kind_cfg: dict = {
            "kind": "Cluster",
            "apiVersion": "kind.x-k8s.io/v1alpha4",
            "name": self.config.cluster_name,
            "nodes": self._build_nodes(),
        }

        if self.network:
            kind_cfg["networking"] = self.network

        return yaml.dump(kind_cfg, default_flow_style=False)

    def _build_nodes(self) -> list:
        """Return the node list (1 control-plane + N workers)."""
        control_plane: dict = {
            "role": "control-plane",
            "image": self.config.kind_image,
        }

        # If ingress is enabled, expose ports 80/443 on the control-plane node
        if self.config.enable_ingress:
            control_plane["kubeadmConfigPatches"] = [
                yaml.dump(
                    {
                        "kind": "InitConfiguration",
                        "nodeRegistration": {
                            "kubeletExtraArgs": {
                                "node-labels": "ingress-ready=true",
                            }
                        },
                    }
                )
            ]
            control_plane["extraPortMappings"] = [
                {
                    "containerPort": 80,
                    "hostPort": 80,
                    "protocol": "TCP",
                },
                {
                    "containerPort": 443,
                    "hostPort": 443,
                    "protocol": "TCP",
                },
            ]

        workers = [
            {"role": "worker", "image": self.config.kind_image}
            for _ in range(self.config.num_worker_nodes)
        ]

        return [control_plane] + workers

    # ------------------------------------------------------------------
    # Pulumi resources
    # ------------------------------------------------------------------
    def deploy_cluster(self) -> dict:
        """Create Pulumi resources: config file, namespaces, quotas, limits."""

        # 1. Write the Kind config as a Pulumi stack output so it can be
        #    consumed by a shell step: kind create cluster --config <file>
        kind_yaml = self._build_kind_config()

        # 2. Create the platform namespaces and their resource quotas
        namespaces = self._create_namespaces()

        return {
            "kind_config_yaml": kind_yaml,
            "namespaces": [ns.metadata["name"] for ns in namespaces],
        }

    def _create_namespaces(self) -> list:
        """Create Kubernetes Namespace + ResourceQuota + LimitRange resources."""
        created: list = []
        opts = pulumi.ResourceOptions(provider=self.provider) if self.provider else None

        for ns_name in self.PLATFORM_NAMESPACES:
            labels = {**self.config.labels, "managed-by": "pulumi"}

            ns = k8s.core.v1.Namespace(
                ns_name,
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    name=ns_name,
                    labels=labels,
                ),
                opts=opts,
            )

            # ResourceQuota -------------------------------------------------
            k8s.core.v1.ResourceQuota(
                f"{ns_name}-quota",
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    name="default-quota",
                    namespace=ns.metadata["name"],
                ),
                spec=k8s.core.v1.ResourceQuotaSpecArgs(
                    hard={
                        "requests.cpu": "2",
                        "requests.memory": "4Gi",
                        "limits.cpu": "4",
                        "limits.memory": "8Gi",
                        "pods": "20",
                    },
                ),
                opts=opts,
            )

            # LimitRange ----------------------------------------------------
            k8s.core.v1.LimitRange(
                f"{ns_name}-limits",
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    name="default-limits",
                    namespace=ns.metadata["name"],
                ),
                spec=k8s.core.v1.LimitRangeSpecArgs(
                    limits=[
                        k8s.core.v1.LimitRangeItemArgs(
                            type="Container",
                            default={
                                "cpu": "500m",
                                "memory": "512Mi",
                            },
                            default_request={
                                "cpu": "100m",
                                "memory": "128Mi",
                            },
                        ),
                    ],
                ),
                opts=opts,
            )

            created.append(ns)

        return created
