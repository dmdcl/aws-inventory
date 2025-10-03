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


def collect_oidc_provider(cluster_details, iam_client):
    """
    Collect OIDC provider information for the cluster.
    
    Args:
        cluster_details: Cluster details from describe_cluster
        iam_client: Boto3 IAM client
        
    Returns:
        dict: OIDC provider information
    """
    try:
        oidc_issuer = cluster_details.get("identity", {}).get("oidc", {}).get("issuer")
        
        if not oidc_issuer:
            return None
        
        # Extract the OIDC provider ID from the issuer URL
        # Format: https://oidc.eks.region.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE
        oidc_id = oidc_issuer.split("/")[-1] if "/" in oidc_issuer else None
        
        # Try to find the provider in IAM
        oidc_provider_arn = None
        try:
            providers = iam_client.list_open_id_connect_providers().get("OpenIDConnectProviderList", [])
            for provider in providers:
                if oidc_id and oidc_id in provider["Arn"]:
                    oidc_provider_arn = provider["Arn"]
                    break
        except Exception:
            pass
        
        return {
            "issuer": oidc_issuer,
            "id": oidc_id,
            "arn": oidc_provider_arn,
            "exists": oidc_provider_arn is not None
        }
    except Exception as e:
        print(f"Error collecting OIDC provider: {e}")
        return None


def collect_service_account_roles(cluster_name, cluster_oidc, iam_client):
    """
    Collect IAM roles configured for service accounts (IRSA).
    
    Args:
        cluster_name: Name of the EKS cluster
        cluster_oidc: OIDC provider information
        iam_client: Boto3 IAM client
        
    Returns:
        list: List of IAM roles configured for service accounts
    """
    try:
        if not cluster_oidc or not cluster_oidc.get("id"):
            return []
        
        oidc_id = cluster_oidc["id"]
        service_account_roles = []
        
        # List all roles and filter those with trust relationships to this cluster's OIDC
        paginator = iam_client.get_paginator('list_roles')
        
        for page in paginator.paginate():
            for role in page.get("Roles", []):
                role_name = role["RoleName"]
                
                # Get the trust policy
                try:
                    assume_role_doc = role.get("AssumeRolePolicyDocument", {})
                    
                    # Check if this role trusts our OIDC provider
                    for statement in assume_role_doc.get("Statement", []):
                        principal = statement.get("Principal", {})
                        federated = principal.get("Federated", "")
                        
                        if oidc_id in federated:
                            # Extract service account from condition
                            condition = statement.get("Condition", {})
                            string_equals = condition.get("StringEquals", {})
                            
                            # Try different possible condition keys
                            sa_key = f"{cluster_oidc['issuer'].replace('https://', '')}:sub"
                            service_account = string_equals.get(sa_key, "")
                            
                            if not service_account:
                                # Try alternative format
                                for key, value in string_equals.items():
                                    if ":sub" in key and oidc_id in key:
                                        service_account = value
                                        break
                            
                            # Extract namespace and SA name from "system:serviceaccount:namespace:sa-name"
                            namespace = ""
                            sa_name = ""
                            if service_account and "system:serviceaccount:" in service_account:
                                parts = service_account.replace("system:serviceaccount:", "").split(":")
                                if len(parts) >= 2:
                                    namespace = parts[0]
                                    sa_name = parts[1]
                            
                            service_account_roles.append({
                                "role_name": role_name,
                                "role_arn": role["Arn"],
                                "namespace": namespace,
                                "service_account": sa_name,
                                "full_service_account": service_account,
                                "created_date": role.get("CreateDate").isoformat() if role.get("CreateDate") else None,
                            })
                            break
                
                except Exception as e:
                    continue
        
        return service_account_roles
    
    except Exception as e:
        print(f"Error collecting service account roles for {cluster_name}: {e}")
        return []


def collect_clusters(eks_client, ec2_client, iam_client):
    """
    Collect all EKS clusters with their associated resources.
    
    Args:
        eks_client: Boto3 EKS client
        ec2_client: Boto3 EC2 client
        iam_client: Boto3 IAM client
        
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
            
            # Collect OIDC and IAM roles for service accounts
            oidc_provider = collect_oidc_provider(cluster_details, iam_client)
            service_account_roles = collect_service_account_roles(cluster_name, oidc_provider, iam_client)
            
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
                "oidc_provider": oidc_provider,
                "service_account_roles": service_account_roles,
                "total_nodes": total_nodes,
            })
        
        return inventory
    except Exception as e:
        print(f"Error collecting EKS clusters: {e}")
        return []