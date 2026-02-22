#!/usr/bin/env python3
"""
Kubernetes Namespace Provisioner

This script automates the provisioning of namespaces with standard configurations:
- Labels for environment and team identification
- Resource quotas for preventing resource exhaustion
- Network policies implementing zero-trust ingress patterns
- RBAC service accounts with appropriate roles

Usage:
    python3 namespace-provisioner.py --namespace platform-apps --env prod --team infra
    python3 namespace-provisioner.py --namespace platform-core --env staging

Prerequisites:
    - kubectl configured and authenticated to target cluster
    - kubeconfig pointing to target cluster
    - RBAC permissions to create namespaces, resource quotas, network policies

Environment Variables:
    KUBECONFIG - Path to kubeconfig file (uses default if not set)
"""

import subprocess
import sys
import json
import argparse
from typing import Dict, Any, Optional


def run_kubectl_command(command: list, check: bool = True) -> subprocess.CompletedProcess:
    """
    Execute kubectl command.
    
    Args:
        command: List of command arguments (e.g., ['get', 'nodes', '-o', 'json'])
        check: Raise exception if command fails
    
    Returns:
        CompletedProcess with stdout, stderr, returncode
    
    Raises:
        subprocess.CalledProcessError if command fails and check=True
    """
    cmd = ['kubectl'] + command
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error executing kubectl: {e.stderr}", file=sys.stderr)
        raise


def create_namespace(namespace: str) -> bool:
    """
    Create Kubernetes namespace if it doesn't exist.
    
    Args:
        namespace: Namespace name
    
    Returns:
        True if created or already exists, False on error
    """
    result = run_kubectl_command(['get', 'ns', namespace], check=False)
    
    if result.returncode == 0:
        print(f"Namespace '{namespace}' already exists")
        return True
    
    print(f"Creating namespace '{namespace}'...")
    result = run_kubectl_command(['create', 'namespace', namespace])
    return result.returncode == 0


def apply_labels(namespace: str, labels: Dict[str, str]) -> bool:
    """
    Apply labels to namespace.
    
    Args:
        namespace: Namespace name
        labels: Dictionary of label key-value pairs
    
    Returns:
        True if labels applied successfully
    """
    label_args = [f"{k}={v}" for k, v in labels.items()]
    cmd = ['label', 'ns', namespace] + label_args + ['--overwrite']
    
    print(f"Applying labels to namespace '{namespace}': {labels}")
    result = run_kubectl_command(cmd)
    return result.returncode == 0


def create_resource_quota(namespace: str, cpu: str, memory: str, pods: int) -> bool:
    """
    Create ResourceQuota for namespace.
    
    Args:
        namespace: Namespace name
        cpu: CPU limit (e.g., '10')
        memory: Memory limit (e.g., '20Gi')
        pods: Maximum pod count
    
    Returns:
        True if quota created successfully
    """
    quota_manifest = f"""
apiVersion: v1
kind: ResourceQuota
metadata:
  name: {namespace}-quota
  namespace: {namespace}
spec:
  hard:
    requests.cpu: "{cpu}"
    requests.memory: "{memory}"
    limits.cpu: "{cpu * 2}"
    limits.memory: "{memory}"
    pods: "{pods}"
    persistentvolumeclaims: "5"
  scopeSelector:
    matchExpressions:
      - operator: NotIn
        scopeName: PriorityClass
        values: ["system-critical"]
"""
    
    print(f"Creating ResourceQuota for namespace '{namespace}'...")
    result = subprocess.run(
        ['kubectl', 'apply', '-f', '-'],
        input=quota_manifest,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"ResourceQuota created for namespace '{namespace}'")
    else:
        print(f"Error creating ResourceQuota: {result.stderr}", file=sys.stderr)
    
    return result.returncode == 0


def create_network_policy(namespace: str, env: str) -> bool:
    """
    Create NetworkPolicy implementing zero-trust ingress.
    
    Args:
        namespace: Namespace name
        env: Environment (prod, staging, dev)
    
    Returns:
        True if policy created successfully
    """
    # Default deny all ingress
    network_policy = f"""
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: {namespace}
spec:
  podSelector: {{}}
  policyTypes:
    - Ingress

---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-same-namespace
  namespace: {namespace}
spec:
  podSelector: {{}}
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector: {{}}

---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-monitoring
  namespace: {namespace}
spec:
  podSelector: {{}}
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: platform-monitoring
      ports:
        - protocol: TCP
          port: 8080  # Prometheus metrics port
"""
    
    # In production, additionally deny egress to internet
    if env == "prod":
        network_policy += f"""
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
  namespace: {namespace}
spec:
  podSelector: {{}}
  policyTypes:
    - Egress
  egress:
    # Allow DNS
    - to:
        - namespaceSelector:
            matchLabels:
              name: kube-system
      ports:
        - protocol: UDP
          port: 53
    # Allow to Kubernetes API
    - to:
        - namespaceSelector: {{}}
          podSelector:
            matchLabels:
              component: kube-apiserver

---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-external-https
  namespace: {namespace}
spec:
  podSelector: {{}}
  policyTypes:
    - Egress
  egress:
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
      ports:
        - protocol: TCP
          port: 443
"""
    
    print(f"Creating NetworkPolicy for namespace '{namespace}'...")
    result = subprocess.run(
        ['kubectl', 'apply', '-f', '-'],
        input=network_policy,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"NetworkPolicy created for namespace '{namespace}'")
    else:
        print(f"Error creating NetworkPolicy: {result.stderr}", file=sys.stderr)
    
    return result.returncode == 0


def create_service_accounts(namespace: str) -> bool:
    """
    Create standard service accounts.
    
    Args:
        namespace: Namespace name
    
    Returns:
        True if service accounts created successfully
    """
    service_accounts = f"""
apiVersion: v1
kind: ServiceAccount
metadata:
  name: default-app
  namespace: {namespace}

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cicd-deployer
  namespace: {namespace}

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-reader
  namespace: {namespace}
rules:
  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-reader-binding
  namespace: {namespace}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: app-reader
subjects:
  - kind: ServiceAccount
    name: default-app
    namespace: {namespace}
"""
    
    print(f"Creating service accounts for namespace '{namespace}'...")
    result = subprocess.run(
        ['kubectl', 'apply', '-f', '-'],
        input=service_accounts,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"Service accounts created for namespace '{namespace}'")
    else:
        print(f"Error creating service accounts: {result.stderr}", file=sys.stderr)
    
    return result.returncode == 0


def provision_namespace(
    namespace: str,
    env: str = "staging",
    team: str = "platform",
    cpu: str = "10",
    memory: str = "20Gi",
    pods: int = 100
) -> bool:
    """
    Complete namespace provisioning workflow.
    
    Args:
        namespace: Namespace name
        env: Environment (prod, staging, dev)
        team: Team name for labels
        cpu: CPU quota
        memory: Memory quota
        pods: Pod count quota
    
    Returns:
        True if all provisioning steps succeeded
    """
    print(f"\n--- Provisioning namespace: {namespace} ---")
    
    steps = [
        ("Create namespace", lambda: create_namespace(namespace)),
        ("Apply labels", lambda: apply_labels(namespace, {
            "environment": env,
            "team": team,
            "managed-by": "platform-provisioner"
        })),
        ("Create resource quota", lambda: create_resource_quota(namespace, cpu, memory, pods)),
        ("Create network policies", lambda: create_network_policy(namespace, env)),
        ("Create service accounts", lambda: create_service_accounts(namespace))
    ]
    
    failed_steps = []
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"Error during '{step_name}': {e}", file=sys.stderr)
            failed_steps.append(step_name)
    
    if failed_steps:
        print(f"\nFailed steps: {', '.join(failed_steps)}", file=sys.stderr)
        return False
    
    print(f"\nNamespace '{namespace}' provisioned successfully!")
    return True


def main():
    """Parse arguments and run provisioning."""
    parser = argparse.ArgumentParser(
        description="Provision Kubernetes namespace with standard configurations"
    )
    parser.add_argument(
        "--namespace",
        required=True,
        help="Namespace name to provision"
    )
    parser.add_argument(
        "--env",
        choices=["prod", "staging", "dev"],
        default="staging",
        help="Environment (default: staging)"
    )
    parser.add_argument(
        "--team",
        default="platform",
        help="Team name for labels (default: platform)"
    )
    parser.add_argument(
        "--cpu",
        default="10",
        help="CPU quota (default: 10)"
    )
    parser.add_argument(
        "--memory",
        default="20Gi",
        help="Memory quota (default: 20Gi)"
    )
    parser.add_argument(
        "--pods",
        type=int,
        default=100,
        help="Pod count quota (default: 100)"
    )
    
    args = parser.parse_args()
    
    success = provision_namespace(
        namespace=args.namespace,
        env=args.env,
        team=args.team,
        cpu=args.cpu,
        memory=args.memory,
        pods=args.pods
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
