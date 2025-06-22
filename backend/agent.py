import os
from typing import Dict, Any, Optional, AsyncGenerator
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import Tool
from dotenv import load_dotenv
import asyncio
import json

from tools import (
    get_network_status, 
    create_ansible_playbook, 
    execute_ssh_command,
    run_ansible_playbook,
    get_node_details,
    update_node_status,
    get_recent_logs,
    get_error_logs,
    search_logs,
    get_device_info
)

load_dotenv()

# Initialize LLM (try OpenAI first, fallback to Llama)
try:
    # Try OpenAI first for better tool calling support
    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4",
        temperature=0.6,
        max_tokens=2048,
        streaming=True
    )
    print("Using OpenAI GPT-4 for tool calling")
except:
    # Fallback to Llama
    llm = ChatOpenAI(
        api_key=os.getenv("LLAMA_API_KEY", "dummy-key"),
        base_url="https://api.llama.com/compat/v1/",
        model="Llama-4-Maverick-17B-128E-Instruct-FP8",
        temperature=0.6,
        max_tokens=2048,
        model_kwargs={
            "top_p": 0.9,
            "frequency_penalty": 0
        },
        streaming=True
    )
    print("Using Llama for tool calling")

# Wrapper for async tools to make them sync
def make_sync_tool(async_func):
    """Wrapper to make async tools work with sync agent"""
    def sync_wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        finally:
            loop.close()
    
    # Create a Tool object with the sync wrapper
    return Tool(
        name=async_func.name,
        description=async_func.description,
        func=sync_wrapper
    )

def create_agent():
    """Create and return the LangGraph agent using prebuilt ReAct pattern"""
    # Convert async tools to sync
    tools = [
        make_sync_tool(get_network_status),
        create_ansible_playbook  # This one is already sync
    ]
    
    # Create agent without system prompt for now
    return create_react_agent(llm, tools)

def create_streaming_agent(context: Optional[Dict[str, Any]] = None):
    """Create a streaming agent with context awareness and enhanced tools"""
    
    # Use async tools directly - LangGraph handles async properly
    tools = [
        get_network_status,
        get_node_details,
        update_node_status,
        get_recent_logs,
        get_error_logs,
        search_logs,
        get_device_info,
        create_ansible_playbook,  # Already sync
        execute_ssh_command,
        run_ansible_playbook
    ]
    
    # Create agent
    return create_react_agent(llm, tools)

async def agent_streaming_chat(message: str, context: Optional[Dict[str, Any]] = None, conversation_history: Optional[list] = None) -> AsyncGenerator[Dict[str, Any], None]:
    """Agent-based streaming chat with tool calling capabilities"""
    
    try:
        # Create agent with tools
        print(f"Creating agent with context: {context}")
        agent = create_streaming_agent(context)
        print(f"Agent created successfully with {len(agent.tools)} tools")
        
        # Build context-aware system prompt
        system_prompt = """You are an expert network infrastructure assistant with real-time access to live network data. You help users manage and troubleshoot their network infrastructure using actual tools and data.

ALWAYS USE TOOLS - Never simulate or guess responses. You have access to:

**Device Analysis Tools:**
- get_device_info(device_id) - Get comprehensive device info with metrics and recent logs
- get_network_status() - Check all network devices status

**Log Analysis Tools (ALWAYS USE THESE):**
- get_recent_logs(device_name, time_range, log_level) - Get recent logs from OpenSearch
- get_error_logs(hours) - Get error/warning logs for troubleshooting  
- search_logs(search_term) - Search logs for specific patterns

**Automation Tools:**
- create_ansible_playbook() - Create real Ansible playbooks for automation
- execute_ssh_command() - Run SSH commands on devices
- run_ansible_playbook() - Execute playbooks

**IMPORTANT**: When asked for logs, device info, or network status, ALWAYS call the appropriate tool. Never provide simulated data.

Context: The user is currently focused on device: {context.get('focused_device', 'none') if context else 'none'}

Remember our conversation history and provide contextual responses based on what we've discussed previously."""
        
        if context and context.get("network_stats"):
            stats = context["network_stats"]
            system_prompt += f"\n\nCurrent network has {stats.get('total_nodes', 0)} nodes, {stats.get('active', 0)} active, {stats.get('issues', 0)} with issues."
        
        if context and context.get("focused_node"):
            focused_node = context["focused_node"]
            system_prompt += f"\n\nUser is currently focused on node: {focused_node.get('label', 'Unknown')} ({focused_node.get('type', 'Unknown type')}, Status: {focused_node.get('status', 'Unknown')})"
        
        # Build messages
        messages = [SystemMessage(content=system_prompt)]
        
        # Add conversation history if provided
        if conversation_history:
            for hist_msg in conversation_history[-10:]:  # Keep last 10 messages for context
                if hist_msg.get("role") == "user":
                    messages.append(HumanMessage(content=hist_msg["content"]))
                elif hist_msg.get("role") == "assistant":
                    messages.append(AIMessage(content=hist_msg["content"]))
        
        # Add current message
        messages.append(HumanMessage(content=message))
        
        print(f"Invoking agent with {len(messages)} messages")
        print(f"User message: {message}")
        
        # Invoke agent with streaming
        async for chunk in agent.astream({"messages": messages}):
            if "agent" in chunk:
                agent_output = chunk["agent"]
                if "messages" in agent_output:
                    for msg in agent_output["messages"]:
                        if hasattr(msg, 'content') and msg.content:
                            yield {"type": "text", "content": msg.content}
            elif "tools" in chunk:
                tools_output = chunk["tools"]
                if "messages" in tools_output:
                    for msg in tools_output["messages"]:
                        if hasattr(msg, 'content') and msg.content:
                            yield {"type": "tool_result", "content": msg.content}
        
        yield {"type": "done"}
        
    except Exception as e:
        print(f"Error in agent streaming chat: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to simple streaming
        async for chunk in simple_streaming_chat(message, context, conversation_history):
            yield chunk

async def simple_streaming_chat(message: str, context: Optional[Dict[str, Any]] = None, conversation_history: Optional[list] = None) -> AsyncGenerator[Dict[str, Any], None]:
    """Simple streaming chat implementation with conversation memory"""
    
    # Build context-aware system prompt
    system_prompt = """You are an expert network infrastructure assistant. You help users manage and troubleshoot their network infrastructure.

Key capabilities:
- Check network device status and details
- Query and analyze system logs (recent logs, error logs, search logs)
- Create and execute Ansible playbooks
- Run SSH commands on remote hosts
- Troubleshoot connectivity issues
- Explain networking concepts

Log Analysis Features:
- View recent logs for any device or time period
- Search for specific error patterns or events
- Analyze error and warning logs for troubleshooting
- Filter logs by level (INFO, WARN, ERROR) and event type

Remember our conversation history and provide contextual responses based on what we've discussed previously."""
    
    if context and context.get("network_stats"):
        stats = context["network_stats"]
        system_prompt += f"\n\nCurrent network has {stats.get('total_nodes', 0)} nodes, {stats.get('active', 0)} active, {stats.get('issues', 0)} with issues."
    
    if context and context.get("focused_node"):
        focused_node = context["focused_node"]
        system_prompt += f"\n\nUser is currently focused on node: {focused_node.get('label', 'Unknown')} ({focused_node.get('type', 'Unknown type')}, Status: {focused_node.get('status', 'Unknown')})"
    
    # Start with system message
    messages = [SystemMessage(content=system_prompt)]
    
    # Add conversation history if provided
    if conversation_history:
        for hist_msg in conversation_history[-10:]:  # Keep last 10 messages for context
            if hist_msg.get("role") == "user":
                messages.append(HumanMessage(content=hist_msg["content"]))
            elif hist_msg.get("role") == "assistant":
                messages.append(AIMessage(content=hist_msg["content"]))
    
    # Add current message
    messages.append(HumanMessage(content=message))
    
    # Stream the response
    async for chunk in llm.astream(messages):
        if chunk.content:
            yield {"type": "text", "content": chunk.content}
    
    yield {"type": "done"} 