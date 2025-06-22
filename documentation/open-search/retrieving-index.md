# OpenSearch Log Retrieval API Reference

This document provides API reference examples for retrieving logs from OpenSearch indexes created by Fluent Bit. The examples are based on the indexes configured in `fluent-bit.conf`.

## Connection Details

Based on the Fluent Bit configuration:

```
Host: 192.168.0.132
Port: 9200
Protocol: HTTPS
Authentication: Basic Auth
Username: admin
Password: xuwzuc-rExzo3-hotjed
TLS Verify: Disabled
```

## Available Indexes

The following indexes are created by Fluent Bit:
- `client-logs`
- `frr-router-logs`
- `server-logs`
- `switch1-logs`
- `switch2-logs`

## API Examples

### 1. Basic Search - Retrieve All Logs from an Index

Retrieve the latest logs from a specific index:

```bash
curl -X GET "https://192.168.0.132:9200/client-logs/_search?pretty" \
  -H "Content-Type: application/json" \
  -u "admin:xuwzuc-rExzo3-hotjed" \
  -k
```

**Response Example:**
```json
{
  "took": 5,
  "timed_out": false,
  "_shards": {
    "total": 1,
    "successful": 1,
    "skipped": 0,
    "failed": 0
  },
  "hits": {
    "total": {
      "value": 1234,
      "relation": "eq"
    },
    "max_score": 1.0,
    "hits": [
      {
        "_index": "client-logs",
        "_id": "abc123",
        "_score": 1.0,
        "_source": {
          "@timestamp": "2024-01-15T10:30:45.123Z",
          "filename": "/home/jack/netviz-backend/demo-infra/logs/client/connection.log",
          "message": "Connection established to server",
          // Additional fields from Fluent Bit
        }
      }
    ]
  }
}
```

### 2. Search with Size Limit

Limit the number of results returned:

```bash
curl -X GET "https://192.168.0.132:9200/server-logs/_search?pretty&size=10" \
  -H "Content-Type: application/json" \
  -u "admin:xuwzuc-rExzo3-hotjed" \
  -k
```

### 3. Search with Time Range Filter

Retrieve logs from the last hour:

```bash
curl -X POST "https://192.168.0.132:9200/frr-router-logs/_search?pretty" \
  -H "Content-Type: application/json" \
  -u "admin:xuwzuc-rExzo3-hotjed" \
  -k \
  -d '{
    "query": {
      "range": {
        "@timestamp": {
          "gte": "now-1h",
          "lte": "now"
        }
      }
    },
    "sort": [
      {
        "@timestamp": {
          "order": "desc"
        }
      }
    ]
  }'
```

### 4. Search by Filename

Find logs from a specific log file:

```bash
curl -X POST "https://192.168.0.132:9200/switch1-logs/_search?pretty" \
  -H "Content-Type: application/json" \
  -u "admin:xuwzuc-rExzo3-hotjed" \
  -k \
  -d '{
    "query": {
      "match": {
        "filename": "ovs-vswitchd.log"
      }
    }
  }'
```

### 5. Full-Text Search in Log Messages

Search for specific text in log messages:

```bash
curl -X POST "https://192.168.0.132:9200/switch2-logs/_search?pretty" \
  -H "Content-Type: application/json" \
  -u "admin:xuwzuc-rExzo3-hotjed" \
  -k \
  -d '{
    "query": {
      "match": {
        "message": "error connection timeout"
      }
    },
    "highlight": {
      "fields": {
        "message": {}
      }
    }
  }'
```

### 6. Multi-Index Search

Search across multiple indexes simultaneously:

```bash
curl -X POST "https://192.168.0.132:9200/client-logs,server-logs/_search?pretty" \
  -H "Content-Type: application/json" \
  -u "admin:xuwzuc-rExzo3-hotjed" \
  -k \
  -d '{
    "query": {
      "bool": {
        "must": [
          {
            "match": {
              "message": "connection"
            }
          }
        ],
        "filter": [
          {
            "range": {
              "@timestamp": {
                "gte": "now-15m"
              }
            }
          }
        ]
      }
    }
  }'
```

### 7. Aggregations - Count Logs by Filename

Get log count grouped by filename:

```bash
curl -X POST "https://192.168.0.132:9200/client-logs/_search?pretty" \
  -H "Content-Type: application/json" \
  -u "admin:xuwzuc-rExzo3-hotjed" \
  -k \
  -d '{
    "size": 0,
    "aggs": {
      "logs_by_file": {
        "terms": {
          "field": "filename.keyword",
          "size": 10
        }
      }
    }
  }'
```

### 8. Wildcard Search Across All Network Component Logs

Search all indexes matching a pattern:

```bash
curl -X POST "https://192.168.0.132:9200/*-logs/_search?pretty" \
  -H "Content-Type: application/json" \
  -u "admin:xuwzuc-rExzo3-hotjed" \
  -k \
  -d '{
    "query": {
      "query_string": {
        "query": "error OR warning OR critical"
      }
    },
    "_source": ["@timestamp", "filename", "message"],
    "size": 50
  }'
```

### 9. Get Index Information

Retrieve metadata about a specific index:

```bash
curl -X GET "https://192.168.0.132:9200/frr-router-logs?pretty" \
  -u "admin:xuwzuc-rExzo3-hotjed" \
  -k
```

### 10. Check All Available Indexes

List all indexes in the cluster:

```bash
curl -X GET "https://192.168.0.132:9200/_cat/indices?v&s=index" \
  -u "admin:xuwzuc-rExzo3-hotjed" \
  -k
```

## Python Example

Using the OpenSearch Python client:

```python
from opensearchpy import OpenSearch
from datetime import datetime, timedelta
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create OpenSearch client
client = OpenSearch(
    hosts=[{'host': '192.168.0.132', 'port': 9200}],
    http_auth=('admin', 'xuwzuc-rExzo3-hotjed'),
    use_ssl=True,
    verify_certs=False,
    ssl_show_warn=False
)

# Example 1: Search for recent errors
def search_recent_errors(index_name):
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"message": "error"}}
                ],
                "filter": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": "now-1h"
                            }
                        }
                    }
                ]
            }
        },
        "sort": [{"@timestamp": {"order": "desc"}}],
        "size": 20
    }
    
    response = client.search(index=index_name, body=query)
    return response['hits']['hits']

# Example 2: Get log statistics
def get_log_stats(index_name):
    query = {
        "size": 0,
        "aggs": {
            "logs_over_time": {
                "date_histogram": {
                    "field": "@timestamp",
                    "calendar_interval": "5m"
                }
            },
            "log_levels": {
                "terms": {
                    "field": "level.keyword",
                    "size": 10
                }
            }
        }
    }
    
    response = client.search(index=index_name, body=query)
    return response['aggregations']

# Usage
errors = search_recent_errors('client-logs')
stats = get_log_stats('frr-router-logs')
```

## JavaScript/Node.js Example

Using the OpenSearch JavaScript client:

```javascript
const { Client } = require('@opensearch-project/opensearch');

// Create client
const client = new Client({
  node: 'https://admin:xuwzuc-rExzo3-hotjed@192.168.0.132:9200',
  ssl: {
    rejectUnauthorized: false
  }
});

// Example: Search for connection issues
async function searchConnectionIssues() {
  const response = await client.search({
    index: 'client-logs,server-logs',
    body: {
      query: {
        bool: {
          should: [
            { match: { message: 'connection failed' }},
            { match: { message: 'connection timeout' }},
            { match: { message: 'connection refused' }}
          ],
          minimum_should_match: 1,
          filter: [
            {
              range: {
                '@timestamp': {
                  gte: 'now-30m'
                }
              }
            }
          ]
        }
      },
      sort: [
        { '@timestamp': { order: 'desc' }}
      ],
      size: 50
    }
  });

  return response.body.hits.hits;
}

// Example: Monitor log flow rate
async function getLogFlowRate() {
  const response = await client.search({
    index: '*-logs',
    body: {
      size: 0,
      aggs: {
        logs_per_minute: {
          date_histogram: {
            field: '@timestamp',
            calendar_interval: '1m',
            min_doc_count: 0
          },
          aggs: {
            by_index: {
              terms: {
                field: '_index',
                size: 5
              }
            }
          }
        }
      }
    }
  });

  return response.body.aggregations;
}
```

## Common Query Patterns

### 1. Find Logs with Specific Severity

```json
{
  "query": {
    "terms": {
      "level": ["ERROR", "CRITICAL", "FATAL"]
    }
  }
}
```

### 2. Search Logs from Multiple Components

```json
{
  "query": {
    "bool": {
      "should": [
        { "term": { "_index": "client-logs" }},
        { "term": { "_index": "server-logs" }}
      ]
    }
  }
}
```

### 3. Complex Time-Based Analysis

```json
{
  "query": {
    "range": {
      "@timestamp": {
        "gte": "2024-01-15T00:00:00Z",
        "lte": "2024-01-15T23:59:59Z",
        "time_zone": "+00:00"
      }
    }
  },
  "aggs": {
    "hourly_logs": {
      "date_histogram": {
        "field": "@timestamp",
        "calendar_interval": "hour",
        "time_zone": "+00:00"
      },
      "aggs": {
        "by_component": {
          "terms": {
            "field": "_index"
          }
        }
      }
    }
  }
}
```

## Error Handling

When working with the API, handle common errors:

1. **Authentication Error (401)**
   - Verify username and password
   - Check if user has required permissions

2. **Index Not Found (404)**
   - Verify index name is correct
   - Check if Fluent Bit is running and creating indexes

3. **Connection Refused**
   - Verify OpenSearch is running
   - Check firewall settings
   - Confirm host and port are correct

4. **SSL/TLS Errors**
   - Use `-k` flag with curl or disable certificate verification in code
   - For production, properly configure certificates

## Performance Tips

1. **Use filters instead of queries when possible** - Filters are cached and faster
2. **Limit result size** - Use the `size` parameter to avoid retrieving too many documents
3. **Use source filtering** - Specify only required fields with `_source`
4. **Enable index patterns** - Search multiple indexes with patterns like `*-logs`
5. **Use aggregations** - For analytics, use aggregations instead of retrieving all documents

## Additional Resources

- [OpenSearch Query DSL Documentation](https://opensearch.org/docs/latest/query-dsl/)
- [OpenSearch Search API](https://opensearch.org/docs/latest/api-reference/search/)
- [OpenSearch Aggregations](https://opensearch.org/docs/latest/aggregations/)
