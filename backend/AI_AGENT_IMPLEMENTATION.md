# AI Agent Chat Feature Implementation

## Overview

This document describes the implementation of the AI Agent chat feature for the NetViz backend, integrating with Assistant UI for a modern streaming chat experience.

## Architecture

### Backend Components

1. **Streaming SSE Endpoint** (`/chat/stream`)
   - Server-Sent Events for real-time streaming
   - Tool execution with partial results
   - Context-aware responses based on focused network node

2. **LangGraph Agent** (`agent.py`)
   - Enhanced with network-specific tools
   - Context-aware system prompts
   - Streaming support via `astream_events`

3. **Enhanced Tools** (`tools.py`)
   - `get_network_status`: Query network node status
   - `get_node_details`: Get detailed node information
   - `update_node_status`: Update node status and metadata
   - `execute_ssh_command`: Execute SSH commands with streaming output
   - `run_ansible_playbook`: Run Ansible playbooks with progress
   - `create_ansible_playbook`: Generate playbooks from natural language

### Frontend Components

1. **ChatPanel Component**
   - Real-time streaming chat UI
   - Tool execution visualization
   - Network context integration
   - Abort/cancel support

2. **API Service**
   - SSE streaming client
   - Automatic reconnection
   - Error handling

## Key Features

### 1. Streaming Support
- Real-time text streaming as the AI generates responses
- Progressive tool execution updates
- SSH command output streaming
- Ansible playbook execution progress

### 2. Context Awareness
The AI agent receives context about:
- Currently focused network node
- Network statistics (total nodes, active, issues)
- Node metadata (IP, status, type, etc.)

### 3. Tool Execution UI
- **SSH Commands**: Terminal-like UI with command and output display
- **Ansible Playbooks**: Syntax-highlighted playbook display with execution results
- **Network Status**: Real-time network status updates

### 4. Security Considerations
- SSH key-based authentication support
- Confirmation prompts for destructive operations
- Secure credential handling

## API Endpoints

### POST `/chat/stream`
Streaming chat endpoint with SSE support.

**Request Body:**
```json
{
  "message": "string",
  "session_id": "string",
  "context": {
    "focused_node": {
      "label": "string",
      "type": "string",
      "ip": "string",
      "status": "string"
    },
    "network_stats": {
      "total_nodes": 0,
      "active": 0,
      "issues": 0
    }
  }
}
```

**Response:** Server-Sent Events stream
```
data: {"type": "text", "content": "Hello..."}
data: {"type": "tool_call", "toolCallId": "call_0", "toolName": "execute_ssh_command", "args": {...}}
data: {"type": "tool_stream", "content": "output line"}
data: {"type": "tool_result", "result": {...}}
data: {"type": "done"}
```

## Usage Examples

### 1. Basic Network Query
```
User: "Show me the status of all network nodes"
Assistant: [Executes get_network_status tool and displays results]
```

### 2. SSH Command Execution
```
User: "Check disk usage on router-1"
Assistant: [Executes SSH command 'df -h' on router-1 and streams output]
```

### 3. Ansible Automation
```
User: "Create a playbook to update packages on all servers"
Assistant: [Generates Ansible playbook and optionally executes it]
```

## Future Enhancements

1. **Assistant UI Full Integration**
   - Implement proper Assistant UI runtime with all features
   - Add support for thread persistence
   - Implement tool approval workflows

2. **Enhanced Streaming**
   - WebSocket support for bidirectional streaming
   - Real-time network topology updates during chat

3. **Advanced Tools**
   - Network diagnostics (ping, traceroute, etc.)
   - Configuration backup/restore
   - Automated troubleshooting workflows

4. **Security Enhancements**
   - Role-based access control for tools
   - Audit logging for all operations
   - Encrypted credential storage

## Development Setup

1. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

3. Configure environment variables:
   ```bash
   # backend/.env
   LLAMA_API_KEY=your-api-key
   DATABASE_URL=sqlite+aiosqlite:///./netviz.db
   ```

4. Run the backend:
   ```bash
   cd backend
   python app.py
   ```

5. Run the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

## Testing

### Manual Testing
1. Open the network visualization
2. Click on a network node to focus it
3. Open the chat panel (bottom right)
4. Try various queries:
   - "What's the status of this node?"
   - "Run uptime command on this server"
   - "Create a playbook to restart nginx"

### API Testing
```bash
# Test streaming endpoint
curl -X POST http://localhost:3001/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test"}'
```

## Troubleshooting

1. **SSE Not Working**: Ensure CORS is properly configured and no proxy is buffering responses
2. **Tools Not Executing**: Check tool permissions and ensure async execution is properly handled
3. **Context Not Working**: Verify the frontend is sending the correct context structure 