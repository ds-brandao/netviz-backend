import json
import asyncio
from typing import Dict, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time graph updates"""
    
    def __init__(self):
        # Store active connections by session ID
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str = "default"):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        
        self.active_connections[session_id].add(websocket)
        self.connection_metadata[websocket] = {
            "session_id": session_id,
            "connected_at": datetime.now(UTC),
            "last_ping": datetime.now(UTC)
        }
        
        logger.info(f"WebSocket connected for session {session_id}")
        
        # Send initial connection confirmation
        await self.send_to_connection(websocket, {
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.now(UTC).isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.connection_metadata:
            session_id = self.connection_metadata[websocket]["session_id"]
            
            # Remove from active connections
            if session_id in self.active_connections:
                self.active_connections[session_id].discard(websocket)
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
            
            # Remove metadata
            del self.connection_metadata[websocket]
            
            logger.info(f"WebSocket disconnected for session {session_id}")
    
    async def send_to_connection(self, websocket: WebSocket, data: Dict[str, Any]):
        """Send data to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")
            self.disconnect(websocket)
    
    async def send_to_session(self, session_id: str, data: Dict[str, Any]):
        """Send data to all connections in a session"""
        if session_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[session_id]:
                try:
                    await websocket.send_text(json.dumps(data))
                except Exception as e:
                    logger.error(f"Error sending to WebSocket in session {session_id}: {e}")
                    disconnected.append(websocket)
            
            # Clean up disconnected websockets
            for websocket in disconnected:
                self.disconnect(websocket)
    
    async def broadcast(self, data: Dict[str, Any], exclude_session: Optional[str] = None):
        """Broadcast data to all active connections"""
        for session_id in list(self.active_connections.keys()):
            if exclude_session and session_id == exclude_session:
                continue
            await self.send_to_session(session_id, data)
    
    async def broadcast_graph_update(self, update_type: str, entity_type: str, 
                                   entity_data: Dict[str, Any], source: str = "api"):
        """Broadcast a graph update to all connected clients"""
        update_message = {
            "type": "graph_update",
            "update_type": update_type,  # created, updated, deleted
            "entity_type": entity_type,  # node, edge
            "entity_data": entity_data,
            "source": source,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        await self.broadcast(update_message)
        logger.info(f"Broadcasted {update_type} {entity_type} update from {source}")
    
    async def send_graph_state(self, session_id: str, nodes: list, edges: list):
        """Send complete graph state to a session"""
        state_message = {
            "type": "graph_state",
            "nodes": nodes,
            "edges": edges,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        await self.send_to_session(session_id, state_message)
    
    async def ping_connections(self):
        """Send ping to all connections to keep them alive"""
        ping_message = {
            "type": "ping",
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        await self.broadcast(ping_message)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_session_count(self) -> int:
        """Get number of active sessions"""
        return len(self.active_connections)

# Global connection manager instance
connection_manager = ConnectionManager()

async def periodic_ping():
    """Periodic task to ping all connections"""
    while True:
        await asyncio.sleep(30)  # Ping every 30 seconds
        await connection_manager.ping_connections() 