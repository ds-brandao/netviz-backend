import { useMemo } from 'react';
import { useRealtimeGraph } from './useRealtimeGraph';
import { useDataMode } from '../contexts/DataModeContext';
import { mockNodes, mockEdges } from '../data/mockNetwork';
import { adaptBackendNodes, adaptBackendEdges } from '../utils/dataAdapter';
import { NetworkNode, NetworkEdge } from '../types/network';

export interface NetworkDataState {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  isConnected: boolean;
  isConnecting: boolean;
  lastUpdated: string | null;
  connectionError: string | null;
  dataMode: 'realtime' | 'fake';
}

export interface NetworkDataActions {
  connect: () => Promise<void>;
  disconnect: () => void;
  requestGraphState: () => void;
  ping: () => void;
  refreshFakeData: () => void;
}

export function useNetworkData(sessionId: string = 'default'): [NetworkDataState, NetworkDataActions] {
  const { isUsingFakeData } = useDataMode();
  const [realtimeState, realtimeActions] = useRealtimeGraph(sessionId);

  // Convert mock data to the expected format
  const fakeData = useMemo(() => {
    // Add some dynamic elements to fake data for testing
    const dynamicNodes = mockNodes.map(node => ({
      ...node,
      metadata: {
        ...node.metadata,
        cpu: Math.floor(Math.random() * 100),
        memory: Math.floor(Math.random() * 100),
        uptime: `${Math.floor(Math.random() * 365)}d ${Math.floor(Math.random() * 24)}h ${Math.floor(Math.random() * 60)}m`
      }
    }));

    const dynamicEdges = mockEdges.map(edge => ({
      ...edge,
      utilization: Math.floor(Math.random() * 100)
    }));

    return {
      nodes: dynamicNodes,
      edges: dynamicEdges
    };
  }, []);

  const state: NetworkDataState = useMemo(() => {
    if (isUsingFakeData) {
      return {
        nodes: fakeData.nodes,
        edges: fakeData.edges,
        isConnected: true,
        isConnecting: false,
        lastUpdated: new Date().toISOString(),
        connectionError: null,
        dataMode: 'fake'
      };
    } else {
      // Convert backend data to frontend format
      const frontendNodes = adaptBackendNodes(realtimeState.nodes);
      const frontendEdges = adaptBackendEdges(realtimeState.edges);

      return {
        nodes: frontendNodes,
        edges: frontendEdges,
        isConnected: realtimeState.isConnected,
        isConnecting: realtimeState.isConnecting,
        lastUpdated: realtimeState.lastUpdated,
        connectionError: realtimeState.connectionError,
        dataMode: 'realtime'
      };
    }
  }, [isUsingFakeData, fakeData, realtimeState]);

  const actions: NetworkDataActions = useMemo(() => {
    if (isUsingFakeData) {
      return {
        connect: async () => {
          // No-op for fake data
        },
        disconnect: () => {
          // No-op for fake data
        },
        requestGraphState: () => {
          // No-op for fake data
        },
        ping: () => {
          // No-op for fake data
        },
        refreshFakeData: () => {
          // Trigger a re-render by forcing component update
          // This is a simple way to refresh fake data
          console.log('Refreshing fake data...');
        }
      };
    } else {
      return {
        ...realtimeActions,
        refreshFakeData: () => {
          // No-op for real-time data
        }
      };
    }
  }, [isUsingFakeData, realtimeActions]);

  return [state, actions];
} 