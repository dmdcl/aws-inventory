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


def render_service_inventory(service_type, data, region=None):
    """
    Render inventory data based on service type.
    
    Args:
        service_type: Type of service (e.g., 'ec2', 'iam')
        data: Structured data to render
        region: Optional region identifier for unique IDs
    
    Returns:
        Rendered HTML string
    """
    if service_type.lower() == "ec2":
        template = Template(get_ec2_template())
        # Make region safe for HTML IDs (replace hyphens)
        region_safe = region.replace("-", "") if region else "global"
        return template.render(vpcs=data, region_safe=region_safe)
    
    # Placeholder for other services
    return f"<div class='alert alert-warning'>Rendering for {service_type} not implemented yet.</div>"


def render_html(inventories_by_service):
    """
    Render the complete HTML report with all service inventories.
    
    Args:
        inventories_by_service: dict like
        {
            "EC2 - us-east-1": {"type": "ec2", "region": "us-east-1", "data": [...]},
            "IAM (Global)": {"type": "iam", "data": [...]}
        }
    """
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Render each service's inventory
    rendered_inventories = {}
    for service_key, inventory_info in inventories_by_service.items():
        service_type = inventory_info.get("type", "unknown")
        data = inventory_info.get("data", [])
        region = inventory_info.get("region")
        
        rendered_html = render_service_inventory(service_type, data, region)
        rendered_inventories[service_key] = rendered_html
    
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>AWS Inventory Report</title>
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
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
      </style>
    </head>
    <body class="p-4">
      
      <div class="header-section">
        <h1 class="mb-2">AWS Inventory Report</h1>
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
    </html>
    """
    
    template = Template(html_template)
    return template.render(
        rendered_inventories=rendered_inventories,
        timestamp=timestamp
    )