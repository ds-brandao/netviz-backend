# Ansible Template Variable Reference Guide

This document provides a comprehensive reference for all variables used in the NetViz Backend Ansible playbook templates.

## Table of Contents
- [Host Targeting Variables](#host-targeting-variables)
- [Configuration Retrieval Variables](#configuration-retrieval-variables)
- [FRRouting-Specific Variables](#frrouting-specific-variables)
- [Open vSwitch-Specific Variables](#open-vswitch-specific-variables)
- [Configuration Rollback Variables](#configuration-rollback-variables)
- [Service Management Variables](#service-management-variables)
- [Safety and Validation Variables](#safety-and-validation-variables)
- [Error Handling Variables](#error-handling-variables)
- [Output and Storage Variables](#output-and-storage-variables)
- [Performance and Execution Variables](#performance-and-execution-variables)

## Host Targeting Variables

### target_hosts
- **Type**: String or List
- **Default**: `"all"`
- **Purpose**: Specifies which hosts to target for operations
- **Examples**:
  ```yaml
  target_hosts: "solo_r1"              # Single router
  target_hosts: "infra"                # All infrastructure devices
  target_hosts: "solo_sw1,solo_sw2"    # Multiple specific devices
  target_hosts: "routers:switches"     # Multiple groups
  ```

### batch_size / rollback_batch_size
- **Type**: Integer
- **Default**: `1`
- **Purpose**: Number of hosts to process simultaneously
- **Usage**:
  ```yaml
  batch_size: 1          # Conservative, one at a time
  batch_size: 3          # Moderate parallelism
  batch_size: 5          # Aggressive parallelism (use with caution)
  ```

## Configuration Retrieval Variables

### backup_timestamp
- **Type**: String (Unix timestamp)
- **Default**: `"{{ ansible_date_time.epoch }}"`
- **Purpose**: Timestamp for backup identification
- **Auto-generated**: Yes
- **Usage**: Used internally for backup directory naming

### backup_directory
- **Type**: String (Path)
- **Default**: `"/tmp/network_backups/{{ backup_timestamp }}"`
- **Purpose**: Directory where configuration backups are stored
- **Customizable**: Yes
- **Examples**:
  ```yaml
  backup_directory: "/opt/netbackups/{{ ansible_date_time.epoch }}"
  backup_directory: "/mnt/shared/configs/backup_{{ ansible_date_time.date }}"
  ```

### config_types
- **Type**: List
- **Default**: `["frr_config", "ovs_config", "interface_config", "system_config"]`
- **Purpose**: Types of configurations to retrieve
- **Options**:
  - `"frr_config"`: FRRouting configuration and state
  - `"ovs_config"`: Open vSwitch database and flows
  - `"interface_config"`: Network interface configuration
  - `"system_config"`: System network configuration

### config_output_format
- **Type**: String
- **Default**: `"json"`
- **Purpose**: Format for configuration output files
- **Options**: `"json"`, `"yaml"`, `"text"`
- **Usage**:
  ```yaml
  config_output_format: "json"    # Machine-readable JSON
  config_output_format: "yaml"    # Human-readable YAML
  config_output_format: "text"    # Plain text format
  ```

### store_configs_locally
- **Type**: Boolean
- **Default**: `true`
- **Purpose**: Whether to store configurations on local controller
- **Usage**:
  ```yaml
  store_configs_locally: true     # Store on Ansible controller
  store_configs_locally: false    # Skip local storage
  ```

### remote_config_storage
- **Type**: String (Path or URL)
- **Default**: `""`
- **Purpose**: Remote storage location for configurations
- **Examples**:
  ```yaml
  remote_config_storage: "s3://bucket/configs"
  remote_config_storage: "/mnt/nfs/network_configs"
  remote_config_storage: "https://api.example.com/configs"
  ```

## FRRouting-Specific Variables

### include_diagnostics
- **Type**: Boolean
- **Default**: `true`
- **Purpose**: Include memory, CPU, and logging diagnostics
- **Template**: `frr-config-retrieval.yml`
- **Usage**:
  ```yaml
  include_diagnostics: true   # Include system diagnostics
  include_diagnostics: false  # Skip diagnostics for faster retrieval
  ```

### compress_frr_backup
- **Type**: Boolean
- **Default**: `false`
- **Purpose**: Compress the FRR backup directory
- **Template**: `frr-config-retrieval.yml`
- **Usage**:
  ```yaml
  compress_frr_backup: true   # Create .tar.gz archive
  compress_frr_backup: false  # Keep uncompressed
  ```

### frr_command_timeout
- **Type**: Integer (seconds)
- **Default**: `30`
- **Purpose**: Timeout for FRR vtysh commands
- **Template**: `frr-config-retrieval.yml`
- **Usage**:
  ```yaml
  frr_command_timeout: 30   # Standard timeout
  frr_command_timeout: 120  # Extended for large BGP tables
  ```

### ignore_command_errors (FRR context)
- **Type**: Boolean
- **Default**: `false`
- **Purpose**: Continue even if some FRR commands fail
- **Template**: `frr-config-retrieval.yml`
- **Usage**:
  ```yaml
  ignore_command_errors: true   # Continue on command failures
  ignore_command_errors: false  # Stop on first error
  ```

## Open vSwitch-Specific Variables

### include_flow_details / include_ovs_flows
- **Type**: Boolean
- **Default**: `true`
- **Purpose**: Include OpenFlow flow table details
- **Template**: `ovs-config-retrieval.yml`
- **Usage**:
  ```yaml
  include_flow_details: true   # Dump all flow tables
  include_flow_details: false  # Skip flow collection
  ```

### include_statistics / include_ovs_stats
- **Type**: Boolean
- **Default**: `true`
- **Purpose**: Include port and queue statistics
- **Template**: `ovs-config-retrieval.yml`
- **Usage**:
  ```yaml
  include_statistics: true   # Collect performance stats
  include_statistics: false  # Skip statistics
  ```

### flow_format / ovs_flow_format
- **Type**: String
- **Default**: `"openflow10"`
- **Purpose**: OpenFlow version for flow dumps
- **Template**: `ovs-config-retrieval.yml`
- **Options**: `"openflow10"`, `"openflow11"`, `"openflow12"`, `"openflow13"`, `"openflow14"`, `"openflow15"`
- **Usage**:
  ```yaml
  flow_format: "openflow10"  # Legacy format
  flow_format: "openflow13"  # Modern SDN controllers
  flow_format: "openflow15"  # Latest features
  ```

### stats_interval / ovs_stats_interval
- **Type**: Integer (seconds)
- **Default**: `5`
- **Purpose**: Interval for statistics collection
- **Template**: `ovs-config-retrieval.yml`
- **Usage**:
  ```yaml
  stats_interval: 5    # Quick snapshot
  stats_interval: 30   # Average over time
  ```

### compress_ovs_backup
- **Type**: Boolean
- **Default**: `false`
- **Purpose**: Compress the OVS backup directory
- **Template**: `ovs-config-retrieval.yml`
- **Usage**:
  ```yaml
  compress_ovs_backup: true   # Create .tar.gz archive
  compress_ovs_backup: false  # Keep uncompressed
  ```

### ovs_command_timeout
- **Type**: Integer (seconds)
- **Default**: `30`
- **Purpose**: Timeout for OVS commands
- **Template**: `ovs-config-retrieval.yml`
- **Usage**:
  ```yaml
  ovs_command_timeout: 30   # Standard timeout
  ovs_command_timeout: 60   # Extended for large flow tables
  ```

## Configuration Rollback Variables

### rollback_target_timestamp
- **Type**: String (Unix timestamp)
- **Required**: Yes (mandatory)
- **Purpose**: Timestamp of the backup to rollback to
- **Usage**:
  ```yaml
  rollback_target_timestamp: "1640995200"    # Specific backup
  rollback_target_timestamp: "{{ backup_id }}"  # From variable
  ```

### rollback_config_source
- **Type**: String (Path)
- **Default**: `"/tmp/network_backups"`
- **Purpose**: Base directory containing configuration backups
- **Usage**:
  ```yaml
  rollback_config_source: "/opt/netbackups"
  rollback_config_source: "/mnt/shared/configs"
  ```

### rollback_types
- **Type**: List
- **Default**: `["frr_config", "ovs_config", "interface_config"]`
- **Purpose**: Types of configurations to rollback
- **Options**: Same as `config_types`
- **Examples**:
  ```yaml
  rollback_types: ["frr_config"]              # Only FRR
  rollback_types: ["ovs_config"]              # Only OVS
  rollback_types: ["frr_config", "ovs_config"] # Both services
  ```

## Service Management Variables

### restart_services / restart_services_after_rollback
- **Type**: Boolean
- **Default**: `true`
- **Purpose**: Whether to restart services after configuration changes
- **Usage**:
  ```yaml
  restart_services_after_rollback: true    # Restart for changes to apply
  restart_services_after_rollback: false   # Manual restart required
  ```

### rollback_service_delay
- **Type**: Integer (seconds)
- **Default**: `10`
- **Purpose**: Delay between service stop/start operations
- **Usage**:
  ```yaml
  rollback_service_delay: 5     # Quick restart (5 seconds)
  rollback_service_delay: 30    # Conservative restart (30 seconds)
  ```

## Safety and Validation Variables

### rollback_dry_run
- **Type**: Boolean
- **Default**: `false`
- **Purpose**: Simulate rollback without applying changes
- **Usage**:
  ```yaml
  rollback_dry_run: true     # Test/simulation mode
  rollback_dry_run: false    # Execute actual rollback
  ```

### backup_before_rollback
- **Type**: Boolean
- **Default**: `true`
- **Purpose**: Create backup of current state before rollback
- **Usage**:
  ```yaml
  backup_before_rollback: true    # Safety backup (recommended)
  backup_before_rollback: false   # Skip backup (faster, riskier)
  ```

### validate_rollback_config
- **Type**: Boolean
- **Default**: `true`
- **Purpose**: Validate configuration syntax before applying
- **Usage**:
  ```yaml
  validate_rollback_config: true    # Validate first (recommended)
  validate_rollback_config: false   # Skip validation (risky)
  ```

### verify_rollback_success
- **Type**: Boolean
- **Default**: `true`
- **Purpose**: Verify services are healthy after rollback
- **Usage**:
  ```yaml
  verify_rollback_success: true    # Verify success (recommended)
  verify_rollback_success: false   # Skip verification
  ```

## Error Handling Variables

### ignore_retrieval_errors
- **Type**: Boolean
- **Default**: `false`
- **Purpose**: Continue execution even if some retrievals fail
- **Usage**:
  ```yaml
  ignore_retrieval_errors: true    # Continue on errors
  ignore_retrieval_errors: false   # Stop on first error
  ```

### config_retrieval_retries
- **Type**: Integer
- **Default**: `3`
- **Purpose**: Number of retry attempts for failed operations
- **Usage**:
  ```yaml
  config_retrieval_retries: 1     # Single retry
  config_retrieval_retries: 5     # Multiple retries
  ```

### config_retrieval_delay
- **Type**: Integer (seconds)
- **Default**: `10`
- **Purpose**: Delay between retry attempts
- **Usage**:
  ```yaml
  config_retrieval_delay: 5      # Quick retry (5 seconds)
  config_retrieval_delay: 30     # Longer delay (30 seconds)
  ```

### enable_auto_recovery
- **Type**: Boolean
- **Default**: `true`
- **Purpose**: Automatically attempt recovery on rollback failure
- **Usage**:
  ```yaml
  enable_auto_recovery: true     # Auto-recover on failure
  enable_auto_recovery: false    # Manual recovery required
  ```

### config_rollback_timeout
- **Type**: Integer (seconds)
- **Default**: `300`
- **Purpose**: Maximum time allowed for rollback operations
- **Usage**:
  ```yaml
  config_rollback_timeout: 120   # 2 minutes timeout
  config_rollback_timeout: 600   # 10 minutes timeout
  ```

### rollback_retries
- **Type**: Integer
- **Default**: `2`
- **Purpose**: Number of rollback retry attempts
- **Usage**:
  ```yaml
  rollback_retries: 1    # Single retry
  rollback_retries: 3    # Multiple retries
  ```

## Output and Storage Variables

### output_format
- **Type**: String
- **Default**: Variable `config_output_format`
- **Purpose**: Format for configuration output
- **Reference**: See `config_output_format`

### store_locally
- **Type**: Boolean
- **Default**: Variable `store_configs_locally`
- **Purpose**: Local storage flag
- **Reference**: See `store_configs_locally`

### remote_storage
- **Type**: String
- **Default**: Variable `remote_config_storage`
- **Purpose**: Remote storage location
- **Reference**: See `remote_config_storage`

## Performance and Execution Variables

### continue_on_error
- **Type**: Boolean
- **Default**: Variable `ignore_retrieval_errors`
- **Purpose**: Continue execution on errors
- **Reference**: See `ignore_retrieval_errors`

### max_retries
- **Type**: Integer
- **Default**: Variable `config_retrieval_retries`
- **Purpose**: Maximum retry attempts
- **Reference**: See `config_retrieval_retries`

### retry_delay
- **Type**: Integer
- **Default**: Variable `config_retrieval_delay`
- **Purpose**: Delay between retries
- **Reference**: See `config_retrieval_delay`

### max_rollback_retries
- **Type**: Integer
- **Default**: Variable `rollback_retries`
- **Purpose**: Maximum rollback retry attempts
- **Reference**: See `rollback_retries`

## Internal Configuration Variables

### frr_config_path
- **Type**: String (Path)
- **Default**: `"/etc/frr/frr.conf"`
- **Purpose**: Path to FRR configuration file
- **Customizable**: Rarely needed

### frr_running_config_cmd
- **Type**: String (Command)
- **Default**: `"vtysh -c 'show running-config'"`
- **Purpose**: Command to retrieve FRR running configuration
- **Customizable**: Rarely needed

### ovs_db_path
- **Type**: String (Path)
- **Default**: `"/etc/openvswitch/conf.db"`
- **Purpose**: Path to OVS database file
- **Customizable**: Rarely needed

## Variable Usage Patterns

### Minimum Required Variables

#### General Template (retrieve-template.yml)
```yaml
# Basic configuration retrieval
target_hosts: "solo_r1"
```

#### FRRouting Template (frr-config-retrieval.yml)
```yaml
# Minimum FRR retrieval
target_hosts: "routers"  # or specific router
# All other variables have sensible defaults
```

#### Open vSwitch Template (ovs-config-retrieval.yml)
```yaml
# Minimum OVS retrieval
target_hosts: "switches"  # or specific switch
# All other variables have sensible defaults
```

#### Rollback Template (rollback-template.yml)
```yaml
# Basic configuration rollback
target_hosts: "solo_r1"
rollback_target_timestamp: "1640995200"
```

### Conservative Safety Configuration
```yaml
# Maximum safety settings
rollback_dry_run: true
backup_before_rollback: true
validate_rollback_config: true
verify_rollback_success: true
enable_auto_recovery: true
batch_size: 1
```

### Performance-Optimized Configuration
```yaml
# Faster execution (use with caution)
batch_size: 3
rollback_service_delay: 5
config_retrieval_retries: 1
config_retrieval_delay: 5
```

### Production-Ready Configurations

#### FRRouting Production Config
```yaml
# Recommended FRR production settings
target_hosts: "routers"
include_diagnostics: true
config_output_format: "json"
compress_frr_backup: true
frr_command_timeout: 60
batch_size: 1
```

#### Open vSwitch Production Config
```yaml
# Recommended OVS production settings
target_hosts: "switches"
include_flow_details: true
include_statistics: true
flow_format: "openflow13"
config_output_format: "json"
compress_ovs_backup: true
ovs_command_timeout: 45
batch_size: 1
```

#### General Template Production Config
```yaml
# Recommended general production settings
target_hosts: "infra"
config_output_format: "json"
store_configs_locally: true
batch_size: 2
continue_on_error: false
```

#### Rollback Production Config
```yaml
# Recommended rollback production settings
target_hosts: "{{ affected_device }}"
rollback_target_timestamp: "{{ verified_backup }}"
backup_before_rollback: true
validate_rollback_config: true
verify_rollback_success: true
enable_auto_recovery: true
rollback_dry_run: true  # Always test first
batch_size: 1
rollback_service_delay: 10
```

## Variable Validation Rules

### Required Variables
- `rollback_target_timestamp` (for rollback operations)

### Mutually Exclusive Variables
- `rollback_dry_run: true` and `verify_rollback_success: true` (verification skipped in dry run)

### Dependent Variables
- `backup_before_rollback: true` requires `store_configs_locally: true` or valid `remote_config_storage`
- `validate_rollback_config: true` requires appropriate service availability

### Range Validations
- `batch_size`: 1-10 (recommended maximum)
- `rollback_service_delay`: 5-60 seconds
- `config_rollback_timeout`: 60-1800 seconds
- `config_retrieval_retries`: 1-10 attempts

## Template-Specific Variable Summary

### FRRouting Template Variables
| Variable | Default | Purpose |
|----------|---------|---------||
| `include_diagnostics` | `true` | System diagnostics |
| `compress_frr_backup` | `false` | Archive creation |
| `frr_command_timeout` | `30` | Command timeout |
| `ignore_command_errors` | `false` | Error handling |

### Open vSwitch Template Variables
| Variable | Default | Purpose |
|----------|---------|---------||
| `include_flow_details` | `true` | Flow table dumps |
| `include_statistics` | `true` | Performance stats |
| `flow_format` | `"openflow10"` | OpenFlow version |
| `stats_interval` | `5` | Stats collection interval |
| `compress_ovs_backup` | `false` | Archive creation |
| `ovs_command_timeout` | `30` | Command timeout |

### Common Variables Across Templates
| Variable | Templates | Purpose |
|----------|-----------|---------||
| `target_hosts` | All | Device targeting |
| `config_output_format` | All retrieval | Output format |
| `backup_directory` | All retrieval | Storage location |
| `batch_size` | All | Parallelism control |
| `command_timeout` | All | General timeout |

This reference guide ensures AI agents understand all available configuration options and can make informed decisions about variable settings based on operational requirements. 