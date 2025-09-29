# AWS Inventory
Python tool to inventory AWS resources (EC2 for now) and generate an HTML report with tabs per region and service.

## Features
* Collects EC2 inventory per region:
    * VPCs, Subnets, Internet Gateways
    * EC2 Instances with names, IDs, type, state, private/public IPs, and Security Groups
* Generates a multi-tab HTML report
* Supports AWS CLI profiles
* Supports region selection
    * Single region
    * Multiple regions
    * All regions

## Requirements
* Python 3.9+
* AWS credentials configures via AWS ClI profiles
* Python packages:
```shell
boto3>=1.30.0
jinja2>=3.1.2
```
Install dependencies:
```bash
pip install -r requirements.txt

## Project Structure
```bash
aws_inventory/
├── aws_inventory/          
│   ├── __init__.py
│   ├── main.py              
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── boto_helpers.py
│   │   ├── html_report.py
│   │   └── common.py       
│   └── regional/
│       ├── __init__.py
│       └── ec2.py
└── reports/                 # Generated HTML reports
```

## Usage
### 1. Configure AWS CLI profile
```bash
aws configure --profile profile_name
```
### 2. Run the tool
from the project root:
**Single region:**
```bash
python -m aws_inventory.main --profile profile_name --regions us-east-1
```
**Multiple regions:**
```bash
python -m aws_inventory.main --profile profile_name --regions us-east-1,us-east-2
```
**All regions:**
```bash
python -m aws_inventory.main --profile profile_name --regions all
```
### View the report
The HTML report is saved in the `reports/` folder:
```bash
reports/inventory_report.html
```

`Made by Dirgo`
