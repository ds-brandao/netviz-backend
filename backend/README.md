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

- **FastAPI Backend**: Simple and efficient REST API
- **LangGraph Agent**: AI-powered chat interface for network operations
- **PostgreSQL Database**: Stores chat history and network infrastructure data
- **Ansible Playbook Generation**: Create playbooks from natural language
- **Network Status Monitoring**: Track and update network node status

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

### Chat
- `POST /chat` - Send a message to the AI agent
- `GET /chats/{session_id}` - Get chat history for a session

### Network Infrastructure
- `GET /network/nodes` - Get all network nodes
- `POST /network/nodes` - Create a new network node
- `PUT /network/nodes/{node_id}` - Update a network node

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

- `app.py` - Main FastAPI application
- `agent.py` - LangGraph agent configuration
- `database.py` - Database models and connection
- `tools.py` - Agent tools for network operations
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - PostgreSQL setup
- `.env.example` - Environment variables template