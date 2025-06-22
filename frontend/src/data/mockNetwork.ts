import { NetworkNode, NetworkEdge } from '../types/network';

export const mockNodes: NetworkNode[] = [
  {
    id: 'core-router-1',
    type: 'router',
    label: 'Core Router 1',
    ip: '10.0.0.1',
    status: 'online',
    layer: 'network',
    metadata: {
      vendor: 'Cisco',
      model: 'ASR 9000',
      version: '7.3.2',
      location: 'Data Center A',
      ports: 48,
      uptime: '45d 12h 30m',
      cpu: 23,
      memory: 67
    },
    position: { x: 0, y: 0 }
  },
  {
    id: 'core-router-2',
    type: 'router',
    label: 'Core Router 2',
    ip: '10.0.0.2',
    status: 'online',
    layer: 'network',
    metadata: {
      vendor: 'Juniper',
      model: 'MX960',
      version: '20.4R3',
      location: 'Data Center B',
      ports: 48,
      uptime: '23d 8h 15m',
      cpu: 31,
      memory: 54
    },
    position: { x: 300, y: 0 }
  },
  {
    id: 'dist-switch-1',
    type: 'switch',
    label: 'Distribution Switch 1',
    ip: '10.0.1.10',
    status: 'online',
    layer: 'datalink',
    metadata: {
      vendor: 'Cisco',
      model: 'Catalyst 9500',
      version: '16.12.04',
      location: 'Floor 2',
      ports: 24,
      uptime: '67d 2h 45m',
      cpu: 15,
      memory: 42
    },
    position: { x: -150, y: 150 }
  },
  {
    id: 'dist-switch-2',
    type: 'switch',
    label: 'Distribution Switch 2',
    ip: '10.0.1.20',
    status: 'warning',
    layer: 'datalink',
    metadata: {
      vendor: 'Arista',
      model: '7280R3',
      version: '4.27.3F',
      location: 'Floor 3',
      ports: 24,
      uptime: '12d 6h 20m',
      cpu: 78,
      memory: 89
    },
    position: { x: 150, y: 150 }
  },
  {
    id: 'firewall-1',
    type: 'firewall',
    label: 'Perimeter Firewall',
    ip: '10.0.0.254',
    status: 'online',
    layer: 'network',
    metadata: {
      vendor: 'Palo Alto',
      model: 'PA-5220',
      version: '10.2.3',
      location: 'DMZ',
      ports: 16,
      uptime: '89d 14h 12m',
      cpu: 45,
      memory: 62
    },
    position: { x: 450, y: 0 }
  },
  {
    id: 'access-switch-1',
    type: 'switch',
    label: 'Access Switch 1',
    ip: '10.0.2.10',
    status: 'online',
    layer: 'datalink',
    metadata: {
      vendor: 'Cisco',
      model: 'Catalyst 2960X',
      version: '15.2(7)E3',
      location: 'Floor 2 Closet A',
      ports: 48,
      uptime: '156d 18h 5m',
      cpu: 8,
      memory: 25
    },
    position: { x: -300, y: 300 }
  },
  {
    id: 'access-switch-2',
    type: 'switch',
    label: 'Access Switch 2',
    ip: '10.0.2.20',
    status: 'online',
    layer: 'datalink',
    metadata: {
      vendor: 'HPE',
      model: 'Aruba 2930F',
      version: '16.10.0009',
      location: 'Floor 2 Closet B',
      ports: 48,
      uptime: '98d 22h 31m',
      cpu: 12,
      memory: 31
    },
    position: { x: 0, y: 300 }
  },
  {
    id: 'server-1',
    type: 'server',
    label: 'Web Server Cluster',
    ip: '10.0.3.100',
    status: 'online',
    layer: 'application',
    metadata: {
      vendor: 'Dell',
      model: 'PowerEdge R750',
      version: 'Ubuntu 22.04',
      location: 'Data Center A Rack 12',
      ports: 4,
      uptime: '234d 7h 42m',
      cpu: 62,
      memory: 78
    },
    position: { x: 300, y: 300 }
  },
  {
    id: 'endpoint-1',
    type: 'endpoint',
    label: 'Engineering Workstations',
    ip: '10.0.4.0/24',
    status: 'online',
    layer: 'application',
    metadata: {
      vendor: 'Various',
      model: 'Mixed',
      version: 'Windows 11/Linux',
      location: 'Engineering Floor',
      ports: 1,
      uptime: 'Variable',
      cpu: 35,
      memory: 45
    },
    position: { x: -450, y: 450 }
  }
];

export const mockEdges: NetworkEdge[] = [
  {
    id: 'e1-2',
    source: 'core-router-1',
    target: 'core-router-2',
    type: 'fiber',
    bandwidth: '100Gbps',
    utilization: 23,
    status: 'active'
  },
  {
    id: 'e1-3',
    source: 'core-router-1',
    target: 'dist-switch-1',
    type: 'fiber',
    bandwidth: '10Gbps',
    utilization: 45,
    status: 'active'
  },
  {
    id: 'e2-4',
    source: 'core-router-2',
    target: 'dist-switch-2',
    type: 'fiber',
    bandwidth: '10Gbps',
    utilization: 67,
    status: 'active'
  },
  {
    id: 'e2-5',
    source: 'core-router-2',
    target: 'firewall-1',
    type: 'ethernet',
    bandwidth: '1Gbps',
    utilization: 12,
    status: 'active'
  },
  {
    id: 'e3-6',
    source: 'dist-switch-1',
    target: 'access-switch-1',
    type: 'ethernet',
    bandwidth: '1Gbps',
    utilization: 34,
    status: 'active'
  },
  {
    id: 'e3-7',
    source: 'dist-switch-1',
    target: 'access-switch-2',
    type: 'ethernet',
    bandwidth: '1Gbps',
    utilization: 28,
    status: 'active'
  },
  {
    id: 'e4-8',
    source: 'dist-switch-2',
    target: 'server-1',
    type: 'ethernet',
    bandwidth: '10Gbps',
    utilization: 56,
    status: 'active'
  },
  {
    id: 'e6-9',
    source: 'access-switch-1',
    target: 'endpoint-1',
    type: 'ethernet',
    bandwidth: '1Gbps',
    utilization: 15,
    status: 'active'
  }
];