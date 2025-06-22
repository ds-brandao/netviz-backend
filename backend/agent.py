import os
from typing import Dict, Any, Optional, AsyncGenerator, List
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import Tool
from dotenv import load_dotenv
import asyncio
import json

# Import the native Llama API client
try:
    from llama_api_client import LlamaAPIClient
    LLAMA_CLIENT_AVAILABLE = False  # Temporarily disable to fix repetition bug
except ImportError:
    LLAMA_CLIENT_AVAILABLE = False
    print("Warning: llama-api-client not installed. Install with: pip install llama-api-client")

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

# Initialize LLM with proper Llama API support
def initialize_llm():
    """Initialize the LLM with proper tool calling support"""
    
    # Try OpenAI first for reliable tool calling
    if os.getenv("OPENAI_API_KEY"):
        try:
            llm = ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-4",
                temperature=0.6,
                max_tokens=2048,
                streaming=True
            )
            print("✅ Using OpenAI GPT-4 for tool calling")
            return llm, "openai"
        except Exception as e:
            print(f"OpenAI initialization failed: {e}")
    
    # Try native Llama API client
    if LLAMA_CLIENT_AVAILABLE and os.getenv("LLAMA_API_KEY"):
        try:
            # Initialize native Llama client
            llama_client = LlamaAPIClient(
                api_key=os.getenv("LLAMA_API_KEY")
            )
            print("✅ Using native Llama API client for tool calling")
            return llama_client, "llama_native"
        except Exception as e:
            print(f"Native Llama API initialization failed: {e}")
    
    # Fallback to OpenAI-compatible Llama API
    try:
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
        print("⚠️  Using Llama API with OpenAI compatibility (limited tool calling)")
        return llm, "llama_compat"
    except Exception as e:
        print(f"Llama API initialization failed: {e}")
        raise Exception("No valid LLM configuration found")

llm, llm_type = initialize_llm()

# Convert tools to Llama API format for native client
def convert_tools_to_llama_format(tools_list):
    """Convert LangChain tools to Llama API function format"""
    functions = []
    
    for tool in tools_list:
        # Extract tool schema
        tool_schema = {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        # Add parameters based on tool signature
        if hasattr(tool, 'args_schema') and tool.args_schema:
            schema = tool.args_schema.schema()
            if 'properties' in schema:
                tool_schema["parameters"]["properties"] = schema['properties']
            if 'required' in schema:
                tool_schema["parameters"]["required"] = schema['required']
        
        functions.append(tool_schema)
    
    return functions

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
        # If using native Llama API, use custom function calling
        if llm_type == "llama_native":
            async for chunk in llama_native_chat_with_tools(message, context, conversation_history):
                yield chunk
            return
        
        # For compatibility mode, try the agent but with better error handling
        print(f"Creating agent with context: {context}")
        print(f"LLM type: {llm_type}")
        
        try:
            agent = create_streaming_agent(context)
            print(f"Agent created successfully with {len(agent.tools)} tools")
            
            # Build context-aware system prompt
            system_prompt = """You are an expert network infrastructure assistant with real-time access to live network data. You help users manage and troubleshoot their network infrastructure using actual tools and data.

CRITICAL: You MUST use the available tools. Do not simulate or make up data. When users ask for:
- Network status → Use get_network_status()
- Device logs → Use get_recent_logs(device_name="device_name")
- Error logs → Use get_error_logs(hours=24)
- Device info → Use get_device_info(device_id="device_id")

Available tools:
- get_network_status() - Get real network device status
- get_recent_logs(device_name, time_range="1h", log_level="INFO") - Get actual logs
- get_error_logs(hours=1) - Get real error/warning logs  
- search_logs(search_term) - Search real log data
- get_device_info(device_id) - Get real device information
- execute_ssh_command(host, command) - Run real SSH commands
- create_ansible_playbook() - Create real automation
- run_ansible_playbook() - Execute real playbooks

IMPORTANT: Always use tools. Never provide fake or simulated data."""
            
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
            return
            
        except Exception as agent_error:
            print(f"Agent execution failed: {agent_error}")
            import traceback
            traceback.print_exc()
            
            # If agent fails, try to manually detect tool calls and execute them
            if any(keyword in message.lower() for keyword in ['network status', 'status', 'devices']):
                print("Detected network status request, executing tool manually")
                yield {"type": "text", "content": "Let me check the network status for you...\n\n"}
                
                try:
                    result = await get_network_status.ainvoke({})
                    yield {"type": "tool_result", "content": f"Network Status:\n{json.dumps(result, indent=2)}"}
                    yield {"type": "done"}
                    return
                except Exception as tool_error:
                    print(f"Manual tool execution failed: {tool_error}")
            
            elif any(keyword in message.lower() for keyword in ['logs', 'recent logs']) and 'switch2' in message.lower():
                print("Detected switch2 logs request, executing tool manually")
                yield {"type": "text", "content": "Let me get the recent logs for switch2...\n\n"}
                
                try:
                    result = await get_recent_logs.ainvoke({"device_name": "switch2"})
                    yield {"type": "tool_result", "content": f"Recent Logs for switch2:\n{json.dumps(result, indent=2)}"}
                    yield {"type": "done"}
                    return
                except Exception as tool_error:
                    print(f"Manual tool execution failed: {tool_error}")
        
        # Fallback to simple streaming if everything fails
        print("Falling back to simple streaming chat")
        async for chunk in simple_streaming_chat(message, context, conversation_history):
            yield chunk
        
    except Exception as e:
        print(f"Error in agent streaming chat: {e}")
        import traceback
        traceback.print_exc()
        yield {"type": "error", "error": str(e)}

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

async def llama_native_chat_with_tools(message: str, context: Optional[Dict[str, Any]] = None, conversation_history: Optional[list] = None) -> AsyncGenerator[Dict[str, Any], None]:
    """Native Llama API chat with custom function calling implementation"""
    
    try:
        # Prepare tools for Llama API
        tools_list = [
            get_network_status,
            get_node_details,
            update_node_status,
            get_recent_logs,
            get_error_logs,
            search_logs,
            get_device_info,
            create_ansible_playbook,
            execute_ssh_command,
            run_ansible_playbook
        ]
        
        # Build enhanced system prompt with function calling instructions
        system_prompt = """You are an expert network infrastructure assistant with real-time access to live network data. You help users manage and troubleshoot their network infrastructure using actual tools and data.

CRITICAL: You have access to the following functions that you MUST use when appropriate. To call a function, use this EXACT format:

FUNCTION_CALL: function_name(parameter1="value1", parameter2="value2")

Available functions:
- get_network_status(node_name=None) - Get status of network devices
- get_device_info(device_id) - Get comprehensive device information  
- get_recent_logs(device_name, time_range="1h", log_level="INFO") - Get recent logs
- get_error_logs(hours=1) - Get error/warning logs for troubleshooting
- search_logs(search_term) - Search logs for specific patterns
- execute_ssh_command(host, command, username="admin") - Run SSH commands
- create_ansible_playbook() - Create Ansible automation playbooks
- run_ansible_playbook() - Execute Ansible playbooks

IMPORTANT RULES:
1. ALWAYS use functions when asked for network status, logs, or device information
2. Use the EXACT format: FUNCTION_CALL: function_name(param="value")
3. Never simulate or make up data - always call the appropriate function
4. When users ask about network status, call get_network_status()
5. When users ask about logs, call get_recent_logs() or get_error_logs()
6. When users want to run commands, call execute_ssh_command()

Remember our conversation history and provide contextual responses."""
        
        if context and context.get("network_stats"):
            stats = context["network_stats"]
            system_prompt += f"\n\nCurrent network has {stats.get('total_nodes', 0)} nodes, {stats.get('active', 0)} active, {stats.get('issues', 0)} with issues."
        
        if context and context.get("focused_node"):
            focused_node = context["focused_node"]
            system_prompt += f"\n\nUser is currently focused on node: {focused_node.get('label', 'Unknown')} ({focused_node.get('type', 'Unknown type')}, Status: {focused_node.get('status', 'Unknown')})"
        
        # Build messages for Llama API
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        if conversation_history:
            for hist_msg in conversation_history[-10:]:
                if hist_msg.get("role") in ["user", "assistant"]:
                    messages.append({
                        "role": hist_msg["role"],
                        "content": hist_msg["content"]
                    })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        print(f"🦙 Making Llama API call with custom function calling")
        
        # Make the API call
        response = llm.chat.completions.create(
            messages=messages,
            model="Llama-4-Maverick-17B-128E-Instruct-FP8",
            stream=True
        )
        
        current_text = ""
        
        # Stream the response and look for function calls
        for chunk in response:
            if hasattr(chunk, 'event') and hasattr(chunk.event, 'delta') and chunk.event.delta.text:
                delta_text = chunk.event.delta.text
                current_text += delta_text
                
                # Check if we have a complete function call
                if "FUNCTION_CALL:" in current_text and ")" in current_text:
                    # Extract and execute function calls
                    lines = current_text.split('\n')
                    for line in lines:
                        if line.strip().startswith("FUNCTION_CALL:"):
                            function_call_text = line.strip().replace("FUNCTION_CALL:", "").strip()
                            
                            # Parse the function call
                            try:
                                function_name, args_text = function_call_text.split('(', 1)
                                function_name = function_name.strip()
                                args_text = args_text.rstrip(')')
                                
                                # Parse arguments
                                args = {}
                                if args_text.strip():
                                    # Simple argument parsing (can be improved)
                                    for arg_pair in args_text.split(','):
                                        if '=' in arg_pair:
                                            key, value = arg_pair.split('=', 1)
                                            key = key.strip()
                                            value = value.strip().strip('"\'')
                                            args[key] = value
                                
                                # Execute the function call
                                yield {
                                    "type": "tool_call",
                                    "toolCallId": f"call_{function_name}_{hash(str(args))}",
                                    "toolName": function_name,
                                    "args": args
                                }
                                
                                # Execute the tool
                                try:
                                    tool_result = await execute_tool_by_name(function_name, args)
                                    yield {
                                        "type": "tool_result",
                                        "toolCallId": f"call_{function_name}_{hash(str(args))}",
                                        "result": tool_result
                                    }
                                    
                                    # Remove the function call from the text
                                    current_text = current_text.replace(line, f"\n[Executed: {function_name}]\n")
                                    
                                except Exception as e:
                                    yield {
                                        "type": "tool_error",
                                        "toolCallId": f"call_{function_name}_{hash(str(args))}",
                                        "error": str(e)
                                    }
                                    
                            except Exception as e:
                                print(f"Error parsing function call '{function_call_text}': {e}")
                
                # Yield the text content (excluding function call lines)
                display_text = current_text
                for line in current_text.split('\n'):
                    if line.strip().startswith("FUNCTION_CALL:"):
                        display_text = display_text.replace(line, "")
                
                if display_text != current_text:
                    yield {"type": "text", "content": display_text}
                else:
                    yield {"type": "text", "content": delta_text}
        
        yield {"type": "done"}
        
    except Exception as e:
        print(f"Error in native Llama chat: {e}")
        import traceback
        traceback.print_exc()
        yield {"type": "error", "error": str(e)}

async def execute_tool_by_name(tool_name: str, args: Dict[str, Any]) -> Any:
    """Execute a tool by name with given arguments"""
    
    tools_map = {
        "get_network_status": get_network_status,
        "get_node_details": get_node_details,
        "update_node_status": update_node_status,
        "get_recent_logs": get_recent_logs,
        "get_error_logs": get_error_logs,
        "search_logs": search_logs,
        "get_device_info": get_device_info,
        "create_ansible_playbook": create_ansible_playbook,
        "execute_ssh_command": execute_ssh_command,
        "run_ansible_playbook": run_ansible_playbook
    }
    
    if tool_name in tools_map:
        tool_func = tools_map[tool_name]
        
        # Handle LangChain tools properly
        if hasattr(tool_func, 'ainvoke'):
            # Use ainvoke method for async LangChain tools
            return await tool_func.ainvoke(args)
        elif hasattr(tool_func, 'invoke'):
            # Use invoke method for sync LangChain tools
            return tool_func.invoke(args)
        elif asyncio.iscoroutinefunction(tool_func):
            return await tool_func(**args)
        else:
            return tool_func(**args)
    else:
        raise ValueError(f"Unknown tool: {tool_name}") 