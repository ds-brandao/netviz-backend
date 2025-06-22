#!/usr/bin/env python3
"""
Test script that simulates frontend behavior to test streaming chat with tool calling
"""

import asyncio
import aiohttp
import json

async def test_frontend_streaming():
    """Simulate frontend streaming chat request"""
    
    print("🌐 Testing Frontend Simulation - Streaming Chat with Tool Calling")
    print("=" * 70)
    
    # Simulate the exact request the frontend makes
    request_data = {
        "message": "Show me the network status",
        "session_id": "test_frontend",
        "context": {
            "focused_node": {
                "id": "test-node",
                "label": "Test Node",
                "type": "router",
                "status": "online",
                "ip": "192.168.1.1"
            },
            "network_stats": {
                "total_nodes": 5,
                "active": 4,
                "issues": 1
            }
        }
    }
    
    print(f"📝 Request: {request_data['message']}")
    print(f"🎯 Context: {request_data['context']['focused_node']['label']}")
    print("\n🤖 AI Response:")
    print("-" * 50)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                'http://localhost:3001/chat/stream',
                json=request_data,
                headers={'Content-Type': 'application/json'}
            ) as response:
                
                if response.status != 200:
                    print(f"❌ HTTP Error: {response.status}")
                    return
                
                # Process SSE stream like the frontend does
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        
                        if data_str == '[DONE]':
                            break
                            
                        try:
                            chunk = json.loads(data_str)
                            
                            # Simulate frontend processing
                            if chunk.get('type') == 'text':
                                print(chunk.get('content', ''), end='', flush=True)
                                
                            elif chunk.get('type') == 'tool_call':
                                print(f"\n🔧 TOOL CALL: {chunk.get('toolName')}")
                                print(f"   📋 Args: {chunk.get('args')}")
                                print(f"   🆔 ID: {chunk.get('toolCallId')}")
                                
                            elif chunk.get('type') == 'tool_result':
                                print(f"\n✅ TOOL RESULT:")
                                result = chunk.get('result')
                                if isinstance(result, dict):
                                    for key, value in result.items():
                                        print(f"   {key}: {value}")
                                else:
                                    print(f"   {result}")
                                    
                            elif chunk.get('type') == 'tool_error':
                                print(f"\n❌ TOOL ERROR: {chunk.get('error')}")
                                
                            elif chunk.get('type') == 'error':
                                print(f"\n💥 ERROR: {chunk.get('error')}")
                                
                            elif chunk.get('type') == 'done':
                                print("\n\n✅ Stream completed!")
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"\n⚠️  JSON Parse Error: {e}")
                            print(f"   Raw data: {data_str}")
                
        except Exception as e:
            print(f"💥 Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_frontend_streaming()) 