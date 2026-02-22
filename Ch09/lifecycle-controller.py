#!/usr/bin/env python3
"""Infrastructure lifecycle controller - enforces age limits and ownership policies.

This controller watches Crossplane claims and enforces organizational policies:
- Maximum age limits per environment tier
- Required owner labels for production resources
- Automatic cleanup scheduling for development resources
"""

import asyncio
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
from kubernetes import client, config, watch


@dataclass
class LifecyclePolicy:
    max_age_days: Optional[int] = None
    require_owner_label: bool = True
    auto_cleanup: bool = False


POLICIES = {
    "development": LifecyclePolicy(max_age_days=30, auto_cleanup=True),
    "staging": LifecyclePolicy(max_age_days=90),
    "production": LifecyclePolicy(max_age_days=None, require_owner_label=True)
}


class LifecycleController:
    def __init__(self):
        config.load_incluster_config()
        self.api = client.CustomObjectsApi()

    def check_violations(self, resource: dict) -> list[str]:
        tier = resource.get("spec", {}).get("parameters", {}).get("tier", "development")
        policy = POLICIES.get(tier, POLICIES["development"])
        violations = []

        # Check age limit
        if policy.max_age_days:
            created = datetime.fromisoformat(
                resource["metadata"]["creationTimestamp"].replace("Z", "+00:00"))
            age = (datetime.now(created.tzinfo) - created).days
            if age > policy.max_age_days:
                violations.append(f"Age {age}d exceeds {policy.max_age_days}d limit")

        # Check owner label
        if policy.require_owner_label:
            if "platform.io/owner" not in resource.get("metadata", {}).get("labels", {}):
                violations.append("Missing platform.io/owner label")

        return violations

    async def run(self):
        for event in watch.Watch().stream(
            self.api.list_cluster_custom_object,
            group="database.platform.io", version="v1alpha1", plural="postgresqlclaims"
        ):
            if event["type"] in ["ADDED", "MODIFIED"]:
                violations = self.check_violations(event["object"])
                if violations:
                    name = event["object"]["metadata"]["name"]
                    print(f"Policy violations for {name}: {violations}")


if __name__ == "__main__":
    asyncio.run(LifecycleController().run())
