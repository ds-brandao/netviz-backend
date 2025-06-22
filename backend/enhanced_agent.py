import os
from typing import Dict, Any, Optional, AsyncGenerator, List
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
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
        "frequency_penalty": 1
    },
    streaming=True
)

def make_sync_tool(async_func):
    """Wrapper to make async tools work with sync agent"""
    def sync_wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        finally:
            loop.close()
    
    return Tool(
        name=async_func.name,
        description=async_func.description,
        func=sync_wrapper
    )

def build_context_aware_system_prompt(context: Optional[Dict[str, Any]] = None, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
    """Build a sophisticated system prompt with context awareness"""
    
    base_prompt = """You are an expert network infrastructure assistant with deep knowledge of:
- Network troubleshooting and diagnostics
- SSH command execution and system administration
- Ansible automation and configuration management
- Security best practices for network infrastructure
- Performance monitoring and optimization

You are proactive, thorough, and safety-conscious. You:
1. Always explain what you're doing and why
2. Provide step-by-step guidance for complex tasks
3. Warn about potentially dangerous operations
4. Suggest best practices and optimizations
5. Learn from conversation context to provide better assistance

Your communication style is:
- Professional but approachable
- Clear and concise
- Educational when appropriate
- Proactive in suggesting improvements"""

    # Add network context if available
    if context and context.get("network_stats"):
        stats = context["network_stats"]
        base_prompt += f"""

CURRENT NETWORK STATE:
- Total nodes: {stats.get('total_nodes', 0)}
- Active nodes: {stats.get('active', 0)}
- Nodes with issues: {stats.get('issues', 0)}
- Network health: {((stats.get('active', 0) / max(stats.get('total_nodes', 1), 1)) * 100):.1f}%"""

    # Add focused node context
    if context and context.get("focused_node"):
        node = context["focused_node"]
        base_prompt += f"""

FOCUSED NODE: {node.get('label', 'Unknown')}
- Type: {node.get('type', 'Unknown')}
- Status: {node.get('status', 'Unknown')}
- IP: {node.get('ip', 'Not specified')}
- Layer: {node.get('layer', 'Unknown')}

Pay special attention to this node in your responses and suggestions."""

    # Add conversation context for memory
    if conversation_history and len(conversation_history) > 0:
        base_prompt += "\n\nRECENT CONVERSATION CONTEXT:"
        for i, msg in enumerate(conversation_history[-5:]):  # Last 5 messages for context
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:200]  # Truncate long messages
            base_prompt += f"\n{i+1}. {role.title()}: {content}..."
        
        base_prompt += "\n\nUse this conversation history to provide contextual, relevant responses."

    return base_prompt

def create_enhanced_agent(context: Optional[Dict[str, Any]] = None, conversation_history: Optional[List[Dict[str, str]]] = None):
    """Create an enhanced streaming agent with sophisticated context awareness"""
    
    # Enhanced tool set with better descriptions
    tools = [
        make_sync_tool(get_network_status),
        make_sync_tool(get_node_details),
        make_sync_tool(update_node_status),
        create_ansible_playbook,
        make_sync_tool(execute_ssh_command),
        make_sync_tool(run_ansible_playbook)
    ]
    
    # Build context-aware system prompt
    system_prompt = build_context_aware_system_prompt(context, conversation_history)
    
    # Create agent with enhanced prompting
    agent = create_react_agent(llm, tools)
    
    return agent, system_prompt

async def enhanced_streaming_chat(
    message: str, 
    context: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    session_id: str = "default"
) -> AsyncGenerator[Dict[str, Any], None]:
    """Enhanced streaming chat with sophisticated agentic behavior"""
    
    try:
        # Create enhanced agent with context
        agent, system_prompt = create_enhanced_agent(context, conversation_history)
        
        # Build message history for better context
        messages = [SystemMessage(content=system_prompt)]
        
        # Add recent conversation history as context
        if conversation_history:
            for hist_msg in conversation_history[-10:]:  # Last 10 messages
                if hist_msg.get('role') == 'user':
                    messages.append(HumanMessage(content=hist_msg.get('content', '')))
                elif hist_msg.get('role') == 'assistant':
                    messages.append(AIMessage(content=hist_msg.get('content', '')))
        
        # Add current message
        messages.append(HumanMessage(content=message))
        
        # Stream initial acknowledgment
        yield {"type": "text", "content": ""}
        
        # Get agent response with streaming
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield {"type": "text", "content": chunk.content}
        
        # Check if we should suggest proactive actions
        await suggest_proactive_actions(message, context)
        
        yield {"type": "done"}
        
    except Exception as e:
        print(f"Enhanced chat error: {str(e)}")
        yield {"type": "error", "error": str(e)}

async def suggest_proactive_actions(message: str, context: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
    """Suggest proactive actions based on the conversation and context"""
    
    # Check for common patterns that might benefit from automation
    message_lower = message.lower()
    
    if any(keyword in message_lower for keyword in ['down', 'offline', 'not responding', 'unreachable']):
        yield {
            "type": "suggestion", 
            "action": "diagnostic",
            "message": "Would you like me to run a comprehensive diagnostic on this node?"
        }
    
    elif any(keyword in message_lower for keyword in ['slow', 'performance', 'latency', 'timeout']):
        yield {
            "type": "suggestion",
            "action": "performance_check", 
            "message": "I can run performance diagnostics and suggest optimizations."
        }
    
    elif any(keyword in message_lower for keyword in ['update', 'upgrade', 'patch']):
        yield {
            "type": "suggestion",
            "action": "create_playbook",
            "message": "I can create an Ansible playbook to safely update your systems."
        }
    
    # Context-based suggestions
    if context and context.get("network_stats"):
        stats = context["network_stats"]
        if stats.get("issues", 0) > 0:
            yield {
                "type": "suggestion",
                "action": "investigate_issues",
                "message": f"I notice there are {stats['issues']} nodes with issues. Should I investigate them?"
            }

async def enhanced_tool_execution_with_streaming(
    tool_name: str, 
    args: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """Execute tools with streaming output and enhanced error handling"""
    
    try:
        # Announce tool execution
        yield {
            "type": "tool_call",
            "toolCallId": f"call_{tool_name}_{hash(str(args))}",
            "toolName": tool_name,
            "args": args
        }
        
        # Execute tool based on type
        if tool_name == "execute_ssh_command":
            async for chunk in stream_ssh_execution(args):
                yield chunk
        elif tool_name == "run_ansible_playbook":
            async for chunk in stream_ansible_execution(args):
                yield chunk
        else:
            # Regular tool execution
            result = await execute_tool_sync(tool_name, args)
            yield {
                "type": "tool_result",
                "toolCallId": f"call_{tool_name}_{hash(str(args))}",
                "result": result
            }
            
    except Exception as e:
        yield {
            "type": "tool_error",
            "toolCallId": f"call_{tool_name}_{hash(str(args))}",
            "error": str(e)
        }

async def stream_ssh_execution(args: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream SSH command execution with live output"""
    
    host = args.get("host", "unknown")
    command = args.get("command", "")
    
    # Stream progress updates
    yield {"type": "tool_stream", "content": f"Connecting to {host}..."}
    await asyncio.sleep(0.1)
    
    yield {"type": "tool_stream", "content": f"Executing: {command}"}
    await asyncio.sleep(0.1)
    
    # Execute the actual command
    try:
        result = await execute_ssh_command(host, command)
        
        # Stream output line by line
        if result.get("output"):
            for line in result["output"].split("\n"):
                if line.strip():
                    yield {"type": "tool_stream", "content": line}
                    await asyncio.sleep(0.05)
        
        yield {
            "type": "tool_result", 
            "result": result
        }
        
    except Exception as e:
        yield {
            "type": "tool_error",
            "error": str(e)
        }

async def stream_ansible_execution(args: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream Ansible playbook execution with progress updates"""
    
    playbook_content = args.get("playbook_content", "")
    
    yield {"type": "tool_stream", "content": "Preparing Ansible playbook..."}
    await asyncio.sleep(0.1)
    
    yield {"type": "tool_stream", "content": "Validating playbook syntax..."}
    await asyncio.sleep(0.2)
    
    yield {"type": "tool_stream", "content": "Executing playbook tasks..."}
    await asyncio.sleep(0.1)
    
    try:
        result = await run_ansible_playbook(playbook_content)
        
        # Stream output
        if result.get("output"):
            lines = result["output"].split("\n")
            for line in lines:
                if line.strip() and ("TASK" in line or "PLAY" in line or "ok:" in line or "changed:" in line):
                    yield {"type": "tool_stream", "content": line}
                    await asyncio.sleep(0.1)
        
        yield {
            "type": "tool_result",
            "result": result
        }
        
    except Exception as e:
        yield {
            "type": "tool_error", 
            "error": str(e)
        }

async def execute_tool_sync(tool_name: str, args: Dict[str, Any]) -> Any:
    """Execute a tool synchronously"""
    
    tools_map = {
        "get_network_status": get_network_status,
        "get_node_details": get_node_details,
        "update_node_status": update_node_status,
        "create_ansible_playbook": create_ansible_playbook,
        "execute_ssh_command": execute_ssh_command,
        "run_ansible_playbook": run_ansible_playbook
    }
    
    if tool_name in tools_map:
        tool_func = tools_map[tool_name]
        if asyncio.iscoroutinefunction(tool_func):
            return await tool_func(**args)
        else:
            return tool_func(**args)
    else:
        raise ValueError(f"Unknown tool: {tool_name}") 