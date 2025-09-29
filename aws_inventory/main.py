import argparse
from aws_inventory.regional.ec2 import collect_ec2
from aws_inventory.utils.html_report import render_html, save_output
from aws_inventory.utils.boto_helpers import create_session, get_all_regions

def parse_regions(regions_arg, session):
    if regions_arg.lower() == "all":
        return get_all_regions("ec2", session)
    return [r.strip() for r in regions_arg.split(",")]

def main():
    parser = argparse.ArgumentParser(description="AWS Inventory Tool")
    parser.add_argument("--profile", required=True, help="AWS profile name")
    parser.add_argument("--regions", default="us-east-1", help="Comma-separated regions or 'all'")
    args = parser.parse_args()

    session = create_session(args.profile)
    regions = parse_regions(args.regions, session)

    inventories_by_service = {}

    for region in regions:
        ec2_html = collect_ec2(args.profile, region)
        inventories_by_service[f"EC2 - {region}"] = ec2_html

    # Example for global services: inventories_by_service["IAM (Global)"] = collect_iam(args.profile)
    html_content = render_html(inventories_by_service)
    filename = f"inventory_report.html"
    save_output(html_content, filename)

if __name__ == "__main__":
    main()
