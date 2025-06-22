from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
import uvicorn
import json
import asyncio
from uuid import uuid4

from agent import create_agent, create_streaming_agent, simple_streaming_chat, agent_streaming_chat
from database import init_db, get_db_session, Chat, NetworkNode, NetworkEdge
from graph_service import graph_service
from websocket_manager import connection_manager, periodic_ping
from sqlalchemy import select
import time
import requests
import urllib3
from requests.auth import HTTPBasicAuth
import ssl

# OpenSearch configuration for demo-infra
OPENSEARCH_BASE_URL = "https://192.168.0.132:9200"
OPENSEARCH_USERNAME = "admin"
OPENSEARCH_PASSWORD = "xuwzuc-rExzo3-hotjed"
OPENSEARCH_INDEXES = [
    "client-logs",
    "frr-router-logs", 
    "server-logs",
    "switch1-logs",
    "switch2-logs",
    "system-metrics-*"
]

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Global variables for data hydration
network_metrics_cache = {}
last_metrics_update = None

def get_opensearch_session():
    """Create requests session with OpenSearch authentication"""
    session = requests.Session()
    session.auth = HTTPBasicAuth(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD)
    session.verify = False  # Disable SSL verification for self-signed certs
    return session

async def query_opensearch_logs(index_pattern: str, query: dict, size: int = 50):
    """Query OpenSearch logs with given parameters"""
    try:
        session = get_opensearch_session()
        url = f"{OPENSEARCH_BASE_URL}/{index_pattern}/_search"
        
        response = session.post(url, json=query, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        
        data = response.json()
        return data.get("hits", {}).get("hits", [])
    except Exception as e:
        print(f"Error querying OpenSearch: {e}")
        return []

async def fetch_recent_logs_from_opensearch(minutes: int = 30, size: int = 100):
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
    
    session = get_opensearch_session()
    url = f"{OPENSEARCH_BASE_URL}/*-logs/_search"
    
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
                    level = "INFO"
                    if any(keyword in log_message.lower() for keyword in ["error", "fail", "exception"]):
                        level = "ERROR"
                    elif any(keyword in log_message.lower() for keyword in ["warn", "warning"]):
                        level = "WARN"
                    
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

async def sync_network_topology_from_metrics():
    """Sync network topology based on MetricBeat data"""
    try:
        # Get fresh metrics
        metrics = await fetch_metrics_from_opensearch()
        
        if not metrics:
            print("No metrics available for topology sync")
            return
            
        async with get_db_session() as session:
            from sqlalchemy import select, delete
            from database import NetworkNode, NetworkEdge
            from datetime import datetime, timedelta
            
            # Get existing nodes
            result = await session.execute(select(NetworkNode))
            existing_nodes = {node.name: node for node in result.scalars().all()}
            
            current_time = datetime.now()
            updated_nodes = set()
            
            # Process each host from metrics
            for host_name, host_data in metrics.items():
                # Create or update host node
                host_node_name = f"host-{host_name}"
                if host_node_name in existing_nodes:
                    host_node = existing_nodes[host_node_name]
                    host_node.last_updated = current_time
                    host_node.status = "online"
                    host_node.node_metadata.update({
                        "cpu_usage": host_data.get("cpu_usage"),
                        "memory_usage": host_data.get("memory_usage"),
                        "memory_total": host_data.get("memory_total"),
                        "memory_used": host_data.get("memory_used"),
                        "disk_usage": host_data.get("disk_usage"),
                        "load_average": host_data.get("load_average"),
                        "uptime": host_data.get("uptime"),
                        "metric_source": "metricbeat"
                    })
                else:
                    host_node = NetworkNode(
                        name=host_node_name,
                        type="host",
                        ip_address=None,
                        status="online",
                        layer="infrastructure",
                        position_x=0.0,
                        position_y=0.0,
                        node_metadata={
                            "cpu_usage": host_data.get("cpu_usage"),
                            "memory_usage": host_data.get("memory_usage"),
                            "memory_total": host_data.get("memory_total"),
                            "memory_used": host_data.get("memory_used"),
                            "disk_usage": host_data.get("disk_usage"),
                            "load_average": host_data.get("load_average"),
                            "uptime": host_data.get("uptime"),
                            "metric_source": "metricbeat"
                        },
                        last_updated=current_time
                    )
                    session.add(host_node)
                    
                updated_nodes.add(host_node_name)
                
                # Process containers for this host
                containers = host_data.get("containers", [])
                for container in containers:
                    container_name = container.get("name")
                    if not container_name:
                        continue
                        
                    # Map container names to network device types
                    device_type = "container"
                    if container_name in ["frr-router"]:
                        device_type = "router"
                    elif container_name in ["switch1", "switch2"]:
                        device_type = "switch"
                    elif container_name in ["server"]:
                        device_type = "server"
                    elif container_name in ["client"]:
                        device_type = "client"
                    
                    # Determine IP based on container name and demo-infra topology
                    ip_address = None
                    if container_name == "client":
                        ip_address = "192.168.10.10"
                    elif container_name == "frr-router":
                        ip_address = "192.168.10.254"  # Primary interface
                    elif container_name == "server":
                        ip_address = "192.168.30.10"
                    
                    if container_name in existing_nodes:
                        container_node = existing_nodes[container_name]
                        container_node.last_updated = current_time
                        container_node.status = "online" if "Up" in container.get("status", "") else "offline"
                        container_node.type = device_type
                        container_node.ip_address = ip_address
                        container_node.node_metadata.update({
                            "container_id": container.get("id"),
                            "container_status": container.get("status"),
                            "cpu_usage": container.get("cpu_usage"),
                            "memory_usage": container.get("memory_usage"),
                            "host": host_name,
                            "metric_source": "metricbeat"
                        })
                    else:
                        container_node = NetworkNode(
                            name=container_name,
                            type=device_type,
                            ip_address=ip_address,
                            status="online" if "Up" in container.get("status", "") else "offline",
                            layer="network",
                            position_x=0.0,
                            position_y=0.0,
                            node_metadata={
                                "container_id": container.get("id"),
                                "container_status": container.get("status"),
                                "cpu_usage": container.get("cpu_usage"),
                                "memory_usage": container.get("memory_usage"),
                                "host": host_name,
                                "metric_source": "metricbeat"
                            },
                            last_updated=current_time
                        )
                        session.add(container_node)
                        
                    updated_nodes.add(container_name)
            
            # Clean up stale nodes (only ones without MetricBeat data and older than 30 minutes)
            stale_threshold = current_time - timedelta(minutes=30)
            for node_name, node in existing_nodes.items():
                if (node_name not in updated_nodes and 
                    node.last_updated < stale_threshold and
                    node.node_metadata.get("metric_source") != "metricbeat"):
                    print(f"Removing stale node: {node_name}")
                    await session.delete(node)
            
            # Create network topology edges based on demo-infra structure
            await create_demo_network_edges(session)
            
            await session.commit()
            print(f"Synced network topology: {len(updated_nodes)} nodes updated")
            
    except Exception as e:
        print(f"Error syncing network topology: {e}")

async def create_demo_network_edges(session):
    """Create edges representing the demo-infra network topology"""
    from sqlalchemy import select
    from database import NetworkNode, NetworkEdge
    
    # Get all nodes by name
    result = await session.execute(select(NetworkNode))
    nodes_by_name = {node.name: node for node in result.scalars().all()}
    
    # Define the demo-infra topology: Client → Switch1 → Router → Switch2 → Server
    topology = [
        ("client", "switch1", "ethernet"),
        ("switch1", "frr-router", "ethernet"), 
        ("frr-router", "switch2", "ethernet"),
        ("switch2", "server", "ethernet"),
    ]
    
    # Get existing edges
    edge_result = await session.execute(select(NetworkEdge))
    existing_edges = {(edge.source_node.name, edge.target_node.name): edge 
                     for edge in edge_result.scalars().all()}
    
    current_time = datetime.now()
    
    for source_name, target_name, connection_type in topology:
        if source_name in nodes_by_name and target_name in nodes_by_name:
            source_node = nodes_by_name[source_name]
            target_node = nodes_by_name[target_name]
            
            # Check if edge already exists (in either direction)
            edge_key = (source_name, target_name)
            reverse_edge_key = (target_name, source_name)
            
            if edge_key not in existing_edges and reverse_edge_key not in existing_edges:
                # Determine subnet based on connection
                subnet_info = "1Gbps"
                if source_name == "client" and target_name == "switch1":
                    subnet_info = "192.168.10.0/24 (1Gbps)"
                elif source_name == "switch1" and target_name == "frr-router":
                    subnet_info = "192.168.10.0/24 (1Gbps)"
                elif source_name == "frr-router" and target_name == "switch2":
                    subnet_info = "192.168.30.0/24 (1Gbps)"
                elif source_name == "switch2" and target_name == "server":
                    subnet_info = "192.168.30.0/24 (1Gbps)"
                
                # Create new edge
                new_edge = NetworkEdge(
                    source_id=source_node.id,
                    target_id=target_node.id,
                    type=connection_type,
                    bandwidth=subnet_info,
                    utilization=0.0,
                    status="active",
                    edge_metadata={
                        "auto_created": True, 
                        "topology": "demo-infra",
                        "subnet": subnet_info.split(" (")[0] if "(" in subnet_info else "N/A"
                    },
                    last_updated=current_time
                )
                session.add(new_edge)
            elif edge_key in existing_edges:
                # Update existing edge
                edge = existing_edges[edge_key]
                edge.last_updated = current_time
                edge.status = "active"
                # Update subnet info if not already set
                if "subnet" not in edge.edge_metadata:
                    subnet_info = "1Gbps"
                    if source_name == "client" and target_name == "switch1":
                        subnet_info = "192.168.10.0/24 (1Gbps)"
                    elif source_name == "switch1" and target_name == "frr-router":
                        subnet_info = "192.168.10.0/24 (1Gbps)"
                    elif source_name == "frr-router" and target_name == "switch2":
                        subnet_info = "192.168.30.0/24 (1Gbps)"
                    elif source_name == "switch2" and target_name == "server":
                        subnet_info = "192.168.30.0/24 (1Gbps)"
                    
                    edge.bandwidth = subnet_info
                    edge.edge_metadata["subnet"] = subnet_info.split(" (")[0] if "(" in subnet_info else "N/A"

async def fetch_metrics_from_opensearch():
    """Fetch system metrics from OpenSearch to hydrate network data"""
    global network_metrics_cache, last_metrics_update
    
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
        session = get_opensearch_session()
        url = f"{OPENSEARCH_BASE_URL}/system-metrics-*/_search"
        
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
        
        network_metrics_cache = metrics
        last_metrics_update = datetime.now()
        print(f"Updated metrics cache with {len(metrics)} hosts")
        
        return metrics
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return {}

app = FastAPI(title="NetViz Backend", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Agent tool functions
@app.post("/ai/query-logs")
async def ai_query_logs(
    device_name: str = None,
    service: str = None,
    log_level: str = None,
    time_range: int = 24,  # hours
    size: int = 50,
    query: str = None
):
    """AI Agent tool for querying logs from OpenSearch with flexible parameters"""
    try:
        print(f"=== AI QUERY LOGS DEBUG ===")
        print(f"device_name='{device_name}', service='{service}', log_level='{log_level}'")
        print(f"time_range={time_range}, size={size}")
        opensearch_query = {
            "size": size,
            "sort": [{"@timestamp": {"order": "desc"}}],
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": f"now-{time_range}h"
                                }
                            }
                        }
                    ]
                }
            }
        }
        
        # Device name to index mapping
        device_to_index = {
            "frr-router": "frr-router-logs",
            "switch1": "switch1-logs", 
            "switch2": "switch2-logs",
            "server": "server-logs",
            "client": "client-logs"
        }
        
        # Default to searching all log indexes if no specific device
        target_indexes = "*-logs"
        
        # Add filters based on parameters
        if device_name:
            # Map device name to specific index
            if device_name in device_to_index:
                target_indexes = device_to_index[device_name]
                print(f"Mapping device '{device_name}' to index '{target_indexes}'")
            else:
                # Fallback to wildcard search
                target_indexes = f"*{device_name}*-logs"
                print(f"Using fallback mapping for device '{device_name}': {target_indexes}")
        
        if service:
            opensearch_query["query"]["bool"]["must"].append({
                "term": {"service": service}
            })
        
        if log_level:
            opensearch_query["query"]["bool"]["must"].append({
                "term": {"level": log_level.upper()}
            })
        
        if query:
            opensearch_query["query"]["bool"]["must"].append({
                "query_string": {"query": query}
            })
        
        session = get_opensearch_session()
        url = f"{OPENSEARCH_BASE_URL}/{target_indexes}/_search"
        print(f"Querying OpenSearch URL: {url}")
        
        response = session.post(url, json=opensearch_query, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        
        data = response.json()
        logs = []
        
        print(f"OpenSearch query: {opensearch_query}")
        print(f"OpenSearch returned {data.get('hits', {}).get('total', {}).get('value', 0)} total hits")
        
        # Debug: show which indexes are being hit
        indexes_hit = set()
        for hit in data.get("hits", {}).get("hits", []):
            indexes_hit.add(hit.get("_index", "unknown"))
        print(f"Indexes in results: {list(indexes_hit)}")
        
        for hit in data.get("hits", {}).get("hits", []):
            source = hit["_source"]
            log_message = source.get("log", source.get("message", ""))
            
            # Infer log level from content (same as working function)
            level = "INFO"
            if any(keyword in log_message.lower() for keyword in ["error", "fail", "exception"]):
                level = "ERROR"
            elif any(keyword in log_message.lower() for keyword in ["warn", "warning"]):
                level = "WARN"
            
            logs.append({
                "id": hit["_id"],
                "timestamp": source.get("@timestamp"),
                "level": level,
                "service": hit.get("_index", "").replace("-logs", ""),
                "message": log_message,
                "metadata": {
                    "filename": source.get("filename", ""),
                    "index": hit.get("_index", ""),
                    **{k: v for k, v in source.items() if k not in ["@timestamp", "log", "message", "filename"]}
                }
            })
        
        return {
            "logs": logs,
            "total": data.get("hits", {}).get("total", {}).get("value", 0),
            "query_params": {
                "device_name": device_name,
                "service": service,
                "log_level": log_level,
                "time_range": time_range,
                "size": size,
                "query": query
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying logs: {str(e)}")

@app.post("/ai/query-metrics")
async def ai_query_metrics(
    device_name: str = None,
    metric_type: str = None,  # system, docker, network
    container_name: str = None,
    time_range: int = 1,  # hours
    aggregation: str = "latest"  # latest, average, max, min
):
    """AI Agent tool for querying metrics from MetricBeat data"""
    try:
        opensearch_query = {
            "size": 0,
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": f"now-{time_range}h"
                                }
                            }
                        }
                    ]
                }
            },
            "aggs": {
                "by_host": {
                    "terms": {
                        "field": "host.name.keyword",
                        "size": 20
                    },
                    "aggs": {
                        "latest_metrics": {
                            "top_hits": {
                                "size": 1,
                                "sort": [{"@timestamp": {"order": "desc"}}]
                            }
                        }
                    }
                }
            }
        }
        
        # Add filters
        if device_name:
            opensearch_query["query"]["bool"]["must"].append({
                "wildcard": {"host.name": f"*{device_name}*"}
            })
        
        if metric_type:
            opensearch_query["query"]["bool"]["must"].append({
                "term": {"metric_type": metric_type}
            })
        
        if container_name:
            opensearch_query["query"]["bool"]["must"].append({
                "term": {"container.name.keyword": container_name}
            })
        
        session = get_opensearch_session()
        url = f"{OPENSEARCH_BASE_URL}/system-metrics-*/_search"
        
        response = session.post(url, json=opensearch_query, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        
        data = response.json()
        metrics = {}
        
        if "aggregations" in data and "by_host" in data["aggregations"]:
            for bucket in data["aggregations"]["by_host"]["buckets"]:
                host_name = bucket["key"]
                
                if bucket["latest_metrics"]["hits"]["hits"]:
                    hit = bucket["latest_metrics"]["hits"]["hits"][0]["_source"]
                    
                    metrics[host_name] = {
                        "timestamp": hit.get("@timestamp"),
                        "host": hit.get("host", {}),
                        "system": hit.get("system", {}),
                        "docker": hit.get("docker", {}),
                        "container": hit.get("container", {}),
                        "metric_type": hit.get("metric_type")
                    }
        
        return {
            "metrics": metrics,
            "query_params": {
                "device_name": device_name,
                "metric_type": metric_type,
                "container_name": container_name,
                "time_range": time_range,
                "aggregation": aggregation
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying metrics: {str(e)}")

@app.get("/ai/device-info/{device_id}")
async def ai_get_device_info(device_id: str):
    """AI Agent tool for getting comprehensive device information"""
    try:
        async with get_db_session() as session:
            # Get device from database
            stmt = select(NetworkNode).where(NetworkNode.id == device_id)
            result = await session.execute(stmt)
            device = result.scalar_one_or_none()
            
            if not device:
                raise HTTPException(status_code=404, detail="Device not found")
            
            # Get recent metrics for this device
            metrics_response = await ai_query_metrics(device_name=device.name, time_range=1)
            
            # Get recent logs for this device
            logs_response = await ai_query_logs(device_name=device.name, time_range=2, size=20)
            
            return {
                "device": {
                    "id": device.id,
                    "name": device.name,
                    "type": device.type,
                    "ip_address": device.ip_address,
                    "status": device.status,
                    "layer": device.layer,
                    "metadata": device.metadata,
                    "last_updated": device.last_updated.isoformat() if device.last_updated else None
                },
                "metrics": metrics_response["metrics"],
                "recent_logs": logs_response["logs"][:10],
                "logs_total": logs_response["total"]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting device info: {str(e)}")

# Function to clear bad/test data
async def clear_bad_data():
    """Clear test devices and invalid string entries"""
    try:
        async with get_db_session() as session:
            from sqlalchemy import select, delete
            from database import NetworkNode, NetworkEdge
            
            # Delete nodes with invalid data
            result = await session.execute(select(NetworkNode))
            nodes_to_delete = []
            
            for node in result.scalars().all():
                # Mark for deletion if it's test data or invalid
                if (node.name in ["string", "Device test-device-001"] or 
                    node.type == "string" or 
                    node.ip_address == "string" or
                    "test-device" in node.name):
                    nodes_to_delete.append(node.id)
            
            if nodes_to_delete:
                # Delete associated edges first
                await session.execute(
                    delete(NetworkEdge).where(
                        (NetworkEdge.source_id.in_(nodes_to_delete)) |
                        (NetworkEdge.target_id.in_(nodes_to_delete))
                    )
                )
                
                # Delete the nodes
                await session.execute(
                    delete(NetworkNode).where(NetworkNode.id.in_(nodes_to_delete))
                )
                
                await session.commit()
                print(f"Cleared {len(nodes_to_delete)} bad/test nodes and their edges")
            else:
                print("No bad data found to clear")
                
    except Exception as e:
        print(f"Error clearing bad data: {e}")

# Background task for metrics hydration and topology sync
async def periodic_metrics_fetch():
    """Periodically fetch metrics from OpenSearch and sync topology"""
    # First run: clear bad data
    await clear_bad_data()
    
    while True:
        try:
            # Fetch metrics and sync topology
            await fetch_metrics_from_opensearch()
            await sync_network_topology_from_metrics()
            await asyncio.sleep(30)  # Update every 30 seconds
        except Exception as e:
            print(f"Error in periodic metrics fetch: {e}")
            await asyncio.sleep(60)  # Wait longer on error

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    await init_db()
    # Start periodic ping task
    asyncio.create_task(periodic_ping())
    # Start periodic metrics fetch
    asyncio.create_task(periodic_metrics_fetch())

# Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

class StreamingChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    context: Optional[Dict[str, Any]] = None  # Network context (focused node, etc)
    conversation_history: Optional[List[Dict[str, str]]] = None  # Previous messages for context
    
class NetworkNodeData(BaseModel):
    name: str
    type: str
    ip_address: Optional[str] = None
    status: str = "unknown"
    layer: str = "network"
    position: Optional[Dict[str, float]] = {"x": 0.0, "y": 0.0}
    metadata: Dict[str, Any] = {}

class NetworkEdgeData(BaseModel):
    source: str  # node ID
    target: str  # node ID
    type: str = "ethernet"
    bandwidth: Optional[str] = None
    utilization: float = 0.0
    status: str = "unknown"
    metadata: Dict[str, Any] = {}

class GraphUpdateRequest(BaseModel):
    """For external devices to send bulk updates"""
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    source: str = "external_device"

class LogQuery(BaseModel):
    level: Optional[List[str]] = None
    event_type: Optional[str] = None
    node_id: Optional[str] = None
    service: Optional[str] = None
    time_range: Optional[str] = None
    size: int = 20
    search_term: Optional[str] = None

class LogEntry(BaseModel):
    id: str
    timestamp: str
    level: str
    service: str
    message: str
    node_id: str
    event_type: str
    metadata: Dict[str, Any]

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str = "default"):
    """WebSocket endpoint for real-time graph updates"""
    await connection_manager.connect(websocket, session_id)
    
    try:
        # Send initial graph state
        nodes = await graph_service.get_nodes()
        edges = await graph_service.get_edges()
        await connection_manager.send_graph_state(session_id, nodes, edges)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await connection_manager.send_to_connection(websocket, {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                elif message.get("type") == "request_graph_state":
                    nodes = await graph_service.get_nodes()
                    edges = await graph_service.get_edges()
                    await connection_manager.send_graph_state(session_id, nodes, edges)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        connection_manager.disconnect(websocket)

# Streaming chat endpoint with SSE
@app.post("/chat/stream")
async def stream_chat(request: StreamingChatRequest):
    """Stream chat responses with tool execution support"""
    
    async def generate_events() -> AsyncGenerator[str, None]:
        try:
            # Debug log
            print(f"Received chat request: {request.message}")
            print(f"Context: {request.context}")
            
            # Try to use the real AI agent, fall back to simple streaming if it fails
            full_response = ""
            
            try:
                # Load conversation history from database
                conversation_history = []
                async with get_db_session() as session:
                    result = await session.execute(
                        select(Chat).where(Chat.session_id == request.session_id).order_by(Chat.timestamp.desc()).limit(20)
                    )
                    chats = result.scalars().all()
                    
                    # Convert to conversation format (reverse to get chronological order)
                    for chat in reversed(chats):
                        conversation_history.append({"role": "user", "content": chat.message})
                        conversation_history.append({"role": "assistant", "content": chat.response})
                
                # Try using the agent streaming chat function with tools
                async for chunk in agent_streaming_chat(request.message, request.context, conversation_history):
                    if chunk["type"] == "text" or chunk["type"] == "content":
                        content = chunk.get("content") or chunk.get("text", "")
                        full_response += content
                        # Normalize to 'text' type for frontend compatibility
                        yield f"data: {json.dumps({'type': 'text', 'content': content})}\n\n"
                    elif chunk["type"] == "tool_result":
                        yield f"data: {json.dumps(chunk)}\n\n"
                    elif chunk["type"] == "done":
                        break
                    else:
                        yield f"data: {json.dumps(chunk)}\n\n"
                        
            except Exception as agent_error:
                print(f"Agent failed: {agent_error}, falling back to rich content demos")
                
                # Simple fallback response
                response_text = f"I understand you're asking about: '{request.message}'. As a network infrastructure assistant, I can help you with various tasks like checking device status, creating Ansible playbooks, and managing network infrastructure. Try asking me to 'show ssh connection', 'create ansible playbook', 'generate documentation', or 'write python script' to see rich content examples."
                
                # Stream the response in chunks
                words = response_text.split()
                chunk_size = 4
                for i in range(0, len(words), chunk_size):
                    chunk = " ".join(words[i:i+chunk_size])
                    if i + chunk_size < len(words):
                        chunk += " "
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.1)
            
            # Save to database
            async with get_db_session() as session:
                chat_record = Chat(
                    session_id=request.session_id,
                    message=request.message,
                    response=full_response or "[No response]",
                    timestamp=datetime.now()
                )
                session.add(chat_record)
                await session.commit()
            
            # Send completion
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
                
        except Exception as e:
            print(f"Error in stream_chat: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )

# Chat endpoint
@app.post("/chat")
async def chat(request: ChatRequest):
    """Handle chat messages with the AI agent"""
    agent = create_agent()
    
    try:
        # Invoke agent
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": request.message}]}
        )
        
        # Get response
        response_content = result["messages"][-1].content
        
        # Store in database
        async with get_db_session() as session:
            chat_record = Chat(
                session_id=request.session_id,
                message=request.message,
                response=response_content,
                timestamp=datetime.now()
            )
            session.add(chat_record)
            await session.commit()
        
        return {
            "response": response_content,
            "session_id": request.session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chats/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    async with get_db_session() as session:
        result = await session.execute(
            select(Chat).where(Chat.session_id == session_id)
        )
        chats = result.scalars().all()
        return [
            {
                "message": chat.message,
                "response": chat.response,
                "timestamp": chat.timestamp
            }
            for chat in chats
        ]

# Enhanced network infrastructure endpoints using graph service
@app.get("/network/graph")
async def get_network_graph():
    """Get complete network graph (nodes and edges)"""
    try:
        graph = await graph_service.get_graph()
        return {
            "nodes": list(graph["nodes"].values()),
            "edges": list(graph["edges"].values()),
            "last_updated": graph["last_updated"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/network/nodes")
async def get_network_nodes():
    """Get all network nodes"""
    try:
        nodes = await graph_service.get_nodes()
        return nodes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/network/edges")
async def get_network_edges():
    """Get all network edges"""
    try:
        edges = await graph_service.get_edges()
        return edges
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/network/stats")
async def get_network_stats():
    """Get network statistics"""
    try:
        stats = await graph_service.get_graph_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/network/nodes")
async def create_network_node(node_data: NetworkNodeData):
    """Create a new network node"""
    try:
        node = await graph_service.create_node(node_data.dict(), source="api")
        return {"success": True, "node": node}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/network/nodes/{node_id}")
async def update_network_node(node_id: str, node_data: NetworkNodeData):
    """Update a network node"""
    try:
        node = await graph_service.update_node(node_id, node_data.dict(), source="api")
        return {"success": True, "node": node}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/network/nodes/{node_id}")
async def delete_network_node(node_id: str):
    """Delete a network node"""
    try:
        success = await graph_service.delete_node(node_id, source="api")
        if success:
            return {"success": True, "message": "Node deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Node not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/network/edges")
async def create_network_edge(edge_data: NetworkEdgeData):
    """Create a new network edge"""
    try:
        edge = await graph_service.create_edge(edge_data.dict(), source="api")
        return {"success": True, "edge": edge}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/network/edges/{edge_id}")
async def update_network_edge(edge_id: str, edge_data: NetworkEdgeData):
    """Update a network edge"""
    try:
        edge = await graph_service.update_edge(edge_id, edge_data.dict(), source="api")
        return {"success": True, "edge": edge}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/network/edges/{edge_id}")
async def delete_network_edge(edge_id: str):
    """Delete a network edge"""
    try:
        success = await graph_service.delete_edge(edge_id, source="api")
        if success:
            return {"success": True, "message": "Edge deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Edge not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Bulk update endpoints for external devices
@app.post("/network/bulk-update")
async def bulk_update_graph(update_request: GraphUpdateRequest):
    """Bulk update endpoint for external devices to push changes"""
    try:
        results = {"nodes": [], "edges": []}
        
        # Process node updates
        if update_request.nodes:
            for node_data in update_request.nodes:
                if "id" in node_data and node_data["id"]:
                    # Update existing node
                    node = await graph_service.update_node(
                        str(node_data["id"]), 
                        node_data, 
                        source=update_request.source
                    )
                    results["nodes"].append({"action": "updated", "node": node})
                else:
                    # Create new node
                    node = await graph_service.create_node(
                        node_data, 
                        source=update_request.source
                    )
                    results["nodes"].append({"action": "created", "node": node})
        
        # Process edge updates
        if update_request.edges:
            for edge_data in update_request.edges:
                if "id" in edge_data and edge_data["id"]:
                    # Update existing edge
                    edge = await graph_service.update_edge(
                        str(edge_data["id"]), 
                        edge_data, 
                        source=update_request.source
                    )
                    results["edges"].append({"action": "updated", "edge": edge})
                else:
                    # Create new edge
                    edge = await graph_service.create_edge(
                        edge_data, 
                        source=update_request.source
                    )
                    results["edges"].append({"action": "created", "edge": edge})
        
        return {
            "success": True,
            "message": f"Processed {len(results['nodes'])} node updates and {len(results['edges'])} edge updates",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/network/device-update/{device_id}")
async def device_update(device_id: str, update_data: Dict[str, Any]):
    """Simple endpoint for external devices to send updates"""
    try:
        # Find or create node for this device
        existing_node = None
        nodes = await graph_service.get_nodes()
        
        for node in nodes:
            if node.get("metadata", {}).get("device_id") == device_id:
                existing_node = node
                break
        
        # Prepare node data
        node_data = {
            "name": update_data.get("name", f"Device {device_id}"),
            "type": update_data.get("type", "endpoint"),
            "ip_address": update_data.get("ip_address"),
            "status": update_data.get("status", "online"),
            "layer": update_data.get("layer", "network"),
            "metadata": {
                "device_id": device_id,
                **update_data.get("metadata", {})
            }
        }
        
        if existing_node:
            # Update existing node
            node = await graph_service.update_node(
                existing_node["id"], 
                node_data, 
                source=f"device_{device_id}"
            )
            action = "updated"
        else:
            # Create new node
            node = await graph_service.create_node(
                node_data, 
                source=f"device_{device_id}"
            )
            action = "created"
        
        return {
            "success": True,
            "action": action,
            "node": node
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket connection info
@app.get("/network/connections")
async def get_connection_info():
    """Get WebSocket connection information"""
    return {
        "active_connections": connection_manager.get_connection_count(),
        "active_sessions": connection_manager.get_session_count()
    }

# Test streaming endpoint
@app.get("/test/stream")
async def test_stream():
    """Test SSE streaming"""
    async def generate():
        for i in range(5):
            yield f"data: {json.dumps({'count': i, 'message': f'Test message {i}'})}\n\n"
            await asyncio.sleep(1)
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/logs", response_model=List[LogEntry])
async def get_logs(
    level: Optional[str] = None,
    event_type: Optional[str] = None,
    node_id: Optional[str] = None,
    service: Optional[str] = None,
    time_range: Optional[str] = None,
    size: int = 20,
    search: Optional[str] = None
):
    """Get logs with optional filtering"""
    try:
        # Build query for OpenSearch
        query = {"match_all": {}}
        filters = []
        
        if time_range:
            filters.append({
                "range": {
                    "@timestamp": {
                        "gte": f"now-{time_range}"
                    }
                }
            })
        
        if node_id:
            filters.append({
                "term": {"_index": f"{node_id}-logs"}
            })
        
        if search:
            query = {
                "multi_match": {
                    "query": search,
                    "fields": ["log", "filename"]
                }
            }
        
        if filters:
            if search:
                query = {
                    "bool": {
                        "must": [query],
                        "filter": filters
                    }
                }
            else:
                query = {
                    "bool": {
                        "filter": filters
                    }
                }
        
        opensearch_query = {
            "query": query,
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": size,
            "_source": ["@timestamp", "filename", "log", "_index"]
        }
        
        logs = await query_opensearch_logs("*-logs", opensearch_query, size)
        
        # Transform to our format
        result_logs = []
        for hit in logs:
            source = hit.get("_source", {})
            log_message = source.get("log", "")
            
            # Infer log level from content
            level = "INFO"
            if any(keyword in log_message.lower() for keyword in ["error", "fail", "exception"]):
                level = "ERROR"
            elif any(keyword in log_message.lower() for keyword in ["warn", "warning"]):
                level = "WARN"
            
            result_logs.append(LogEntry(
                id=hit.get("_id", ""),
                timestamp=source.get("@timestamp", ""),
                level=level,
                service=hit.get("_index", "").replace("-logs", ""),
                message=log_message,
                node_id=hit.get("_index", "").replace("-logs", ""),
                event_type="log_entry",
                metadata={
                    "filename": source.get("filename", ""),
                    "index": hit.get("_index", "")
                }
            ))
        
        return result_logs
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return []

@app.get("/logs/recent", response_model=List[LogEntry])
async def get_recent_logs(minutes: int = 30, size: int = 50):
    """Get logs from the last N minutes"""
    return await fetch_recent_logs_from_opensearch(minutes, size)

@app.get("/metrics")
async def get_current_metrics():
    """Get current network metrics from cache"""
    global network_metrics_cache, last_metrics_update
    
    # Fetch fresh metrics if cache is empty or old
    if not network_metrics_cache or not last_metrics_update or \
       (datetime.now() - last_metrics_update).seconds > 60:
        await fetch_metrics_from_opensearch()
    
    return {
        "metrics": network_metrics_cache,
        "last_updated": last_metrics_update.isoformat() if last_metrics_update else None,
        "cache_size": len(network_metrics_cache)
    }

@app.post("/network/sync")
async def force_network_sync():
    """Force sync network topology from MetricBeat data"""
    try:
        await clear_bad_data()
        await fetch_metrics_from_opensearch()
        await sync_network_topology_from_metrics()
        return {"success": True, "message": "Network topology synced from MetricBeat data"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@app.post("/network/clear")
async def clear_network_data():
    """Clear all bad/test network data"""
    try:
        await clear_bad_data()
        return {"success": True, "message": "Bad/test network data cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear failed: {str(e)}")

@app.get("/network/status")
async def get_network_status():
    """Get network sync status and update information"""
    global network_metrics_cache, last_metrics_update
    
    try:
        async with get_db_session() as session:
            from sqlalchemy import select, func
            from database import NetworkNode
            
            # Get node counts by type
            result = await session.execute(
                select(NetworkNode.type, func.count(NetworkNode.id))
                .group_by(NetworkNode.type)
            )
            node_counts = {row[0]: row[1] for row in result}
            
            # Get most recent update times
            result = await session.execute(
                select(func.max(NetworkNode.last_updated))
            )
            last_node_update = result.scalar()
            
            return {
                "metrics_cache_size": len(network_metrics_cache),
                "last_metrics_update": last_metrics_update.isoformat() if last_metrics_update else None,
                "last_node_update": last_node_update.isoformat() if last_node_update else None,
                "node_counts": node_counts,
                "total_nodes": sum(node_counts.values()),
                "sync_status": "active" if last_metrics_update else "inactive"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status fetch failed: {str(e)}")

@app.get("/logs/errors", response_model=List[LogEntry])
async def get_error_logs(hours: int = 24, size: int = 100):
    """Get error and warning logs from the last N hours - searches for error patterns"""
    try:
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": "error OR warning OR failed OR timeout OR refused",
                                "fields": ["log"]
                            }
                        }
                    ],
                    "filter": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": f"now-{hours}h"
                                }
                            }
                        }
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": size,
            "_source": ["@timestamp", "filename", "log", "_index"]
        }
        
        logs = await query_opensearch_logs("*-logs", query, size)
        
        result_logs = []
        for hit in logs:
            source = hit.get("_source", {})
            log_message = source.get("log", "")
            
            # Determine error level from content
            level = "ERROR"
            if any(keyword in log_message.lower() for keyword in ["warn", "warning"]):
                level = "WARN"
                
            result_logs.append(LogEntry(
                id=hit.get("_id", ""),
                timestamp=source.get("@timestamp", ""),
                level=level,
                service=hit.get("_index", "").replace("-logs", ""),
                message=log_message,
                node_id=hit.get("_index", "").replace("-logs", ""),
                event_type="error_log",
                metadata={
                    "filename": source.get("filename", ""),
                    "index": hit.get("_index", "")
                }
            ))
        
        return result_logs
    except Exception as e:
        print(f"Error fetching error logs: {e}")
        return []

@app.get("/logs/node/{node_id}", response_model=List[LogEntry])
async def get_node_logs(node_id: str, hours: int = 24, size: int = 50):
    """Get logs for a specific node/device"""
    try:
        query = {
            "query": {
                "bool": {
                    "filter": [
                        {
                            "term": {"_index": f"{node_id}-logs"}
                        },
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": f"now-{hours}h"
                                }
                            }
                        }
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": size,
            "_source": ["@timestamp", "filename", "log", "_index"]
        }
        
        logs = await query_opensearch_logs(f"{node_id}-logs", query, size)
        
        result_logs = []
        for hit in logs:
            source = hit.get("_source", {})
            log_message = source.get("log", "")
            
            # Infer log level from content
            level = "INFO"
            if any(keyword in log_message.lower() for keyword in ["error", "fail", "exception"]):
                level = "ERROR"
            elif any(keyword in log_message.lower() for keyword in ["warn", "warning"]):
                level = "WARN"
                
            result_logs.append(LogEntry(
                id=hit.get("_id", ""),
                timestamp=source.get("@timestamp", ""),
                level=level,
                service=node_id,
                message=log_message,
                node_id=node_id,
                event_type="log_entry",
                metadata={
                    "filename": source.get("filename", ""),
                    "index": hit.get("_index", "")
                }
            ))
        
        return result_logs
    except Exception as e:
        print(f"Error fetching node logs: {e}")
        return []

@app.post("/logs/search", response_model=List[LogEntry])
async def search_logs(query: LogQuery):
    """Advanced log search with multiple filters"""
    return await get_logs(
        level=",".join(query.level) if query.level else None,
        event_type=query.event_type,
        node_id=query.node_id,
        service=query.service,
        time_range=query.time_range,
        size=query.size,
        search=query.search_term
    )

@app.get("/logs/stats")
async def get_log_stats():
    """Get log statistics and counts"""
    try:
        session = get_opensearch_session()
        
        # Get total count across all log indexes
        total_count = 0
        for index in ["client-logs", "frr-router-logs", "server-logs", "switch1-logs", "switch2-logs"]:
            url = f"{OPENSEARCH_BASE_URL}/{index}/_count"
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
        
        url = f"{OPENSEARCH_BASE_URL}/*-logs/_count"
        response = session.post(url, json=recent_query, headers={"Content-Type": "application/json"})
        recent_count = response.json().get("count", 0) if response.status_code == 200 else 0
        
        return {
            "total_logs": total_count,
            "recent_logs_1h": recent_count,
            "level_counts": {"INFO": total_count},  # Simplified since logs don't have explicit levels
            "opensearch_available": True,
            "indexes": ["client-logs", "frr-router-logs", "server-logs", "switch1-logs", "switch2-logs"]
        }
        
    except Exception as e:
        return {
            "total_logs": 0,
            "recent_logs_1h": 0,
            "level_counts": {},
            "opensearch_available": False,
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3001) 