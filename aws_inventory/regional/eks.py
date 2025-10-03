# EKS inventory collector - orchestrates all EKS resource collection
import aws_inventory.collectors.clusters as clusters

print("File used:", clusters.collect_clusters.__code__.co_filename)
print("Arg count:", clusters.collect_clusters.__code__.co_argcount)
print("Arg names:", clusters.collect_clusters.__code__.co_varnames)

from aws_inventory.utils.boto_helpers import create_session
from aws_inventory.collectors.clusters import collect_clusters


def collect_eks(profile, region):
    """
    Collect EKS inventory for a given region

    This function orchestrates the collection of all EKS resources:
    - EKS Clusters
    - Node Groups
    - Fargate Profiles
    - Addons
    - OIDC Providers
    - IAM Roles for Service Accounts (IRSA)

    Args:
        profile: AWS profile name
        region: AWS region name

    Returns: 
        list: List of EKS cluster dictionaries with all nested resources
    """
    session = create_session(profile)
    eks = session.client("eks", region_name=region)
    ec2 = session.client("ec2", region_name=region)
    iam = session.client("iam", region_name=region)

    inventory = collect_clusters(eks, ec2, iam)

    return inventory