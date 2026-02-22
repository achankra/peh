#!/usr/bin/env python3
"""Handle custom infrastructure requests requiring approval.

For infrastructure needs that fall outside standard blueprints,
this module provides a governed request and approval workflow.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import json


class RequestStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROVISIONED = "provisioned"


@dataclass
class InfrastructureRequest:
    """A request for custom infrastructure."""
    id: str
    requester: str
    team: str
    description: str
    resource_type: str
    specifications: Dict[str, Any]
    justification: str
    estimated_monthly_cost: float
    status: RequestStatus = RequestStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None


class InfrastructureRequestHandler:
    """Handle infrastructure request workflow."""

    def __init__(self):
        self.requests: Dict[str, InfrastructureRequest] = {}

    def submit_request(self, request: InfrastructureRequest) -> str:
        """Submit a new infrastructure request."""
        # Validate required fields
        if not request.justification:
            raise ValueError("Business justification is required")

        if request.estimated_monthly_cost > 10000:
            # High-cost requests require additional approval
            request.specifications["requires_finance_approval"] = True

        self.requests[request.id] = request
        self._notify_platform_team(request)
        return request.id

    def approve_request(
        self,
        request_id: str,
        reviewer: str,
        notes: Optional[str] = None
    ) -> InfrastructureRequest:
        """Approve an infrastructure request."""
        request = self.requests.get(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found")

        request.status = RequestStatus.APPROVED
        request.reviewed_by = reviewer
        request.review_notes = notes

        # Generate Crossplane manifests for the request
        self._generate_manifests(request)
        return request

    def reject_request(
        self,
        request_id: str,
        reviewer: str,
        reason: str
    ) -> InfrastructureRequest:
        """Reject an infrastructure request."""
        request = self.requests.get(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found")

        request.status = RequestStatus.REJECTED
        request.reviewed_by = reviewer
        request.review_notes = reason

        self._notify_requester(request, rejected=True)
        return request

    def _generate_manifests(self, request: InfrastructureRequest) -> str:
        """Generate Crossplane manifests for approved request."""
        # This would generate appropriate Crossplane resources
        # based on the request specifications
        manifest = {
            "apiVersion": "infrastructure.platform.io/v1alpha1",
            "kind": "CustomResource",
            "metadata": {
                "name": f"custom-{request.id}",
                "labels": {
                    "platform.io/team": request.team,
                    "platform.io/request-id": request.id,
                    "platform.io/approved-by": request.reviewed_by
                }
            },
            "spec": request.specifications
        }
        return json.dumps(manifest, indent=2)

    def _notify_platform_team(self, request: InfrastructureRequest):
        """Send notification about new request."""
        print(f"New infrastructure request: {request.id}")
        print(f"  Team: {request.team}")
        print(f"  Type: {request.resource_type}")
        print(f"  Cost: ${request.estimated_monthly_cost}/month")

    def _notify_requester(self, request: InfrastructureRequest, rejected: bool = False):
        """Notify requester about request status."""
        status = "rejected" if rejected else "approved"
        print(f"Request {request.id} has been {status}")
        if request.review_notes:
            print(f"  Notes: {request.review_notes}")


# Example usage
if __name__ == "__main__":
    handler = InfrastructureRequestHandler()

    # Submit a request
    request = InfrastructureRequest(
        id="req-001",
        requester="developer@example.com",
        team="team-alpha",
        description="GPU node pool for ML training",
        resource_type="gpu-nodepool",
        specifications={
            "gpu_type": "nvidia-a100",
            "node_count": 2,
            "spot_instances": True
        },
        justification="Required for training ML models for recommendation engine",
        estimated_monthly_cost=2500.00
    )

    handler.submit_request(request)

    # Approve the request
    handler.approve_request("req-001", "platform-admin@example.com", "Approved for Q1 budget")
