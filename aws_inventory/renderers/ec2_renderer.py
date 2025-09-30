"""EC2-specific HTML rendering logic."""
from jinja2 import Template
from aws_inventory.utils.stats import calculate_ec2_stats, calculate_region_stats
from aws_inventory.renderers import templates


def render_sg_rules_table(sg, direction="inbound"):
    """
    Render security group rules table.
    
    Args:
        sg: Security group dictionary
        direction: 'inbound' or 'outbound'
        
    Returns:
        str: Rendered HTML table
    """
    rules = sg.get(f"{direction}_rules", [])
    source_dest = "sources" if direction == "inbound" else "destinations"
    label = "Source" if direction == "inbound" else "Destination"
    icon = "arrow-down-circle" if direction == "inbound" else "arrow-up-circle"
    color = "success" if direction == "inbound" else "warning"
    
    if not rules:
        return f'<p class="text-muted"><em>No {direction} rules</em></p>'
    
    html = f"""
    <h6 class="text-{color}">
      <i class="bi bi-{icon}"></i> {direction.capitalize()} Rules
    </h6>
    <table class="table table-sm table-bordered mb-3">
      <thead>
        <tr>
          <th>Protocol</th>
          <th>Port Range</th>
          <th>{label}</th>
          <th>Description</th>
        </tr>
      </thead>
      <tbody>
    """
    
    for rule in rules:
        from_port = rule.get("from_port", "all")
        to_port = rule.get("to_port", "all")
        port_range = from_port if from_port == to_port else f"{from_port} - {to_port}"
        
        html += f"""
        <tr>
          <td><span class="badge bg-secondary">{rule.get('protocol', 'all')}</span></td>
          <td>{port_range}</td>
          <td>
        """
        
        for item in rule.get(source_dest, []):
            badge_class = "bg-info" if item.get("type") == "cidr" else "bg-primary"
            html += f'<span class="badge {badge_class}">{item.get("value", "")}</span><br>'
        
        html += "</td><td>"
        
        for item in rule.get(source_dest, []):
            desc = item.get("description", "-")
            html += f'<small class="text-muted">{desc}</small><br>'
        
        html += "</td></tr>"
    
    html += "</tbody></table>"
    return html


def render_security_groups(vpc, region_safe, vpc_index):
    """Render security groups section for a VPC."""
    if not vpc.get("security_groups"):
        return ""
    
    html = '<div class="mb-4"><h5>Security Groups</h5>'
    html += f'<div class="accordion" id="sgAccordion{region_safe}{vpc_index}">'
    
    for sg_index, sg in enumerate(vpc["security_groups"], 1):
        inbound_table = render_sg_rules_table(sg, "inbound")
        outbound_table = render_sg_rules_table(sg, "outbound")
        
        html += f"""
        <div class="accordion-item">
          <h2 class="accordion-header">
            <button class="accordion-button collapsed" type="button"
                    data-bs-toggle="collapse"
                    data-bs-target="#sg{region_safe}{vpc_index}{sg_index}"
                    aria-expanded="false">
              <code>{sg['id']}</code>
              <span class="ms-2"><strong>{sg['name']}</strong></span>
              <span class="ms-2 text-muted small">{sg['description']}</span>
              <span class="ms-auto me-2">
                <span class="badge bg-success" title="Inbound rules">
                  ↓ {len(sg.get('inbound_rules', []))}
                </span>
                <span class="badge bg-warning text-dark" title="Outbound rules">
                  ↑ {len(sg.get('outbound_rules', []))}
                </span>
              </span>
            </button>
          </h2>
          <div id="sg{region_safe}{vpc_index}{sg_index}"
               class="accordion-collapse collapse">
            <div class="accordion-body">
              {inbound_table}
              {outbound_table}
            </div>
          </div>
        </div>
        """
    
    html += '</div></div>'
    return html


def render_instances_table(instances):
    """Render instances table for a subnet."""
    if not instances:
        return '<p class="text-muted"><em>No instances in this subnet</em></p>'
    
    html = """
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
    """
    
    for instance in instances:
        state = instance.get("state", "unknown")
        if state == "running":
            state_badge = f'<span class="badge bg-success">{state}</span>'
        elif state == "stopped":
            state_badge = f'<span class="badge bg-danger">{state}</span>'
        else:
            state_badge = f'<span class="badge bg-warning">{state}</span>'
        
        sg_badges = ""
        for sg in instance.get("security_groups", []):
            title = f"{sg['name']} - {sg['description']}"
            sg_badges += f'<span class="badge bg-primary" title="{title}">{sg["id"]}</span> '
        
        html += f"""
        <tr>
          <td><code>{instance.get('id', '')}</code></td>
          <td>{instance.get('name') or '-'}</td>
          <td><span class="badge bg-light text-dark">{instance.get('type', '')}</span></td>
          <td>{state_badge}</td>
          <td><code>{instance.get('private_ip') or '-'}</code></td>
          <td><code>{instance.get('public_ip') or '-'}</code></td>
          <td>{sg_badges}</td>
        </tr>
        """
    
    html += "</tbody></table></div>"
    return html


def render_subnets(vpc):
    """Render subnets section for a VPC."""
    if not vpc.get("subnets"):
        return '<p class="text-muted"><em>No subnets in this VPC</em></p>'
    
    html = '<h5>Subnets</h5>'
    
    for subnet in vpc["subnets"]:
        instance_count = len(subnet.get("instances", []))
        instances_html = render_instances_table(subnet.get("instances", []))
        
        html += f"""
        <div class="card mb-2">
          <div class="card-body">
            <h6 class="card-subtitle mb-2">
              <span class="badge bg-secondary">{subnet['id']}</span>
              {'<strong>' + subnet['name'] + '</strong>' if subnet.get('name') else ''}
              <span class="badge bg-primary ms-2">
                <i class="bi bi-server"></i> {instance_count} instance(s)
              </span>
            </h6>
            <p class="mb-2">
              <small>
                <strong>CIDR:</strong> {subnet.get('cidr', '')} | 
                <strong>AZ:</strong> {subnet.get('az', '')}
              </small>
            </p>
            {instances_html}
          </div>
        </div>
        """
    
    return html


def render_vpc_body(vpc, region_safe, vpc_index):
    """Render the complete body of a VPC accordion."""
    igws_html = ""
    if vpc.get("igws"):
        igws_html = '<div class="mb-3"><strong>Internet Gateways:</strong> '
        for igw in vpc["igws"]:
            name_part = f" ({igw['name']})" if igw.get('name') else ""
            igws_html += f'<span class="badge bg-info">{igw["id"]}{name_part}</span> '
        igws_html += '</div>'
    else:
        igws_html = '<div class="mb-3"><strong>Internet Gateways:</strong> <span class="text-muted">None</span></div>'
    
    sg_html = render_security_groups(vpc, region_safe, vpc_index)
    subnets_html = render_subnets(vpc)
    
    return igws_html + sg_html + subnets_html


def render_region_tabs(regions_data):
    """Render region tabs with resource counts."""
    html = '<ul class="nav nav-pills mb-3" id="regionTabs" role="tablist">'
    
    for idx, (region, data) in enumerate(regions_data.items(), 1):
        active_class = "active" if idx == 1 else ""
        stats = calculate_region_stats(data)
        
        html += f"""
        <li class="nav-item" role="presentation">
          <button class="nav-link {active_class}" id="region-tab-{idx}" 
                  data-bs-toggle="pill" data-bs-target="#region-{idx}" 
                  type="button" role="tab">
            {region}
            <span class="badge bg-light text-dark ms-1">{stats['vpc_count']} VPC(s)</span>
            <span class="badge bg-primary ms-1">{stats['instance_count']} EC2</span>
          </button>
        </li>
        """
    
    html += '</ul>'
    return html


def render_region_content(regions_data):
    """Render content for each region tab."""
    html = '<div class="tab-content" id="regionTabContent">'
    
    for idx, (region, vpcs) in enumerate(regions_data.items(), 1):
        active_class = "show active" if idx == 1 else ""
        region_safe = region.replace("-", "")
        
        html += f'<div class="tab-pane fade {active_class}" id="region-{idx}" role="tabpanel">'
        html += f'<div class="accordion" id="vpcAccordion{region_safe}">'
        
        if vpcs:
            for vpc_index, vpc in enumerate(vpcs, 1):
                instance_count = sum(len(s.get("instances", [])) for s in vpc.get("subnets", []))
                vpc_name = f" - {vpc['name']}" if vpc.get('name') else ""
                
                html += f"""
                <div class="accordion-item">
                  <h2 class="accordion-header" id="heading{region_safe}{vpc_index}">
                    <button class="accordion-button collapsed" type="button" 
                            data-bs-toggle="collapse" 
                            data-bs-target="#collapse{region_safe}{vpc_index}"
                            aria-expanded="false">
                      <strong>VPC:</strong>&nbsp;{vpc['id']} ({vpc.get('cidr', '')}){vpc_name}
                      
                      <span class="ms-3">
                        <span class="badge bg-info" title="Subnets">
                          <i class="bi bi-diagram-3"></i> {len(vpc.get('subnets', []))} subnet(s)
                        </span>
                        <span class="badge bg-success ms-1" title="Security Groups">
                          <i class="bi bi-shield-check"></i> {len(vpc.get('security_groups', []))} SG(s)
                        </span>
                        <span class="badge bg-primary ms-1" title="Instances">
                          <i class="bi bi-server"></i> {instance_count} instance(s)
                        </span>
                      </span>
                    </button>
                  </h2>
                  <div id="collapse{region_safe}{vpc_index}" 
                       class="accordion-collapse collapse" 
                       data-bs-parent="#vpcAccordion{region_safe}">
                    <div class="accordion-body">
                      {render_vpc_body(vpc, region_safe, vpc_index)}
                    </div>
                  </div>
                </div>
                """
        else:
            html += '<div class="alert alert-info">No VPCs found in this region.</div>'
        
        html += '</div></div>'
    
    html += '</div>'
    return html


def render_ec2_stats(stats):
    """Render EC2 statistics dashboard."""
    html = """
    <div class="row mb-4">
      <div class="col-md-2">
        <div class="card text-center">
          <div class="card-body">
            <h5 class="card-title text-primary">{}</h5>
            <p class="card-text small">VPCs</p>
          </div>
        </div>
      </div>
      <div class="col-md-2">
        <div class="card text-center">
          <div class="card-body">
            <h5 class="card-title text-info">{}</h5>
            <p class="card-text small">Subnets</p>
          </div>
        </div>
      </div>
      <div class="col-md-2">
        <div class="card text-center">
          <div class="card-body">
            <h5 class="card-title text-success">{}</h5>
            <p class="card-text small">Instances</p>
          </div>
        </div>
      </div>
      <div class="col-md-2">
        <div class="card text-center">
          <div class="card-body">
            <h5 class="card-title text-warning">{}</h5>
            <p class="card-text small">Security Groups</p>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card">
          <div class="card-body">
            <h6 class="card-subtitle mb-2 text-muted">Instances by State</h6>
            <p class="mb-0">
    """.format(
        stats['total_vpcs'],
        stats['total_subnets'],
        stats['total_instances'],
        stats['total_security_groups']
    )
    
    for state, count in stats['instances_by_state'].items():
        if state == "running":
            badge_class = "bg-success"
        elif state == "stopped":
            badge_class = "bg-danger"
        else:
            badge_class = "bg-warning"
        html += f'<span class="badge {badge_class} me-1">{state}: {count}</span>'
    
    html += """
            </p>
          </div>
        </div>
      </div>
    </div>
    """
    
    return html


def render_ec2_inventory(regions_data):
    """
    Main function to render EC2 inventory.
    
    Args:
        regions_data: Dict of {region: [vpcs]}
        
    Returns:
        str: Complete HTML for EC2 service
    """
    stats = calculate_ec2_stats(regions_data)
    
    html = render_ec2_stats(stats)
    html += render_region_tabs(regions_data)
    html += render_region_content(regions_data)
    
    return html