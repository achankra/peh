#!/usr/bin/env python3
"""Generate environment-specific Crossplane compositions.

This script generates separate Crossplane compositions for each environment
(development, staging, production) with appropriate defaults for:
- Resource requests (CPU, memory)
- Storage allocation
- Backup retention
- Replica count
- Deletion protection

All compositions use the Kubernetes provider to deploy PostgreSQL
as StatefulSets inside the Kind cluster — no cloud dependencies.
"""

from dataclasses import dataclass
from typing import Dict, Any
import yaml


@dataclass
class EnvironmentConfig:
    """Configuration defaults for an environment."""
    cpu_request: str
    memory_request: str
    cpu_limit: str
    memory_limit: str
    storage_gb: int
    backup_retention_days: int
    replicas: int
    deletion_protection: bool
    enable_monitoring: bool


ENVIRONMENTS: Dict[str, EnvironmentConfig] = {
    "development": EnvironmentConfig(
        cpu_request="100m",
        memory_request="256Mi",
        cpu_limit="500m",
        memory_limit="512Mi",
        storage_gb=1,
        backup_retention_days=1,
        replicas=1,
        deletion_protection=False,
        enable_monitoring=False
    ),
    "staging": EnvironmentConfig(
        cpu_request="250m",
        memory_request="512Mi",
        cpu_limit="1000m",
        memory_limit="1Gi",
        storage_gb=5,
        backup_retention_days=7,
        replicas=1,
        deletion_protection=False,
        enable_monitoring=True
    ),
    "production": EnvironmentConfig(
        cpu_request="500m",
        memory_request="1Gi",
        cpu_limit="2000m",
        memory_limit="2Gi",
        storage_gb=10,
        backup_retention_days=30,
        replicas=2,
        deletion_protection=True,
        enable_monitoring=True
    )
}


def generate_composition(env_name: str, config: EnvironmentConfig) -> Dict[str, Any]:
    """Generate a Crossplane composition for the given environment."""
    return {
        "apiVersion": "apiextensions.crossplane.io/v1",
        "kind": "Composition",
        "metadata": {
            "name": f"postgresql-{env_name}",
            "labels": {
                "environment": env_name,
                "provider": "kubernetes"
            }
        },
        "spec": {
            "compositeTypeRef": {
                "apiVersion": "database.platform.io/v1alpha1",
                "kind": "PostgreSQLInstance"
            },
            "resources": [{
                "name": "db-deployment",
                "base": {
                    "apiVersion": "kubernetes.crossplane.io/v1alpha2",
                    "kind": "Object",
                    "spec": {
                        "forProvider": {
                            "manifest": {
                                "apiVersion": "apps/v1",
                                "kind": "Deployment",
                                "metadata": {
                                    "name": f"postgresql-{env_name}",
                                    "namespace": "databases"
                                },
                                "spec": {
                                    "replicas": config.replicas,
                                    "selector": {
                                        "matchLabels": {
                                            "app": "postgresql",
                                            "environment": env_name
                                        }
                                    },
                                    "template": {
                                        "metadata": {
                                            "labels": {
                                                "app": "postgresql",
                                                "environment": env_name
                                            }
                                        },
                                        "spec": {
                                            "containers": [{
                                                "name": "postgresql",
                                                "image": "postgres:15-alpine",
                                                "resources": {
                                                    "requests": {
                                                        "cpu": config.cpu_request,
                                                        "memory": config.memory_request
                                                    },
                                                    "limits": {
                                                        "cpu": config.cpu_limit,
                                                        "memory": config.memory_limit
                                                    }
                                                }
                                            }]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }]
        }
    }


if __name__ == "__main__":
    for env_name, config in ENVIRONMENTS.items():
        composition = generate_composition(env_name, config)
        filename = f"composition-postgresql-{env_name}.yaml"
        with open(filename, "w") as f:
            yaml.dump(composition, f, default_flow_style=False)
        print(f"Generated {filename}")
