#!/usr/bin/env python3
"""
Script to query OpenSearch logs for the NetViz backend.
Provides various filtering and search options.
"""

import requests
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class OpenSearchLogQuery:
    def __init__(self, base_url: str = "http://localhost:9200", index: str = "network-logs"):
        self.base_url = base_url
        self.index = index
    
    def query_logs(self, 
                   level: Optional[List[str]] = None,
                   event_type: Optional[str] = None,
                   node_id: Optional[str] = None,
                   service: Optional[str] = None,
                   time_range: Optional[str] = None,
                   size: int = 10,
                   sort_order: str = "desc") -> Dict:
        """
        Query logs with various filters
        
        Args:
            level: List of log levels (INFO, WARN, ERROR)
            event_type: Specific event type to filter
            node_id: Specific node ID to filter
            service: Service name to filter
            time_range: Time range (e.g., "1h", "30m", "1d")
            size: Number of results to return
            sort_order: Sort order ("asc" or "desc")
        """
        
        # Build query
        query = {"match_all": {}}
        filters = []
        
        if level:
            filters.append({
                "terms": {
                    "level.keyword": level
                }
            })
        
        if event_type:
            filters.append({
                "term": {
                    "event_type.keyword": event_type
                }
            })
        
        if node_id:
            filters.append({
                "term": {
                    "node_id.keyword": node_id
                }
            })
        
        if service:
            filters.append({
                "term": {
                    "service.keyword": service
                }
            })
        
        if time_range:
            filters.append({
                "range": {
                    "timestamp": {
                        "gte": f"now-{time_range}"
                    }
                }
            })
        
        if filters:
            query = {
                "bool": {
                    "must": filters
                }
            }
        
        # Build search request
        search_body = {
            "query": query,
            "sort": [
                {
                    "timestamp": {
                        "order": sort_order
                    }
                }
            ],
            "size": size
        }
        
        # Execute query
        url = f"{self.base_url}/{self.index}/_search"
        response = requests.post(url, 
                               headers={"Content-Type": "application/json"},
                               json=search_body)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Query failed: {response.status_code} - {response.text}")
    
    def get_recent_logs(self, minutes: int = 30, size: int = 20) -> Dict:
        """Get logs from the last N minutes"""
        return self.query_logs(time_range=f"{minutes}m", size=size)
    
    def get_error_logs(self, hours: int = 24, size: int = 50) -> Dict:
        """Get error and warning logs from the last N hours"""
        return self.query_logs(level=["ERROR", "WARN"], time_range=f"{hours}h", size=size)
    
    def get_device_logs(self, device_id: str, hours: int = 24, size: int = 30) -> Dict:
        """Get logs for a specific device"""
        return self.query_logs(node_id=device_id, time_range=f"{hours}h", size=size)
    
    def search_logs(self, search_term: str, size: int = 20) -> Dict:
        """Search logs by message content"""
        search_body = {
            "query": {
                "multi_match": {
                    "query": search_term,
                    "fields": ["message", "event_type", "node_id"]
                }
            },
            "sort": [
                {
                    "timestamp": {
                        "order": "desc"
                    }
                }
            ],
            "size": size
        }
        
        url = f"{self.base_url}/{self.index}/_search"
        response = requests.post(url, 
                               headers={"Content-Type": "application/json"},
                               json=search_body)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Search failed: {response.status_code} - {response.text}")
    
    def format_log_output(self, results: Dict, show_metadata: bool = False) -> str:
        """Format query results for display"""
        if "hits" not in results or "hits" not in results["hits"]:
            return "No logs found."
        
        logs = results["hits"]["hits"]
        if not logs:
            return "No logs found."
        
        output = []
        output.append(f"Found {results['hits']['total']['value']} total logs\n")
        output.append("=" * 80)
        
        for log in logs:
            source = log["_source"]
            timestamp = source.get("timestamp", "N/A")
            level = source.get("level", "N/A")
            service = source.get("service", "N/A")
            node_id = source.get("node_id", "N/A")
            event_type = source.get("event_type", "N/A")
            message = source.get("message", "N/A")
            
            output.append(f"[{timestamp}] {level} - {service}")
            output.append(f"Node: {node_id} | Event: {event_type}")
            output.append(f"Message: {message}")
            
            if show_metadata and "metadata" in source:
                metadata = source["metadata"]
                output.append("Metadata:")
                for key, value in metadata.items():
                    output.append(f"  {key}: {value}")
            
            output.append("-" * 80)
        
        return "\n".join(output)

def main():
    parser = argparse.ArgumentParser(description="Query OpenSearch logs for NetViz backend")
    parser.add_argument("--level", nargs="+", choices=["INFO", "WARN", "ERROR"], 
                       help="Filter by log level")
    parser.add_argument("--event-type", help="Filter by event type")
    parser.add_argument("--node-id", help="Filter by node ID")
    parser.add_argument("--service", help="Filter by service name")
    parser.add_argument("--time-range", help="Time range (e.g., 1h, 30m, 1d)")
    parser.add_argument("--size", type=int, default=10, help="Number of results")
    parser.add_argument("--search", help="Search term for message content")
    parser.add_argument("--recent", type=int, help="Get logs from last N minutes")
    parser.add_argument("--errors", type=int, help="Get error logs from last N hours")
    parser.add_argument("--device", help="Get logs for specific device")
    parser.add_argument("--metadata", action="store_true", help="Show metadata in output")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    
    args = parser.parse_args()
    
    query_client = OpenSearchLogQuery()
    
    try:
        # Determine which query to run
        if args.recent:
            results = query_client.get_recent_logs(args.recent, args.size)
        elif args.errors:
            results = query_client.get_error_logs(args.errors, args.size)
        elif args.device:
            hours = 24
            if args.time_range and args.time_range.endswith('h'):
                hours = int(args.time_range[:-1])
            results = query_client.get_device_logs(args.device, hours, args.size)
        elif args.search:
            results = query_client.search_logs(args.search, args.size)
        else:
            # General query with filters
            results = query_client.query_logs(
                level=args.level,
                event_type=args.event_type,
                node_id=args.node_id,
                service=args.service,
                time_range=args.time_range,
                size=args.size
            )
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(query_client.format_log_output(results, args.metadata))
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 