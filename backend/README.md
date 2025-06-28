# NetViz Backend

A simple FastAPI backend for network infrastructure monitoring with AI-powered Ansible playbook generation.

We're using this backend to monitor and make changes to network infrastructure using Ansible Playbooks. An AI Agent will either 1) create Ansible Playbooks from natural language, or 2) validate that the playbooks uploaded are accurate. But the backend's job isn't to host the agent - it's to serve an agent or human with viewing basic info about infrastructure, chat with the AI Agent, keeing the network infrastructure info up to date, etc.

Tools will refer to this backend as a source of truth or reliable actions. The backend will store chats, a data structure of live infrastructure changes, a way to query opensearch using standardized queries, etc. And we will also have a worker hydrate the data structure through the backend. 

I want to use langgraph with https://www.assistant-ui.com/ Assistant UI to make this happen. OpenAI spec model using code that I promise you works: 

```

import os
from openai import OpenAI

client = OpenAI(
  api_key=os.environ.get("LLAMA_API_KEY"),
  base_url="https://api.llama.com/compat/v1/",
)

response = client.chat.completions.create(
  messages=[

    ],
  model="Llama-4-Maverick-17B-128E-Instruct-FP8",
  temperature=0.6,
  max_completion_tokens=2048,
  top_p=0.9,
  frequency_penalty=1
)

print(response)

```

And to keep information updated for the frontend, we'll need a way to store and update information about the 
network infrastructure. Maybe some sort of graph makes sense like neo4j, but on the other hand, maybe SQL makes 
more sense if we're dealing with live information. But one thing's for sure - I'll need to interact with this data 
structure often to add changes to it. PostgreSQL could be nice too if it makes sense for this use-case (does it? 
you tell me) but I need the configuration to be extremely simple and done automatically. 

## Features

- **FastAPI Backend**: Simple and efficient REST API with structured routing
- **LangGraph Agent**: AI-powered chat interface for network operations
- **PostgreSQL Database**: Stores chat history and network infrastructure data
- **Ansible Playbook Generation**: Create and execute playbooks from natural language
- **Network Graph Management**: Real-time network topology visualization and updates
- **OpenSearch Integration**: Advanced log querying and analysis
- **WebSocket Support**: Real-time updates and streaming responses
- **Metrics Synchronization**: Automated data synchronization across services
- **Modular Architecture**: Clean separation of concerns with services, models, and controllers

## Setup

### Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Llama API key (for AI agent)

### Quick Start

1. Clone the repository and navigate to the backend folder:
```bash
cd backend
```

2. Run the setup script:
```bash
./run.sh
```

This will:
- Create a `.env` file from `.env.example`
- Start PostgreSQL using Docker Compose
- Install Python dependencies
- Start the FastAPI server on http://localhost:3001

3. Update the `.env` file with your Llama API key:
```
LLAMA_API_KEY=your_actual_api_key_here
```

### Manual Setup

If you prefer to set up manually:

1. Copy the environment file:
```bash
cp .env.example .env
```

2. Start PostgreSQL:
```bash
docker-compose up -d
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the server:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 3001
```

## API Endpoints

### Health Check
- `GET /health` - Check if the service is running

### Chat & Agent
- `POST /agent/chat` - Send a message to the AI agent
- `GET /agent/chats/{session_id}` - Get chat history for a session
- `POST /agent/stream` - Stream chat responses

### Network Infrastructure
- `GET /network/graph` - Get complete network topology
- `POST /network/graph` - Update network graph
- `GET /network/nodes` - Get all network nodes
- `POST /network/nodes` - Create a new network node
- `PUT /network/nodes/{node_id}` - Update a network node

### Logs & Metrics
- `GET /logs/search` - Search through network logs
- `GET /logs/recent` - Get recent log entries
- `GET /metrics/sync` - Synchronize metrics data

### WebSocket
- `/ws/{session_id}` - WebSocket connection for real-time updates

## Architecture

The backend uses:
- **FastAPI** for the web framework
- **LangGraph** for the AI agent orchestration
- **PostgreSQL** for data persistence
- **SQLAlchemy** for async database operations
- **Llama model** via OpenAI-compatible API

## Development

The API documentation is available at http://localhost:3001/docs when the server is running.

## Project Structure

```
backend/
├── app.py                          # Main FastAPI application entry point
├── websocket_manager.py            # WebSocket connection management
├── requirements.txt                # Python dependencies
├── docker-compose.yml              # PostgreSQL setup
├── run.sh                          # Setup and run script
├── pytest.ini                      # Test configuration
├── database/                       # Database layer
│   ├── database.py                 # Database models and connection
│   ├── migrate_database.py         # Database migration utilities
│   └── reset_database.py           # Database reset utilities
├── src/                            # Main source code
│   ├── agent/
│   │   └── agent.py                # LangGraph agent configuration
│   ├── api/
│   │   └── routers/                # API route handlers
│   │       ├── agent.py            # Agent chat endpoints
│   │       ├── network.py          # Network infrastructure endpoints
│   │       ├── logs.py             # Log querying endpoints
│   │       ├── metrics.py          # Metrics endpoints
│   │       ├── test.py             # Test endpoints
│   │       └── websocket.py        # WebSocket endpoints
│   ├── config/
│   │   └── settings.py             # Application configuration
│   ├── models/
│   │   └── api_models.py           # Pydantic models for API
│   ├── services/                   # Business logic services
│   │   ├── graph_service.py        # Network graph management
│   │   ├── opensearch_service.py   # OpenSearch integration
│   │   ├── query_logs.py           # Log querying service
│   │   └── metrics_sync_service.py # Metrics synchronization
│   └── tools/
│       └── tools.py                # Agent tools for network operations
├── tests/                          # Test suite
│   ├── conftest.py                 # Test configuration
│   ├── test_api_integration.py     # API integration tests
│   └── test_function_calling_pytest.py # Function calling tests
├── documentation/                  # Technical documentation
│   ├── AI_AGENT_IMPLEMENTATION.md
│   ├── FUNCTION_CALLING_SETUP.md
│   └── OPENSEARCH_SETUP.md
├── playbooks/                      # Ansible playbooks and templates
│   ├── retrieve-configs/           # Configuration retrieval playbooks
│   ├── rollback-configs/           # Configuration rollback playbooks
│   ├── AI_AGENT_INSTRUCTIONS.md
│   └── EXAMPLES.md
└── archieve/                       # Legacy/archived code
    ├── enhanced_agent.py
    └── tools.py
```
