from aws_inventory.utils.boto_helpers import create_session
from aws_inventory.utils.html_report import save_output
from aws_inventory.utils.common import get_name


def collect_ec2(profile, region):
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
                {"id": igw["InternetGatewayId"], "name": get_name(igw.get("Tags"))}
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

    # Render EC2 tab HTML
    html = "<div class='accordion' id='vpcAccordion'>"
    for idx, vpc in enumerate(inventory, 1):
        html += f"""
        <div class="accordion-item">
          <h2 class="accordion-header" id="heading{idx}">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse{idx}">
              VPC {vpc['id']} ({vpc['cidr']}){' - '+vpc['name'] if vpc['name'] else ''}
            </button>
          </h2>
          <div id="collapse{idx}" class="accordion-collapse collapse">
            <div class="accordion-body">
              <p><b>Internet Gateways:</b> {', '.join([igw['id'] + (' - '+igw['name'] if igw['name'] else '') for igw in vpc['igws']]) or 'None'}</p>
              <h5>Subnets</h5><ul>
        """
        for subnet in vpc["subnets"]:
            html += f"<li>{subnet['id']} ({subnet['cidr']}, {subnet['az']}){' - '+subnet['name'] if subnet['name'] else ''}"
            if subnet["instances"]:
                html += "<ul>"
                for inst in subnet["instances"]:
                    html += f"<li>EC2 {inst['id']}{' - '+inst['name'] if inst['name'] else ''} - {inst['type']} [{inst['state']}]<br>Private IP: {inst['private_ip']} | Public IP: {inst['public_ip']}<br>SGs: {', '.join(inst['sgs'])}</li>"
                html += "</ul>"
            else:
                html += "<br><i>No instances</i>"
            html += "</li>"
        html += "</ul></div></div></div>"
    html += "</div>"
    return html
