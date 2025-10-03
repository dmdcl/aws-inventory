"""EKS-specific HTML rendering logic."""
from jinja2 import Template
from aws_inventory.utils.stats import calculate_eks_stats, calculate_region_stats_eks


def render_node_groups(cluster):
    """Render node groups section for a cluster."""
    node_groups = cluster.get("node_groups", [])
    
    if not node_groups:
        return '<p class="text-muted"><em>No node groups in this cluster</em></p>'
    
    html = '<h6 class="mt-3">Node Groups:</h6>'
    html += '<div class="table-responsive"><table class="table table-sm table-hover"><thead><tr>'
    html += '<th>Name</th><th>Status</th><th>Instance Types</th><th>Capacity</th>'
    html += '<th>AMI Type</th><th>Capacity Type</th><th>Version</th></tr></thead><tbody>'
    
    for ng in node_groups:
        status = ng.get("status", "unknown")
        status_badge = f'<span class="badge bg-success">{status}</span>' if status == "ACTIVE" else f'<span class="badge bg-warning">{status}</span>'
        
        instance_types = ", ".join(ng.get("instance_types", []))
        capacity = f"{ng.get('desired_size', 0)} (min: {ng.get('min_size', 0)}, max: {ng.get('max_size', 0)})"
        
        html += f"""
        <tr>
          <td><strong>{ng.get('name', '')}</strong></td>
          <td>{status_badge}</td>
          <td><code>{instance_types}</code></td>
          <td>{capacity}</td>
          <td><span class="badge bg-light text-dark">{ng.get('ami_type', '')}</span></td>
          <td><span class="badge bg-info">{ng.get('capacity_type', '')}</span></td>
          <td><code>{ng.get('version', '')}</code></td>
        </tr>
        """
    
    html += '</tbody></table></div>'
    return html


def render_fargate_profiles(cluster):
    """Render Fargate profiles section for a cluster."""
    fargate_profiles = cluster.get("fargate_profiles", [])
    
    if not fargate_profiles:
        return '<p class="text-muted"><em>No Fargate profiles in this cluster</em></p>'
    
    html = '<h6 class="mt-3">Fargate Profiles:</h6>'
    html += '<div class="table-responsive"><table class="table table-sm table-hover"><thead><tr>'
    html += '<th>Name</th><th>Status</th><th>Subnets</th><th>Selectors</th></tr></thead><tbody>'
    
    for fp in fargate_profiles:
        status = fp.get("status", "unknown")
        status_badge = f'<span class="badge bg-success">{status}</span>' if status == "ACTIVE" else f'<span class="badge bg-warning">{status}</span>'
        
        subnet_count = len(fp.get("subnets", []))
        selector_count = len(fp.get("selectors", []))
        
        html += f"""
        <tr>
          <td><strong>{fp.get('name', '')}</strong></td>
          <td>{status_badge}</td>
          <td>{subnet_count} subnet(s)</td>
          <td>{selector_count} selector(s)</td>
        </tr>
        """
    
    html += '</tbody></table></div>'
    return html


def render_addons(cluster):
    """Render addons section for a cluster."""
    addons = cluster.get("addons", [])
    
    if not addons:
        return '<p class="text-muted"><em>No addons in this cluster</em></p>'
    
    html = '<h6 class="mt-3">Addons:</h6>'
    html += '<div class="table-responsive"><table class="table table-sm table-hover"><thead><tr>'
    html += '<th>Name</th><th>Version</th><th>Status</th><th>Health</th></tr></thead><tbody>'
    
    for addon in addons:
        status = addon.get("status", "unknown")
        status_badge = f'<span class="badge bg-success">{status}</span>' if status == "ACTIVE" else f'<span class="badge bg-warning">{status}</span>'
        
        health = addon.get("health", {})
        health_issues = health.get("issues", [])
        health_badge = '<span class="badge bg-success">Healthy</span>' if not health_issues else f'<span class="badge bg-danger">{len(health_issues)} issue(s)</span>'
        
        html += f"""
        <tr>
          <td><strong>{addon.get('name', '')}</strong></td>
          <td><code>{addon.get('version', '')}</code></td>
          <td>{status_badge}</td>
          <td>{health_badge}</td>
        </tr>
        """
    
    html += '</tbody></table></div>'
    return html


def render_oidc_provider(cluster):
    """Render OIDC provider information."""
    oidc = cluster.get("oidc_provider")
    
    if not oidc:
        return '<p class="text-muted"><em>No OIDC provider configured</em></p>'
    
    status_badge = '<span class="badge bg-success">Configured</span>' if oidc.get("exists") else '<span class="badge bg-warning">Not Found in IAM</span>'
    
    html = f"""
    <h6 class="mt-3">OIDC Identity Provider:</h6>
    <div class="card mb-3">
      <div class="card-body">
        <p class="mb-2"><strong>Status:</strong> {status_badge}</p>
        <p class="mb-2"><strong>Issuer:</strong> <code>{oidc.get('issuer', '')}</code></p>
        <p class="mb-2"><strong>Provider ID:</strong> <code>{oidc.get('id', '')}</code></p>
    """
    
    if oidc.get("arn"):
        html += f'<p class="mb-0"><strong>ARN:</strong> <code>{oidc.get("arn")}</code></p>'
    
    html += """
      </div>
    </div>
    """
    
    return html


def render_service_account_roles(cluster):
    """Render IAM roles for service accounts (IRSA)."""
    sa_roles = cluster.get("service_account_roles", [])
    
    if not sa_roles:
        return '<p class="text-muted"><em>No IAM roles configured for service accounts</em></p>'
    
    html = f"""
    <h6 class="mt-3">IAM Roles for Service Accounts (IRSA):</h6>
    <div class="alert alert-info mb-2">
      <small><i class="bi bi-info-circle"></i> <strong>{len(sa_roles)}</strong> IAM role(s) configured with trust relationships to this cluster's OIDC provider</small>
    </div>
    <div class="table-responsive">
      <table class="table table-sm table-hover">
        <thead>
          <tr>
            <th>IAM Role</th>
            <th>Namespace</th>
            <th>Service Account</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
    """
    
    for sa_role in sa_roles:
        namespace = sa_role.get('namespace', '') or '-'
        sa_name = sa_role.get('service_account', '') or '-'
        created = sa_role.get('created_date', 'N/A')
        
        # Truncate created date to just the date part
        if created and created != 'N/A':
            created = created.split('T')[0]
        
        html += f"""
        <tr>
          <td>
            <strong>{sa_role.get('role_name', '')}</strong><br>
            <small class="text-muted"><code>{sa_role.get('role_arn', '')}</code></small>
          </td>
          <td><span class="badge bg-primary">{namespace}</span></td>
          <td><code>{sa_name}</code></td>
          <td><small>{created}</small></td>
        </tr>
        """
    
    html += """
        </tbody>
      </table>
    </div>
    """
    
    return html


def render_cluster_body(cluster, region_safe, cluster_index):
    """Render the complete body of a cluster accordion."""
    # Cluster details
    details_html = f"""
    <div class="row mb-3">
      <div class="col-md-6">
        <p><strong>Version:</strong> <code>{cluster.get('version', '')}</code></p>
        <p><strong>Platform Version:</strong> <code>{cluster.get('platform_version', '')}</code></p>
        <p><strong>Status:</strong> <span class="badge bg-{'success' if cluster.get('status') == 'ACTIVE' else 'warning'}">{cluster.get('status', '')}</span></p>
        <p><strong>Created:</strong> {cluster.get('created_at', 'N/A')}</p>
      </div>
      <div class="col-md-6">
        <p><strong>VPC:</strong> <code>{cluster.get('vpc_id', '')}</code></p>
        <p><strong>Endpoint Access:</strong> Public: {'✓' if cluster.get('public_access') else '✗'} | Private: {'✓' if cluster.get('private_access') else '✗'}</p>
        <p><strong>Subnets:</strong> {len(cluster.get('subnet_ids', []))} subnet(s)</p>
        <p><strong>Security Groups:</strong> {len(cluster.get('security_group_ids', []))} SG(s)</p>
      </div>
    </div>
    """
    
    # Endpoint info
    if cluster.get('endpoint'):
        details_html += f"""
        <div class="alert alert-info mb-3">
          <strong>API Endpoint:</strong> <code>{cluster.get('endpoint')}</code>
        </div>
        """
    
    node_groups_html = render_node_groups(cluster)
    fargate_html = render_fargate_profiles(cluster)
    addons_html = render_addons(cluster)
    oidc_html = render_oidc_provider(cluster)
    sa_roles_html = render_service_account_roles(cluster)
    
    return details_html + oidc_html + sa_roles_html + node_groups_html + fargate_html + addons_html


def render_region_tabs_eks(regions_data):
    """Render region tabs with cluster counts."""
    html = '<ul class="nav nav-pills mb-3" id="regionTabsEKS" role="tablist">'
    
    for idx, (region, data) in enumerate(regions_data.items(), 1):
        active_class = "active" if idx == 1 else ""
        stats = calculate_region_stats_eks(data)
        
        html += f"""
        <li class="nav-item" role="presentation">
          <button class="nav-link {active_class}" id="region-eks-tab-{idx}" 
                  data-bs-toggle="pill" data-bs-target="#region-eks-{idx}" 
                  type="button" role="tab">
            {region}
            <span class="badge bg-light text-dark ms-1">{stats['cluster_count']} Cluster(s)</span>
            <span class="badge bg-primary ms-1">{stats['total_nodes']} Nodes</span>
          </button>
        </li>
        """
    
    html += '</ul>'
    return html


def render_region_content_eks(regions_data):
    """Render content for each region tab."""
    html = '<div class="tab-content" id="regionTabContentEKS">'
    
    for idx, (region, clusters) in enumerate(regions_data.items(), 1):
        active_class = "show active" if idx == 1 else ""
        region_safe = region.replace("-", "")
        
        html += f'<div class="tab-pane fade {active_class}" id="region-eks-{idx}" role="tabpanel">'
        html += f'<div class="accordion" id="clusterAccordion{region_safe}">'
        
        if clusters:
            for cluster_index, cluster in enumerate(clusters, 1):
                total_nodes = cluster.get("total_nodes", 0)
                node_group_count = len(cluster.get("node_groups", []))
                fargate_count = len(cluster.get("fargate_profiles", []))
                addon_count = len(cluster.get("addons", []))
                
                status = cluster.get("status", "unknown")
                status_badge = f'<span class="badge bg-success ms-2">{status}</span>' if status == "ACTIVE" else f'<span class="badge bg-warning ms-2">{status}</span>'
                
                # Count service account roles
                sa_role_count = len(cluster.get("service_account_roles", []))
                
                html += f"""
                <div class="accordion-item">
                  <h2 class="accordion-header" id="heading{region_safe}{cluster_index}">
                    <button class="accordion-button collapsed" type="button" 
                            data-bs-toggle="collapse" 
                            data-bs-target="#collapse{region_safe}{cluster_index}"
                            aria-expanded="false">
                      <strong>Cluster:</strong>&nbsp;{cluster['name']}{status_badge}
                      <span class="ms-2 text-muted">v{cluster.get('version', '')}</span>
                      
                      <span class="ms-auto me-2">
                        <span class="badge bg-info" title="Node Groups">
                          <i class="bi bi-hdd-stack"></i> {node_group_count} NG(s)
                        </span>
                        <span class="badge bg-primary ms-1" title="Total Nodes">
                          <i class="bi bi-server"></i> {total_nodes} node(s)
                        </span>
                        <span class="badge bg-secondary ms-1" title="Fargate Profiles">
                          <i class="bi bi-layers"></i> {fargate_count} FG
                        </span>
                        <span class="badge bg-success ms-1" title="Addons">
                          <i class="bi bi-puzzle"></i> {addon_count} addon(s)
                        </span>
                        <span class="badge bg-warning text-dark ms-1" title="IAM Roles for Service Accounts">
                          <i class="bi bi-key"></i> {sa_role_count} IRSA
                        </span>
                      </span>
                    </button>
                  </h2>
                  <div id="collapse{region_safe}{cluster_index}" 
                       class="accordion-collapse collapse" 
                       data-bs-parent="#clusterAccordion{region_safe}">
                    <div class="accordion-body">
                      {render_cluster_body(cluster, region_safe, cluster_index)}
                    </div>
                  </div>
                </div>
                """
        else:
            html += '<div class="alert alert-info">No EKS clusters found in this region.</div>'
        
        html += '</div></div>'
    
    html += '</div>'
    return html


def render_eks_stats(stats):
    """Render EKS statistics dashboard."""
    html = """
    <div class="row mb-4">
      <div class="col-md-2">
        <div class="card text-center">
          <div class="card-body">
            <h5 class="card-title text-primary">{}</h5>
            <p class="card-text small">Clusters</p>
          </div>
        </div>
      </div>
      <div class="col-md-2">
        <div class="card text-center">
          <div class="card-body">
            <h5 class="card-title text-info">{}</h5>
            <p class="card-text small">Node Groups</p>
          </div>
        </div>
      </div>
      <div class="col-md-2">
        <div class="card text-center">
          <div class="card-body">
            <h5 class="card-title text-success">{}</h5>
            <p class="card-text small">Total Nodes</p>
          </div>
        </div>
      </div>
      <div class="col-md-2">
        <div class="card text-center">
          <div class="card-body">
            <h5 class="card-title text-warning">{}</h5>
            <p class="card-text small">Fargate Profiles</p>
          </div>
        </div>
      </div>
      <div class="col-md-2">
        <div class="card text-center">
          <div class="card-body">
            <h5 class="card-title text-secondary">{}</h5>
            <p class="card-text small">IRSA Roles</p>
          </div>
        </div>
      </div>
      <div class="col-md-2">
        <div class="card text-center">
          <div class="card-body">
            <h5 class="card-title text-dark">{}</h5>
            <p class="card-text small">Regions</p>
          </div>
        </div>
      </div>
    </div>
    """.format(
        stats['total_clusters'],
        stats['total_node_groups'],
        stats['total_nodes'],
        stats['total_fargate_profiles'],
        stats['total_service_account_roles'],
        stats['regions_with_resources']
    )
    
    return html


def render_eks_inventory(regions_data):
    """
    Main function to render EKS inventory.
    
    Args:
        regions_data: Dict of {region: [clusters]}
        
    Returns:
        str: Complete HTML for EKS service
    """
    stats = calculate_eks_stats(regions_data)
    
    html = render_eks_stats(stats)
    html += render_region_tabs_eks(regions_data)
    html += render_region_content_eks(regions_data)
    
    return html