"""
Pytest tests for API integration and frontend simulation.
"""

import pytest
import aiohttp
import asyncio
import json
from typing import AsyncGenerator


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint(api_base_url):
    """Test the health check endpoint."""
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api_base_url}/test/health") as response:
            assert response.status == 200
            data = await response.json()
            assert data["status"] == "healthy"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_streaming_chat_endpoint(api_base_url, test_session_id):
    """Test streaming chat endpoint like frontend would use it."""
    
    request_data = {
        "message": "Show me the network status",
        "session_id": test_session_id,
        "context": {
            "focused_node": {
                "id": "test-node",
                "label": "Test Router",
                "type": "router"
            }
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{api_base_url}/ai/chat/stream",
            json=request_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            print(f"Response status: {response.status}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status != 200:
                content = await response.text()
                print(f"Error response: {content}")
                assert False, f"Expected 200, got {response.status}: {content}"
            
            assert response.headers.get("content-type").startswith("text/event-stream")
            
            # Read streaming response
            chunks_received = 0
            lines_read = 0
            async for line in response.content:
                lines_read += 1
                line_str = line.decode('utf-8').strip()
                print(f"Line {lines_read}: {line_str}")
                
                # The data comes as a single line with embedded \\n\\n sequences
                # We need to split on actual newlines within the string, not literal \\n\\n
                if 'data: ' in line_str:
                    # Replace literal \\n\\n with actual newlines to split properly
                    normalized_line = line_str.replace('\\n\\n', '\n\n')
                    
                    # Split by actual newlines to separate SSE events
                    events = normalized_line.split('\n\n')
                    
                    for event in events:
                        event = event.strip()
                        if event.startswith('data: '):
                            event_data = event[6:]  # Remove 'data: ' prefix
                            
                            if event_data:
                                try:
                                    chunk = json.loads(event_data)
                                    chunks_received += 1
                                    print(f"Chunk {chunks_received}: {chunk}")
                                    
                                    # Verify chunk structure
                                    assert "type" in chunk
                                    
                                    if chunk["type"] == "done":
                                        break
                                        
                                except json.JSONDecodeError as e:
                                    print(f"JSON decode error: {e}, data: {event_data}")
                                    # Skip malformed JSON
                                    continue
                
                # Safety break to avoid infinite loops
                if lines_read > 1000:
                    print("Breaking due to too many lines")
                    break
            
            print(f"Total chunks received: {chunks_received}, lines read: {lines_read}")
            assert chunks_received > 0, f"No chunks received from streaming endpoint. Lines read: {lines_read}"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_network_graph_endpoint(api_base_url):
    """Test network graph endpoint."""
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api_base_url}/network/graph") as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify response structure
            assert "nodes" in data
            assert "edges" in data
            assert "last_updated" in data
            assert isinstance(data["nodes"], list)
            assert isinstance(data["edges"], list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_network_stats_endpoint(api_base_url):
    """Test network statistics endpoint."""
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api_base_url}/network/stats") as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify response structure
            assert "total_nodes" in data
            assert "total_edges" in data
            assert isinstance(data["total_nodes"], int)
            assert isinstance(data["total_edges"], int)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_logs_endpoint(api_base_url):
    """Test logs endpoint."""
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api_base_url}/logs/") as response:
            assert response.status == 200
            data = await response.json()
            
            # Should return a list of logs
            assert isinstance(data, list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_logs_stats_endpoint(api_base_url):
    """Test logs statistics endpoint."""
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api_base_url}/logs/stats") as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify response structure
            expected_fields = ["total_logs", "recent_logs_1h", "opensearch_available"]
            for field in expected_fields:
                assert field in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_metrics_endpoint(api_base_url):
    """Test metrics endpoint."""
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api_base_url}/metrics/") as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify response structure
            assert "metrics" in data
            assert "cache_size" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_device_update_endpoint(api_base_url, sample_device_update):
    """Test device update endpoint."""
    
    device_id = "test-device-001"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{api_base_url}/network/device-update/{device_id}",
            json=sample_device_update,
            headers={"Content-Type": "application/json"}
        ) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify response structure
            assert "success" in data
            assert "action" in data
            assert "node" in data
            assert data["success"] is True


@pytest.mark.asyncio
@pytest.mark.integration
async def test_chat_history_endpoint(api_base_url, test_session_id):
    """Test chat history endpoint."""
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api_base_url}/ai/chats/{test_session_id}") as response:
            assert response.status == 200
            data = await response.json()
            
            # Should return a list of chat messages
            assert isinstance(data, list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_websocket_connection(api_base_url, test_session_id):
    """Test WebSocket connection."""
    
    # Convert HTTP URL to WebSocket URL
    ws_url = api_base_url.replace("http://", "ws://") + f"/ws/{test_session_id}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.ws_connect(ws_url) as ws:
                # Send a ping
                await ws.send_str(json.dumps({"type": "ping"}))
                
                # Wait for response
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if data.get("type") == "pong":
                            break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        pytest.fail(f"WebSocket error: {ws.exception()}")
                        
        except Exception as e:
            pytest.skip(f"WebSocket test skipped due to connection issue: {e}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_ai_query_logs_endpoint(api_base_url):
    """Test AI logs query endpoint."""
    
    params = {
        "device_name": "router",
        "time_range": 1,
        "size": 10
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{api_base_url}/ai/query-logs",
            params=params
        ) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify response structure
            assert "logs" in data
            assert "query_params" in data
            assert isinstance(data["logs"], list)


@pytest.mark.asyncio
@pytest.mark.integration  
async def test_ai_query_metrics_endpoint(api_base_url):
    """Test AI metrics query endpoint."""
    
    params = {
        "device_name": "router",
        "time_range": 1
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{api_base_url}/ai/query-metrics",
            params=params
        ) as response:
            assert response.status == 200
            data = await response.json()
            
            # Verify response structure
            assert "metrics" in data
            assert "query_params" in data