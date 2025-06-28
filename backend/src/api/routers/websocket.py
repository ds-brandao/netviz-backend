"""
WebSocket API endpoints.
Handles real-time communication with clients.
"""

import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.services.graph_service import graph_service
from websocket_manager import connection_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{session_id}")
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