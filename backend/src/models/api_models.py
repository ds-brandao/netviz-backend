"""
Pydantic models for API request/response validation.
Centralized location for all API data models.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Model for basic chat requests"""
    message: str
    session_id: Optional[str] = "default"


class StreamingChatRequest(BaseModel):
    """Model for streaming chat requests with context"""
    message: str
    session_id: Optional[str] = "default"
    context: Optional[Dict[str, Any]] = None  # Network context (focused node, etc)
    conversation_history: Optional[List[Dict[str, str]]] = None  # Previous messages for context
    

class NetworkNodeData(BaseModel):
    """Model for network node data"""
    name: str
    type: str
    ip_address: Optional[str] = None
    status: str = "unknown"
    layer: str = "network"
    position: Optional[Dict[str, float]] = {"x": 0.0, "y": 0.0}
    metadata: Dict[str, Any] = {}


class NetworkEdgeData(BaseModel):
    """Model for network edge data"""
    source: str  # node ID
    target: str  # node ID
    type: str = "ethernet"
    bandwidth: Optional[str] = None
    utilization: float = 0.0
    status: str = "unknown"
    metadata: Dict[str, Any] = {}


class GraphUpdateRequest(BaseModel):
    """Model for bulk graph updates from external devices"""
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    source: str = "external_device"


class LogQuery(BaseModel):
    """Model for log search queries"""
    level: Optional[List[str]] = None
    event_type: Optional[str] = None
    node_id: Optional[str] = None
    service: Optional[str] = None
    time_range: Optional[str] = None
    size: int = 20
    search_term: Optional[str] = None


class LogEntry(BaseModel):
    """Model for log entries"""
    id: str
    timestamp: str
    level: str
    service: str
    message: str
    node_id: str
    event_type: str
    metadata: Dict[str, Any]