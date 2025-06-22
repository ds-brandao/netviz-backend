import os
from typing import Dict, Any, Optional, AsyncGenerator, List
from dotenv import load_dotenv
import asyncio
import json
from llama_api_client import LlamaAPIClient

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

# Initialize Llama API Client
llm = LlamaAPIClient(api_key=os.getenv("LLAMA_API_KEY"))

# Tool definitions for Llama API
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_network_status",
            "description": "Get the status of network infrastructure nodes",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_name": {
                        "type": "string",
                        "description": "Optional specific node name to get status for"
                    }
                },
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "get_node_details",
            "description": "Get detailed information about a specific network node",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_name": {
                        "type": "string",
                        "description": "The name of the node to get details for"
                    }
                },
                "required": ["node_name"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_node_status",
            "description": "Update the status and metadata of a network node",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_name": {
                        "type": "string",
                        "description": "The name of the node to update"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status (active, inactive, warning, error, maintenance)"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Optional metadata to update"
                    }
                },
                "required": ["node_name", "status"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_logs",
            "description": "Get recent logs from OpenSearch for a device",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_name": {
                        "type": "string",
                        "description": "The device name to get logs for"
                    },
                    "time_range": {
                        "type": "integer",
                        "description": "Time range in hours (default: 2)"
                    },
                    "log_level": {
                        "type": "string",
                        "description": "Log level filter (INFO, WARN, ERROR)"
                    }
                },
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_error_logs",
            "description": "Get error and warning logs from the last N hours",
            "parameters": {
                "type": "object",
                "properties": {
                    "hours": {
                        "type": "integer",
                        "description": "Number of hours to look back (default: 24)"
                    }
                },
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_logs",
            "description": "Search logs for specific terms or patterns",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "The term to search for in logs"
                    }
                },
                "required": ["search_term"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_device_info",
            "description": "Get comprehensive device information including recent logs and metrics",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {
                        "type": "string",
                        "description": "The device ID to get information for"
                    }
                },
                "required": ["device_id"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_ansible_playbook",
            "description": "Create an Ansible playbook based on natural language description",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Description of what the playbook should do"
                    },
                    "target_hosts": {
                        "type": "string",
                        "description": "Target hosts (default: all)"
                    }
                },
                "required": ["task_description"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_ssh_command",
            "description": "Execute SSH command on a remote host",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "description": "The hostname or IP to connect to"
                    },
                    "command": {
                        "type": "string",
                        "description": "The command to execute"
                    },
                    "username": {
                        "type": "string",
                        "description": "SSH username (default: admin)"
                    },
                    "password": {
                        "type": "string",
                        "description": "SSH password (optional)"
                    },
                    "key_file": {
                        "type": "string",
                        "description": "Path to SSH key file (optional)"
                    }
                },
                "required": ["host", "command"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_ansible_playbook",
            "description": "Execute an Ansible playbook",
            "parameters": {
                "type": "object",
                "properties": {
                    "playbook_content": {
                        "type": "string",
                        "description": "The YAML content of the playbook"
                    },
                    "inventory": {
                        "type": "string",
                        "description": "Inventory hosts (default: localhost,)"
                    },
                    "extra_vars": {
                        "type": "object",
                        "description": "Extra variables for the playbook"
                    }
                },
                "required": ["playbook_content"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
]

# Tool execution mapping
TOOL_MAPPING = {
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

def build_system_prompt(context: Optional[Dict[str, Any]] = None) -> str:
    """Build context-aware system prompt"""
    
    system_prompt = """You are an expert network infrastructure assistant with real-time access to live network data. You help users manage and troubleshoot their network infrastructure using actual tools and data.

You have access to the following tools:
- get_network_status: Get status of network devices
- get_node_details: Get detailed information about a specific node
- update_node_status: Update node status and metadata
- get_recent_logs: Get recent logs from OpenSearch for any device
- get_error_logs: Get error/warning logs for troubleshooting
- search_logs: Search logs for specific patterns
- get_device_info: Get comprehensive device information
- execute_ssh_command: Run SSH commands on remote hosts
- create_ansible_playbook: Create Ansible automation playbooks
- run_ansible_playbook: Execute Ansible playbooks

IMPORTANT: Always use the appropriate tool when users ask for network status, logs, or device information. Never simulate or make up data."""
    
    if context and context.get("network_stats"):
        stats = context["network_stats"]
        system_prompt += f"\n\nCurrent network: {stats.get('total_nodes', 0)} nodes, {stats.get('active', 0)} active, {stats.get('issues', 0)} with issues."
    
    if context and context.get("focused_node"):
        node = context["focused_node"]
        system_prompt += f"\n\nUser is focused on: {node.get('label', 'Unknown')} ({node.get('type', 'Unknown')}, Status: {node.get('status', 'Unknown')})"
    
    return system_prompt

async def execute_tool(tool_name: str, args: Dict[str, Any]) -> Any:
    """Execute a tool by name with given arguments"""
    
    print(f"=== EXECUTE_TOOL DEBUG ===")
    print(f"tool_name: {tool_name}")
    print(f"args: {args}")
    
    if tool_name not in TOOL_MAPPING:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    tool_func = TOOL_MAPPING[tool_name]
    print(f"tool_func: {tool_func}")
    print(f"has ainvoke: {hasattr(tool_func, 'ainvoke')}")
    print(f"has invoke: {hasattr(tool_func, 'invoke')}")
    print(f"is coroutine: {asyncio.iscoroutinefunction(tool_func)}")
    
    # Handle LangChain tools
    if hasattr(tool_func, 'ainvoke'):
        print(f"LangChain tool detected, calling underlying function directly")
        # Skip LangChain's ainvoke and call the underlying function directly
        if hasattr(tool_func, 'coroutine'):
            print(f"Calling coroutine directly with **args: {args}")
            return await tool_func.coroutine(**args)
        elif hasattr(tool_func, 'func'):
            print(f"Calling underlying function directly with **args: {args}")
            return await tool_func.func(**args)
        else:
            print(f"Fallback: trying ainvoke with args: {args}")
            return await tool_func.ainvoke(args)
    elif hasattr(tool_func, 'invoke'):
        print(f"Calling invoke with args: {args}")
        try:
            return tool_func.invoke(args)
        except Exception as e:
            print(f"invoke failed with dict args: {e}")
            # Try calling the underlying function directly
            if hasattr(tool_func, 'func'):
                print(f"Calling underlying function directly with **args")
                return tool_func.func(**args)
            else:
                raise e
    elif asyncio.iscoroutinefunction(tool_func):
        print(f"Calling async function with **args: {args}")
        return await tool_func(**args)
    else:
        print(f"Calling sync function with **args: {args}")
        return tool_func(**args)

async def agent_streaming_chat(
    message: str, 
    context: Optional[Dict[str, Any]] = None, 
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """Main agent chat function using Llama API with proper tool calling"""
    
    try:
        # Build messages
        messages = [{"role": "system", "content": build_system_prompt(context)}]
        
        # Add conversation history
        if conversation_history:
            for hist_msg in conversation_history[-10:]:  # Keep last 10 messages
                if hist_msg.get("role") in ["user", "assistant"]:
                    messages.append({
                        "role": hist_msg["role"],
                        "content": hist_msg["content"]
                    })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # First call to detect tool calls (non-streaming)
        tool_calls = []
        completion_message = None
        
        try:
            print("Making initial call to detect tool calls...")
            response = llm.chat.completions.create(
                model="Llama-4-Maverick-17B-128E-Instruct-FP8",
                messages=messages,
                tools=TOOL_DEFINITIONS,
                max_completion_tokens=2048,
                temperature=0.6,
                stream=False
            )
            
            # Extract completion message
            completion_message = response.completion_message.model_dump()
            
            # Check for tool calls in the response
            if completion_message.get("tool_calls"):
                tool_calls = completion_message["tool_calls"]
                print(f"Found {len(tool_calls)} tool calls: {tool_calls}")
                
                # Execute tool calls
                for tool_call in tool_calls:
                    try:
                        # Parse arguments
                        args = json.loads(tool_call["function"]["arguments"]) if tool_call["function"]["arguments"] else {}
                        
                        # Notify about tool execution
                        yield {
                            "type": "tool_call",
                            "toolCallId": tool_call["id"],
                            "toolName": tool_call["function"]["name"],
                            "args": args
                        }
                        
                        # Execute tool
                        result = await execute_tool(tool_call["function"]["name"], args)
                        
                        # Return tool result
                        yield {
                            "type": "tool_result",
                            "toolCallId": tool_call["id"],
                            "result": result
                        }
                        
                        # Add tool result to messages for next turn
                        messages.append(completion_message)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": str(result)
                        })
                        
                    except Exception as e:
                        print(f"Tool execution error: {e}")
                        yield {
                            "type": "tool_error",
                            "toolCallId": tool_call["id"],
                            "error": str(e)
                        }
            
            # Check if the response contains text that looks like function calls (fallback parsing)
            elif completion_message.get("content"):
                content = completion_message["content"]
                if isinstance(content, dict) and content.get("text"):
                    content_text = content["text"]
                elif isinstance(content, str):
                    content_text = content
                else:
                    content_text = str(content)
                
                # Try to parse function calls from text content
                import re
                function_pattern = r'\[(\w+)\((.*?)\)\]'
                matches = re.findall(function_pattern, content_text)
                
                if matches:
                    print(f"Found {len(matches)} function calls in text: {matches}")
                    
                    # Store tool results for building context
                    tool_results = []
                    
                    for i, (func_name, args_str) in enumerate(matches):
                        if func_name in TOOL_MAPPING:
                            try:
                                # Parse arguments from string
                                args = {}
                                if args_str:
                                    print(f"Parsing arguments from: '{args_str}'")
                                    
                                    # Try multiple patterns for parsing arguments
                                    # Pattern 1: key="value" or key='value'
                                    arg_pairs = re.findall(r'(\w+)=(["\'])(.*?)\2', args_str)
                                    print(f"Found quoted argument pairs: {arg_pairs}")
                                    
                                    # Pattern 2: key=value (without quotes)
                                    if not arg_pairs:
                                        arg_pairs = re.findall(r'(\w+)=([^,\)]+)', args_str)
                                        print(f"Found unquoted argument pairs: {arg_pairs}")
                                        # Convert to same format as quoted pairs
                                        arg_pairs = [(key, '', value.strip()) for key, value in arg_pairs]
                                    
                                    for key, _, value in arg_pairs:
                                        args[key] = value.strip()
                                    print(f"Parsed args: {args}")
                                
                                tool_call_id = f"call_{i+1}"
                                
                                # Notify about tool execution
                                yield {
                                    "type": "tool_call",
                                    "toolCallId": tool_call_id,
                                    "toolName": func_name,
                                    "args": args
                                }
                                
                                # Execute tool
                                print(f"About to execute tool {func_name} with args {args}")
                                result = await execute_tool(func_name, args)
                                print(f"Tool {func_name} completed successfully, result length: {len(str(result))}")
                                print(f"Tool result preview: {str(result)[:200]}...")
                                
                                # Store result for context
                                tool_results.append({
                                    "function": func_name,
                                    "args": args,
                                    "result": result
                                })
                                
                                # Return tool result
                                yield {
                                    "type": "tool_result",
                                    "toolCallId": tool_call_id,
                                    "result": result
                                }
                                
                            except Exception as e:
                                print(f"Tool execution error for {func_name}: {e}")
                                yield {
                                    "type": "tool_error",
                                    "toolCallId": f"call_{i+1}",
                                    "error": str(e)
                                }
                    
                    # After executing parsed tool calls, generate a follow-up response with tool results
                    if tool_results:
                        try:
                            # Build context message with tool results
                            results_summary = "Tool execution results:\n"
                            for tr in tool_results:
                                results_summary += f"- {tr['function']}({tr['args']}): {str(tr['result'])[:200]}...\n"
                            
                            follow_up_messages = messages + [
                                {"role": "assistant", "content": content_text},
                                {"role": "user", "content": f"Based on the tool execution results below, please provide a clear summary and analysis:\n\n{results_summary}"}
                            ]
                            
                            follow_up_response = llm.chat.completions.create(
                                model="Llama-4-Maverick-17B-128E-Instruct-FP8",
                                messages=follow_up_messages,
                                max_completion_tokens=2048,
                                temperature=0.6,
                                stream=True
                            )
                            
                            # Stream the follow-up response
                            for chunk in follow_up_response:
                                if hasattr(chunk, 'event') and chunk.event:
                                    if hasattr(chunk.event, 'delta') and chunk.event.delta:
                                        if hasattr(chunk.event.delta, 'text') and chunk.event.delta.text:
                                            yield {"type": "text", "content": chunk.event.delta.text}
                                            
                        except Exception as follow_error:
                            print(f"Follow-up response failed: {follow_error}")
                            # Provide a basic summary of the tool results
                            summary = f"Successfully executed {len(tool_results)} tool(s):\n"
                            for tr in tool_results:
                                summary += f"• {tr['function']}: Retrieved data successfully\n"
                            yield {"type": "text", "content": summary}
                else:
                    # No function calls found, return the original content
                    yield {"type": "text", "content": content_text}
                    
            else:
                # No tool calls, stream the original response
                if completion_message.get("content"):
                    # If we have content from the non-streaming call, yield it
                    content = completion_message["content"]
                    if isinstance(content, dict) and content.get("text"):
                        yield {"type": "text", "content": content["text"]}
                    elif isinstance(content, str):
                        yield {"type": "text", "content": content}
                else:
                    # Fallback to streaming without tools
                    try:
                        streaming_response = llm.chat.completions.create(
                            model="Llama-4-Maverick-17B-128E-Instruct-FP8",
                            messages=messages,
                            max_completion_tokens=2048,
                            temperature=0.6,
                            stream=True
                        )
                        
                        for chunk in streaming_response:
                            if hasattr(chunk, 'event') and chunk.event:
                                if hasattr(chunk.event, 'delta') and chunk.event.delta:
                                    if hasattr(chunk.event.delta, 'text') and chunk.event.delta.text:
                                        yield {"type": "text", "content": chunk.event.delta.text}
                                        
                    except Exception as streaming_error:
                        print(f"Streaming fallback failed: {streaming_error}")
                        yield {"type": "text", "content": "I'm having trouble generating a response. Please try again."}
                        
        except Exception as api_error:
            print(f"API call failed: {api_error}")
            # Fallback to simple streaming without tools
            try:
                fallback_response = llm.chat.completions.create(
                    model="Llama-4-Maverick-17B-128E-Instruct-FP8",
                    messages=messages,
                    max_completion_tokens=2048,
                    temperature=0.6,
                    stream=True
                )
                
                for chunk in fallback_response:
                    if hasattr(chunk, 'event') and chunk.event:
                        if hasattr(chunk.event, 'delta') and chunk.event.delta:
                            if hasattr(chunk.event.delta, 'text') and chunk.event.delta.text:
                                yield {"type": "text", "content": chunk.event.delta.text}
                                
            except Exception as fallback_error:
                print(f"Fallback failed: {fallback_error}")
                yield {"type": "error", "error": "Unable to generate response"}
        
        yield {"type": "done"}
        
    except Exception as e:
        print(f"Error in agent streaming chat: {e}")
        import traceback
        traceback.print_exc()
        yield {"type": "error", "error": str(e)}

# Backward compatibility functions
def create_agent():
    """Legacy function for compatibility"""
    return None

def create_streaming_agent(context: Optional[Dict[str, Any]] = None):
    """Legacy function for compatibility"""
    return None

async def simple_streaming_chat(
    message: str, 
    context: Optional[Dict[str, Any]] = None, 
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """Fallback simple chat without tools"""
    
    messages = [{"role": "system", "content": build_system_prompt(context)}]
    
    if conversation_history:
        for hist_msg in conversation_history[-10:]:
            if hist_msg.get("role") in ["user", "assistant"]:
                messages.append({
                    "role": hist_msg["role"],
                    "content": hist_msg["content"]
                })
    
    messages.append({"role": "user", "content": message})
    
    response = llm.chat.completions.create(
        model="Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=messages,
        stream=True,
        temperature=0.6
    )
    
    for chunk in response:
        # Handle llama-api-client specific structure
        if hasattr(chunk, 'event') and chunk.event:
            event = chunk.event
            if hasattr(event, 'delta') and event.delta and hasattr(event.delta, 'text'):
                text = event.delta.text
                if text:
                    yield {"type": "text", "content": text}
        # Fallback to other structures
        elif hasattr(chunk, 'choices') and chunk.choices and len(chunk.choices) > 0:
            choice = chunk.choices[0]
            if hasattr(choice, 'delta') and hasattr(choice.delta, 'content') and choice.delta.content:
                yield {"type": "text", "content": choice.delta.content}
        elif hasattr(chunk, 'content') and chunk.content:
            yield {"type": "text", "content": chunk.content}
        elif isinstance(chunk, dict) and 'content' in chunk and chunk['content']:
            yield {"type": "text", "content": chunk['content']}
    
    yield {"type": "done"}