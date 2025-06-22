import { NetworkNode } from '../types/network';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001';
const WS_BASE_URL = API_BASE_URL.replace('http', 'ws');

export interface BackendNetworkNode {
  id: string;
  name: string;
  type: string;
  ip_address?: string;
  status: string;
  layer: string;
  position: { x: number; y: number };
  metadata: Record<string, unknown>;
  last_updated: string;
}

export interface BackendNetworkEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  bandwidth?: string;
  utilization: number;
  status: string;
  metadata: Record<string, unknown>;
  last_updated: string;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR';
  service: string;
  message: string;
  node_id: string;
  event_type: string;
  metadata: Record<string, unknown>;
}

export interface LogQuery {
  level?: string[];
  event_type?: string;
  node_id?: string;
  service?: string;
  time_range?: string;
  size?: number;
  search_term?: string;
}

export interface LogStats {
  total_logs: number;
  level_counts: Record<string, number>;
  opensearch_available: boolean;
  error?: string;
}

export interface GraphState {
  nodes: BackendNetworkNode[];
  edges: BackendNetworkEdge[];
  last_updated: string;
}

export interface GraphUpdate {
  type: 'graph_update' | 'graph_state' | 'connection_established' | 'ping' | 'pong';
  update_type?: 'created' | 'updated' | 'deleted';
  entity_type?: 'node' | 'edge';
  entity_data?: BackendNetworkNode | BackendNetworkEdge;
  nodes?: BackendNetworkNode[];
  edges?: BackendNetworkEdge[];
  source?: string;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
}

export interface ChatMessage {
  message: string;
  session_id: string;
  context?: {
    focused_node?: {
      id: string;
      label: string;
      type: string;
      status: string;
      ip?: string;
    };
  };
}

export interface ChatStreamEvent {
  type: 'text' | 'done' | 'error' | 'tool_call' | 'tool_result' | 'thinking' | 'markdown' | 'code' | 'ssh_session' | 'ansible_playbook';
  content?: string;
  error?: string;
  tool_name?: string;
  tool_args?: Record<string, unknown>;
  thinking?: string;
  // Rich content properties
  contentType?: 'text' | 'markdown' | 'code' | 'ssh_session' | 'ansible_playbook';
  language?: string;
  ssh_session?: {
    host: string;
    status: 'connecting' | 'connected' | 'disconnected' | 'error';
    output: string[];
    current_command?: string;
  };
  metadata?: Record<string, unknown>;
}

export interface StreamingChatOptions {
  message: string;
  sessionId?: string;
  context?: {
    focused_node?: NetworkNode;
    network_stats?: {
      total_nodes: number;
      active: number;
      issues: number;
    };
  };
  onChunk?: (chunk: unknown) => void;
  signal?: AbortSignal;
}

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private sessionId: string = 'default';
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000;
  private messageHandlers: Set<(update: GraphUpdate) => void> = new Set();

  constructor(sessionId: string = 'default') {
    this.sessionId = sessionId;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${WS_BASE_URL}/ws/${this.sessionId}`);
        
        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const update: GraphUpdate = JSON.parse(event.data);
            this.messageHandlers.forEach(handler => handler(update));
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect().catch(console.error);
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  addMessageHandler(handler: (update: GraphUpdate) => void) {
    this.messageHandlers.add(handler);
  }

  removeMessageHandler(handler: (update: GraphUpdate) => void) {
    this.messageHandlers.delete(handler);
  }

  send(message: Record<string, unknown>) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  requestGraphState() {
    this.send({ type: 'request_graph_state' });
  }

  ping() {
    this.send({ type: 'ping' });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export class ApiService {
  static async fetchNetworkGraph(): Promise<GraphState> {
    const response = await fetch(`${API_BASE_URL}/network/graph`);
    if (!response.ok) {
      throw new Error('Failed to fetch network graph');
    }
    return response.json();
  }

  static async fetchNetworkNodes(): Promise<BackendNetworkNode[]> {
    const response = await fetch(`${API_BASE_URL}/network/nodes`);
    if (!response.ok) {
      throw new Error('Failed to fetch network nodes');
    }
    return response.json();
  }

  static async fetchNetworkEdges(): Promise<BackendNetworkEdge[]> {
    const response = await fetch(`${API_BASE_URL}/network/edges`);
    if (!response.ok) {
      throw new Error('Failed to fetch network edges');
    }
    return response.json();
  }

  static async fetchNetworkStats(): Promise<Record<string, unknown>> {
    const response = await fetch(`${API_BASE_URL}/network/stats`);
    if (!response.ok) {
      throw new Error('Failed to fetch network stats');
    }
    return response.json();
  }

  static async createNetworkNode(nodeData: Partial<BackendNetworkNode>): Promise<{ success: boolean; node: BackendNetworkNode }> {
    const response = await fetch(`${API_BASE_URL}/network/nodes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(nodeData),
    });
    if (!response.ok) {
      throw new Error('Failed to create network node');
    }
    return response.json();
  }

  static async updateNetworkNode(id: string, nodeData: Partial<BackendNetworkNode>): Promise<{ success: boolean; node: BackendNetworkNode }> {
    const response = await fetch(`${API_BASE_URL}/network/nodes/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(nodeData),
    });
    if (!response.ok) {
      throw new Error('Failed to update network node');
    }
    return response.json();
  }

  static async deleteNetworkNode(id: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/network/nodes/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete network node');
    }
    return response.json();
  }

  static async createNetworkEdge(edgeData: Partial<BackendNetworkEdge>): Promise<{ success: boolean; edge: BackendNetworkEdge }> {
    const response = await fetch(`${API_BASE_URL}/network/edges`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(edgeData),
    });
    if (!response.ok) {
      throw new Error('Failed to create network edge');
    }
    return response.json();
  }

  static async updateNetworkEdge(id: string, edgeData: Partial<BackendNetworkEdge>): Promise<{ success: boolean; edge: BackendNetworkEdge }> {
    const response = await fetch(`${API_BASE_URL}/network/edges/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(edgeData),
    });
    if (!response.ok) {
      throw new Error('Failed to update network edge');
    }
    return response.json();
  }

  static async deleteNetworkEdge(id: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/network/edges/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete network edge');
    }
    return response.json();
  }

  static async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      throw new Error('Failed to send chat message');
    }
    return response.json();
  }

  static async getChatHistory(sessionId: string): Promise<ChatMessage[]> {
    const response = await fetch(`${API_BASE_URL}/chats/${sessionId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch chat history');
    }
    const history = await response.json();
    
    // Convert to ChatMessage format
    return history.flatMap((item: Record<string, unknown>) => [
      { role: 'user', content: item.message },
      { role: 'assistant', content: item.response }
    ]);
  }

  static async healthCheck(): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error('Backend health check failed');
    }
  }

  static async *streamChat(options: StreamingChatOptions): AsyncGenerator<Record<string, unknown>, void, unknown> {
    const { message, sessionId = 'default', context, signal } = options;

    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        context,
      }),
      signal,
    });

    if (!response.ok) {
      throw new Error(`Chat stream failed: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              return;
            }
            try {
              const parsed = JSON.parse(data);
              yield parsed;
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  static async *streamChatMessage(chatMessage: ChatMessage): AsyncGenerator<ChatStreamEvent> {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(chatMessage),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body reader available');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6)) as ChatStreamEvent;
              yield data;
              
              if (data.type === 'done' || data.type === 'error') {
                return;
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', parseError);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  // Log API methods
  static async fetchLogs(params?: {
    level?: string;
    event_type?: string;
    node_id?: string;
    service?: string;
    time_range?: string;
    size?: number;
    search?: string;
  }): Promise<LogEntry[]> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }

    const response = await fetch(`${API_BASE_URL}/logs?${searchParams}`);
    if (!response.ok) {
      throw new Error('Failed to fetch logs');
    }
    return response.json();
  }

  static async fetchRecentLogs(minutes: number = 30, size: number = 50): Promise<LogEntry[]> {
    const response = await fetch(`${API_BASE_URL}/logs/recent?minutes=${minutes}&size=${size}`);
    if (!response.ok) {
      throw new Error('Failed to fetch recent logs');
    }
    return response.json();
  }

  static async fetchErrorLogs(hours: number = 24, size: number = 100): Promise<LogEntry[]> {
    const response = await fetch(`${API_BASE_URL}/logs/errors?hours=${hours}&size=${size}`);
    if (!response.ok) {
      throw new Error('Failed to fetch error logs');
    }
    return response.json();
  }

  static async fetchNodeLogs(nodeId: string, hours: number = 24, size: number = 50): Promise<LogEntry[]> {
    const response = await fetch(`${API_BASE_URL}/logs/node/${nodeId}?hours=${hours}&size=${size}`);
    if (!response.ok) {
      throw new Error('Failed to fetch node logs');
    }
    return response.json();
  }

  static async searchLogs(query: LogQuery): Promise<LogEntry[]> {
    const response = await fetch(`${API_BASE_URL}/logs/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(query),
    });
    if (!response.ok) {
      throw new Error('Failed to search logs');
    }
    return response.json();
  }

  static async fetchLogStats(): Promise<LogStats> {
    const response = await fetch(`${API_BASE_URL}/logs/stats`);
    if (!response.ok) {
      throw new Error('Failed to fetch log stats');
    }
    return response.json();
  }
} 