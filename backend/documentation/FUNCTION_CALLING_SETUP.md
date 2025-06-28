# Llama API Function Calling Setup Guide

This guide explains how to enable proper function calling with the Llama API in your AI Assistant.

## 🚀 Quick Setup

### 1. Install the Official Llama API Client

```bash
pip install llama-api-client
```

### 2. Set Your API Key

Add your Llama API key to your `.env` file:

```bash
# .env
LLAMA_API_KEY=your_llama_api_key_here
```

### 3. Test Function Calling

Run the test script:

```bash
python test_function_calling.py
```

## 🔧 How It Works

### Native Llama API vs OpenAI Compatibility

Your updated `agent.py` now supports three modes:

1. **🥇 OpenAI GPT-4** (Best tool calling support)
   - Uses: `OPENAI_API_KEY`
   - Fallback order: #1

2. **🦙 Native Llama API** (Proper Llama function calling)
   - Uses: `LLAMA_API_KEY` + `llama-api-client`
   - Fallback order: #2
   - **This is what enables proper tool calling!**

3. **⚠️ OpenAI-Compatible Llama API** (Limited tool calling)
   - Uses: `LLAMA_API_KEY` + OpenAI compatibility layer
   - Fallback order: #3
   - **This was your previous setup - limited function calling**

### Function Calling Implementation

The native Llama API implementation:

```python
# Convert your tools to Llama API format
functions = [
    {
        "name": "get_network_status",
        "description": "Get the status of network infrastructure nodes",
        "parameters": {
            "type": "object",
            "properties": {
                "node_name": {
                    "type": "string",
                    "description": "Optional specific node name"
                }
            }
        }
    }
    # ... more functions
]

# Make API call with function calling
response = llama_client.chat.completions.create(
    messages=messages,
    model="Llama-4-Maverick-17B-128E-Instruct-FP8",
    functions=functions,  # This enables function calling!
    stream=True
)
```

## 🧪 Testing

### Test 1: Simple Chat
```bash
python test_function_calling.py
```

Expected output:
```
🤖 AI Response:
Hello! I'm your network infrastructure assistant...
```

### Test 2: Function Calling
Ask: "Show me the current network status"

Expected output:
```
🔧 Tool Call: get_network_status
   Args: {}
✅ Tool Result: {"total_nodes": 5, "active": 3, ...}
```

## 🐛 Troubleshooting

### Issue: "Warning: llama-api-client not installed"
**Solution**: Install the client:
```bash
pip install llama-api-client
```

### Issue: "No valid LLM configuration found"
**Solution**: Set your API key:
```bash
export LLAMA_API_KEY=your_key_here
# or add to .env file
```

### Issue: Functions not being called
**Possible causes**:
1. Using OpenAI compatibility mode instead of native Llama API
2. API key not set correctly
3. Model doesn't support function calling

**Check the logs**:
- ✅ `Using native Llama API client for tool calling` = Good!
- ⚠️ `Using Llama API with OpenAI compatibility` = Limited function calling
- ❌ `Using OpenAI GPT-4 for tool calling` = Need Llama API key

## 📚 Available Functions

Your AI Assistant has access to these functions:

### Device Analysis
- `get_device_info(device_id)` - Get comprehensive device info
- `get_network_status(node_name?)` - Check network devices status

### Log Analysis  
- `get_recent_logs(device_name, time_range, log_level)` - Get recent logs
- `get_error_logs(hours)` - Get error/warning logs
- `search_logs(search_term)` - Search logs for patterns

### Automation
- `create_ansible_playbook()` - Create Ansible playbooks
- `execute_ssh_command(host, command)` - Run SSH commands
- `run_ansible_playbook()` - Execute playbooks

## 🎯 Usage Examples

### Example 1: Check Network Status
**User**: "What's the status of my network?"
**AI**: Calls `get_network_status()` → Returns actual network data

### Example 2: Search Logs
**User**: "Show me any error logs from the last hour"
**AI**: Calls `get_error_logs(hours=1)` → Returns actual error logs

### Example 3: Run SSH Command
**User**: "Check the disk usage on server1"
**AI**: Calls `execute_ssh_command(host="server1", command="df -h")` → Returns disk usage

## 🔗 References

- [Llama API Documentation](https://docs.llama.com)
- [Context7 Llama API Python Guide](https://context7.com/meta-llama/llama-api-python)
- [Function Calling Examples](https://github.com/meta-llama/llama-api-python/examples)

---

## 🎉 Success!

If you see this in your logs:
```
✅ Using native Llama API client for tool calling
🦙 Making Llama API call with 10 functions available
🔧 Tool Call: get_network_status
```

**Congratulations! Your AI Assistant now has proper tool calling! 🎉** 