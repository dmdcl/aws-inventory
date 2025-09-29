import boto3
import json
from jinja2 import Template

# ---------- Step 1: Collect Data ----------
session = boto3.Session(region_name="us-east-1")  # change region here
ec2 = session.client("ec2")

# Get resources
vpcs = ec2.describe_vpcs()["Vpcs"]
subnets = ec2.describe_subnets()["Subnets"]
instances = ec2.describe_instances()["Reservations"]
sgs = ec2.describe_security_groups()["SecurityGroups"]
igws = ec2.describe_internet_gateways()["InternetGateways"]

# ---------- Step 2: Build Relationships ----------
inventory = []

for vpc in vpcs:
    vpc_id = vpc["VpcId"]
    vpc_entry = {
        "id": vpc_id,
        "cidr": vpc.get("CidrBlock"),
        "subnets": [],
        "igws": [igw["InternetGatewayId"] for igw in igws if any(att["VpcId"] == vpc_id for att in igw["Attachments"])]
    }

    # Subnets in this VPC
    for subnet in [s for s in subnets if s["VpcId"] == vpc_id]:
        subnet_entry = {
            "id": subnet["SubnetId"],
            "cidr": subnet.get("CidrBlock"),
            "az": subnet.get("AvailabilityZone"),
            "instances": []
        }

        # Instances in this Subnet
        for r in instances:
            for i in r["Instances"]:
                if i["SubnetId"] == subnet["SubnetId"]:
                    subnet_entry["instances"].append({
                        "id": i["InstanceId"],
                        "type": i["InstanceType"],
                        "state": i["State"]["Name"],
                        "private_ip": i.get("PrivateIpAddress"),
                        "public_ip": i.get("PublicIpAddress"),
                        "sgs": [sg["GroupId"] for sg in i["SecurityGroups"]]
                    })

        vpc_entry["subnets"].append(subnet_entry)

    inventory.append(vpc_entry)

# ---------- Step 3: HTML Template ----------
html_template = """
<!DOCTYPE html>
<html>
<head>
  <title>Genaro Inventory</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body class="p-4">
  <h1>Genaro Inventory Report</h1>
  <div class="accordion" id="vpcAccordion">
    {% for vpc in inventory %}
    <div class="accordion-item">
      <h2 class="accordion-header" id="heading{{ loop.index }}">
        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse{{ loop.index }}">
          VPC {{ vpc.id }} ({{ vpc.cidr }})
        </button>
      </h2>
      <div id="collapse{{ loop.index }}" class="accordion-collapse collapse">
        <div class="accordion-body">
          <p><b>Internet Gateways:</b> {{ vpc.igws | join(", ") if vpc.igws else "None" }}</p>
          <h5>Subnets</h5>
          <ul>
            {% for subnet in vpc.subnets %}
            <li>
              {{ subnet.id }} ({{ subnet.cidr }}, {{ subnet.az }})
              {% if subnet.instances %}
              <ul>
                {% for inst in subnet.instances %}
                <li>
                  EC2 {{ inst.id }} - {{ inst.type }} [{{ inst.state }}] <br>
                  Private IP: {{ inst.private_ip }} | Public IP: {{ inst.public_ip }} <br>
                  SGs: {{ inst.sgs | join(", ") }}
                </li>
                {% endfor %}
              </ul>
              {% else %}
              <i>No instances</i>
              {% endif %}
            </li>
            {% endfor %}
          </ul>
        </div>
      </div>
    </div>
    {% endfor %}
  </div>
</body>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</html>
"""

# ---------- Step 4: Render & Save ----------
template = Template(html_template)
html_content = template.render(inventory=inventory)

with open("genaro_inventory.html", "w") as f:
    f.write(html_content)

print("✅ Inventory written to genaro_inventory.html")

