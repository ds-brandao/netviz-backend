# Metricbeat Monitoring for Ubuntu Server and Docker Containers

This directory contains configuration and setup scripts for monitoring your Ubuntu server and Docker containers using Metricbeat with OpenSearch.

## Overview

Metricbeat is a lightweight shipper for collecting and shipping system and service metrics. It's part of the Elastic Beat family and works seamlessly with OpenSearch.

### What Gets Monitored

**System Metrics:**
- CPU usage (per core and total)
- Memory usage and statistics
- Disk I/O and filesystem usage
- Network statistics
- Process information
- System load and uptime

**Docker Metrics:**
- Container status and health
- Container CPU and memory usage
- Container network I/O
- Container disk I/O
- Container events and lifecycle

## Files in This Directory

- `metricbeat.yml` - Main Metricbeat configuration
- `docker-compose.metricbeat.yml` - Docker Compose file for containerized deployment
- `setup-metricbeat.sh` - Installation and setup script
- `opensearch-monitors.json` - Example OpenSearch alerting monitors
- `README.md` - This documentation

## Installation Options

### Option 1: Install on Host (Recommended for Production)

```bash
sudo chmod +x setup-metricbeat.sh
sudo ./setup-metricbeat.sh
# Choose option 1
```

**Advantages:**
- Lower overhead
- Direct access to system metrics
- Runs as a system service
- Better for production environments

### Option 2: Run in Docker Container

```bash
sudo chmod +x setup-metricbeat.sh
sudo ./setup-metricbeat.sh
# Choose option 2
```

**Advantages:**
- Easier to deploy and manage
- No system-wide installation needed
- Good for testing and development

## Configuration Details

### Key Configuration Settings

The `metricbeat.yml` file is pre-configured with:

1. **System Module** - Collects host metrics every 10 seconds
2. **Docker Module** - Monitors all Docker containers
3. **OpenSearch Output** - Sends data to your OpenSearch instance
4. **Performance Optimizations**:
   - Drops paused/exited containers
   - Uses bulk operations
   - Compresses data
   - Single shard indices

### OpenSearch Connection

The configuration uses the same OpenSearch instance as your Fluent Bit setup:
- Host: `192.168.0.132`
- Port: `9200`
- Protocol: `HTTPS`
- Authentication: Basic Auth
- SSL Verification: Disabled (for self-signed certificates)

## Verifying the Installation

### 1. Check Metricbeat Status

**For Host Installation:**
```bash
sudo systemctl status metricbeat
sudo journalctl -u metricbeat -f
```

**For Docker Installation:**
```bash
docker ps | grep metricbeat
docker logs -f metricbeat
```

### 2. Verify Data in OpenSearch

Check if indices are created:
```bash
curl -sk -u admin:xuwzuc-rExzo3-hotjed \
  'https://192.168.0.132:9200/_cat/indices/metricbeat-*?v'
```

Query sample data:
```bash
curl -sk -u admin:xuwzuc-rExzo3-hotjed \
  'https://192.168.0.132:9200/metricbeat-*/_search?size=1&pretty'
```

### 3. Check Specific Metrics

**System CPU:**
```bash
curl -sk -u admin:xuwzuc-rExzo3-hotjed \
  'https://192.168.0.132:9200/metricbeat-*/_search?pretty' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "term": {
        "metricset.name": "cpu"
      }
    },
    "size": 1
  }'
```

**Docker Container Status:**
```bash
curl -sk -u admin:xuwzuc-rExzo3-hotjed \
  'https://192.168.0.132:9200/metricbeat-*/_search?pretty' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "term": {
        "metricset.name": "container"
      }
    },
    "size": 5
  }'
```

## Setting Up Alerts

### 1. Create Alert Destination

First, create a destination in OpenSearch for alerts:

```bash
curl -sk -u admin:xuwzuc-rExzo3-hotjed \
  -X POST 'https://192.168.0.132:9200/_plugins/_alerting/destinations' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "my-alert-destination",
    "type": "custom_webhook",
    "custom_webhook": {
      "url": "https://your-webhook-url.com/alerts",
      "method": "POST",
      "header_params": {
        "Content-Type": "application/json"
      }
    }
  }'
```

### 2. Import Monitor Templates

The `opensearch-monitors.json` file contains pre-configured monitors for:
- Container health status
- High CPU usage
- High memory usage
- Low disk space
- Container restart loops

To import them, update the `destination_id` in the file and use the OpenSearch API or Dashboards UI.

### 3. Example: Create Container Health Monitor via API

```bash
curl -sk -u admin:xuwzuc-rExzo3-hotjed \
  -X POST 'https://192.168.0.132:9200/_plugins/_alerting/monitors' \
  -H 'Content-Type: application/json' \
  -d @opensearch-monitors.json
```

## Visualizations in OpenSearch Dashboards

### Creating a Dashboard

1. Access OpenSearch Dashboards: `https://192.168.0.132:5601`
2. Go to **Visualize** → **Create visualization**
3. Select index pattern: `metricbeat-*`

### Recommended Visualizations

1. **System Overview**:
   - CPU usage gauge
   - Memory usage gauge
   - Disk usage table
   - Network I/O line chart

2. **Docker Container Dashboard**:
   - Container status table
   - Container CPU/Memory usage
   - Container network traffic
   - Container health timeline

3. **Host Metrics Timeline**:
   - CPU usage over time
   - Memory usage over time
   - Disk I/O over time
   - Network traffic over time

## Performance Tuning

### Reduce Metric Collection Frequency

Edit `metricbeat.yml` and change the `period`:
```yaml
period: 30s  # Instead of 10s
```

### Disable Unused Metricsets

Comment out metricsets you don't need:
```yaml
metricsets:
  - cpu
  - memory
  # - process  # Disable if not needed
  # - socket_summary  # Disable if not needed
```

### Optimize Docker Monitoring

For many containers, consider:
```yaml
- module: docker
  metricsets:
    - container
    - cpu
    - memory
    # Remove detailed metricsets if not needed
  period: 30s  # Longer interval
```

## Troubleshooting

### Metricbeat Not Starting

1. Check logs:
   ```bash
   sudo journalctl -u metricbeat -n 50
   ```

2. Test configuration:
   ```bash
   sudo metricbeat test config
   sudo metricbeat test output
   ```

### No Data in OpenSearch

1. Verify connectivity:
   ```bash
   curl -sk -u admin:xuwzuc-rExzo3-hotjed \
     'https://192.168.0.132:9200'
   ```

2. Check Metricbeat output:
   ```bash
   sudo metricbeat -e -d "*"
   ```

### High Resource Usage

1. Increase collection period
2. Reduce number of metricsets
3. Enable filtering to exclude certain processes/containers

### Docker Permission Issues

Ensure Metricbeat can access Docker socket:
```bash
sudo usermod -aG docker metricbeat
sudo chmod 666 /var/run/docker.sock
```

## Integration with Your Network Monitoring

This Metricbeat setup complements your existing Fluent Bit log monitoring:

- **Fluent Bit**: Collects and ships logs from your network components
- **Metricbeat**: Collects performance metrics and health status

Together, they provide comprehensive observability of your infrastructure.

## Maintenance

### Index Lifecycle Management

Create a policy to manage Metricbeat indices:

```bash
curl -sk -u admin:xuwzuc-rExzo3-hotjed \
  -X PUT 'https://192.168.0.132:9200/_opendistro/_ism/policies/metricbeat-policy' \
  -H 'Content-Type: application/json' \
  -d '{
    "policy": {
      "description": "Metricbeat index lifecycle",
      "default_state": "hot",
      "states": [{
        "name": "hot",
        "actions": [],
        "transitions": [{
          "state_name": "delete",
          "conditions": {
            "min_index_age": "7d"
          }
        }]
      }, {
        "name": "delete",
        "actions": [{
          "delete": {}
        }]
      }]
    }
  }'
```

Apply to indices:
```bash
curl -sk -u admin:xuwzuc-rExzo3-hotjed \
  -X PUT 'https://192.168.0.132:9200/metricbeat-*/_settings' \
  -H 'Content-Type: application/json' \
  -d '{
    "index.opendistro.index_state_management.policy_id": "metricbeat-policy"
  }'
```

## Additional Resources

- [Metricbeat Documentation](https://www.elastic.co/guide/en/beats/metricbeat/current/index.html)
- [OpenSearch Alerting](https://opensearch.org/docs/latest/observing-your-data/alerting/index/)
- [OpenSearch Dashboards](https://opensearch.org/docs/latest/dashboards/index/) 