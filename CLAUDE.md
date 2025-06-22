# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NetViz is a self-healing network visualization and management system that combines AI-powered analysis with network automation. The system monitors network infrastructure, detects issues, and can automatically remediate problems using Ansible playbooks.

### Architecture

- **Backend**: FastAPI application with WebSocket support for real-time communication
- **Frontend**: React/TypeScript with Vite, featuring network visualization using ReactFlow
- **AI Agent**: LangGraph-based agent with network management tools (supports OpenAI GPT-4 and Llama API)
- **Database**: PostgreSQL with async support (SQLAlchemy + asyncpg)
- **Infrastructure**: Docker-based demo network with FRR routers and OVS switches
- **Monitoring**: OpenSearch integration for log analysis and querying

## Development Commands

### Backend (Python/FastAPI)
```bash
cd backend
pip install -r requirements.txt
./run.sh  # Starts PostgreSQL + backend server on port 3001
uvicorn app:app --reload --host 0.0.0.0 --port 3001  # Direct run

# Database operations
python reset_database.py     # Reset database
python migrate_database.py   # Run migrations
```

### Frontend (React/TypeScript)
```bash
cd frontend
npm install
npm run dev        # Start dev server (http://localhost:5173)
npm run build      # Production build
npm run lint       # ESLint
./start.sh         # Automated start script
```

### Demo Infrastructure
```bash
cd demo-infra
./setup-ssh.sh              # Setup SSH keys (required first time)
docker-compose up -d        # Start network topology
./cleanup.sh                # Clean up containers
./test-connection-chain.sh  # Test network connectivity
```

## Key Components

### Backend Services
- `app.py`: Main FastAPI application with REST and WebSocket endpoints
- `agent.py`: AI agent using LangGraph with network management tools
- `graph_service.py`: Network topology management with caching and real-time updates
- `websocket_manager.py`: WebSocket connection management for real-time updates
- `tools.py`: Network management tools (SSH, Ansible, OpenSearch queries)
- `database.py`: SQLAlchemy models for network nodes, edges, and chat history

### Frontend Structure
- `NetworkVisualization.tsx`: Main network graph component using ReactFlow
- `EnhancedCombinedControlPanel.tsx`: Primary control interface
- `ChatPanel.tsx`: AI assistant chat interface
- `LogViewer.tsx` / `LogsPanel.tsx`: Log viewing and analysis components
- `hooks/useRealtimeGraph.ts`: WebSocket integration for live network updates
- `services/api.ts`: Backend API integration

### AI Agent Tools
The agent has access to network management tools including:
- Network status monitoring
- SSH command execution on network devices
- Ansible playbook creation and execution
- OpenSearch log querying and analysis
- Node status updates and topology changes

## Network Topology

The demo infrastructure creates a multi-tier network:
```
Client (192.168.10.10) → Switch1 → FRR Router → Switch2 → Server (192.168.30.10)
```

- Management Network: 172.25.0.0/24 (SSH access)
- Client Network: 192.168.10.0/24  
- Server Network: 192.168.30.0/24
- Router IPs: 192.168.10.254 (client-side), 192.168.30.254 (server-side)

### SSH Access Ports
- Switch1: port 7771
- Router: port 7777
- Switch2: port 7778
- Server: port 7780

## Environment Setup

Backend requires `.env` file with:
```
LLAMA_API_KEY=your_llama_api_key_here
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/netviz
OPENSEARCH_URL=https://localhost:9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=admin
```

## Real-time Features

- WebSocket connections for live network topology updates
- Server-sent events (SSE) for streaming AI responses
- Automatic network status polling and updates
- Real-time log monitoring and alerting
- In-memory graph caching for performance

## Testing

Currently no formal test framework. Manual test scripts available:
- `test_external_updates.py`: Tests external graph updates
- `test_frontend_simulation.py`: Simulates frontend interactions
- `test_function_calling.py`: Tests AI agent function calling

## Code Architecture Patterns

- **Async-First**: All database operations and API endpoints use async/await
- **Service Layer**: `graph_service.py` abstracts graph operations from API layer
- **Repository Pattern**: Database models separated from business logic
- **Event-Driven Updates**: Graph changes broadcast to all WebSocket clients
- **Multi-LLM Fallback**: OpenAI → Native Llama → OpenAI-compatible Llama API

## Important Notes

- OpenSearch demo instance hardcoded at 192.168.0.132:9200 in some places
- SSL certificate verification disabled for self-signed certificates
- No formal code linting configuration (no .flake8, .pylintrc)
- Frontend uses Vite for development with hot module replacement