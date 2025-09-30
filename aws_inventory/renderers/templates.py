# Jinja2 templates for rendering HTML reports

def get_base_html_template():
    # Return the base HTML template with header, footer and tabs
    return """
     <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>AWS Inventory Report</title>
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
      <style>
        {{ styles | safe }}
      </style>
    </head>
    <body class="p-4">
      {{ header | safe }}
      {{ tabs | safe }}
      {{ content | safe }}
      {{ footer | safe }}
    </body>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <script>
      {{ scripts | safe }}
    </script>
    </html>
    """
def get_styles():
    """Return CSS styles for the report."""
    return """
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
        .card {
          box-shadow: 0 2px 4px rgba(0,0,0,0.05);
          transition: transform 0.2s;
        }
        .card:hover {
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
    """


def get_scripts():
    """Return JavaScript for export functionality."""
    return """
      function exportToPDF() {
        const element = document.body;
        const opt = {
          margin: 10,
          filename: 'aws-inventory-report-' + new Date().toISOString().split('T')[0] + '.pdf',
          image: { type: 'jpeg', quality: 0.98 },
          html2canvas: { scale: 2, logging: false },
          jsPDF: { unit: 'mm', format: 'a4', orientation: 'landscape' }
        };
        
        const allTabPanes = document.querySelectorAll('.tab-pane');
        const allAccordions = document.querySelectorAll('.accordion-collapse');
        
        allTabPanes.forEach(pane => {
          pane.classList.add('show', 'active');
        });
        
        allAccordions.forEach(accordion => {
          accordion.classList.add('show');
        });
        
        html2pdf().set(opt).from(element).save().then(() => {
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
    """


def get_ec2_stats_template():
    """Return template for EC2 statistics dashboard."""
    return """
        <div class="row mb-4">
          <div class="col-md-2">
            <div class="card text-center">
              <div class="card-body">
                <h5 class="card-title text-primary">{{ stats.total_vpcs }}</h5>
                <p class="card-text small">VPCs</p>
              </div>
            </div>
          </div>
          <div class="col-md-2">
            <div class="card text-center">
              <div class="card-body">
                <h5 class="card-title text-info">{{ stats.total_subnets }}</h5>
                <p class="card-text small">Subnets</p>
              </div>
            </div>
          </div>
          <div class="col-md-2">
            <div class="card text-center">
              <div class="card-body">
                <h5 class="card-title text-success">{{ stats.total_instances }}</h5>
                <p class="card-text small">Instances</p>
              </div>
            </div>
          </div>
          <div class="col-md-2">
            <div class="card text-center">
              <div class="card-body">
                <h5 class="card-title text-warning">{{ stats.total_security_groups }}</h5>
                <p class="card-text small">Security Groups</p>
              </div>
            </div>
          </div>
          <div class="col-md-4">
            <div class="card">
              <div class="card-body">
                <h6 class="card-subtitle mb-2 text-muted">Instances by State</h6>
                <p class="mb-0">
                  {% for state, count in stats.instances_by_state.items() %}
                    {% if state == 'running' %}
                      <span class="badge bg-success me-1">{{ state }}: {{ count }}</span>
                    {% elif state == 'stopped' %}
                      <span class="badge bg-danger me-1">{{ state }}: {{ count }}</span>
                    {% else %}
                      <span class="badge bg-warning me-1">{{ state }}: {{ count }}</span>
                    {% endif %}
                  {% endfor %}
                </p>
              </div>
            </div>
          </div>
        </div>
    """


def get_ec2_sg_template():
    """Return template for security groups section."""
    return """
                <div class="accordion-item">
                  <h2 class="accordion-header">
                    <button class="accordion-button collapsed" type="button"
                            data-bs-toggle="collapse"
                            data-bs-target="#sg{{ region_safe }}{{ vpc_index }}{{ sg_index }}"
                            aria-expanded="false">
                      <code>{{ sg.id }}</code>
                      <span class="ms-2"><strong>{{ sg.name }}</strong></span>
                      <span class="ms-2 text-muted small">{{ sg.description }}</span>
                      <span class="ms-auto me-2">
                        <span class="badge bg-success" title="Inbound rules">
                          ↓ {{ sg.inbound_rules|length }}
                        </span>
                        <span class="badge bg-warning text-dark" title="Outbound rules">
                          ↑ {{ sg.outbound_rules|length }}
                        </span>
                      </span>
                    </button>
                  </h2>
                  <div id="sg{{ region_safe }}{{ vpc_index }}{{ sg_index }}"
                       class="accordion-collapse collapse">
                    <div class="accordion-body">
                      {{ sg_rules_table | safe }}
                    </div>
                  </div>
                </div>
    """


def get_ec2_vpc_template():
    """Return template for VPC accordion section."""
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
            
            <span class="ms-3">
              <span class="badge bg-info" title="Subnets">
                <i class="bi bi-diagram-3"></i> {{ vpc.subnets|length }} subnet(s)
              </span>
              <span class="badge bg-success ms-1" title="Security Groups">
                <i class="bi bi-shield-check"></i> {{ vpc.security_groups|length }} SG(s)
              </span>
              {% set instance_count = vpc.subnets|sum(attribute='instances|length', start=0) %}
              <span class="badge bg-primary ms-1" title="Instances">
                <i class="bi bi-server"></i> {{ instance_count }} instance(s)
              </span>
            </span>
          </button>
        </h2>
        <div id="collapse{{ region_safe }}{{ loop.index }}" 
             class="accordion-collapse collapse" 
             data-bs-parent="#vpcAccordion{{ region_safe }}">
          <div class="accordion-body">
            {{ vpc_body | safe }}
          </div>
        </div>
      </div>
      {% endfor %}
    </div>
    
    {% if not vpcs %}
      <div class="alert alert-info">No VPCs found in this region.</div>
    {% endif %}
    """
