# OpenSearch Setup and Log Querying Guide

## Overview

This guide covers the OpenSearch setup for the NetViz backend, including Docker configuration, log ingestion, and querying capabilities.

## Services Running

### Docker Services
- **PostgreSQL**: `localhost:5432` - Main database
- **OpenSearch**: `localhost:9200` - Log storage and search
- **OpenSearch Dashboards**: `localhost:5601` - Web UI for log visualization

### Service Status
Check all services are running:
```bash
docker ps
```

Expected output should show:
- `netviz_postgres` (healthy)
- `netviz_opensearch` (healthy) 
- `netviz_opensearch_dashboards` (health: starting/healthy)

## OpenSearch Configuration

### Index Structure
- **Index Name**: `network-logs`
- **Document Structure**:
  ```json
  {
    "timestamp": "2025-06-22T12:03:33.3NZ",
    "level": "INFO|WARN|ERROR",
    "service": "netviz-backend",
    "message": "Log message content",
    "node_id": "device-identifier",
    "event_type": "websocket_connect|device_update|connection_error|performance_alert",
    "metadata": {
      "device_id": "device-001",
      "custom_field": "value"
    }
  }
  ```

### Field Mappings
- `level`: Text with keyword subfield for exact matching
- `timestamp`: Date field for time-based queries
- `metadata`: Object with dynamic properties
- All text fields have `.keyword` subfields for exact matching

## Querying Logs

### Using the Python Script

The `query_logs.py` script provides a convenient interface for querying OpenSearch logs:

#### Basic Usage
```bash
# Get 10 most recent logs
python query_logs.py

# Get 20 most recent logs
python query_logs.py --size 20

# Get logs with metadata details
python query_logs.py --metadata --size 5
```

#### Filter by Log Level
```bash
# Get only ERROR logs
python query_logs.py --level ERROR

# Get ERROR and WARN logs
python query_logs.py --level ERROR WARN

# Get ERROR/WARN logs with metadata
python query_logs.py --level ERROR WARN --metadata
```

#### Search by Content
```bash
# Search for logs containing "device"
python query_logs.py --search "device"

# Search for connection-related logs
python query_logs.py --search "connection"
```

#### Filter by Event Type
```bash
# Get only websocket connection events
python query_logs.py --event-type websocket_connect

# Get device update events
python query_logs.py --event-type device_update
```

#### Filter by Node/Device
```bash
# Get logs for specific device
python query_logs.py --node-id test-device-001

# Get logs for specific device with metadata
python query_logs.py --node-id switch-003 --metadata
```

#### Time-based Queries
```bash
# Get logs from last 30 minutes
python query_logs.py --recent 30

# Get error logs from last 24 hours
python query_logs.py --errors 24

# Get logs from last 2 hours
python query_logs.py --time-range 2h
```

#### Output Formats
```bash
# Human-readable format (default)
python query_logs.py --level ERROR

# Raw JSON output
python query_logs.py --level ERROR --json
```

### Direct curl Commands

#### Get All Logs
```bash
curl -X GET "http://localhost:9200/network-logs/_search" -H 'Content-Type: application/json' -d '{
  "query": {"match_all": {}},
  "sort": [{"timestamp": {"order": "desc"}}],
  "size": 10
}' | python -m json.tool
```

#### Filter by Log Level
```bash
curl -X GET "http://localhost:9200/network-logs/_search" -H 'Content-Type: application/json' -d '{
  "query": {
    "terms": {
      "level.keyword": ["ERROR", "WARN"]
    }
  },
  "sort": [{"timestamp": {"order": "desc"}}],
  "size": 5
}' | python -m json.tool
```

#### Search by Message Content
```bash
curl -X GET "http://localhost:9200/network-logs/_search" -H 'Content-Type: application/json' -d '{
  "query": {
    "multi_match": {
      "query": "device",
      "fields": ["message", "event_type", "node_id"]
    }
  },
  "sort": [{"timestamp": {"order": "desc"}}],
  "size": 5
}' | python -m json.tool
```

## OpenSearch Dashboards Web UI

Access the web interface at: `http://localhost:5601`

### Initial Setup
1. Open browser to `http://localhost:5601`
2. Go to "Stack Management" → "Index Patterns"
3. Create index pattern: `network-logs*`
4. Set time field: `timestamp`

### Creating Visualizations
1. Go to "Discover" to explore logs
2. Use "Visualize" to create charts and graphs
3. Build dashboards in "Dashboard" section

## Log Ingestion

### Adding New Logs
```bash
curl -X POST "http://localhost:9200/network-logs/_doc" -H 'Content-Type: application/json' -d '{
  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
  "level": "INFO",
  "service": "netviz-backend",
  "message": "Your log message here",
  "node_id": "device-id",
  "event_type": "custom_event",
  "metadata": {
    "custom_field": "value"
  }
}'
```

### Refresh Index
After adding logs, refresh the index to make them searchable:
```bash
curl -X POST "http://localhost:9200/network-logs/_refresh"
```

## Maintenance Commands

### Check Index Status
```bash
curl -s "http://localhost:9200/_cat/indices?v"
```

### Check Cluster Health
```bash
curl -s "http://localhost:9200/_cluster/health" | python -m json.tool
```

### View Index Mapping
```bash
curl -X GET "http://localhost:9200/network-logs/_mapping" | python -m json.tool
```

### Delete Index (if needed)
```bash
curl -X DELETE "http://localhost:9200/network-logs"
```

## Troubleshooting

### Services Not Starting
1. Check Docker is running: `docker --version`
2. Check available memory: OpenSearch requires sufficient RAM
3. Restart services: `docker-compose restart opensearch opensearch-dashboards`

### Connection Issues
1. Verify services are healthy: `docker ps`
2. Check ports are not in use: `lsof -i :9200` and `lsof -i :5601`
3. Check logs: `docker logs netviz_opensearch`

### Query Issues
1. Ensure index exists: `curl -s "http://localhost:9200/_cat/indices?v"`
2. Check field mappings for correct field names
3. Use `.keyword` subfields for exact text matching
4. Refresh index after adding new documents

## Sample Log Entries

The system currently has these sample log types:
- **WebSocket connections**: Session establishment and management
- **Device updates**: External device status changes
- **Connection errors**: Network device connectivity issues
- **Performance alerts**: CPU/memory threshold violations

Each log entry includes structured metadata for detailed analysis and filtering. 