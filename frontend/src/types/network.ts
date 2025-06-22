export interface NetworkNode {
  id: string;
  type: 'router' | 'switch' | 'firewall' | 'server' | 'endpoint' | 'client' | 'host';
  label: string;
  ip?: string;
  status: 'online' | 'offline' | 'warning' | 'error';
  layer: 'physical' | 'datalink' | 'network' | 'transport' | 'application';
  metadata: {
    vendor?: string;
    model?: string;
    version?: string;
    location?: string;
    ports?: number;
    uptime?: string;
    cpu?: number;
    memory?: number;
  };
  position: { x: number; y: number };
}

export interface NetworkEdge {
  id: string;
  source: string;
  target: string;
  type: 'ethernet' | 'fiber' | 'wireless' | 'vpn';
  bandwidth?: string;
  utilization?: number;
  status: 'active' | 'inactive' | 'error';
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  context?: {
    nodeId?: string;
    action?: string;
  };
}

export type LayoutMode = 'force' | 'hierarchical' | 'hierarchical-horizontal' | 'circular' | 'grid';
export type FilterLayer = 'physical' | 'datalink' | 'network' | 'transport' | 'application';