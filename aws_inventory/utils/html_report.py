# Main HTML report generation.
import os
from datetime import datetime
from jinja2 import Template
from aws_inventory.renderers.ec2_renderer import render_ec2_inventory
from aws_inventory.renderers.eks_renderer import render_eks_inventory
from aws_inventory.renderers import templates


def save_output(content, filename, folder="reports"):
    """Save HTML content to a file."""
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Inventory written to {path}")
    return path


def render_header(profile_name, timestamp):
    """Render the header section."""
    profile_html = f'<p class="mb-1"><strong>Profile:</strong> {profile_name}</p>' if profile_name else ''
    
    return f"""
    <div class="header-section position-relative">
      <div class="export-buttons">
        <button class="export-btn me-2" onclick="exportToPDF()">
          <i class="bi bi-file-pdf"></i> Export PDF
        </button>
        <button class="export-btn" onclick="window.print()">
          <i class="bi bi-printer"></i> Print
        </button>
      </div>
      <h1 class="mb-2">AWS Inventory Report</h1>
      {profile_html}
      <p class="timestamp mb-0">Generated on: {timestamp}</p>
    </div>
    """


def render_service_tabs(inventories_by_service):
    """Render service-level tabs."""
    html = '<ul class="nav nav-tabs" id="myTab" role="tablist">'
    
    for idx, service in enumerate(inventories_by_service.keys(), 1):
        active_class = "active" if idx == 1 else ""
        html += f"""
        <li class="nav-item" role="presentation">
          <button class="nav-link {active_class}" 
                  id="tab{idx}" 
                  data-bs-toggle="tab" 
                  data-bs-target="#content{idx}" 
                  type="button"
                  role="tab">
            {service}
          </button>
        </li>
        """
    
    html += '</ul>'
    return html


def render_service_content(inventories_by_service):
    """Render content for each service tab."""
    html = '<div class="tab-content mt-3 p-3 bg-white rounded shadow-sm">'
    
    for idx, (service, inventory_info) in enumerate(inventories_by_service.items(), 1):
        active_class = "show active" if idx == 1 else ""
        service_type = inventory_info.get("type", "unknown")
        
        if "regions" in inventory_info:
            # Regional service
            regions_data = inventory_info["regions"]
            if service_type.lower() == "ec2":
                rendered_html = render_ec2_inventory(regions_data)
            elif service_type.lower() == "eks":
                rendered_html = render_eks_inventory(regions_data)
            else:
                rendered_html = f'<div class="alert alert-warning">Rendering for {service_type} not implemented yet.</div>'
        else:
            # Global service
            rendered_html = '<div class="alert alert-info">Global service rendering coming soon</div>'
        
        html += f"""
        <div class="tab-pane fade {active_class}" 
             id="content{idx}"
             role="tabpanel">
          {rendered_html}
        </div>
        """
    
    html += '</div>'
    return html


def render_footer():
    """Render the footer section."""
    return """
    <footer class="mt-4 text-center text-muted">
      <small>AWS Inventory Tool</small>
    </footer>
    """


def render_html(inventories_by_service, profile_name=None):
    """
    Render the complete HTML report with all service inventories.
    
    Args:
        inventories_by_service: dict like
        {
            "EC2": {
                "type": "ec2",
                "regions": {
                    "us-east-1": [...],
                    "us-west-2": [...]
                }
            },
            "EKS": {
                "type": "eks",
                "regions": {
                    "us-east-1": [...],
                    "us-west-2": [...]
                }
            },
            "IAM": {"type": "iam", "global": True, "data": [...]}
        }
        profile_name: AWS profile name used
        
    Returns:
        str: Complete HTML document
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Build the page sections
    header = render_header(profile_name, timestamp)
    tabs = render_service_tabs(inventories_by_service)
    content = render_service_content(inventories_by_service)
    footer = render_footer()
    
    # Combine everything
    base_template = Template(templates.get_base_html_template())
    
    return base_template.render(
        styles=templates.get_styles(),
        scripts=templates.get_scripts(),
        header=header,
        tabs=tabs,
        content=content,
        footer=footer
    )