import argparse
from tqdm import tqdm
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

    print(f"\nStarting AWS inventory collection for {len(regions)} region(s)...\n")

    # Collect inventories grouped by service type
    inventories_by_service = {}

    # Collect EC2 data for all regions with progress bar
    ec2_regions_data = {}
    for region in tqdm(regions, desc="Collecting EC2 data", unit="region"):
        ec2_data = collect_ec2(args.profile, region)
        ec2_regions_data[region] = ec2_data

    # Group by service
    if ec2_regions_data:
        inventories_by_service["EC2"] = {
            "type": "ec2",
            "regions": ec2_regions_data
        }

    print("\nGenerating HTML report...")

    # Render HTML from structured data
    html_content = render_html(inventories_by_service, args.profile)
    filename = "inventory_report.html"
    save_output(html_content, filename)

    print("Inventory collection complete!\n")


if __name__ == "__main__":
    main()