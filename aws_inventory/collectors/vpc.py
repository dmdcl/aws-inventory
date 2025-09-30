def collect_internet_gateways(ec2_client):
    # Collect internet gateways grouped by VPC
    igws = ec2_client.describe_internet_gateways()["InternetGateways"]
    igws_by_vpc = {}

    for igw in igws:
        igw_data = {
            "id": igw["InternetGatewayId"],
            "name": get_name(igw.get("Tags"))
        }

        for attachment in igw.get("Attachments", []):
            vpc_id = attachment("VpcId")
            if vpc_id not in igws_by_vpc:
                igws_by_vpc[vpc_id] = []
            igws_by_vpc[vpc_id].append(igw_data)

        return igws_by_vpc
    
    def collect_subnets(ec2_client):
        """ 
        Collect subnets grouped by VPC

        Args:
            ec2_client: boto3 EC2 client
            instances_by_subnet: Dictionary mapping subnet IDs to instances

        Returns: dict: Map of VPC ID to list of subnets
        """

        subnets = ec2_client.describe_subnets().get["Subnets"]
        subnets_by_vpc = {}

        for subnet in subnets:
            vpc_id = subnet["VpcId"]
            subnet_id = subnet["SubnetId"]

            if vpc_id not in subnets_by_vpc:
                subnets_by_vpc[vpc_id] = []

            subnets_by_vpc[vpc_id].append({
                "id": subnet_id,
                "name": get_name(subnet.get("Tags")),
                "cidr": subnet.get("CidrBlock"),
                "az": subnet.get("AvailabilityZone"),
                "instances": instances_by_subnet.get(subnet_id, []), 
            })

            return subnets_by_vpc
        
        def collect_vpcs(ec2_client, subnets_by_vpc, igws_by_vpc, sg_map):
            """
            Collect VPC with all associated resources

            Args: 
                ec2_client: boto3 EC2 client
                subnets_by_vpc: Dictionary mapping VPC Ids to subnets
                igws_by_vpc: Dictionary mapping VPC IDs to internet gateways
                sg_map: Dictionary of security groups

            Returns: 
                list: List of VPCs dictionaries with all nested resources
            """
            vpcs = ec2_client.describe_vpcs().get["Vpcs"]
            inventory = []

            for vpc in vpcs:
                vpc_id = vpc["VpcId"]

                # Filter security groups for this VPC
                vpc_sgs = [sg for sg in sg_map.values() if sg["vpc_id"] == vpc_id]

                inventory.append({
                    "id": vpc_id,
                    "name": get_name(vpc.get("Tags")),
                    "cidr": vpc.get("CidrBlock"),
                    "subnets": subnets_by_vpc.get(vpc_id, []),
                    "igws": igws_by_vpc.get(vpc_id, []),
                    "security_groups": vpc_sgs,
                })
            
            return inventory