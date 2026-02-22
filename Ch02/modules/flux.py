"""
Flux GitOps Controller Configuration Module

This module manages Flux CD configuration for declarative continuous deployment.
It implements the App of Apps pattern to organize applications hierarchically
and provides GitOps-based reconciliation of cluster state.

Classes:
    FluxSourceConfig: Git source configuration for Flux
    FluxKustomizationConfig: Kustomization configuration for reconciliation
    FluxAppOfAppsManager: Manages hierarchical application structure
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts
from pulumi_kubernetes.core.v1 import Namespace
from pulumi_kubernetes.meta.v1 import ObjectMeta


@dataclass
class FluxSourceConfig:
    """
    Git repository source configuration for Flux.
    
    Attributes:
        name: Source identifier
        namespace: Kubernetes namespace for the source
        repository_url: Git repository URL (https or ssh)
        branch: Branch to track (default: main)
        interval: Sync interval (default: "5m0s")
        username: Username for private repositories
        password: Password/token for private repositories (use secrets in production)
        ssh_key: SSH private key for git authentication
        skip_tls_verify: Skip TLS verification for self-signed certs
        commit_message_template: Template for automatic commits
    """
    name: str
    namespace: str
    repository_url: str
    branch: str = "main"
    interval: str = "5m0s"
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_key: Optional[str] = None
    skip_tls_verify: bool = False
    commit_message_template: Optional[str] = None

    def to_kubernetes_resource(self) -> Dict[str, Any]:
        """
        Convert to Kubernetes GitRepository resource.
        
        Returns:
            GitRepository manifest for Flux
        """
        spec: Dict[str, Any] = {
            "interval": self.interval,
            "ref": {"branch": self.branch},
            "url": self.repository_url,
        }

        if self.skip_tls_verify:
            spec["insecureSkipTlsVerify"] = True

        return {
            "apiVersion": "source.toolkit.fluxcd.io/v1beta2",
            "kind": "GitRepository",
            "metadata": {"name": self.name, "namespace": self.namespace},
            "spec": spec,
        }


@dataclass
class FluxKustomizationConfig:
    """
    Kustomization configuration for Flux reconciliation.
    
    Attributes:
        name: Kustomization identifier
        namespace: Kubernetes namespace
        source_name: Name of the Git source
        source_namespace: Namespace of the Git source
        path: Path in git repository
        interval: Reconciliation interval
        validation: Validation strategy ("none", "server", "client")
        prune: Automatically delete resources not in git
        force: Force reconciliation even if no changes
        wait: Wait for resources to be ready (max 5 minutes)
        retry_interval: Retry failed reconciliations every N duration
        health_checks: Resources to check for readiness
        patches: Strategic merge patches to apply
        depends_on: Other kustomizations this depends on
    """
    name: str
    namespace: str
    source_name: str
    source_namespace: str
    path: str
    interval: str = "5m0s"
    validation: str = "server"
    prune: bool = True
    force: bool = False
    wait: bool = True
    retry_interval: str = "1m0s"
    health_checks: List[Dict[str, str]] = field(default_factory=list)
    patches: List[Dict[str, Any]] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)

    def to_kubernetes_resource(self) -> Dict[str, Any]:
        """
        Convert to Kubernetes Kustomization resource.
        
        Returns:
            Kustomization manifest for Flux
        """
        spec: Dict[str, Any] = {
            "interval": self.interval,
            "sourceRef": {
                "apiVersion": "source.toolkit.fluxcd.io/v1beta2",
                "kind": "GitRepository",
                "name": self.source_name,
                "namespace": self.source_namespace,
            },
            "path": self.path,
            "prune": self.prune,
            "force": self.force,
            "wait": self.wait,
            "retryInterval": self.retry_interval,
        }

        if self.validation != "none":
            spec["validation"] = self.validation

        if self.health_checks:
            spec["healthChecks"] = self.health_checks

        if self.patches:
            spec["patches"] = self.patches

        if self.depends_on:
            spec["dependsOn"] = [
                {
                    "name": dep,
                    "namespace": self.namespace,
                }
                for dep in self.depends_on
            ]

        return {
            "apiVersion": "kustomize.toolkit.fluxcd.io/v1beta2",
            "kind": "Kustomization",
            "metadata": {"name": self.name, "namespace": self.namespace},
            "spec": spec,
        }


class FluxAppOfAppsManager:
    """
    Manages hierarchical application structure using Flux App of Apps pattern.
    
    The App of Apps pattern creates a root application that manages other
    applications, enabling scalable and organized GitOps workflows.
    
    Example hierarchy:
        root-app (manages)
        ├── platform-services (istio, cert-manager, monitoring)
        └── workload-apps (user applications)
    """

    def __init__(
        self,
        git_repository_url: str,
        git_branch: str = "main",
        namespace: str = "flux-system",
        stack_name: str = "dev",
    ):
        """
        Initialize Flux AppOfApps manager.
        
        Args:
            git_repository_url: Git repository URL for Flux
            git_branch: Git branch to track
            namespace: Kubernetes namespace for Flux
            stack_name: Pulumi stack name
        """
        self.git_repository_url = git_repository_url
        self.git_branch = git_branch
        self.namespace = namespace
        self.stack_name = stack_name
        self.sources: Dict[str, FluxSourceConfig] = {}
        self.kustomizations: Dict[str, FluxKustomizationConfig] = {}

    def add_source(
        self,
        name: str,
        repository_url: str,
        branch: str = "main",
        interval: str = "5m0s",
    ) -> FluxSourceConfig:
        """
        Add a Git source for Flux.
        
        Args:
            name: Source identifier
            repository_url: Git repository URL
            branch: Branch to track
            interval: Sync interval
            
        Returns:
            FluxSourceConfig instance
        """
        source = FluxSourceConfig(
            name=name,
            namespace=self.namespace,
            repository_url=repository_url,
            branch=branch,
            interval=interval,
        )
        self.sources[name] = source
        return source

    def add_kustomization(
        self,
        name: str,
        source_name: str,
        path: str,
        depends_on: Optional[List[str]] = None,
        **kwargs,
    ) -> FluxKustomizationConfig:
        """
        Add a Kustomization for Flux reconciliation.
        
        Args:
            name: Kustomization identifier
            source_name: Name of the Git source
            path: Path in git repository
            depends_on: List of kustomizations this depends on
            **kwargs: Additional Kustomization parameters
            
        Returns:
            FluxKustomizationConfig instance
        """
        kustomization = FluxKustomizationConfig(
            name=name,
            namespace=self.namespace,
            source_name=source_name,
            source_namespace=self.namespace,
            path=path,
            depends_on=depends_on or [],
            **kwargs,
        )
        self.kustomizations[name] = kustomization
        return kustomization

    def create_root_application(self) -> FluxKustomizationConfig:
        """
        Create root application that manages all others.
        
        The root application serves as the entry point for the App of Apps pattern,
        managing platform services and workload applications.
        
        Returns:
            Root Kustomization configuration
        """
        root = self.add_kustomization(
            name="root-app",
            source_name="primary-source",
            path="./apps",
            interval="1m0s",
            validation="server",
        )
        return root

    def create_platform_services_app(self) -> FluxKustomizationConfig:
        """
        Create platform services application.
        
        Manages cluster-wide services:
        - Istio service mesh
        - cert-manager for TLS
        - Prometheus/Grafana monitoring
        - OPA/Gatekeeper policies
        
        Returns:
            Platform services Kustomization configuration
        """
        platform_app = self.add_kustomization(
            name="platform-services-app",
            source_name="primary-source",
            path="./platform-services",
            interval="5m0s",
            validation="server",
            depends_on=["root-app"],
            health_checks=[
                {
                    "apiVersion": "v1",
                    "kind": "Deployment",
                    "name": "istiod",
                    "namespace": "istio-system",
                },
                {
                    "apiVersion": "v1",
                    "kind": "Deployment",
                    "name": "cert-manager",
                    "namespace": "cert-manager",
                },
            ],
        )
        return platform_app

    def create_workload_app(
        self,
        app_name: str,
        path: str,
        namespace: str,
    ) -> FluxKustomizationConfig:
        """
        Create a workload application.
        
        Workload applications are user-facing services managed by Flux.
        
        Args:
            app_name: Application identifier
            path: Path in git repository
            namespace: Kubernetes namespace for the application
            
        Returns:
            Workload Kustomization configuration
        """
        workload_app = self.add_kustomization(
            name=f"{app_name}-app",
            source_name="primary-source",
            path=path,
            interval="5m0s",
            validation="server",
            depends_on=["platform-services-app"],
            health_checks=[
                {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": app_name,
                    "namespace": namespace,
                },
            ],
        )
        return workload_app

    def deploy_flux(self, provider: k8s.Provider) -> Dict[str, pulumi.Output[Any]]:
        """
        Deploy Flux GitOps controller to cluster.
        
        Installs Flux components and configures GitOps sources and kustomizations.
        
        Args:
            provider: Kubernetes provider for resource creation
            
        Returns:
            Dictionary of Flux-related outputs
        """
        # Create Flux namespace
        flux_namespace = Namespace(
            "flux-system-ns",
            metadata=ObjectMeta(
                name=self.namespace,
                labels={
                    "toolkit.fluxcd.io/tenant": "sre",
                },
            ),
            opts=pulumi.ResourceOptions(provider=provider),
        )

        # Install Flux via Helm chart
        flux_chart = Chart(
            "flux2",
            ChartOpts(
                chart="flux2",
                namespace=self.namespace,
                values={
                    "gitRepository": {
                        "url": self.git_repository_url,
                        "branch": self.git_branch,
                    },
                    "historyLimit": 10,
                    "installCRDs": True,
                },
                repo="https://fluxcd-community.github.io/helm-charts",
            ),
            opts=pulumi.ResourceOptions(
                provider=provider,
                depends_on=[flux_namespace],
            ),
        )

        # Export Flux configuration
        outputs = {
            "flux_namespace": self.namespace,
            "git_repository": self.git_repository_url,
            "git_branch": self.git_branch,
            "sources_count": len(self.sources),
            "kustomizations_count": len(self.kustomizations),
        }

        pulumi.export("flux_namespace", self.namespace)
        pulumi.export("git_repository", self.git_repository_url)

        return outputs

    def generate_manifests(self) -> Dict[str, str]:
        """
        Generate Kubernetes manifests for Flux sources and kustomizations.
        
        Useful for applying Flux configuration declaratively without Helm.
        
        Returns:
            Dictionary mapping resource names to YAML manifests
        """
        manifests = {}

        # Generate source manifests
        for name, source in self.sources.items():
            import yaml
            manifests[f"{name}-source"] = yaml.dump(
                source.to_kubernetes_resource()
            )

        # Generate kustomization manifests
        for name, kustomization in self.kustomizations.items():
            import yaml
            manifests[f"{name}-kustomization"] = yaml.dump(
                kustomization.to_kubernetes_resource()
            )

        return manifests


def create_default_flux_app_of_apps(
    git_repository_url: str,
    git_branch: str = "main",
) -> FluxAppOfAppsManager:
    """
    Create a default App of Apps configuration for Flux.
    
    Creates hierarchical application structure with:
    - Root application
    - Platform services (Istio, cert-manager, monitoring)
    - Sample workload applications
    
    Args:
        git_repository_url: Git repository URL for Flux
        git_branch: Git branch to track
        
    Returns:
        Configured FluxAppOfAppsManager instance
    """
    manager = FluxAppOfAppsManager(
        git_repository_url=git_repository_url,
        git_branch=git_branch,
    )

    # Add primary source
    manager.add_source(
        name="primary-source",
        repository_url=git_repository_url,
        branch=git_branch,
        interval="5m0s",
    )

    # Create root application
    manager.create_root_application()

    # Create platform services application
    manager.create_platform_services_app()

    # Create sample workload applications
    manager.create_workload_app(
        app_name="api-backend",
        path="./applications/api-backend",
        namespace="application",
    )

    manager.create_workload_app(
        app_name="frontend",
        path="./applications/frontend",
        namespace="application",
    )

    return manager
