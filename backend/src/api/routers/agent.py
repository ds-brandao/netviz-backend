"""
AI Agent API endpoints.
Handles chat, streaming chat, and AI tool endpoints.
"""

import json
import asyncio
from typing import AsyncGenerator
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from database.database import get_db_session, Chat, NetworkNode
from src.agent.agent import create_agent, agent_streaming_chat
from src.models.api_models import ChatRequest, StreamingChatRequest
from src.services.opensearch_service import opensearch_service

router = APIRouter(prefix="/ai", tags=["AI Agent"])


@router.post("/query-logs")
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
        
        print(f"Querying OpenSearch with target indexes: {target_indexes}")
        
        logs = await opensearch_service.query_logs(target_indexes, opensearch_query, size)
        
        print(f"OpenSearch query: {opensearch_query}")
        print(f"OpenSearch returned {len(logs)} hits")
        
        # Debug: show which indexes are being hit
        indexes_hit = set()
        for hit in logs:
            indexes_hit.add(hit.get("_index", "unknown"))
        print(f"Indexes in results: {list(indexes_hit)}")
        
        formatted_logs = []
        for hit in logs:
            source = hit["_source"]
            log_message = source.get("log", source.get("message", ""))
            
            # Infer log level from content
            level = opensearch_service._infer_log_level(log_message)
            
            formatted_logs.append({
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
            "logs": formatted_logs,
            "total": len(logs),
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


@router.post("/query-metrics")
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
        
        metrics_data = await opensearch_service.fetch_metrics()
        
        # Filter metrics based on query parameters
        filtered_metrics = {}
        for host_name, host_data in metrics_data.items():
            if device_name and device_name.lower() not in host_name.lower():
                continue
                
            # Apply metric_type filter if specified
            if metric_type:
                # Filter system metrics by type
                if metric_type in ["cpu", "memory", "disk", "load", "uptime"] and "system" in host_data:
                    filtered_host_data = {
                        "timestamp": host_data.get("timestamp"),
                        "host": host_data.get("host", {}),
                        "system": {metric_type: host_data["system"].get(metric_type)},
                        "metric_type": metric_type
                    }
                # Filter container metrics
                elif metric_type == "docker" and "containers" in host_data:
                    filtered_host_data = {
                        "timestamp": host_data.get("timestamp"),
                        "host": host_data.get("host", {}),
                        "containers": host_data.get("containers", []),
                        "metric_type": metric_type
                    }
                else:
                    continue
                filtered_metrics[host_name] = filtered_host_data
            else:
                # No metric_type filter, include all data
                filtered_metrics[host_name] = host_data
        
        metrics = filtered_metrics
        
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


@router.get("/device-info/{device_id}")
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
                    "metadata": device.node_metadata,
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


@router.post("/chat")
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


@router.post("/chat/stream")
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


@router.get("/chats/{session_id}")
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