# Statistics calculation utilieties.

def calculate_ec2_stats(regions_data):
    """
    Calculate statistics for EC2 resources across regions

    Args: 
        regions_data: Dictionary of {region: [vpcs]} data

    Returns: 
        dict: Statistics including totals and breakdowns
    """
    stats = {
        "total_vpcs": 0,
        "total_subnets":0,
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
    
    def calculate_vpc_stats(vpcs):
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
        Calculate statistics for a region.
        
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