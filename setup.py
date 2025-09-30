from setuptools import setup, find_packages

setup(
    name="aws_inventory",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "boto3>=1.30.0",
        "jinja2>=3.1.2",
        "tqdm>=4.66.0",
        "python-dateutil>=2.9.0"
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "aws-inventory=aws_inventory.main:main",
        ],
    },
    author="Dirgo",
    description="AWS resource inventory tool with HTML reporting",
    keywords="aws inventory ec2 cloud infrastructure",
)