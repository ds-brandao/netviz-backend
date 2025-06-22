import os
from typing import Dict, Any, Optional, AsyncGenerator
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import Tool
from dotenv import load_dotenv
import asyncio

from tools import (
    get_network_status, 
    create_ansible_playbook, 
    execute_ssh_command,
    run_ansible_playbook,
    get_node_details,
    update_node_status
)

load_dotenv()

# Initialize Llama model with OpenAI compatibility
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
    streaming=True  # Enable streaming
)

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
        create_ansible_playbook,  # Already sync
        execute_ssh_command,
        run_ansible_playbook
    ]
    
    # Create agent
    return create_react_agent(llm, tools)

async def simple_streaming_chat(message: str, context: Optional[Dict[str, Any]] = None, conversation_history: Optional[list] = None) -> AsyncGenerator[Dict[str, Any], None]:
    """Simple streaming chat implementation with conversation memory"""
    
    # Build context-aware system prompt
    system_prompt = """You are an expert network infrastructure assistant. You help users manage and troubleshoot their network infrastructure.

Key capabilities:
- Check network device status and details
- Create and execute Ansible playbooks
- Run SSH commands on remote hosts
- Troubleshoot connectivity issues
- Explain networking concepts

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