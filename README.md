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
boto3 >=1.30.0
jinja2 >=3.1.2
```
## Installation 
### 1. Create a virtual environment (recommended)
```bash
python -m venv name_venv
source name_venv/bin/activate # Linux/Mac
name_venv/Scripts/activate # Windows
```
### 2. Install the tool
#### Option A: Editable install (recommended for development)
```bash
git clone <repo-url>
cd aws-inventory
pip install -e.
```
> This installs the package in editable mode, so any changes to the source code are inmediatly available.
#### Option B: Regular pip install
```bash
git clone <repo-url>
cd aws-inventory
pip install . 
```
> Dependencies (`boto3`, `jinja2`) are automatically installed from `setup.py`
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
From the project root run:
**Single region:**
```bash
python3 -m aws_inventory.main --profile profile_name --regions us-east-1
```
**Multiple regions:**
```bash
python3 -m aws_inventory.main --profile profile_name --regions us-east-1,us-east-2
```
**All regions:**
```bash
python3 -m aws_inventory.main --profile profile_name --regions all
```
### 3. View the report
The HTML report is saved in the `reports/` folder:
```bash
reports/inventory_report.html
```
### 4. View report in browser via local HTTP server
#### 1. Navigate to the reports folder:
```bash
cd reports
```
#### 2. Start a simple HTTP server:
```bash
python3 -m http.server # Linux/Mac
py -m http.server # Windows
```
#### 3. Open a browser and go to: 
```bash
http://ipaddress:8000/inventory_report.html
```
> You can use `ipconfig` on Windows or `ip a` on Linux to know your ip address

`Made by Dirgo`
