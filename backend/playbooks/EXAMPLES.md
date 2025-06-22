# Ansible Template Usage Examples for LLM Agents

## Quick Reference - Template Selection

### When to Use Each Template

| Task | Template | Reason |
|------|----------|--------|
| Gather router BGP/OSPF configs | `frr-config-retrieval.yml` | Specialized for routing protocols |
| Analyze switch flow tables | `ovs-config-retrieval.yml` | Optimized for OVS operations |
| Unknown device type | `retrieve-template.yml` | Auto-detects services |
| Mixed FRR+OVS device | `retrieve-template.yml` | Handles both services |

## Configuration Backup Examples

### FRRouting-Specific Backups

#### Backup Single Router with BGP Analysis
```bash
ansible-playbook retrieve-configs/frr-config-retrieval.yml \
  -e target_hosts=solo_r1 \
  -e include_diagnostics=true \
  -e config_output_format=json
```

#### Backup All Routers with Compression
```bash
ansible-playbook retrieve-configs/frr-config-retrieval.yml \
  -e target_hosts=routers \
  -e compress_backup=true \
  -e backup_directory=/opt/frr_backups/$(date +%s)
```

### Open vSwitch-Specific Backups

#### Extract Switch Flow Tables
```bash
ansible-playbook retrieve-configs/ovs-config-retrieval.yml \
  -e target_hosts=solo_sw1 \
  -e include_flow_details=true \
  -e flow_format=openflow13
```

#### Full Switch Analysis with Statistics
```bash
ansible-playbook retrieve-configs/ovs-config-retrieval.yml \
  -e target_hosts="solo_sw1,solo_sw2" \
  -e include_statistics=true \
  -e include_flow_details=true \
  -e compress_backup=true
```

### General Template Backups

#### Backup Unknown Device Type
```bash
ansible-playbook retrieve-configs/retrieve-template.yml \
  -e target_hosts=new_device \
  -e config_output_format=json
```

#### Backup Mixed Infrastructure
```bash
ansible-playbook retrieve-configs/retrieve-template.yml \
  -e target_hosts=infra \
  -e config_output_format=yaml \
  -e backup_directory=/opt/backups/$(date +%s)
```

### Configuration Rollback Examples

#### Emergency Router Rollback
```bash
ansible-playbook rollback-configs/rollback-template.yml \
  -e target_hosts=solo_r1 \
  -e rollback_target_timestamp=1640995200 \
  -e rollback_types='["frr_config"]' \
  -e rollback_dry_run=false
```

#### Safe Switch Rollback (Test First)
```bash
# Test first
ansible-playbook rollback-configs/rollback-template.yml \
  -e target_hosts=solo_sw1 \
  -e rollback_target_timestamp=1640995200 \
  -e rollback_dry_run=true

# Execute if test passes
ansible-playbook rollback-configs/rollback-template.yml \
  -e target_hosts=solo_sw1 \
  -e rollback_target_timestamp=1640995200 \
  -e rollback_dry_run=false
```

#### Infrastructure-Wide Rollback
```bash
ansible-playbook rollback-configs/rollback-template.yml \
  -e target_hosts=infra \
  -e rollback_target_timestamp=1640995200 \
  -e rollback_batch_size=1 \
  -e backup_before_rollback=true
```

## Variable Configuration Examples

### Conservative (Production)
```yaml
target_hosts: "infra"
rollback_dry_run: true
backup_before_rollback: true
validate_rollback_config: true
verify_rollback_success: true
enable_auto_recovery: true
batch_size: 1
rollback_service_delay: 15
```

### Aggressive (Testing)
```yaml
target_hosts: "solo_*"
rollback_dry_run: false
backup_before_rollback: false
validate_rollback_config: false
batch_size: 5
rollback_service_delay: 5
```

## Device-Specific Targeting

| Device Group | Hosts | Purpose |
|--------------|-------|---------|
| `solo_r1` | Single router | Individual router ops |
| `solo_sw1,solo_sw2` | Both switches | Switch operations |
| `solo_ub` | Ubuntu server | Server operations |
| `infra` | All infrastructure | Full network ops |

## Common AI Agent Patterns

### Pattern 1: Router Protocol Analysis
```yaml
# Analyze routing protocols on FRR routers
playbook: "frr-config-retrieval.yml"
variables:
  target_hosts: "routers"
  include_diagnostics: true
  config_output_format: "json"
  compress_backup: false  # Keep uncompressed for analysis
```

### Pattern 2: Switch Flow Monitoring
```yaml
# Monitor flow tables on OVS switches
playbook: "ovs-config-retrieval.yml"
variables:
  target_hosts: "switches"
  include_flow_details: true
  include_statistics: true
  flow_format: "openflow13"
  backup_directory: "/opt/flow_analysis/{{ ansible_date_time.epoch }}"
```

### Pattern 3: Emergency Configuration Backup
```yaml
# Quick backup before major change
playbook: "retrieve-template.yml"  # Use general for speed
variables:
  target_hosts: "{{ devices_to_change }}"
  config_output_format: "json"
  store_configs_locally: true
  # Skip detailed analysis for speed
```

### Pattern 4: Scheduled Infrastructure Backup
```yaml
# Nightly comprehensive backup
playbook_sequence:
  - playbook: "frr-config-retrieval.yml"
    variables:
      target_hosts: "routers"
      compress_backup: true
  - playbook: "ovs-config-retrieval.yml"
    variables:
      target_hosts: "switches"
      compress_backup: true
```

### Pattern 5: Troubleshooting Data Collection
```yaml
# Collect diagnostics for issue analysis
router_diagnostics:
  playbook: "frr-config-retrieval.yml"
  variables:
    target_hosts: "{{ problem_router }}"
    include_diagnostics: true
    command_timeout: 60  # Allow more time

switch_diagnostics:
  playbook: "ovs-config-retrieval.yml"
  variables:
    target_hosts: "{{ problem_switch }}"
    include_statistics: true
    include_flow_details: true
```

## LLM Agent Decision Examples

### Scenario 1: "Backup all BGP configurations"
```bash
# Agent should choose FRR template for BGP-specific task
ansible-playbook retrieve-configs/frr-config-retrieval.yml \
  -e target_hosts=routers \
  -e include_diagnostics=false \
  -e config_output_format=json
```

### Scenario 2: "Analyze switch performance issues"
```bash
# Agent should choose OVS template with statistics
ansible-playbook retrieve-configs/ovs-config-retrieval.yml \
  -e target_hosts="{{ affected_switches }}" \
  -e include_statistics=true \
  -e include_flow_details=true \
  -e stats_interval=5
```

### Scenario 3: "Backup entire network before maintenance"
```bash
# Agent should run both specialized templates
# First routers
ansible-playbook retrieve-configs/frr-config-retrieval.yml \
  -e target_hosts=routers \
  -e compress_backup=true

# Then switches
ansible-playbook retrieve-configs/ovs-config-retrieval.yml \
  -e target_hosts=switches \
  -e compress_backup=true
```

## Error Handling Examples

### Handle Service Not Running
```yaml
# If FRR service check fails, skip gracefully
continue_on_error: true
ignore_command_errors: true
```

### Handle Command Timeouts
```yaml
# For large BGP tables or complex flows
command_timeout: 120  # 2 minutes
frr_command_timeout: 180  # 3 minutes for BGP
ovs_command_timeout: 60   # 1 minute for flows
```

This guide provides practical examples for LLM agents to implement network automation tasks effectively using the appropriate specialized templates. 