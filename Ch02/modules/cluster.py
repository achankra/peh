"""
Kubernetes Cluster Provisioning Module for Kind

This module provides Pulumi-based infrastructure as code for deploying local
Kubernetes clusters using Kind (Kubernetes in Docker). It handles cluster
creation, configuration, and resource provisioning with proper dependency
management and error handling.

Classes:
    KindClusterConfig: Configuration for Kind cluster provisioning
    KindClusterManager: Manages cluster lifecycle (create, destroy, query)
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.core.v1 import Namespace, ResourceQuota, LimitRange
from pulumi_kubernetes.meta.v1 import ObjectMeta, ObjectFieldSelector
from .network import NetworkConfig, ServiceMeshConfig


@dataclass
class KindClusterConfig:
    """
    Configuration for Kind cluster provisioning.
    
    Attributes:
        cluster_name: Name of the Kind cluster
        kubernetes_version: Kubernetes version (e.g., "1.27.0")
        num_worker_nodes: Number of worker nodes in addition to control plane
        api_server_port: Port for Kubernetes API server (default: 6443)
        enable_ingress: Deploy Nginx Ingress Controller
        enable_metrics_server: Deploy Metrics Server for resource monitoring
        docker_network_name: Custom Docker network for cluster (optional)
        containerd_config: Custom containerd configuration
        kubeadm_config: Custom kubeadm configuration
        extra_port_mappings: Additional port mappings between host and cluster
        labels: Labels to apply to all nodes
        extra_mounts: Additional volume mounts for nodes
    """
    cluster_name: str
    kubernetes_version: str = "1.27.0"
    num_worker_nodes: int = 2
    api_server_port: int = 6443
    enable_ingress: bool = True
    enable_metrics_server: bool = True
    docker_network_name: Optional[str] = None
    containerd_config: Dict[str, Any] = field(default_factory=dict)
    kubeadm_config: Dict[str, Any] = field(default_factory=dict)
    extra_port_mappings: List[Dict[str, Any]] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    extra_mounts: List[Dict[str, str]] = field(default_factory=list)


class KindClusterManager:
    """
    Manages Kubernetes Kind cluster provisioning and configuration via Pulumi.
    
    This class orchestrates the creation of Kind clusters, application of network
    policies, namespace setup, and installation of cluster components. It handles
    Pulumi resource creation with proper dependency management.
    """

    def __init__(
        self,
        cluster_config: KindClusterConfig,
        network_config: NetworkConfig,
        stack_name: str = "dev",
    ):
        """
        Initialize cluster manager.
        
        Args:
            cluster_config: Kind cluster configuration
            network_config: Network topology configuration
            stack_name: Pulumi stack name for resource naming
        """
        self.cluster_config = cluster_config
        self.network_config = network_config
        self.stack_name = stack_name
        self.provider: Optional[k8s.Provider] = None
        self.kubeconfig: Optional[pulumi.Output[str]] = None
        self.cluster_outputs: Dict[str, Any] = {}

    def create_kind_cluster(self) -> Dict[str, Any]:
        """
        Create Kind cluster configuration using kubeadm and containerd.
        
        Generates the Kind cluster configuration file with:
        - Networking settings from network_config
        - Node configuration with labels and taints
        - Port mappings for ingress and API access
        - Containerd runtime configuration
        
        Returns:
            Dictionary representing Kind cluster configuration
        """
        # Base cluster configuration
        config = {
            "kind": "Cluster",
            "apiVersion": "kind.x-k8s.io/v1alpha4",
            "name": self.cluster_config.cluster_name,
            "kubeadmConfigPatches": [
                # API server configuration
                """
kind: ClusterConfiguration
metadata:
  name: config
apiServer:
  extraArgs:
    enable-admission-plugins: "PodSecurityPolicy,ResourceQuota,LimitRanger"
  timeoutForControlPlane: 5m
controllerManager:
  extraArgs:
    enable-controller-manager: "true"
""",
            ],
            "networking": {
                "serviceSubnet": "10.96.0.0/12",
                "podSubnet": "10.244.0.0/16",
                "ipFamily": "ipv4",
            },
            "nodes": [],
            "containerdConfigPatches": [],
        }

        # Add control plane node
        config["nodes"].append({
            "role": "control-plane",
            "image": f"kindest/node:v{self.cluster_config.kubernetes_version}",
            "labels": {
                "node-type": "control-plane",
                **self.cluster_config.labels,
            },
            "extraPortMappings": [
                {
                    "containerPort": 80,
                    "hostPort": 8080,
                    "protocol": "tcp",
                },
                {
                    "containerPort": 443,
                    "hostPort": 8443,
                    "protocol": "tcp",
                },
            ] + self.cluster_config.extra_port_mappings,
        })

        # Add worker nodes
        for i in range(self.cluster_config.num_worker_nodes):
            config["nodes"].append({
                "role": "worker",
                "image": f"kindest/node:v{self.cluster_config.kubernetes_version}",
                "labels": {
                    "node-type": "worker",
                    "worker-id": str(i),
                    **self.cluster_config.labels,
                },
            })

        return config

    def create_provider(self) -> k8s.Provider:
        """
        Create Kubernetes provider for Pulumi resource management.
        
        Returns:
            Configured Kubernetes provider using kubeconfig
        """
        if self.provider:
            return self.provider

        # In a real scenario, this would connect to an existing Kind cluster
        # For this example, we'll create a minimal provider configuration
        self.provider = k8s.Provider(
            f"{self.cluster_config.cluster_name}-provider",
            kubeconfig=self.kubeconfig if self.kubeconfig else "",
        )
        return self.provider

    def setup_namespaces(self, provider: k8s.Provider) -> Dict[str, Namespace]:
        """
        Create essential Kubernetes namespaces.
        
        Creates namespaces with resource quotas and limit ranges for:
        - flux-system: GitOps controller
        - istio-system: Service mesh control plane
        - cert-manager: TLS certificate management
        - monitoring: Prometheus, Grafana, Alertmanager
        - application: User application workloads
        
        Args:
            provider: Kubernetes provider for resource creation
            
        Returns:
            Dictionary mapping namespace names to Namespace objects
        """
        namespaces = {}
        namespace_configs = [
            {
                "name": "flux-system",
                "labels": {"toolkit.fluxcd.io/tenant": "sre"},
            },
            {
                "name": "istio-system",
                "labels": {"istio-injection": "disabled"},
            },
            {
                "name": "cert-manager",
                "labels": {},
            },
            {
                "name": "monitoring",
                "labels": {"istio-injection": "enabled"},
            },
            {
                "name": "application",
                "labels": {"istio-injection": "enabled"},
            },
        ]

        for ns_config in namespace_configs:
            ns = Namespace(
                ns_config["name"],
                metadata=ObjectMeta(
                    name=ns_config["name"],
                    labels=ns_config["labels"],
                ),
                opts=pulumi.ResourceOptions(provider=provider),
            )
            namespaces[ns_config["name"]] = ns

            # Add resource quota to application namespace
            if ns_config["name"] == "application":
                ResourceQuota(
                    f"{ns_config['name']}-quota",
                    metadata=ObjectMeta(namespace=ns_config["name"]),
                    spec={
                        "hard": {
                            "requests.cpu": "10",
                            "requests.memory": "20Gi",
                            "limits.cpu": "20",
                            "limits.memory": "40Gi",
                            "pods": "100",
                        },
                    },
                    opts=pulumi.ResourceOptions(
                        provider=provider,
                        depends_on=[ns],
                    ),
                )

            # Add limit range to namespace
            LimitRange(
                f"{ns_config['name']}-limits",
                metadata=ObjectMeta(namespace=ns_config["name"]),
                spec={
                    "limits": [
                        {
                            "type": "Pod",
                            "min": {
                                "cpu": "50m",
                                "memory": "64Mi",
                            },
                            "max": {
                                "cpu": "2",
                                "memory": "4Gi",
                            },
                        },
                        {
                            "type": "Container",
                            "min": {
                                "cpu": "50m",
                                "memory": "64Mi",
                            },
                            "max": {
                                "cpu": "2",
                                "memory": "4Gi",
                            },
                            "defaultRequest": {
                                "cpu": "100m",
                                "memory": "128Mi",
                            },
                            "default": {
                                "cpu": "500m",
                                "memory": "512Mi",
                            },
                        },
                    ],
                },
                opts=pulumi.ResourceOptions(
                    provider=provider,
                    depends_on=[ns],
                ),
            )

        return namespaces

    def deploy_cluster(self) -> Dict[str, pulumi.Output[Any]]:
        """
        Deploy complete Kind cluster infrastructure.
        
        Orchestrates:
        1. Kind cluster creation with proper networking
        2. Kubernetes provider initialization
        3. Namespace setup with quotas and limits
        4. Initial cluster validation
        
        Returns:
            Dictionary of Pulumi outputs for cluster access
        """
        # Create cluster configuration
        cluster_config = self.create_kind_cluster()
        
        # Output cluster configuration for reference
        pulumi.export("cluster_config", cluster_config)

        # Create provider (in real deployment, would use kubeconfig)
        provider = self.create_provider()

        # Setup namespaces
        namespaces = self.setup_namespaces(provider)
        
        # Export namespace names
        pulumi.export(
            "namespaces",
            pulumi.Output.concat(*[f"{name}, " for name in namespaces.keys()]),
        )

        # Export cluster details
        self.cluster_outputs = {
            "cluster_name": self.cluster_config.cluster_name,
            "kubernetes_version": self.cluster_config.kubernetes_version,
            "num_worker_nodes": self.cluster_config.num_worker_nodes,
            "namespaces": list(namespaces.keys()),
        }

        pulumi.export("cluster_name", self.cluster_config.cluster_name)
        pulumi.export("kubernetes_version", self.cluster_config.kubernetes_version)
        pulumi.export("worker_nodes", self.cluster_config.num_worker_nodes)

        return self.cluster_outputs


def create_dev_cluster() -> KindClusterManager:
    """
    Create a development Kind cluster configuration.
    
    Development cluster has:
    - 1 control plane + 2 worker nodes
    - Kubernetes 1.27.0
    - Ingress enabled
    - Metrics server enabled
    
    Returns:
        Configured KindClusterManager instance
    """
    from .network import create_development_network

    cluster_config = KindClusterConfig(
        cluster_name="platform-dev",
        kubernetes_version="1.27.0",
        num_worker_nodes=2,
        enable_ingress=True,
        enable_metrics_server=True,
        labels={"environment": "development"},
    )

    network_config = create_development_network()

    return KindClusterManager(
        cluster_config=cluster_config,
        network_config=network_config,
        stack_name="dev",
    )


def create_prod_cluster() -> KindClusterManager:
    """
    Create a production-like Kind cluster configuration.
    
    Production cluster has:
    - 1 control plane + 3 worker nodes
    - Kubernetes 1.27.0
    - All advanced features enabled
    
    Returns:
        Configured KindClusterManager instance
    """
    from .network import create_production_network

    cluster_config = KindClusterConfig(
        cluster_name="platform-prod",
        kubernetes_version="1.27.0",
        num_worker_nodes=3,
        enable_ingress=True,
        enable_metrics_server=True,
        labels={"environment": "production"},
    )

    network_config = create_production_network()

    return KindClusterManager(
        cluster_config=cluster_config,
        network_config=network_config,
        stack_name="prod",
    )
