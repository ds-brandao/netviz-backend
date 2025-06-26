#!/usr/bin/env python3
"""
Test script to verify Llama API function calling is working properly.
"""

import os
import sys
import asyncio
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the Python path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.agent import agent_streaming_chat

load_dotenv()

@pytest.mark.asyncio
async def test_function_calling():
    """Test function calling with a simple network status request"""
    
    print("🧪 Testing Llama API Function Calling...")
    print("=" * 50)
    
    # Test message that should trigger tool calling
    test_message = "Show me the current network status"
    
    print(f"📝 Test message: {test_message}")
    print("\n🤖 AI Response:")
    print("-" * 30)
    
    try:
        async for chunk in agent_streaming_chat(test_message):
            if chunk["type"] == "text":
                print(chunk["content"], end="", flush=True)
            elif chunk["type"] == "tool_call":
                print(f"\n🔧 Tool Call: {chunk['toolName']}")
                print(f"   Args: {chunk['args']}")
            elif chunk["type"] == "tool_result":
                print(f"✅ Tool Result: {chunk['result']}")
            elif chunk["type"] == "tool_error":
                print(f"❌ Tool Error: {chunk['error']}")
            elif chunk["type"] == "error":
                print(f"💥 Error: {chunk['error']}")
            elif chunk["type"] == "done":
                print("\n\n✅ Test completed!")
                break
                
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()

@pytest.mark.asyncio
async def test_simple_chat():
    """Test simple chat without function calling"""
    
    print("\n🧪 Testing Simple Chat...")
    print("=" * 50)
    
    test_message = "Hello! Can you explain what you do?"
    
    print(f"📝 Test message: {test_message}")
    print("\n🤖 AI Response:")
    print("-" * 30)
    
    try:
        async for chunk in agent_streaming_chat(test_message):
            if chunk["type"] == "text":
                print(chunk["content"], end="", flush=True)
            elif chunk["type"] == "done":
                print("\n\n✅ Simple chat test completed!")
                break
                
    except Exception as e:
        print(f"💥 Test failed with error: {e}")

if __name__ == "__main__":
    print("🦙 Llama API Function Calling Test")
    print("=" * 60)
    
    # Check if API key is set
    if not os.getenv("LLAMA_API_KEY"):
        print("❌ LLAMA_API_KEY environment variable not set!")
        print("   Please set your Llama API key in .env file")
        exit(1)
    
    print(f"✅ LLAMA_API_KEY found: {os.getenv('LLAMA_API_KEY')[:10]}...")
    print()
    
    # Run tests
    asyncio.run(test_simple_chat())
    asyncio.run(test_function_calling()) 