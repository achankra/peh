"""
Chapter 2: Scalable Platform Runtime - Pulumi EKS Cluster
==========================================================
Deploys an AWS EKS cluster with VPC, managed node groups, and add-ons.
This is the Pulumi equivalent of a production-ready Kubernetes setup.

Usage:
    pulumi stack init dev
    pulumi up

Prerequisites:
    - AWS credentials configured (aws configure)
    - Pulumi CLI installed (curl -fsSL https://get.pulumi.com | sh)
    - Python 3.10+
"""

import pulumi
import pulumi_aws as aws
import pulumi_eks as eks

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
config = pulumi.Config()
cluster_config = pulumi.Config("cluster")

cluster_name = cluster_config.get("name") or "platform-cluster"
kubernetes_version = cluster_config.get("kubernetesVersion") or "1.28"
num_worker_nodes = cluster_config.get_int("numWorkerNodes") or 3
environment = cluster_config.get("environment") or "dev"

aws_config = pulumi.Config("aws")
region = aws_config.get("region") or "us-east-1"

# ---------------------------------------------------------------------------
# VPC
# ---------------------------------------------------------------------------
vpc = aws.ec2.Vpc(
    f"{cluster_name}-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": f"{cluster_name}-vpc",
        "Environment": environment,
        "ManagedBy": "Pulumi",
    },
)

igw = aws.ec2.InternetGateway(
    f"{cluster_name}-igw",
    vpc_id=vpc.id,
    tags={"Name": f"{cluster_name}-igw"},
)

# Availability zones
azs = aws.get_availability_zones(state="available")

# Public subnets
public_subnets = []
for i in range(2):
    subnet = aws.ec2.Subnet(
        f"{cluster_name}-public-{i+1}",
        vpc_id=vpc.id,
        cidr_block=f"10.0.{i+1}.0/24",
        availability_zone=azs.names[i],
        map_public_ip_on_launch=True,
        tags={
            "Name": f"{cluster_name}-public-{i+1}",
            "kubernetes.io/role/elb": "1",
            f"kubernetes.io/cluster/{cluster_name}": "shared",
        },
    )
    public_subnets.append(subnet)

# Private subnets
private_subnets = []
for i in range(2):
    subnet = aws.ec2.Subnet(
        f"{cluster_name}-private-{i+1}",
        vpc_id=vpc.id,
        cidr_block=f"10.0.{i+10}.0/24",
        availability_zone=azs.names[i],
        tags={
            "Name": f"{cluster_name}-private-{i+1}",
            "kubernetes.io/role/internal-elb": "1",
            f"kubernetes.io/cluster/{cluster_name}": "shared",
        },
    )
    private_subnets.append(subnet)

# Public route table
public_rt = aws.ec2.RouteTable(
    f"{cluster_name}-public-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        )
    ],
    tags={"Name": f"{cluster_name}-public-rt"},
)

for i, subnet in enumerate(public_subnets):
    aws.ec2.RouteTableAssociation(
        f"{cluster_name}-public-rta-{i+1}",
        subnet_id=subnet.id,
        route_table_id=public_rt.id,
    )

# ---------------------------------------------------------------------------
# EKS Cluster
# ---------------------------------------------------------------------------
# IAM role for the EKS cluster control plane
cluster_role = aws.iam.Role(
    f"{cluster_name}-cluster-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {"Service": "eks.amazonaws.com"}
        }]
    }""",
)

aws.iam.RolePolicyAttachment(
    f"{cluster_name}-cluster-policy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
    role=cluster_role.name,
)

# IAM role for worker nodes
worker_role = aws.iam.Role(
    f"{cluster_name}-worker-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"}
        }]
    }""",
)

for policy_name, policy_arn in [
    ("worker-node", "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"),
    ("worker-cni", "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"),
    ("worker-registry", "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"),
]:
    aws.iam.RolePolicyAttachment(
        f"{cluster_name}-{policy_name}",
        policy_arn=policy_arn,
        role=worker_role.name,
    )

# EKS cluster
eks_cluster = aws.eks.Cluster(
    f"{cluster_name}",
    name=cluster_name,
    role_arn=cluster_role.arn,
    version=kubernetes_version,
    vpc_config=aws.eks.ClusterVpcConfigArgs(
        subnet_ids=[s.id for s in public_subnets + private_subnets],
        endpoint_private_access=True,
        endpoint_public_access=True,
    ),
    enabled_cluster_log_types=[
        "api", "audit", "authenticator", "controllerManager", "scheduler"
    ],
    tags={
        "Environment": environment,
        "ManagedBy": "Pulumi",
    },
)

# Launch template for worker nodes
launch_template = aws.ec2.LaunchTemplate(
    f"{cluster_name}-worker-lt",
    name_prefix=f"{cluster_name}-worker-",
    description="Launch template for EKS worker nodes",
    block_device_mappings=[
        aws.ec2.LaunchTemplateBlockDeviceMappingArgs(
            device_name="/dev/xvda",
            ebs=aws.ec2.LaunchTemplateBlockDeviceMappingEbsArgs(
                volume_size=100,
                volume_type="gp3",
                delete_on_termination="true",
            ),
        )
    ],
    tag_specifications=[
        aws.ec2.LaunchTemplateTagSpecificationArgs(
            resource_type="instance",
            tags={"Name": f"{cluster_name}-worker"},
        )
    ],
)

# Managed node group
node_group = aws.eks.NodeGroup(
    f"{cluster_name}-nodegroup",
    cluster_name=eks_cluster.name,
    node_group_name=f"{cluster_name}-nodegroup",
    node_role_arn=worker_role.arn,
    subnet_ids=[s.id for s in public_subnets],
    version=kubernetes_version,
    scaling_config=aws.eks.NodeGroupScalingConfigArgs(
        desired_size=num_worker_nodes,
        max_size=10,
        min_size=1,
    ),
    instance_types=["t3.medium"],
    launch_template=aws.eks.NodeGroupLaunchTemplateArgs(
        id=launch_template.id,
        version=launch_template.latest_version,
    ),
    tags={
        "Environment": environment,
        "ManagedBy": "Pulumi",
    },
)

# EKS Add-ons: CoreDNS, kube-proxy
aws.eks.Addon(
    f"{cluster_name}-coredns",
    cluster_name=eks_cluster.name,
    addon_name="coredns",
    addon_version="v1.10.1-eksbuild.2",
    resolve_conflicts_on_create="OVERWRITE",
    tags={"Environment": environment},
    opts=pulumi.ResourceOptions(depends_on=[node_group]),
)

aws.eks.Addon(
    f"{cluster_name}-kube-proxy",
    cluster_name=eks_cluster.name,
    addon_name="kube-proxy",
    addon_version="v1.28.1-eksbuild.1",
    resolve_conflicts_on_create="OVERWRITE",
    tags={"Environment": environment},
    opts=pulumi.ResourceOptions(depends_on=[node_group]),
)

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
pulumi.export("cluster_name", eks_cluster.name)
pulumi.export("cluster_endpoint", eks_cluster.endpoint)
pulumi.export("cluster_arn", eks_cluster.arn)
pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnet_ids", [s.id for s in public_subnets])
pulumi.export("private_subnet_ids", [s.id for s in private_subnets])
pulumi.export("node_group_id", node_group.id)
pulumi.export("kubernetes_version", kubernetes_version)
pulumi.export("worker_nodes", num_worker_nodes)
pulumi.export(
    "configure_kubectl",
    pulumi.Output.concat(
        "aws eks update-kubeconfig --region ", region, " --name ", eks_cluster.name
    ),
)
pulumi.export(
    "kubeconfig_certificate_authority_data",
    eks_cluster.certificate_authorities[0].data,
)
