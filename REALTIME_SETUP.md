# Real-Time Network Visualization System

This system provides real-time updates for network graph visualization with WebSocket connectivity and external device integration.

## Features

### 🔄 Real-Time Updates
- **WebSocket Connection**: Live updates pushed to frontend automatically
- **Auto-Reconnection**: Handles connection drops with exponential backoff
- **Connection Status**: Visual indicator showing connection state
- **Empty Field Filtering**: Only displays fields with actual data

### 📡 External Device Integration
- **Device Update Endpoint**: Simple API for devices to send updates
- **Bulk Update Endpoint**: Efficient batch updates for network scanners
- **Graph Synchronization**: Database and cache automatically updated
- **Update Tracking**: Full audit trail of all changes

### 🗄️ Enhanced Database Schema
- **Network Nodes**: Complete device information with metadata
- **Network Edges**: Connection details with utilization metrics
- **Graph Updates**: Audit log of all changes with source tracking
- **Position Tracking**: Node positions for layout persistence

## Getting Started

### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (optional)
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/netviz"

# Run the backend
python app.py
```

The backend will start on `http://localhost:3001` with:
- REST API endpoints
- WebSocket endpoint at `/ws/{session_id}`
- Database auto-initialization

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will connect automatically to the WebSocket and show:
- Live connection status indicator
- Real-time graph updates
- Filtered metadata display (empty fields hidden)

### 3. Test External Updates

```bash
cd backend

# Send a single test update
python test_external_updates.py single

# Run continuous simulation
python test_external_updates.py
```

## API Endpoints

### WebSocket Connection
```
WS /ws/{session_id}
```
- Receives real-time graph updates
- Sends initial graph state on connection
- Handles ping/pong for keep-alive

### Device Updates
```
POST /network/device-update/{device_id}
```
Simple endpoint for external devices:
```json
{
  "name": "Router-001",
  "type": "router",
  "ip_address": "192.168.1.1",
  "status": "online",
  "metadata": {
    "vendor": "Cisco",
    "model": "ASR-9000",
    "cpu": 45,
    "memory": 62
  }
}
```

### Bulk Updates
```
POST /network/bulk-update
```
For network scanners and batch operations:
```json
{
  "source": "network_scanner",
  "nodes": [...],
  "edges": [...]
}
```

### Graph Data
```
GET /network/graph          # Complete graph
GET /network/nodes          # All nodes
GET /network/edges          # All edges
GET /network/stats          # Statistics
```

## Real-Time Message Types

### Graph Updates
```json
{
  "type": "graph_update",
  "update_type": "created|updated|deleted",
  "entity_type": "node|edge",
  "entity_data": {...},
  "source": "api|device_xxx|network_scanner",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Graph State
```json
{
  "type": "graph_state",
  "nodes": [...],
  "edges": [...],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Connection Events
```json
{
  "type": "connection_established",
  "session_id": "default",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Empty Field Handling

The system automatically filters out empty/null/undefined fields:

### Backend
- Database stores only non-empty values
- API responses exclude null fields
- Metadata filtering in graph service

### Frontend
- Utility functions filter display data
- UI components hide empty sections
- Metadata organized by category

### Examples

**Hidden Fields:**
- `null`, `undefined`, `""` (empty string)
- `[]` (empty arrays)
- `{}` (empty objects)
- Whitespace-only strings

**Displayed Fields:**
- `"Cisco"`, `42`, `true`
- `["item1", "item2"]`
- `{"key": "value"}`

## Database Schema

### NetworkNode
```sql
id              INTEGER PRIMARY KEY
name            VARCHAR
type            VARCHAR
ip_address      VARCHAR (nullable)
status          VARCHAR
layer           VARCHAR
position_x      FLOAT
position_y      FLOAT
node_metadata   JSON
last_updated    TIMESTAMP
```

### NetworkEdge
```sql
id              INTEGER PRIMARY KEY
source_id       INTEGER (FK)
target_id       INTEGER (FK)
type            VARCHAR
bandwidth       VARCHAR (nullable)
utilization     FLOAT
status          VARCHAR
edge_metadata   JSON
last_updated    TIMESTAMP
```

### GraphUpdate
```sql
id              INTEGER PRIMARY KEY
update_type     VARCHAR
entity_type     VARCHAR
entity_id       INTEGER
old_data        JSON (nullable)
new_data        JSON (nullable)
source          VARCHAR
timestamp       TIMESTAMP
```

## Troubleshooting

### WebSocket Connection Issues
1. Check backend is running on correct port
2. Verify CORS settings allow WebSocket connections
3. Check browser console for connection errors
4. Monitor backend logs for WebSocket events

### Missing Updates
1. Verify WebSocket connection is established
2. Check if updates are being sent to correct endpoints
3. Monitor database for update records
4. Check graph service cache invalidation

### Empty Fields Still Showing
1. Verify data adapter filtering functions
2. Check component conditional rendering
3. Ensure metadata is properly structured
4. Test with known empty values

## Development

### Adding New Update Sources
1. Create endpoint in `app.py`
2. Use `graph_service` for database operations
3. Ensure WebSocket broadcast is triggered
4. Add source tracking in `GraphUpdate`

### Extending Metadata Fields
1. Update database schema if needed
2. Add field mapping in `dataAdapter.ts`
3. Update display categorization
4. Test empty field filtering

### Custom WebSocket Messages
1. Add message type in `WebSocketManager`
2. Handle in `useRealtimeGraph` hook
3. Update backend message broadcasting
4. Test message flow end-to-end 