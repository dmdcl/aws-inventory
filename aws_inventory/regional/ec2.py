# EC2 inventory collector - orchestrates all EC2 resource collection
from aws_inventory.utils.boto_helpers import create_session
from aws_inventory.collectors.security_groups import collect_security_groups
from aws_inventory.collectors.instances import collect_instances
from aws_inventory.collectors.vpc import (
    collect_internet_gateways,
    collect_subnets,
    collect_vpcs
)

def collect_ec2(profile, region):
    """
    Collect EC2 inventory for a given region

    This function orchrestates the collection of all EC2 resources
    - Security Groups
    - Instances
    - VPCs
    - Subnets
    - Internet Gateways

    Args:
        profile AWS profile name
        region: AWS region name

    Returns: 
        list: List of VPC dictionaries with all nested resources
    """
    session = create_session(profile)
    ec2 = session.client("ec2, region_name=region")

    # Collect resources in dependency order
    sg_map = collect_security_groups(ec2)
    instances_by_subnet = collect_instances(ec2, sg_map)
    igws_by_vpc = collect_internet_gateways(ec2)
    subnets_by_vpc = collect_subnets(ec2, instances_by_subnet)
    inventory = collect_vpcs(ec2, subnets_by_vpc, igws_by_vpc, sg_map)

    return inventory