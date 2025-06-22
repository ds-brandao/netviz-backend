# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NetViz is a self-healing network visualization and management system that combines AI-powered analysis with network automation. The system monitors network infrastructure, detects issues, and can automatically remediate problems using Ansible playbooks.

### Architecture

- **Backend**: FastAPI application with WebSocket support for real-time communication
- **Frontend**: React/TypeScript with Vite, featuring network visualization using ReactFlow
- **AI Agent**: LangGraph-based agent with network management tools
- **Database**: SQLite/PostgreSQL for storing network topology and chat history
- **Infrastructure**: Docker-based demo network with FRR routers and OVS switches
- **Monitoring**: OpenSearch integration for log analysis and querying

## Development Commands

### Backend (Python/FastAPI)
```bash
cd backend
pip install -r requirements.txt
./run.sh  # Starts PostgreSQL + backend server on port 3001
uvicorn app:app --reload --host 0.0.0.0 --port 3001  # Direct run
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
docker-compose up -d     # Start network topology
./cleanup.sh            # Clean up containers
./test-connection-chain.sh  # Test network connectivity
```

## Key Components

### Backend Services
- `app.py`: Main FastAPI application with REST and WebSocket endpoints
- `agent.py`: AI agent using LangGraph with network management tools
- `graph_service.py`: Network topology management and real-time updates
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

- Management Network: 172.25.0.0/24
- Client Network: 192.168.10.0/24  
- Server Network: 192.168.30.0/24

## Environment Setup

Backend requires `.env` file with:
- `LLAMA_API_KEY`: API key for LLM service
- Database connection settings
- OpenSearch configuration (default: localhost:9200)

## Real-time Features

- WebSocket connections for live network topology updates
- Server-sent events for streaming AI responses
- Automatic network status polling and updates
- Real-time log monitoring and alerting