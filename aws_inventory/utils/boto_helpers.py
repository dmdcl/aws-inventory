import boto3

def create_session(profile):
    """Create a boto3 session using a profile"""
    return boto3.Session(profile_name=profile)

def get_all_regions(service_name="ec2", session=None):
    """Return list of all regions for a given service"""
    if not session:
        session = boto3.Session()
    ec2 = session.client(service_name, region_name="us-east-1")
    return [r["RegionName"] for r in ec2.describe_regions()["Regions"]]
