
import argparse
from aws_inventory.regional.ec2 import collect_ec2
from aws_inventory.utils.html_report import render_html, save_output
from aws_inventory.utils.boto_helpers import create_session, get_all_regions


def parse_regions(regions_arg, session):
    """Parse the regions argument into a list of region names."""
    if regions_arg.lower() == "all":
        return get_all_regions("ec2", session)
    return [r.strip() for r in regions_arg.split(",")]


def main():
    parser = argparse.ArgumentParser(description="AWS Inventory Tool")
    parser.add_argument("--profile", required=True, help="AWS profile name")
    parser.add_argument(
        "--regions", 
        default="us-east-1", 
        help="Comma-separated regions or 'all'"
    )
    args = parser.parse_args()

    session = create_session(args.profile)
    regions = parse_regions(args.regions, session)

    # Collect inventories with structured data
    inventories_by_service = {}

    for region in regions:
        # collect_ec2 now returns structured data, not HTML
        ec2_data = collect_ec2(args.profile, region)
        
        # Store with metadata for rendering
        inventories_by_service[f"EC2 - {region}"] = {
            "type": "ec2",
            "region": region,
            "data": ec2_data
        }

    # Example for future global services:
    # iam_data = collect_iam(args.profile)
    # inventories_by_service["IAM (Global)"] = {
    #     "type": "iam",
    #     "data": iam_data
    # }

    # Render HTML from structured data
    html_content = render_html(inventories_by_service)
    filename = "inventory_report.html"
    save_output(html_content, filename)


if __name__ == "__main__":
    main()