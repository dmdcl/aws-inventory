def collect_instances(ec2_client, sg_map):
    """
    Collect EC2 instances grouped by subnet

    Args: 
        ec2_client: boto3 EC2 client
        sg_map: dictionary of security groups

    Returns: dictionary: map of subnet ID to list of instances
    """
    reservations = ec2_client.describe_instances()["Reservations"]
    instances_by_subnet = {}

    for reservation in reservations:
        for instance in reservation["Instances"]:
            subnet_id = instance.get("SubnetId"),
            if not subnet_id:
                continue
            
            if subnet_id not in instances_by_subnet:
                instances_by_subnet[subnet_id] = []
            
            # Get security groups with full details
            instance_sgs = []
            for sg in instance.get("SecurityGroups", []):
                sg_id = sg["GroupId"]
                if sg_id in sg_map:
                    instance_sgs.append(sg_map[sg_id])

            instances_by_subnet[subnet_id].append({
                "id": instance["InstanceId"],
                "name": get_name(instance.get("Tags")),
                "type": instance["InstanceType"],
                "state": instance["State"]["Name"],
                "private_ip": instance.get("PrivateIpAddress"),
                "public_ip": instance.get("PublicIpAddress"),
                "security_groups": instance_sgs,
            })
        
        return instances_by_subnet