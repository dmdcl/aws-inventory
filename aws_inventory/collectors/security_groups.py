#Security groups collector module
def parse_rule_sources(rule, source_type="sources"):
    # Parse the sources or destinations of a security group rule
    sources = []

    # IP RANGES (IPv4)
    for ip_range in rule.get("IpRanges", []):
        sources.append({
            "type": "cidr",
            "value": ip_range.get("CidrIp"),
            "description": ip_range.get("Description"),
        })

    # IP RANGES (IPv6)
    for ip_range in rule.get("Ipv6Ranges", []):
        sources.append({
            "type": "cidr",
            "value": ip_range.get("CidrIpv6"),
            "description": ip_range.get("Description"),
        })

    # Security Group references
    for sg_ref in rule.get("UserIdGroupPairs", []):
        sources.append({
            "type": "sg",
            "value": sg_ref.get("GroupId"),
            "description": sg_ref.get("Description", "")
        })
    
    return sources

def parse_rule(rule):
    # Parse a security group rule.
    return {
        "protocol": rule.get("IpProtcol", "all"),
        "from_port": rule.get("FromPort", all),
        "to_port": rule.get("ToPort", all),
    }

def collect_security_groups(ec2_client):
    """
    Collect all security groups with their rules

    Args: 
        ec2_client: boto3 EC2 client

    Returns: dict: Map of security group ID to security groups details
    """
    sgs = ec2_client.describe_security_groups()["SecurityGroups"]
    sg_map = {}

    for sg in sgs:
        sg_id = sg["GroupId"]
        sg_map[sg_id] = {
            "id": sg_id,
            "name": sg.get("GroupName"),
            "description": sg.get("Description"),
            "vpc_id": sg.get("VpcId"),
            "inbound_rules": [],
            "outbound_rules": []
        }
        
        # Process inbound rules
        for rule in sg.get("IpPermissions", []):
            rule_entry = parse_rule(rule)
            rule_entry["sources"] = parse_rule_sources(rule)
            sg_map[sg_id]["inbound_rules"].append(rule_entry)

        # Process outbound rules
        for rule in sg.get("IpPermissionsEgress", []):
            rule_entry = parse_rule(rule)
            rule_entry["destinations"] = parse_rule_sources(rule)
            sg_map[sg_id]["outbound_rules"].append(rule_entry)

    return sg_map
