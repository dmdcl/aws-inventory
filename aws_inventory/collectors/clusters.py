# EKS Clusters collector module
from aws_inventory.utils.common import get_name


def collect_node_groups(eks_client, cluster_name):
    """
    Collect node groups for a specific cluster.
    
    Args:
        eks_client: Boto3 EKS client
        cluster_name: Name of the EKS cluster
        
    Returns:
        list: List of node group dictionaries
    """
    try:
        nodegroup_names = eks_client.list_nodegroups(clusterName=cluster_name).get("nodegroups", [])
        node_groups = []
        
        for ng_name in nodegroup_names:
            ng_details = eks_client.describe_nodegroup(
                clusterName=cluster_name,
                nodegroupName=ng_name
            )["nodegroup"]
            
            node_groups.append({
                "name": ng_name,
                "status": ng_details.get("status"),
                "instance_types": ng_details.get("instanceTypes", []),
                "desired_size": ng_details.get("scalingConfig", {}).get("desiredSize", 0),
                "min_size": ng_details.get("scalingConfig", {}).get("minSize", 0),
                "max_size": ng_details.get("scalingConfig", {}).get("maxSize", 0),
                "ami_type": ng_details.get("amiType"),
                "capacity_type": ng_details.get("capacityType"),
                "disk_size": ng_details.get("diskSize"),
                "subnets": ng_details.get("subnets", []),
                "version": ng_details.get("version"),
            })
        
        return node_groups
    except Exception as e:
        print(f"Error collecting node groups for {cluster_name}: {e}")
        return []


def collect_fargate_profiles(eks_client, cluster_name):
    """
    Collect Fargate profiles for a specific cluster.
    
    Args:
        eks_client: Boto3 EKS client
        cluster_name: Name of the EKS cluster
        
    Returns:
        list: List of Fargate profile dictionaries
    """
    try:
        profile_names = eks_client.list_fargate_profiles(clusterName=cluster_name).get("fargateProfileNames", [])
        fargate_profiles = []
        
        for profile_name in profile_names:
            profile_details = eks_client.describe_fargate_profile(
                clusterName=cluster_name,
                fargateProfileName=profile_name
            )["fargateProfile"]
            
            fargate_profiles.append({
                "name": profile_name,
                "status": profile_details.get("status"),
                "subnets": profile_details.get("subnets", []),
                "selectors": profile_details.get("selectors", []),
            })
        
        return fargate_profiles
    except Exception as e:
        print(f"Error collecting Fargate profiles for {cluster_name}: {e}")
        return []


def collect_addons(eks_client, cluster_name):
    """
    Collect addons for a specific cluster.
    
    Args:
        eks_client: Boto3 EKS client
        cluster_name: Name of the EKS cluster
        
    Returns:
        list: List of addon dictionaries
    """
    try:
        addon_names = eks_client.list_addons(clusterName=cluster_name).get("addons", [])
        addons = []
        
        for addon_name in addon_names:
            addon_details = eks_client.describe_addon(
                clusterName=cluster_name,
                addonName=addon_name
            )["addon"]
            
            addons.append({
                "name": addon_name,
                "version": addon_details.get("addonVersion"),
                "status": addon_details.get("status"),
                "health": addon_details.get("health", {}),
            })
        
        return addons
    except Exception as e:
        print(f"Error collecting addons for {cluster_name}: {e}")
        return []


def collect_clusters(eks_client, ec2_client):
    """
    Collect all EKS clusters with their associated resources.
    
    Args:
        eks_client: Boto3 EKS client
        ec2_client: Boto3 EC2 client
        
    Returns:
        list: List of EKS cluster dictionaries with all nested resources
    """
    try:
        cluster_names = eks_client.list_clusters().get("clusters", [])
        inventory = []
        
        for cluster_name in cluster_names:
            cluster_details = eks_client.describe_cluster(name=cluster_name)["cluster"]
            
            # Collect associated resources
            node_groups = collect_node_groups(eks_client, cluster_name)
            fargate_profiles = collect_fargate_profiles(eks_client, cluster_name)
            addons = collect_addons(eks_client, cluster_name)
            
            # Calculate total node count
            total_nodes = sum(ng.get("desired_size", 0) for ng in node_groups)
            
            inventory.append({
                "name": cluster_name,
                "arn": cluster_details.get("arn"),
                "version": cluster_details.get("version"),
                "status": cluster_details.get("status"),
                "endpoint": cluster_details.get("endpoint"),
                "platform_version": cluster_details.get("platformVersion"),
                "role_arn": cluster_details.get("roleArn"),
                "vpc_id": cluster_details.get("resourcesVpcConfig", {}).get("vpcId"),
                "subnet_ids": cluster_details.get("resourcesVpcConfig", {}).get("subnetIds", []),
                "security_group_ids": cluster_details.get("resourcesVpcConfig", {}).get("securityGroupIds", []),
                "cluster_security_group_id": cluster_details.get("resourcesVpcConfig", {}).get("clusterSecurityGroupId"),
                "public_access": cluster_details.get("resourcesVpcConfig", {}).get("endpointPublicAccess"),
                "private_access": cluster_details.get("resourcesVpcConfig", {}).get("endpointPrivateAccess"),
                "created_at": cluster_details.get("createdAt").isoformat() if cluster_details.get("createdAt") else None,
                "tags": cluster_details.get("tags", {}),
                "node_groups": node_groups,
                "fargate_profiles": fargate_profiles,
                "addons": addons,
                "total_nodes": total_nodes,
            })
        
        return inventory
    except Exception as e:
        print(f"Error collecting EKS clusters: {e}")
        return []