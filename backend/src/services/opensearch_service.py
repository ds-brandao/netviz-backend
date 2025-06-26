"""
OpenSearch service for querying logs and metrics.
Handles all OpenSearch interactions in a centralized way.
"""

import requests
import urllib3
from typing import Dict, List, Optional, Any
from datetime import datetime
from requests.auth import HTTPBasicAuth

from src.config.settings import Settings

settings = Settings()

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class OpenSearchService:
    """Service for interacting with OpenSearch"""
    
    def __init__(self):
        self.base_url = settings.OPENSEARCH_BASE_URL
        self.username = settings.OPENSEARCH_USERNAME
        self.password = settings.OPENSEARCH_PASSWORD
        self.verify_ssl = settings.OPENSEARCH_VERIFY_SSL
        
    def _get_session(self) -> requests.Session:
        """Create requests session with OpenSearch authentication"""
        session = requests.Session()
        session.auth = HTTPBasicAuth(self.username, self.password)
        session.verify = self.verify_ssl
        return session
    
    async def query_logs(
        self, 
        index_pattern: str, 
        query: dict, 
        size: int = 50
    ) -> List[Dict[str, Any]]:
        """Query OpenSearch logs with given parameters"""
        try:
            session = self._get_session()
            url = f"{self.base_url}/{index_pattern}/_search"
            
            response = session.post(url, json=query, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            
            data = response.json()
            return data.get("hits", {}).get("hits", [])
        except Exception as e:
            print(f"Error querying OpenSearch: {e}")
            return []
    
    async def fetch_recent_logs(
        self, 
        minutes: int = 30, 
        size: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch recent logs from all network device indexes - balanced sampling"""
        # Use aggregation to get balanced samples from each device
        per_device_size = max(2, size // 6)  # Distribute across ~6 devices
        
        query = {
            "size": 0,
            "query": {
                "range": {
                    "@timestamp": {
                        "gte": f"now-{minutes}m"
                    }
                }
            },
            "aggs": {
                "by_device": {
                    "terms": {
                        "field": "_index",
                        "size": 10
                    },
                    "aggs": {
                        "recent_logs": {
                            "top_hits": {
                                "size": per_device_size,
                                "sort": [{"@timestamp": {"order": "desc"}}],
                                "_source": ["@timestamp", "filename", "log"]
                            }
                        }
                    }
                }
            }
        }
        
        session = self._get_session()
        url = f"{self.base_url}/*-logs/_search"
        
        try:
            response = session.post(url, json=query, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            data = response.json()
            
            # Transform aggregated results to our format
            transformed_logs = []
            
            if "aggregations" in data and "by_device" in data["aggregations"]:
                for bucket in data["aggregations"]["by_device"]["buckets"]:
                    device_index = bucket["key"]
                    device_name = device_index.replace("-logs", "")
                    
                    for hit in bucket["recent_logs"]["hits"]["hits"]:
                        source = hit.get("_source", {})
                        log_message = source.get("log", "")
                        
                        # Infer log level from content
                        level = self._infer_log_level(log_message)
                        
                        transformed_logs.append({
                            "id": hit.get("_id", ""),
                            "timestamp": source.get("@timestamp", ""),
                            "level": level,
                            "service": device_name,
                            "message": log_message,
                            "node_id": device_name,
                            "event_type": "log_entry",
                            "metadata": {
                                "filename": source.get("filename", ""),
                                "index": device_index
                            }
                        })
            
            # Sort all logs by timestamp (most recent first)
            transformed_logs.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return transformed_logs[:size]
            
        except Exception as e:
            print(f"Error fetching balanced logs: {e}")
            return []
    
    async def fetch_metrics(self) -> Dict[str, Any]:
        """Fetch system metrics from OpenSearch to hydrate network data"""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": "now-5m"
                                }
                            }
                        }
                    ]
                }
            },
            "sort": [
                {
                    "@timestamp": {
                        "order": "desc"
                    }
                }
            ],
            "size": 100,
            "aggs": {
                "by_host": {
                    "terms": {
                        "field": "host.name.keyword",
                        "size": 10
                    },
                    "aggs": {
                        "latest_system_metrics": {
                            "filter": {
                                "term": {"metric_type": "system"}
                            },
                            "aggs": {
                                "latest": {
                                    "top_hits": {
                                        "size": 1,
                                        "sort": [{"@timestamp": {"order": "desc"}}]
                                    }
                                }
                            }
                        },
                        "docker_containers": {
                            "filter": {
                                "term": {"metric_type": "docker"}
                            },
                            "aggs": {
                                "containers": {
                                    "terms": {
                                        "field": "container.name.keyword",
                                        "size": 20
                                    },
                                    "aggs": {
                                        "latest": {
                                            "top_hits": {
                                                "size": 1,
                                                "sort": [{"@timestamp": {"order": "desc"}}]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        try:
            session = self._get_session()
            url = f"{self.base_url}/{settings.OPENSEARCH_METRICS_INDEX_PATTERN}/_search"
            
            response = session.post(url, json=query, headers={"Content-Type": "application/json"})
            response.raise_for_status()
            
            data = response.json()
            
            # Process aggregations to build host metrics
            metrics = {}
            if "aggregations" in data and "by_host" in data["aggregations"]:
                for bucket in data["aggregations"]["by_host"]["buckets"]:
                    host_name = bucket["key"]
                    
                    # Get system metrics
                    system_metrics = {}
                    if "latest_system_metrics" in bucket and bucket["latest_system_metrics"]["latest"]["hits"]["hits"]:
                        system_hit = bucket["latest_system_metrics"]["latest"]["hits"]["hits"][0]["_source"]
                        system_data = system_hit.get("system", {})
                        system_metrics = {
                            "timestamp": system_hit.get("@timestamp"),
                            "cpu_usage": system_data.get("cpu", {}).get("usage_percent"),
                            "memory_usage": system_data.get("memory", {}).get("usage_percent"),
                            "memory_total": system_data.get("memory", {}).get("total_mb"),
                            "memory_used": system_data.get("memory", {}).get("used_mb"),
                            "disk_usage": system_data.get("disk", {}).get("usage_percent"),
                            "load_average": system_data.get("load", {}).get("1m"),
                            "uptime": system_data.get("uptime", {}).get("seconds"),
                            "metric_type": "system"
                        }
                    
                    # Get docker container metrics
                    containers = []
                    if "docker_containers" in bucket and "containers" in bucket["docker_containers"]:
                        for container_bucket in bucket["docker_containers"]["containers"]["buckets"]:
                            if container_bucket["latest"]["hits"]["hits"]:
                                container_hit = container_bucket["latest"]["hits"]["hits"][0]["_source"]
                                container_data = {
                                    "name": container_hit.get("container", {}).get("name"),
                                    "id": container_hit.get("container", {}).get("id"),
                                    "status": container_hit.get("container", {}).get("status"),
                                    "cpu_usage": container_hit.get("docker", {}).get("cpu", {}).get("usage_percent"),
                                    "memory_usage": container_hit.get("docker", {}).get("memory", {}).get("usage_percent"),
                                    "timestamp": container_hit.get("@timestamp")
                                }
                                containers.append(container_data)
                    
                    metrics[host_name] = {
                        **system_metrics,
                        "containers": containers
                    }
            
            return metrics
        except Exception as e:
            print(f"Error fetching metrics: {e}")
            return {}
    
    async def get_log_stats(self) -> Dict[str, Any]:
        """Get log statistics and counts"""
        try:
            session = self._get_session()
            
            # Get total count across all log indexes
            total_count = 0
            for index in settings.OPENSEARCH_LOG_INDEXES:
                url = f"{self.base_url}/{index}/_count"
                response = session.get(url, timeout=10)
                if response.status_code == 200:
                    total_count += response.json().get("count", 0)
            
            # Get recent activity count
            recent_query = {
                "query": {
                    "range": {
                        "@timestamp": {
                            "gte": "now-1h"
                        }
                    }
                }
            }
            
            url = f"{self.base_url}/*-logs/_count"
            response = session.post(url, json=recent_query, headers={"Content-Type": "application/json"})
            recent_count = response.json().get("count", 0) if response.status_code == 200 else 0
            
            return {
                "total_logs": total_count,
                "recent_logs_1h": recent_count,
                "level_counts": {"INFO": total_count},  # Simplified since logs don't have explicit levels
                "opensearch_available": True,
                "indexes": settings.OPENSEARCH_LOG_INDEXES
            }
            
        except Exception as e:
            return {
                "total_logs": 0,
                "recent_logs_1h": 0,
                "level_counts": {},
                "opensearch_available": False,
                "error": str(e)
            }
    
    @staticmethod
    def _infer_log_level(log_message: str) -> str:
        """Infer log level from message content"""
        message_lower = log_message.lower()
        if any(keyword in message_lower for keyword in ["error", "fail", "exception"]):
            return "ERROR"
        elif any(keyword in message_lower for keyword in ["warn", "warning"]):
            return "WARN"
        return "INFO"


# Create a global instance
opensearch_service = OpenSearchService()