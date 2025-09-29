from jinja2 import Template
import os

def save_output(content, filename, folder="reports"):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    with open(path, "w") as f:
        f.write(content)
    print(f"Inventory written to {path}")
    return path

def render_html(inventories_by_service):
    """
    inventories_by_service: dict like
    {
        "EC2 - us-east-1": ec2_inventory_data,
        "EC2 - us-west-2": ec2_inventory_data,
        "IAM (Global)": iam_inventory_data
    }
    """
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>AWS Inventory Report</title>
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    </head>
    <body class="p-4">
      <h1>Genaro Inventory Report</h1>

      <ul class="nav nav-tabs" id="myTab" role="tablist">
        {% for service in inventories_by_service.keys() %}
        <li class="nav-item" role="presentation">
          <button class="nav-link {% if loop.first %}active{% endif %}" id="tab{{ loop.index }}" 
                  data-bs-toggle="tab" data-bs-target="#content{{ loop.index }}" type="button">
            {{ service }}
          </button>
        </li>
        {% endfor %}
      </ul>

      <div class="tab-content mt-3">
        {% for service, inventory in inventories_by_service.items() %}
        <div class="tab-pane fade {% if loop.first %}show active{% endif %}" id="content{{ loop.index }}">
          {{ inventory | safe }}
        </div>
        {% endfor %}
      </div>
    </body>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </html>
    """
    return Template(html_template).render(inventories_by_service=inventories_by_service)
