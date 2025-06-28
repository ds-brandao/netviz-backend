"""
Logs API endpoints.
Handles log querying, searching, and statistics.
"""

from typing import List, Optional
from fastapi import APIRouter

from src.models import LogQuery, LogEntry
from src.services.opensearch_service import opensearch_service

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("/", response_model=List[LogEntry])
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
        
        logs = await opensearch_service.query_logs("*-logs", opensearch_query, size)
        
        # Transform to our format
        result_logs = []
        for hit in logs:
            source = hit.get("_source", {})
            log_message = source.get("log", "")
            
            # Infer log level from content
            level = opensearch_service._infer_log_level(log_message)
            
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


@router.get("/recent", response_model=List[LogEntry])
async def get_recent_logs(minutes: int = 30, size: int = 50):
    """Get logs from the last N minutes"""
    return await opensearch_service.fetch_recent_logs(minutes, size)


@router.get("/errors", response_model=List[LogEntry])
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
        
        logs = await opensearch_service.query_logs("*-logs", query, size)
        
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


@router.get("/node/{node_id}", response_model=List[LogEntry])
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
        
        logs = await opensearch_service.query_logs(f"{node_id}-logs", query, size)
        
        result_logs = []
        for hit in logs:
            source = hit.get("_source", {})
            log_message = source.get("log", "")
            
            # Infer log level from content
            level = opensearch_service._infer_log_level(log_message)
                
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


@router.post("/search", response_model=List[LogEntry])
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


@router.get("/stats")
async def get_log_stats():
    """Get log statistics and counts"""
    return await opensearch_service.get_log_stats()