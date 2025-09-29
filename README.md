# AWS-inventory
This tool uses boto 3 to list all the ec2 instances and the sg attached to them on a VPC. It also lists subnets, and empty subnets inside a VPC.
 ## How to install
 * Install and configure AWS cli
 * Create a virtual enviroment using: `python -m venv venvname`
 * Install boto3 and jinja: `pip install boto3 jinja2`

## How to run
`python aws_inventory.py`
* After that, serve a http server with: `python -m http.server`
