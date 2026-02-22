#!/usr/bin/env python3
"""Generate environment-specific Crossplane compositions.

This script generates separate Crossplane compositions for each environment
(development, staging, production) with appropriate defaults for:
- Instance class/size
- Storage allocation
- Backup retention
- Multi-AZ configuration
- Deletion protection
- Performance insights
"""

from dataclasses import dataclass
from typing import Dict, Any
import yaml


@dataclass
class EnvironmentConfig:
    """Configuration defaults for an environment."""
    instance_class: str
    storage_gb: int
    backup_retention_days: int
    multi_az: bool
    deletion_protection: bool
    performance_insights: bool


ENVIRONMENTS: Dict[str, EnvironmentConfig] = {
    "development": EnvironmentConfig(
        instance_class="db.t3.micro",
        storage_gb=20,
        backup_retention_days=1,
        multi_az=False,
        deletion_protection=False,
        performance_insights=False
    ),
    "staging": EnvironmentConfig(
        instance_class="db.t3.small",
        storage_gb=50,
        backup_retention_days=7,
        multi_az=False,
        deletion_protection=False,
        performance_insights=True
    ),
    "production": EnvironmentConfig(
        instance_class="db.r6g.large",
        storage_gb=100,
        backup_retention_days=30,
        multi_az=True,
        deletion_protection=True,
        performance_insights=True
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
                "provider": "aws"
            }
        },
        "spec": {
            "compositeTypeRef": {
                "apiVersion": "database.platform.io/v1alpha1",
                "kind": "PostgreSQLInstance"
            },
            "resources": [{
                "name": "rds-instance",
                "base": {
                    "apiVersion": "rds.aws.upbound.io/v1beta1",
                    "kind": "Instance",
                    "spec": {
                        "forProvider": {
                            "engine": "postgres",
                            "instanceClass": config.instance_class,
                            "allocatedStorage": config.storage_gb,
                            "backupRetentionPeriod": config.backup_retention_days,
                            "multiAz": config.multi_az,
                            "deletionProtection": config.deletion_protection,
                            "performanceInsightsEnabled": config.performance_insights,
                            "storageEncrypted": True,
                            "publiclyAccessible": False
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
