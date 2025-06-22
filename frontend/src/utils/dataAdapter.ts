import { NetworkNode, NetworkEdge } from '../types/network';
import { BackendNetworkNode, BackendNetworkEdge } from '../services/api';

// Helper function to check if a value is empty/null/undefined
export function isEmpty(value: unknown): boolean {
  if (value === null || value === undefined || value === '') {
    return true;
  }
  if (typeof value === 'string' && value.trim() === '') {
    return true;
  }
  if (Array.isArray(value) && value.length === 0) {
    return true;
  }
  if (typeof value === 'object' && Object.keys(value as Record<string, unknown>).length === 0) {
    return true;
  }
  return false;
}

// Filter out empty fields from an object
export function filterEmptyFields<T extends Record<string, unknown>>(obj: T): Partial<T> {
  const filtered: Partial<T> = {};
  
  for (const [key, value] of Object.entries(obj)) {
    if (!isEmpty(value)) {
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        // Recursively filter nested objects
        const filteredNested = filterEmptyFields(value as Record<string, unknown>);
        if (Object.keys(filteredNested).length > 0) {
          filtered[key as keyof T] = filteredNested as T[keyof T];
        }
      } else {
        filtered[key as keyof T] = value as T[keyof T];
      }
    }
  }
  
  return filtered;
}

// Convert backend node to frontend format with empty field filtering
export function adaptBackendNode(backendNode: BackendNetworkNode): NetworkNode {
  const filteredMetadata = filterEmptyFields(backendNode.metadata || {});
  
  return {
    id: backendNode.id,
    type: backendNode.type as NetworkNode['type'],
    label: backendNode.name,
    ip: backendNode.ip_address || undefined,
    status: backendNode.status as NetworkNode['status'],
    layer: backendNode.layer as NetworkNode['layer'],
    metadata: {
      vendor: filteredMetadata.vendor as string || undefined,
      model: filteredMetadata.model as string || undefined,
      version: filteredMetadata.version as string || undefined,
      location: filteredMetadata.location as string || undefined,
      ports: filteredMetadata.ports as number || undefined,
      uptime: filteredMetadata.uptime as string || undefined,
      cpu: filteredMetadata.cpu as number || undefined,
      memory: filteredMetadata.memory as number || undefined,
      // Include any additional metadata fields
      ...Object.fromEntries(
        Object.entries(filteredMetadata).filter(([key]) => 
          !['vendor', 'model', 'version', 'location', 'ports', 'uptime', 'cpu', 'memory'].includes(key)
        )
      )
    },
    position: backendNode.position || { x: 0, y: 0 }
  };
}

// Convert backend edge to frontend format with empty field filtering
export function adaptBackendEdge(backendEdge: BackendNetworkEdge): NetworkEdge {
  return {
    id: backendEdge.id,
    source: backendEdge.source,
    target: backendEdge.target,
    type: backendEdge.type as NetworkEdge['type'],
    bandwidth: backendEdge.bandwidth || undefined,
    utilization: backendEdge.utilization || undefined,
    status: backendEdge.status as NetworkEdge['status']
  };
}

// Convert frontend node to backend format
export function adaptFrontendNode(frontendNode: NetworkNode): Partial<BackendNetworkNode> {
  return {
    name: frontendNode.label,
    type: frontendNode.type,
    ip_address: frontendNode.ip,
    status: frontendNode.status,
    layer: frontendNode.layer,
    position: frontendNode.position,
    metadata: filterEmptyFields(frontendNode.metadata || {})
  };
}

// Convert frontend edge to backend format
export function adaptFrontendEdge(frontendEdge: NetworkEdge): Partial<BackendNetworkEdge> {
  return {
    source: frontendEdge.source,
    target: frontendEdge.target,
    type: frontendEdge.type,
    bandwidth: frontendEdge.bandwidth,
    utilization: frontendEdge.utilization,
    status: frontendEdge.status,
    metadata: {}
  };
}

// Convert multiple backend nodes to frontend format
export function adaptBackendNodes(backendNodes: BackendNetworkNode[]): NetworkNode[] {
  return backendNodes.map(adaptBackendNode);
}

// Convert multiple backend edges to frontend format
export function adaptBackendEdges(backendEdges: BackendNetworkEdge[]): NetworkEdge[] {
  return backendEdges.map(adaptBackendEdge);
}

// Helper to format metadata for display (hide empty fields)
export function formatMetadataForDisplay(metadata: Record<string, unknown>): Record<string, string> {
  const filtered = filterEmptyFields(metadata);
  const formatted: Record<string, string> = {};
  
  for (const [key, value] of Object.entries(filtered)) {
    if (typeof value === 'string') {
      formatted[key] = value;
    } else if (typeof value === 'number') {
      formatted[key] = value.toString();
    } else if (typeof value === 'boolean') {
      formatted[key] = value ? 'Yes' : 'No';
    } else if (value !== null && value !== undefined) {
      formatted[key] = JSON.stringify(value);
    }
  }
  
  return formatted;
}

// Helper to get display-friendly field names
export function getDisplayFieldName(fieldKey: string): string {
  const fieldMap: Record<string, string> = {
    ip_address: 'IP Address',
    vendor: 'Vendor',
    model: 'Model',
    version: 'Version',
    location: 'Location',
    ports: 'Ports',
    uptime: 'Uptime',
    cpu: 'CPU Usage (%)',
    memory: 'Memory Usage (%)',
    bandwidth: 'Bandwidth',
    utilization: 'Utilization (%)',
    last_updated: 'Last Updated',
    device_id: 'Device ID'
  };
  
  return fieldMap[fieldKey] || fieldKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

export class DataAdapter {
  static backendToFrontendNode(backendNode: BackendNetworkNode): NetworkNode {
    // Use the new adapter function with empty field filtering
    return adaptBackendNode(backendNode);
  }

  static frontendToBackendNode(frontendNode: NetworkNode): Omit<BackendNetworkNode, 'id' | 'last_updated'> {
    const adapted = adaptFrontendNode(frontendNode);
    return {
      name: adapted.name!,
      type: adapted.type!,
      ip_address: adapted.ip_address,
      status: adapted.status!,
      layer: adapted.layer!,
      position: adapted.position!,
      metadata: adapted.metadata || {},
    };
  }

  private static mapNodeType(backendType: string): 'router' | 'switch' | 'firewall' | 'server' | 'endpoint' {
    const typeMap: Record<string, 'router' | 'switch' | 'firewall' | 'server' | 'endpoint'> = {
      'router': 'router',
      'switch': 'switch',
      'firewall': 'firewall',
      'server': 'server',
      'endpoint': 'endpoint',
      'host': 'endpoint',
      'device': 'endpoint'
    };
    return typeMap[backendType.toLowerCase()] || 'endpoint';
  }

  private static mapNodeStatus(backendStatus: string): 'online' | 'offline' | 'warning' | 'error' {
    const statusMap: Record<string, 'online' | 'offline' | 'warning' | 'error'> = {
      'active': 'online',
      'online': 'online',
      'up': 'online',
      'inactive': 'offline',
      'offline': 'offline',
      'down': 'offline',
      'warning': 'warning',
      'error': 'error',
      'failed': 'error',
      'unknown': 'warning'
    };
    return statusMap[backendStatus.toLowerCase()] || 'warning';
  }

  private static mapNodeLayer(nodeType: string): 'physical' | 'datalink' | 'network' | 'transport' | 'application' {
    const layerMap: Record<string, 'physical' | 'datalink' | 'network' | 'transport' | 'application'> = {
      'router': 'network',
      'switch': 'datalink',
      'firewall': 'network',
      'server': 'application',
      'endpoint': 'application',
      'host': 'application'
    };
    return layerMap[nodeType.toLowerCase()] || 'application';
  }

  // Generate mock edges for nodes since backend doesn't provide them yet
  static generateMockEdges(nodes: NetworkNode[]): NetworkEdge[] {
    const edges: NetworkEdge[] = [];
    const routers = nodes.filter(n => n.type === 'router');
    const switches = nodes.filter(n => n.type === 'switch');
    const servers = nodes.filter(n => n.type === 'server');

    // Connect routers to each other
    for (let i = 0; i < routers.length - 1; i++) {
      edges.push({
        id: `${routers[i].id}-${routers[i + 1].id}`,
        source: routers[i].id,
        target: routers[i + 1].id,
        type: 'fiber',
        bandwidth: '100Gbps',
        utilization: Math.floor(Math.random() * 80) + 10,
        status: 'active'
      });
    }

    // Connect switches to routers
    switches.forEach((switchNode, index) => {
      const router = routers[index % routers.length];
      if (router) {
        edges.push({
          id: `${router.id}-${switchNode.id}`,
          source: router.id,
          target: switchNode.id,
          type: 'fiber',
          bandwidth: '10Gbps',
          utilization: Math.floor(Math.random() * 60) + 20,
          status: 'active'
        });
      }
    });

    // Connect servers to switches
    servers.forEach((server, index) => {
      const switchNode = switches[index % switches.length];
      if (switchNode) {
        edges.push({
          id: `${switchNode.id}-${server.id}`,
          source: switchNode.id,
          target: server.id,
          type: 'ethernet',
          bandwidth: '1Gbps',
          utilization: Math.floor(Math.random() * 70) + 15,
          status: 'active'
        });
      }
    });

    return edges;
  }
} 