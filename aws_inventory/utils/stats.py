"""Statistics calculation utilities."""


def calculate_ec2_stats(regions_data):
    """
    Calculate statistics for EC2 resources across all regions.
    
    Args:
        regions_data: Dictionary of {region: [vpcs]} data
        
    Returns:
        dict: Statistics including totals and breakdowns
    """
    stats = {
        "total_vpcs": 0,
        "total_subnets": 0,
        "total_instances": 0,
        "total_security_groups": 0,
        "instances_by_state": {},
        "regions_with_resources": 0
    }
    
    for region, vpcs in regions_data.items():
        if vpcs:
            stats["regions_with_resources"] += 1
            
        for vpc in vpcs:
            stats["total_vpcs"] += 1
            stats["total_subnets"] += len(vpc.get("subnets", []))
            stats["total_security_groups"] += len(vpc.get("security_groups", []))
            
            for subnet in vpc.get("subnets", []):
                for instance in subnet.get("instances", []):
                    stats["total_instances"] += 1
                    state = instance.get("state", "unknown")
                    stats["instances_by_state"][state] = stats["instances_by_state"].get(state, 0) + 1
    
    return stats


def calculate_vpc_stats(vpc):
    """
    Calculate statistics for a single VPC.
    
    Args:
        vpc: VPC dictionary
        
    Returns:
        dict: VPC-level statistics
    """
    instance_count = sum(
        len(subnet.get("instances", [])) 
        for subnet in vpc.get("subnets", [])
    )
    
    return {
        "subnet_count": len(vpc.get("subnets", [])),
        "sg_count": len(vpc.get("security_groups", [])),
        "instance_count": instance_count
    }


def calculate_region_stats(vpcs):
    """
    Calculate statistics for a single region (EC2).
    
    Args:
        vpcs: List of VPC dictionaries
        
    Returns:
        dict: Region-level statistics
    """
    vpc_count = len(vpcs)
    instance_count = sum(
        len(subnet.get("instances", []))
        for vpc in vpcs
        for subnet in vpc.get("subnets", [])
    )
    
    return {
        "vpc_count": vpc_count,
        "instance_count": instance_count
    }


def calculate_eks_stats(regions_data):
    """
    Calculate statistics for EKS resources across all regions.
    
    Args:
        regions_data: Dictionary of {region: [clusters]} data
        
    Returns:
        dict: Statistics including totals and breakdowns
    """
    stats = {
        "total_clusters": 0,
        "total_node_groups": 0,
        "total_nodes": 0,
        "total_fargate_profiles": 0,
        "total_service_account_roles": 0,
        "clusters_by_status": {},
        "regions_with_resources": 0
    }
    
    for region, clusters in regions_data.items():
        if clusters:
            stats["regions_with_resources"] += 1
            
        for cluster in clusters:
            stats["total_clusters"] += 1
            stats["total_node_groups"] += len(cluster.get("node_groups", []))
            stats["total_nodes"] += cluster.get("total_nodes", 0)
            stats["total_fargate_profiles"] += len(cluster.get("fargate_profiles", []))
            stats["total_service_account_roles"] += len(cluster.get("service_account_roles", []))
            
            status = cluster.get("status", "unknown")
            stats["clusters_by_status"][status] = stats["clusters_by_status"].get(status, 0) + 1
    
    return stats


def calculate_region_stats_eks(clusters):
    """
    Calculate statistics for a single region (EKS).
    
    Args:
        clusters: List of EKS cluster dictionaries
        
    Returns:
        dict: Region-level statistics
    """
    cluster_count = len(clusters)
    total_nodes = sum(cluster.get("total_nodes", 0) for cluster in clusters)
    
    return {
        "cluster_count": cluster_count,
        "total_nodes": total_nodes
    }