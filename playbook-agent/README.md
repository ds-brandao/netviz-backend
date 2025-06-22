# Playbook Agent

A modular LLM-powered Ansible playbook generation and testing system that safely tests playbooks on production devices with automatic rollback capabilities.

## Architecture

```
playbook-agent/
├── config/                     # Configuration management
│   ├── agent_config.yaml      # Agent settings
│   ├── secrets.yaml.example   # Secret configuration template
│   └── ingestion_config.py     # Centralized configuration manager
├── src/
│   ├── agent/                  # Main agent logic
│   │   ├── playbook_agent.py   # Core agent orchestration
│   │   └── api.py             # FastAPI agent API
│   ├── mcp_server/            # MCP server for GitHub/Ansible integration
│   │   ├── server.py          # MCP server main
│   │   ├── github_client.py   # GitHub API integration
│   │   └── ansible_runner.py  # Ansible execution
│   └── utils/                 # Shared utilities
│       ├── device_manager.py  # Device connection & config management
│       ├── llm_client.py      # LLM API integration
│       ├── playbook_validator.py # Playbook validation & linting
│       └── mcp_client.py      # MCP client for agent
├── scripts/                   # Run scripts
│   ├── run_agent.py          # Start agent only
│   ├── run_mcp_server.py     # Start MCP server only
│   └── run_all.py            # Start both services
├── tests/                    # Test files
└── requirements.txt          # Python dependencies
```

## Features

### Core Capabilities
- **LLM-Powered Generation**: Uses Llama4 to generate Ansible playbooks
- **Safe Testing**: Captures device configuration before changes
- **Automatic Rollback**: Restores original state if playbook fails
- **Iterative Improvement**: Learns from errors across up to 5 iterations
- **GitHub Integration**: Stores playbook versions in GitHub
- **Comprehensive Validation**: YAML syntax, structure, and ansible-lint validation

### Components

#### Playbook Agent
- Orchestrates the entire generation and testing workflow
- Manages device connections and configuration capture
- Handles iterative improvement with error feedback
- Provides RESTful API for external integration

#### MCP Server
- Manages GitHub storage of playbooks
- Executes Ansible playbooks against devices
- Provides centralized playbook management
- Handles Ansible inventory generation

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configuration

Copy the example secrets file and configure:
```bash
cp config/secrets.yaml.example config/secrets.yaml
```

Edit `config/secrets.yaml`:
```yaml
llm:
  api_key: "your_llama_api_key_here"

github:
  token: "your_github_token_here"
  username: "your_github_username"

mcp_server:
  url: "http://localhost:8080"
```

### 3. Environment Variables (Optional)
Alternatively, set environment variables:
```bash
export LLAMA_API_KEY="your_llama_api_key"
export GITHUB_TOKEN="your_github_token"
export GITHUB_USERNAME="your_username"
```

## Usage

### Start All Services
```bash
python scripts/run_all.py
```

### Start Individual Services
```bash
# MCP Server only
python scripts/run_mcp_server.py

# Agent API only
python scripts/run_agent.py
```

### API Usage

#### Generate Playbook
```bash
curl -X POST "http://localhost:8000/generate-playbook" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "router-01",
    "device_host": "192.168.1.1",
    "device_user": "admin",
    "device_password": "password",
    "intentions": "Configure OSPF routing with area 0"
  }'
```

#### Check Task Status
```bash
curl "http://localhost:8000/task/{task_id}"
```

#### Health Check
```bash
curl "http://localhost:8000/health"
```

## Configuration

### Agent Configuration (`config/agent_config.yaml`)
```yaml
agent:
  max_iterations: 5          # Maximum retry attempts
  timeout_seconds: 300       # Overall timeout
  log_level: "INFO"         # Logging level

llm:
  model: "llama-3.1-405b"   # LLM model to use
  temperature: 0.1          # Generation temperature
  max_tokens: 4000          # Max response tokens

device:
  connection_timeout: 30     # SSH connection timeout
  command_timeout: 60       # Command execution timeout
  config_backup_enabled: true # Enable configuration backup
```

### Secrets Configuration (`config/secrets.yaml`)
Contains sensitive information like API keys and tokens.

## Workflow

1. **API Request**: Agent receives playbook generation request
2. **Device Connection**: Connects to target device via SSH
3. **Configuration Capture**: Backs up current device configuration
4. **Playbook Generation**: LLM generates initial playbook
5. **Validation**: Validates YAML syntax, structure, and linting
6. **GitHub Storage**: Stores playbook version in GitHub
7. **Execution**: Runs playbook via MCP server
8. **Error Handling**: On failure, restores configuration and iterates
9. **Success**: Returns final working playbook

## Safety Features

- **Configuration Backup**: Always captures original state
- **Automatic Rollback**: Restores configuration on any failure
- **Validation Pipeline**: Multi-layer validation before execution
- **Iteration Limits**: Prevents infinite retry loops
- **Error Tracking**: Comprehensive error logging and feedback

## Development

### Project Structure
- `config/`: Configuration management with YAML files
- `src/agent/`: Main agent logic and API
- `src/mcp_server/`: MCP server implementation
- `src/utils/`: Shared utilities and clients
- `scripts/`: Execution scripts
- `tests/`: Test files (to be implemented)

### Adding New Features
1. Update configuration schemas in `config/`
2. Implement logic in appropriate `src/` subdirectory
3. Update configuration manager in `config/ingestion_config.py`
4. Add tests in `tests/`

## Troubleshooting

### Common Issues

1. **Connection Failures**
   - Check device credentials and network connectivity
   - Verify SSH key permissions if using key-based auth

2. **LLM API Errors**
   - Verify API key is correct and has sufficient credits
   - Check model availability and quota limits

3. **GitHub Integration Issues**
   - Ensure GitHub token has repository access
   - Verify repository exists and is accessible

4. **Ansible Execution Failures**
   - Check Ansible installation and configuration
   - Verify device modules are available

### Logs
All components use Python logging. Adjust log level in configuration:
```yaml
agent:
  log_level: "DEBUG"  # For detailed logging
```

## Security Considerations

- Store secrets in `config/secrets.yaml` (not version controlled)
- Use SSH keys instead of passwords when possible
- Ensure GitHub tokens have minimal required permissions
- Monitor API usage and rate limits
- Review generated playbooks before production use

## License

[Your License Here]