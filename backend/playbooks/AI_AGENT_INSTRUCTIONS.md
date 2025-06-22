# AI Agent Instructions for Ansible Network Automation Templates

## Overview

This document provides comprehensive guidance for AI agents on how to properly structure, fill out, and execute Ansible playbook templates for network device automation in the NetViz Backend infrastructure.

## Infrastructure Context

### Target Environment
- **Operating System**: Ubuntu 22.04 (containerized)
- **Network Services**: FRRouting (FRR) and Open vSwitch (OVS)
- **Container Management**: Docker Compose
- **Authentication**: SSH with password authentication (`ansible123`)
- **Management Network**: 192.168.0.130 with different SSH ports per device

### Device Types and Ports
- **Router (solo_r1/infra_r1)**: Port 7777 - FRRouting service
- **Switch 1 (solo_sw1/infra_sw1)**: Port 7771 - Open vSwitch service  
- **Switch 2 (solo_sw2/infra_sw2)**: Port 7778 - Open vSwitch service
- **Server (solo_ub)**: Port 7780 - Ubuntu server with basic services

## Red Hat Ansible Best Practices Implementation

### 1. Playbook Structure Standards

#### Mandatory Components
```yaml
---
# Header comment block with purpose, target, and metadata
- name: "Descriptive playbook name in Title Case"
  hosts: "{{ target_hosts | default('all') }}"
  gather_facts: true
  become: true
  serial: "{{ batch_size | default(1) }}"
```

#### Variable Organization
- **Template Variables**: Use Jinja2 templating with defaults
- **Inventory Variables**: Reference from host_vars and group_vars
- **Runtime Variables**: Accept via extra-vars or playbook parameters
- **Default Values**: Always provide sensible defaults

### 2. Task Naming and Documentation

#### Task Naming Standards
- Use descriptive names in Title Case with quotes
- Include the purpose and target component
- Example: `"Retrieve FRRouting BGP Configuration"`

#### Documentation Requirements
- Comment blocks explaining complex logic
- Tag all tasks appropriately
- Use ansible.builtin.debug for progress reporting

### 3. Error Handling and Safety

#### Required Safety Measures
```yaml
# Connectivity validation
- name: "Validate target hosts are reachable"
  ansible.builtin.ping:
  register: connectivity_check
  failed_when: false

# Service state verification
- name: "Check service status before operations"
  ansible.builtin.systemd:
    name: "{{ service_name }}"
  register: service_status
  failed_when: false
```

#### Error Recovery Patterns
- Use `block/rescue/always` constructs
- Implement rollback handlers
- Log all failures with timestamps
- Provide meaningful error messages

## Template Usage Guidelines

### Available Templates

#### 1. General Configuration Retrieval Template (`retrieve-template.yml`)
- **Purpose**: Retrieve configurations from devices with mixed services (FRR + OVS)
- **Use Case**: When you need to gather all configurations from a device regardless of service type
- **Best For**: Initial discovery, full system backups, or when device type is unknown

#### 2. FRRouting Configuration Template (`frr-config-retrieval.yml`)
- **Purpose**: Specialized retrieval for FRRouting routers only
- **Use Case**: When targeting routers specifically for routing protocol configurations
- **Best For**: BGP, OSPF, ISIS, RIP configurations and routing table analysis
- **Advantages**: Daemon-aware retrieval, protocol-specific commands, optimized for routing

#### 3. Open vSwitch Configuration Template (`ovs-config-retrieval.yml`)
- **Purpose**: Specialized retrieval for Open vSwitch switches only
- **Use Case**: When targeting switches for flow tables, bridges, and virtual networking
- **Best For**: SDN configurations, flow analysis, bridge management
- **Advantages**: Flow table extraction, per-bridge operations, statistics collection

### Template Selection Logic

```yaml
# Decision tree for template selection
if target_device == "router" or service == "frr":
    use: "frr-config-retrieval.yml"
elif target_device == "switch" or service == "ovs":
    use: "ovs-config-retrieval.yml"
elif target_device == "mixed" or unknown:
    use: "retrieve-template.yml"
```

### Configuration Retrieval Template

#### Required Variables
```yaml
# AI Agent must define these variables
target_hosts: "router_group"  # or specific inventory pattern
config_output_format: "json"  # json, yaml, or text
backup_directory: "/tmp/network_backups/{{ ansible_date_time.epoch }}"
```

#### Variable Customization Examples

##### General Template Variables
```yaml
# For router-only operations
target_hosts: "solo_r1"
config_types:
  - "frr_config"
  - "system_config"

# For switch-only operations  
target_hosts: "solo_sw1,solo_sw2"
config_types:
  - "ovs_config"
  - "interface_config"

# For full infrastructure
target_hosts: "infra"
config_types:
  - "frr_config"
  - "ovs_config"
  - "interface_config"
  - "system_config"
```

##### FRRouting Template Variables
```yaml
# Basic FRR retrieval
target_hosts: "solo_r1"
config_output_format: "json"

# FRR with diagnostics
target_hosts: "routers"
include_diagnostics: true
compress_backup: true

# FRR with custom timeout
target_hosts: "infra_r1"
command_timeout: 60
continue_on_error: true
```

##### Open vSwitch Template Variables
```yaml
# Basic OVS retrieval
target_hosts: "solo_sw1"
config_output_format: "yaml"

# OVS with flow analysis
target_hosts: "switches"
include_flow_details: true
flow_format: "openflow13"

# OVS with statistics
target_hosts: "infra_sw*"
include_statistics: true
stats_interval: 10
compress_backup: true
```

### Configuration Rollback Template

#### Required Variables
```yaml
# Mandatory for rollback operations
rollback_target_timestamp: "1640995200"  # Unix timestamp of backup
target_hosts: "specific_device_or_group"
rollback_types: ["frr_config", "ovs_config"]
```

#### Safety Options
```yaml
# Recommended safety settings
rollback_dry_run: false        # Set true for simulation
backup_before_rollback: true   # Always backup current state
validate_rollback_config: true # Validate before applying
enable_auto_recovery: true     # Auto-recover on failure
```

## FRRouting-Specific Guidance

### Supported FRR Commands
```bash
# Configuration retrieval
vtysh -c 'show running-config'
vtysh -c 'show ip bgp summary'
vtysh -c 'show ip ospf neighbor'
vtysh -c 'show ip route'

# Daemon management
vtysh -c 'show daemons'
vtysh -c 'show version'
```

### FRR Configuration Patterns
- Configuration files located at `/etc/frr/frr.conf`
- Daemon configuration at `/etc/frr/daemons`
- Service name: `frr`
- User/group: `frr:frr`
- File permissions: `0640`

## Open vSwitch-Specific Guidance

### Supported OVS Commands
```bash
# Configuration retrieval
ovs-vsctl show
ovs-vsctl list bridge
ovs-vsctl list port
ovs-vsctl list interface
ovs-ofctl dump-flows <bridge_name>

# Version information
ovs-vsctl --version
```

### OVS Configuration Patterns
- Service name: `openvswitch-switch`
- Database location: `/etc/openvswitch/conf.db`
- Bridge management via ovs-vsctl commands
- Flow management via ovs-ofctl commands

## AI Agent Decision Matrix

### When to Use Which Template

| Scenario | Template | Required Variables |
|----------|----------|-------------------|
| Backup all devices (mixed) | retrieve-template.yml | `target_hosts: "all"` |
| Backup routers only | frr-config-retrieval.yml | `target_hosts: "routers"` |
| Backup switches only | ovs-config-retrieval.yml | `target_hosts: "switches"` |
| Analyze BGP configurations | frr-config-retrieval.yml | `target_hosts: "router_group"`, `include_diagnostics: true` |
| Extract flow tables | ovs-config-retrieval.yml | `target_hosts: "switch_group"`, `include_flow_details: true` |
| Quick router check | frr-config-retrieval.yml | `target_hosts: "solo_r1"`, `compress_backup: false` |
| Full switch analysis | ovs-config-retrieval.yml | `target_hosts: "solo_sw1"`, `include_statistics: true` |
| Rollback router config | rollback-configs | `target_hosts: "solo_r1"`, `rollback_target_timestamp` |
| Emergency rollback | rollback-configs | `rollback_dry_run: false`, `enable_auto_recovery: true` |
| Configuration validation | rollback-configs | `rollback_dry_run: true` |

### Variable Selection Logic

#### 1. Host Targeting
```yaml
# Single device operations
target_hosts: "solo_r1"           # Specific router
target_hosts: "solo_sw1"          # Specific switch
target_hosts: "solo_ub"           # Specific server

# Group operations
target_hosts: "infra"             # All infrastructure devices
target_hosts: "routers"           # All routers
target_hosts: "switches"          # All switches

# Pattern matching
target_hosts: "solo_*"            # All solo devices
target_hosts: "infra_sw*"         # All infrastructure switches
```

#### 2. Operation Scope
```yaml
# Full configuration backup/rollback
rollback_types:
  - "frr_config"
  - "ovs_config"
  - "interface_config"

# Service-specific operations
rollback_types:
  - "frr_config"      # Only FRRouting

rollback_types:
  - "ovs_config"      # Only Open vSwitch
```

#### 3. Safety and Performance
```yaml
# Conservative approach (recommended)
batch_size: 1                     # One device at a time
rollback_dry_run: true           # Test first
validate_rollback_config: true   # Always validate
backup_before_rollback: true     # Safety backup

# Aggressive approach (use with caution)
batch_size: 5                    # Multiple devices
rollback_dry_run: false          # Execute directly
auto_recovery_on_failure: true   # Auto-recover
```

## Execution Workflows

### Standard Configuration Backup
1. Validate connectivity to target hosts
2. Detect device types and running services
3. Retrieve configurations based on detected services
4. Store configurations in structured format
5. Generate summary reports and logs

### Standard Configuration Rollback
1. Validate prerequisites and backup availability
2. Create pre-rollback backup of current state
3. Validate target configuration syntax
4. Stop affected services
5. Apply configuration changes
6. Restart services
7. Verify successful rollback
8. Generate reports and logs

### Error Handling Workflow
1. Detect failure condition
2. Log error details with context
3. Attempt automatic recovery if enabled
4. Notify about failure and recovery status
5. Provide recommended next steps

## Integration with NetViz Backend

### Inventory Integration
- Use existing inventory structure from `hosts/hosts.md`
- Reference device groups: `solo_*`, `infra_*`
- Leverage group variables for common settings

### Logging and Monitoring
- All operations logged to timestamped directories
- Integration points for OpenSearch logging
- Status reporting for monitoring systems

### API Integration
- Playbooks designed for programmatic execution
- JSON/YAML output formats for API consumption
- Structured error reporting

## Common Patterns and Examples

### Example 1: FRRouting BGP Analysis
```yaml
# Analyze BGP configurations on all routers
ansible-playbook retrieve-configs/frr-config-retrieval.yml \
  -e target_hosts=routers \
  -e include_diagnostics=true \
  -e config_output_format=json \
  -e compress_backup=true
```

### Example 2: Open vSwitch Flow Table Extraction
```yaml
# Extract flow tables from specific switches
ansible-playbook retrieve-configs/ovs-config-retrieval.yml \
  -e target_hosts="solo_sw1,solo_sw2" \
  -e include_flow_details=true \
  -e flow_format=openflow13 \
  -e include_statistics=true
```

### Example 3: Mixed Infrastructure Backup
```yaml
# Backup all devices with appropriate service detection
ansible-playbook retrieve-configs/retrieve-template.yml \
  -e target_hosts=all \
  -e config_output_format=yaml \
  -e store_configs_locally=true
```

### Example 4: Emergency Router Rollback
```yaml
# Execute emergency rollback of router configuration
ansible-playbook rollback-configs/rollback-template.yml \
  -e target_hosts=solo_r1 \
  -e rollback_target_timestamp=1640995200 \
  -e rollback_types='["frr_config"]' \
  -e rollback_dry_run=false \
  -e enable_auto_recovery=true
```

### Example 5: Switch Configuration Validation
```yaml
# Validate OVS configuration without changes
ansible-playbook retrieve-configs/ovs-config-retrieval.yml \
  -e target_hosts=solo_sw1 \
  -e include_flow_details=false \
  -e include_statistics=false \
  -e command_timeout=10
```

## Troubleshooting Guide

### Common Issues and Solutions

#### SSH Connection Failures
- Verify host connectivity: `ansible all -m ping`
- Check SSH key authentication
- Validate inventory host definitions
- Confirm container status: `docker ps`

#### Service Detection Issues
- Verify service names match target environment
- Check service status manually: `systemctl status frr`
- Validate container service configuration

#### Configuration Syntax Errors
- Use dry-run mode for validation
- Check FRR syntax: `vtysh --dry-run -f config_file`
- Validate OVS commands before execution

#### Rollback Failures
- Review pre-rollback backup creation
- Verify backup file integrity and format
- Check service restart status and logs
- Use auto-recovery for critical failures

## Security Considerations

### Authentication and Authorization
- Use secure authentication methods in production
- Implement proper privilege escalation
- Rotate credentials regularly
- Use Ansible Vault for sensitive data

### Network Security
- Validate configuration changes don't break connectivity
- Test rollback procedures in non-production first
- Implement change approval workflows
- Monitor for unauthorized configuration changes

### Audit and Compliance
- Maintain detailed logs of all operations
- Implement configuration drift detection
- Regular backup verification
- Document all changes and their rationale

## Performance Optimization

### Execution Efficiency
- Use appropriate batch sizes for parallel execution
- Minimize fact gathering when not needed
- Cache frequently accessed data
- Use tags for selective task execution

### Resource Management
- Monitor disk space for backup operations
- Implement backup retention policies
- Optimize network bandwidth usage
- Balance speed vs. safety requirements

## Template-Specific Best Practices

### FRRouting Template Best Practices
1. **Always check daemon status first** - Not all routing protocols may be enabled
2. **Use appropriate timeouts** - BGP commands can take longer on large networks
3. **Include diagnostics for troubleshooting** - Memory and CPU usage help identify issues
4. **Compress large routing tables** - BGP full tables can be very large

### Open vSwitch Template Best Practices
1. **Discover bridges before flow operations** - Flows are per-bridge
2. **Use correct OpenFlow version** - Match your controller's version
3. **Include statistics for performance analysis** - Port stats reveal bottlenecks
4. **Backup the OVSDB** - Critical for full restoration

### General Template Best Practices
1. **Use for initial discovery** - When device types are unknown
2. **Good for mixed environments** - Handles both FRR and OVS gracefully
3. **Lighter weight than specialized** - Fewer detailed commands

## AI Agent Workflow Recommendations

### Discovery Workflow
1. Start with general template to identify device types
2. Use specialized templates for detailed analysis
3. Store results with appropriate naming conventions

### Analysis Workflow
1. Use FRR template for routing protocol analysis
2. Use OVS template for flow and bridge analysis
3. Correlate results across device types

### Backup Workflow
1. Run specialized templates for each device type
2. Compress and archive results
3. Maintain backup rotation policy

This guide ensures AI agents can effectively utilize the network automation templates while maintaining high standards of reliability, security, and operational excellence. 