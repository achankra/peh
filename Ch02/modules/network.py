"""
Network Configuration Module for Scalable Platform Runtime

This module defines network infrastructure configuration using Python DataClasses.
It provides a clean, type-safe way to configure VPCs, subnets, and service mesh settings
for Kubernetes deployments on Kind clusters.

Classes:
    SubnetConfig: Individual subnet configuration with CIDR and AZ
    NetworkConfig: Complete network topology for the cluster
    ServiceMeshConfig: Service mesh (Istio) configuration
    FirewallRule: Network policy enforcement rules
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class TrafficPolicy(Enum):
    """Network traffic policies for service mesh."""
    ALLOW_ALL = "allow_all"
    DENY_ALL = "deny_all"
    ISTIO_MUTUAL_TLS = "istio_mutual_tls"
    STRICT = "strict"


class LoggingLevel(Enum):
    """Logging verbosity levels for network debugging."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class SubnetConfig:
    """
    Configuration for a single subnet.
    
    Attributes:
        cidr_block: CIDR notation for the subnet (e.g., "10.0.1.0/24")
        name: Friendly name for the subnet
        availability_zone: AZ for the subnet (e.g., "us-east-1a")
        enable_nat: Whether to deploy NAT gateway for egress
        enable_public_ip: Assign public IPs to resources in subnet
        tags: Custom tags for the subnet
        route_table_name: Custom route table identifier
    """
    cidr_block: str
    name: str
    availability_zone: str
    enable_nat: bool = True
    enable_public_ip: bool = False
    tags: Dict[str, str] = field(default_factory=lambda: {"Environment": "dev"})
    route_table_name: Optional[str] = None

    def __post_init__(self):
        """Validate CIDR block format."""
        if "/" not in self.cidr_block:
            raise ValueError(f"Invalid CIDR format: {self.cidr_block}. Expected format: 10.0.0.0/24")


@dataclass
class ServiceMeshConfig:
    """
    Configuration for Istio service mesh.
    
    Attributes:
        enabled: Enable service mesh deployment
        version: Istio version (e.g., "1.17.1")
        namespace: Namespace for Istio control plane
        ingress_enabled: Deploy Istio Ingress Gateway
        egress_enabled: Deploy Istio Egress Gateway
        traffic_policy: Default traffic policy (mTLS settings)
        observability_enabled: Enable Prometheus/Kiali/Jaeger integration
        tracing_enabled: Enable distributed tracing
        logging_level: Logging verbosity
        pilot_replicas: Number of Istio Pilot replicas
        proxy_resources: Resource limits for sidecar proxies
    """
    enabled: bool = True
    version: str = "1.17.1"
    namespace: str = "istio-system"
    ingress_enabled: bool = True
    egress_enabled: bool = True
    traffic_policy: TrafficPolicy = TrafficPolicy.ISTIO_MUTUAL_TLS
    observability_enabled: bool = True
    tracing_enabled: bool = True
    logging_level: LoggingLevel = LoggingLevel.INFO
    pilot_replicas: int = 2
    proxy_resources: Dict[str, Dict[str, str]] = field(
        default_factory=lambda: {
            "requests": {"memory": "128Mi", "cpu": "100m"},
            "limits": {"memory": "256Mi", "cpu": "500m"},
        }
    )


@dataclass
class FirewallRule:
    """
    Network policy rule for traffic control.
    
    Attributes:
        name: Unique rule identifier
        direction: "ingress" or "egress"
        protocol: "tcp", "udp", or "all"
        port: Port number or range (e.g., "8080" or "8000-9000")
        source_cidr: Source CIDR block
        destination_cidr: Destination CIDR block
        action: "allow" or "deny"
        enabled: Whether the rule is active
    """
    name: str
    direction: str
    protocol: str
    source_cidr: str
    destination_cidr: str
    action: str = "allow"
    port: Optional[str] = None
    enabled: bool = True

    def __post_init__(self):
        """Validate rule configuration."""
        if self.direction not in ["ingress", "egress"]:
            raise ValueError(f"Invalid direction: {self.direction}")
        if self.protocol not in ["tcp", "udp", "all"]:
            raise ValueError(f"Invalid protocol: {self.protocol}")
        if self.action not in ["allow", "deny"]:
            raise ValueError(f"Invalid action: {self.action}")


@dataclass
class OPAConfig:
    """
    Configuration for OPA/Gatekeeper policy engine.
    
    Attributes:
        enabled: Enable OPA policy enforcement
        version: Gatekeeper version
        namespace: Namespace for OPA controllers
        constraint_templates: Custom constraint template definitions
        audit_interval: How often to audit cluster compliance
        enable_audit_logging: Log all policy decisions
    """
    enabled: bool = True
    version: str = "3.13.0"
    namespace: str = "gatekeeper-system"
    constraint_templates: List[str] = field(default_factory=list)
    audit_interval: str = "30s"
    enable_audit_logging: bool = True


@dataclass
class NetworkConfig:
    """
    Complete network topology configuration for Kubernetes cluster.
    
    This is the root configuration object that aggregates all network settings
    for infrastructure provisioning via Pulumi.
    
    Attributes:
        vpc_cidr: VPC CIDR block (e.g., "10.0.0.0/16")
        cluster_name: Kubernetes cluster identifier
        subnets: List of subnet configurations
        service_mesh: Istio service mesh configuration
        firewall_rules: Network policy rules
        opa: OPA/Gatekeeper policy engine settings
        enable_service_mesh: Deprecated - use service_mesh.enabled
        enable_policy: Deprecated - use opa.enabled
        dns_zone: DNS domain for cluster services
        nat_gateway_count: Number of NAT gateways to create
        enable_flow_logs: Enable VPC flow logs for debugging
        tags: Global tags for all resources
    """
    vpc_cidr: str
    cluster_name: str
    subnets: List[SubnetConfig]
    service_mesh: ServiceMeshConfig = field(default_factory=ServiceMeshConfig)
    firewall_rules: List[FirewallRule] = field(default_factory=list)
    opa: OPAConfig = field(default_factory=OPAConfig)
    dns_zone: str = "cluster.local"
    nat_gateway_count: int = 1
    enable_flow_logs: bool = True
    tags: Dict[str, str] = field(
        default_factory=lambda: {
            "Environment": "dev",
            "ManagedBy": "Pulumi",
            "Project": "ScalablePlatform",
        }
    )

    # Backward compatibility
    enable_service_mesh: bool = True
    enable_policy: bool = True

    def __post_init__(self):
        """Validate network configuration and set backward compatibility flags."""
        if "/" not in self.vpc_cidr:
            raise ValueError(f"Invalid VPC CIDR format: {self.vpc_cidr}")
        
        # Update service_mesh and opa based on deprecated flags if they differ
        if not self.enable_service_mesh:
            self.service_mesh.enabled = False
        if not self.enable_policy:
            self.opa.enabled = False

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary format for serialization.
        
        Returns:
            Dictionary representation of all configuration settings
        """
        return {
            "vpc_cidr": self.vpc_cidr,
            "cluster_name": self.cluster_name,
            "subnets": [
                {
                    "cidr_block": s.cidr_block,
                    "name": s.name,
                    "availability_zone": s.availability_zone,
                    "enable_nat": s.enable_nat,
                    "enable_public_ip": s.enable_public_ip,
                    "tags": s.tags,
                }
                for s in self.subnets
            ],
            "service_mesh": {
                "enabled": self.service_mesh.enabled,
                "version": self.service_mesh.version,
                "namespace": self.service_mesh.namespace,
                "ingress_enabled": self.service_mesh.ingress_enabled,
                "egress_enabled": self.service_mesh.egress_enabled,
                "traffic_policy": self.service_mesh.traffic_policy.value,
                "observability_enabled": self.service_mesh.observability_enabled,
                "tracing_enabled": self.service_mesh.tracing_enabled,
                "pilot_replicas": self.service_mesh.pilot_replicas,
            },
            "firewall_rules": [
                {
                    "name": r.name,
                    "direction": r.direction,
                    "protocol": r.protocol,
                    "port": r.port,
                    "source_cidr": r.source_cidr,
                    "destination_cidr": r.destination_cidr,
                    "action": r.action,
                    "enabled": r.enabled,
                }
                for r in self.firewall_rules
            ],
            "opa": {
                "enabled": self.opa.enabled,
                "version": self.opa.version,
                "namespace": self.opa.namespace,
                "audit_interval": self.opa.audit_interval,
                "enable_audit_logging": self.opa.enable_audit_logging,
            },
            "dns_zone": self.dns_zone,
            "nat_gateway_count": self.nat_gateway_count,
            "enable_flow_logs": self.enable_flow_logs,
            "tags": self.tags,
        }


def create_development_network() -> NetworkConfig:
    """
    Create a default network configuration for development environments.
    
    Returns:
        NetworkConfig with sensible development defaults
    """
    return NetworkConfig(
        vpc_cidr="10.0.0.0/16",
        cluster_name="platform-dev",
        subnets=[
            SubnetConfig(
                cidr_block="10.0.1.0/24",
                name="subnet-primary",
                availability_zone="us-east-1a",
                enable_nat=True,
            ),
            SubnetConfig(
                cidr_block="10.0.2.0/24",
                name="subnet-secondary",
                availability_zone="us-east-1b",
                enable_nat=True,
            ),
        ],
        service_mesh=ServiceMeshConfig(
            enabled=True,
            version="1.17.1",
            traffic_policy=TrafficPolicy.ISTIO_MUTUAL_TLS,
        ),
        opa=OPAConfig(enabled=True),
    )


def create_production_network() -> NetworkConfig:
    """
    Create a network configuration for production environments.
    
    Returns:
        NetworkConfig with production-grade settings
    """
    return NetworkConfig(
        vpc_cidr="10.0.0.0/16",
        cluster_name="platform-prod",
        subnets=[
            SubnetConfig(
                cidr_block="10.0.1.0/24",
                name="subnet-az1",
                availability_zone="us-east-1a",
                enable_nat=True,
            ),
            SubnetConfig(
                cidr_block="10.0.2.0/24",
                name="subnet-az2",
                availability_zone="us-east-1b",
                enable_nat=True,
            ),
            SubnetConfig(
                cidr_block="10.0.3.0/24",
                name="subnet-az3",
                availability_zone="us-east-1c",
                enable_nat=True,
            ),
        ],
        service_mesh=ServiceMeshConfig(
            enabled=True,
            version="1.17.1",
            traffic_policy=TrafficPolicy.STRICT,
            pilot_replicas=3,
        ),
        opa=OPAConfig(
            enabled=True,
            enable_audit_logging=True,
        ),
        nat_gateway_count=3,
        enable_flow_logs=True,
    )
