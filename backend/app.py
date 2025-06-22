from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
import uvicorn
import json
import asyncio
from uuid import uuid4

from agent import create_agent, create_streaming_agent, simple_streaming_chat
from database import init_db, get_db_session, Chat, NetworkNode, NetworkEdge
from graph_service import graph_service
from websocket_manager import connection_manager, periodic_ping
from sqlalchemy import select
import time

app = FastAPI(title="NetViz Backend", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    await init_db()
    # Start periodic ping task
    asyncio.create_task(periodic_ping())

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
                
                # Try using the simple streaming chat function with history
                async for chunk in simple_streaming_chat(request.message, request.context, conversation_history):
                    if chunk["type"] == "text":
                        full_response += chunk["content"]
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3001) 