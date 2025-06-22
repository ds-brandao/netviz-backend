# Lightweight Monitoring System

This monitoring system provides a minimal-footprint solution for tracking server resources and Docker containers, sending metrics directly to OpenSearch without requiring heavy monitoring agents.

## Overview

The monitoring system consists of two main components:

- **lightweight-monitor.sh**: The core monitoring script that collects and sends metrics
- **install-lightweight.sh**: Installation script that sets up the monitoring as a systemd service

## How It Works

### 1. Installation Process

The `install-lightweight.sh` script:

- Installs required dependencies (curl, net-tools)
- Copies the monitoring script to `/usr/local/bin/lightweight-monitor`
- Creates a systemd service for automatic startup and management
- Enables and starts the monitoring service
- Verifies that metrics are being sent to OpenSearch

### 2. Metrics Collection

The monitoring script collects metrics every 30 seconds:

#### System Metrics

- **CPU Usage**: Calculated from `/proc/stat`
- **Memory Usage**: Total, used, and percentage from `free` command
- **Disk Usage**: Root filesystem usage percentage
- **Load Average**: 1-minute load average from `/proc/loadavg`
- **System Uptime**: Seconds since boot

#### Docker Metrics

- **Container CPU Usage**: Per-container CPU percentage
- **Container Memory Usage**: Per-container memory percentage
- **Container Status**: Running status of each container

#### Service Health Checks

- **SSH Service**: Checks if SSH is listening on port 22
- **Docker Service**: Verifies Docker daemon is running

### 3. Data Storage

All metrics are sent to OpenSearch at `192.168.0.132:9200` with:
- Index pattern: `system-metrics-YYYY.MM.DD` (daily indices)
- Authentication: Basic auth with provided credentials
- SSL/TLS: Secure connection (self-signed certificates accepted)

## Data Format

Each metric is stored as a JSON document with:

- `@timestamp`: UTC timestamp
- `host.name`: Server hostname
- `metric_type`: Type of metric (system, docker, or service_health)
- Metric-specific fields based on type

## Usage

### Service Management

```bash
# Check service status
sudo systemctl status lightweight-monitor

# View real-time logs
sudo journalctl -u lightweight-monitor -f

# Stop monitoring
sudo systemctl stop lightweight-monitor

# Restart monitoring
sudo systemctl restart lightweight-monitor
```

### Querying Data in OpenSearch

```bash
# View all monitoring indices
curl -sk -u admin:xuwzuc-rExzo3-hotjed \
  'https://192.168.0.132:9200/_cat/indices/system-metrics-*?v'

# Get latest metrics
curl -sk -u admin:xuwzuc-rExzo3-hotjed \
  'https://192.168.0.132:9200/system-metrics-*/_search?size=1&pretty'

# Query specific metric types
curl -sk -u admin:xuwzuc-rExzo3-hotjed \
  'https://192.168.0.132:9200/system-metrics-*/_search?q=metric_type:docker&pretty'
```

## Benefits

- **Lightweight**: Minimal resource usage with bash-based collection
- **No Agent Required**: Direct HTTP posts to OpenSearch
- **Automatic**: Runs as systemd service with auto-restart
- **Comprehensive**: Covers system resources, Docker containers, and service health
- **Simple**: Easy to modify and extend for additional metrics