from jinja2 import Template
import os
from datetime import datetime


def save_output(content, filename, folder="reports"):
    """Save HTML content to a file."""
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Inventory written to {path}")
    return path


def get_ec2_template():
    """Return the Jinja2 template for EC2 resources."""
    return """
    <div class="accordion" id="vpcAccordion{{ region_safe }}">
      {% for vpc in vpcs %}
      <div class="accordion-item">
        <h2 class="accordion-header" id="heading{{ region_safe }}{{ loop.index }}">
          <button class="accordion-button collapsed" type="button" 
                  data-bs-toggle="collapse" 
                  data-bs-target="#collapse{{ region_safe }}{{ loop.index }}"
                  aria-expanded="false">
            <strong>VPC:</strong>&nbsp;{{ vpc.id }} ({{ vpc.cidr }})
            {% if vpc.name %} - {{ vpc.name }}{% endif %}
          </button>
        </h2>
        <div id="collapse{{ region_safe }}{{ loop.index }}" 
             class="accordion-collapse collapse" 
             data-bs-parent="#vpcAccordion{{ region_safe }}">
          <div class="accordion-body">
            
            <!-- Internet Gateways -->
            <div class="mb-3">
              <strong>Internet Gateways:</strong>
              {% if vpc.igws %}
                {% for igw in vpc.igws %}
                  <span class="badge bg-info">
                    {{ igw.id }}{% if igw.name %} ({{ igw.name }}){% endif %}
                  </span>
                {% endfor %}
              {% else %}
                <span class="text-muted">None</span>
              {% endif %}
            </div>

            <!-- Subnets -->
            <h5>Subnets</h5>
            {% if vpc.subnets %}
              {% for subnet in vpc.subnets %}
              <div class="card mb-2">
                <div class="card-body">
                  <h6 class="card-subtitle mb-2">
                    <span class="badge bg-secondary">{{ subnet.id }}</span>
                    {% if subnet.name %}<strong>{{ subnet.name }}</strong>{% endif %}
                  </h6>
                  <p class="mb-2">
                    <small>
                      <strong>CIDR:</strong> {{ subnet.cidr }} | 
                      <strong>AZ:</strong> {{ subnet.az }}
                    </small>
                  </p>

                  <!-- Instances in Subnet -->
                  {% if subnet.instances %}
                    <h6 class="mt-3">EC2 Instances:</h6>
                    <div class="table-responsive">
                      <table class="table table-sm table-hover">
                        <thead>
                          <tr>
                            <th>Instance ID</th>
                            <th>Name</th>
                            <th>Type</th>
                            <th>State</th>
                            <th>Private IP</th>
                            <th>Public IP</th>
                            <th>Security Groups</th>
                          </tr>
                        </thead>
                        <tbody>
                          {% for instance in subnet.instances %}
                          <tr>
                            <td><code>{{ instance.id }}</code></td>
                            <td>{{ instance.name or '-' }}</td>
                            <td><span class="badge bg-light text-dark">{{ instance.type }}</span></td>
                            <td>
                              {% if instance.state == 'running' %}
                                <span class="badge bg-success">{{ instance.state }}</span>
                              {% elif instance.state == 'stopped' %}
                                <span class="badge bg-danger">{{ instance.state }}</span>
                              {% else %}
                                <span class="badge bg-warning">{{ instance.state }}</span>
                              {% endif %}
                            </td>
                            <td><code>{{ instance.private_ip or '-' }}</code></td>
                            <td><code>{{ instance.public_ip or '-' }}</code></td>
                            <td>
                              {% for sg in instance.sgs %}
                                <span class="badge bg-primary">{{ sg }}</span>
                              {% endfor %}
                            </td>
                          </tr>
                          {% endfor %}
                        </tbody>
                      </table>
                    </div>
                  {% else %}
                    <p class="text-muted"><em>No instances in this subnet</em></p>
                  {% endif %}
                </div>
              </div>
              {% endfor %}
            {% else %}
              <p class="text-muted"><em>No subnets in this VPC</em></p>
            {% endif %}

          </div>
        </div>
      </div>
      {% endfor %}
    </div>
    
    {% if not vpcs %}
      <div class="alert alert-info">No VPCs found in this region.</div>
    {% endif %}
    """


def render_service_inventory(service_type, regions_data):
    """
    Render inventory data based on service type with nested regions.
    
    Args:
        service_type: Type of service (e.g., 'ec2', 'iam')
        regions_data: Dict of {region: data} for regional services
    
    Returns:
        Rendered HTML string with nested region tabs
    """
    if service_type.lower() == "ec2":
        ec2_template = Template(get_ec2_template())
        
        # Create nested region tabs
        nested_html = """
        <ul class="nav nav-pills mb-3" id="regionTabs" role="tablist">
        """
        
        # Generate region tabs
        for idx, region in enumerate(regions_data.keys(), 1):
            active_class = "active" if idx == 1 else ""
            nested_html += f"""
            <li class="nav-item" role="presentation">
              <button class="nav-link {active_class}" id="region-tab-{idx}" 
                      data-bs-toggle="pill" data-bs-target="#region-{idx}" 
                      type="button" role="tab">
                {region}
              </button>
            </li>
            """
        
        nested_html += "</ul><div class='tab-content' id='regionTabContent'>"
        
        # Generate region content
        for idx, (region, data) in enumerate(regions_data.items(), 1):
            active_class = "show active" if idx == 1 else ""
            region_safe = region.replace("-", "")
            rendered_region = ec2_template.render(vpcs=data, region_safe=region_safe)
            
            nested_html += f"""
            <div class="tab-pane fade {active_class}" id="region-{idx}" role="tabpanel">
              {rendered_region}
            </div>
            """
        
        nested_html += "</div>"
        return nested_html
    
    # Placeholder for other services
    return f"<div class='alert alert-warning'>Rendering for {service_type} not implemented yet.</div>"


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
            "IAM": {"type": "iam", "global": True, "data": [...]}
        }
        profile_name: AWS profile name used
    """
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Render each service's inventory
    rendered_inventories = {}
    for service_name, inventory_info in inventories_by_service.items():
        service_type = inventory_info.get("type", "unknown")
        
        if "regions" in inventory_info:
            # Regional service (like EC2)
            regions_data = inventory_info["regions"]
            rendered_html = render_service_inventory(service_type, regions_data)
        else:
            # Global service (like IAM)
            data = inventory_info.get("data", [])
            rendered_html = f"<div class='alert alert-info'>Global service rendering coming soon</div>"
        
        rendered_inventories[service_name] = rendered_html
    
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>AWS Inventory Report</title>
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
      <style>
        body {
          background-color: #f8f9fa;
        }
        .header-section {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 2rem;
          border-radius: 0.5rem;
          margin-bottom: 2rem;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .nav-tabs .nav-link {
          color: #495057;
          font-weight: 500;
        }
        .nav-tabs .nav-link.active {
          color: #667eea;
          font-weight: 600;
        }
        .nav-pills .nav-link {
          color: #495057;
        }
        .nav-pills .nav-link.active {
          background-color: #667eea;
        }
        .accordion-button:not(.collapsed) {
          background-color: #e7f1ff;
          color: #0c63e4;
        }
        code {
          background-color: #f8f9fa;
          padding: 0.2rem 0.4rem;
          border-radius: 0.25rem;
          font-size: 0.875rem;
        }
        .timestamp {
          font-size: 0.875rem;
          opacity: 0.9;
        }
        .export-buttons {
          position: absolute;
          top: 2rem;
          right: 2rem;
        }
        .export-btn {
          background-color: rgba(255, 255, 255, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.3);
          color: white;
          padding: 0.5rem 1rem;
          border-radius: 0.25rem;
          cursor: pointer;
          transition: all 0.3s;
        }
        .export-btn:hover {
          background-color: rgba(255, 255, 255, 0.3);
          transform: translateY(-2px);
        }
        @media print {
          .export-buttons, .nav-tabs, .nav-pills {
            display: none;
          }
          .tab-pane {
            display: block !important;
            opacity: 1 !important;
          }
          .accordion-collapse {
            display: block !important;
          }
          .accordion-button {
            display: none;
          }
        }
      </style>
    </head>
    <body class="p-4">
      
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
        {% if profile_name %}
        <p class="mb-1"><strong>Profile:</strong> {{ profile_name }}</p>
        {% endif %}
        <p class="timestamp mb-0">Generated on: {{ timestamp }}</p>
      </div>

      <ul class="nav nav-tabs" id="myTab" role="tablist">
        {% for service in rendered_inventories.keys() %}
        <li class="nav-item" role="presentation">
          <button class="nav-link {% if loop.first %}active{% endif %}" 
                  id="tab{{ loop.index }}" 
                  data-bs-toggle="tab" 
                  data-bs-target="#content{{ loop.index }}" 
                  type="button"
                  role="tab">
            {{ service }}
          </button>
        </li>
        {% endfor %}
      </ul>

      <div class="tab-content mt-3 p-3 bg-white rounded shadow-sm">
        {% for service, inventory_html in rendered_inventories.items() %}
        <div class="tab-pane fade {% if loop.first %}show active{% endif %}" 
             id="content{{ loop.index }}"
             role="tabpanel">
          {{ inventory_html | safe }}
        </div>
        {% endfor %}
      </div>

      <footer class="mt-4 text-center text-muted">
        <small>AWS Inventory Tool</small>
      </footer>

    </body>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <script>
      function exportToPDF() {
        const element = document.body;
        const opt = {
          margin: 10,
          filename: 'aws-inventory-report-' + new Date().toISOString().split('T')[0] + '.pdf',
          image: { type: 'jpeg', quality: 0.98 },
          html2canvas: { scale: 2, logging: false },
          jsPDF: { unit: 'mm', format: 'a4', orientation: 'landscape' }
        };
        
        // Show all content before export
        const allTabPanes = document.querySelectorAll('.tab-pane');
        const allAccordions = document.querySelectorAll('.accordion-collapse');
        
        allTabPanes.forEach(pane => {
          pane.classList.add('show', 'active');
        });
        
        allAccordions.forEach(accordion => {
          accordion.classList.add('show');
        });
        
        html2pdf().set(opt).from(element).save().then(() => {
          // Restore original state
          allTabPanes.forEach((pane, idx) => {
            if (idx !== 0) {
              pane.classList.remove('show', 'active');
            }
          });
          allAccordions.forEach(accordion => {
            accordion.classList.remove('show');
          });
        });
      }
    </script>
    </html>
    """
    
    template = Template(html_template)
    return template.render(
        rendered_inventories=rendered_inventories,
        timestamp=timestamp,
        profile_name=profile_name
    )