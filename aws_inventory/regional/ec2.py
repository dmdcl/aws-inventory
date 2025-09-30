from aws_inventory.utils.boto_helpers import create_session
from aws_inventory.utils.common import get_name


def collect_ec2(profile, region):
    """
    Collect EC2 inventory for a given region.
    Returns structured data (dict/list) instead of HTML.
    """
    session = create_session(profile)
    ec2 = session.client("ec2", region_name=region)

    vpcs = ec2.describe_vpcs()["Vpcs"]
    subnets = ec2.describe_subnets()["Subnets"]
    instances = ec2.describe_instances()["Reservations"]
    igws = ec2.describe_internet_gateways()["InternetGateways"]

    inventory = []

    for vpc in vpcs:
        vpc_id = vpc["VpcId"]
        vpc_entry = {
            "id": vpc_id,
            "name": get_name(vpc.get("Tags")),
            "cidr": vpc.get("CidrBlock"),
            "subnets": [],
            "igws": [
                {
                    "id": igw["InternetGatewayId"], 
                    "name": get_name(igw.get("Tags"))
                }
                for igw in igws
                if any(att["VpcId"] == vpc_id for att in igw["Attachments"])
            ],
        }

        for subnet in [s for s in subnets if s["VpcId"] == vpc_id]:
            subnet_entry = {
                "id": subnet["SubnetId"],
                "name": get_name(subnet.get("Tags")),
                "cidr": subnet.get("CidrBlock"),
                "az": subnet.get("AvailabilityZone"),
                "instances": [],
            }

            for r in instances:
                for i in r["Instances"]:
                    if i["SubnetId"] == subnet["SubnetId"]:
                        subnet_entry["instances"].append(
                            {
                                "id": i["InstanceId"],
                                "name": get_name(i.get("Tags")),
                                "type": i["InstanceType"],
                                "state": i["State"]["Name"],
                                "private_ip": i.get("PrivateIpAddress"),
                                "public_ip": i.get("PublicIpAddress"),
                                "sgs": [sg["GroupId"] for sg in i["SecurityGroups"]],
                            }
                        )

            vpc_entry["subnets"].append(subnet_entry)

        inventory.append(vpc_entry)

    return inventory