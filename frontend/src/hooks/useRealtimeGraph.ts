import { useState, useEffect, useCallback, useRef } from 'react';
import { WebSocketManager, GraphUpdate, BackendNetworkNode, BackendNetworkEdge } from '../services/api';

export interface RealtimeGraphState {
  nodes: BackendNetworkNode[];
  edges: BackendNetworkEdge[];
  isConnected: boolean;
  isConnecting: boolean;
  lastUpdated: string | null;
  connectionError: string | null;
}

export interface RealtimeGraphActions {
  connect: () => Promise<void>;
  disconnect: () => void;
  requestGraphState: () => void;
  ping: () => void;
}

export function useRealtimeGraph(sessionId: string = 'default'): [RealtimeGraphState, RealtimeGraphActions] {
  const [state, setState] = useState<RealtimeGraphState>({
    nodes: [],
    edges: [],
    isConnected: false,
    isConnecting: false,
    lastUpdated: null,
    connectionError: null,
  });

  const wsManagerRef = useRef<WebSocketManager | null>(null);

  const handleGraphUpdate = useCallback((update: GraphUpdate) => {
    console.log('Received graph update:', update);

    setState(prevState => {
      switch (update.type) {
        case 'connection_established':
          return {
            ...prevState,
            isConnected: true,
            isConnecting: false,
            connectionError: null,
          };

        case 'graph_state':
          // Complete graph state update
          return {
            ...prevState,
            nodes: update.nodes || [],
            edges: update.edges || [],
            lastUpdated: update.timestamp,
          };

        case 'graph_update':
          // Individual entity update
          if (update.update_type && update.entity_type && update.entity_data) {
            const newState = { ...prevState };

            if (update.entity_type === 'node') {
              const nodeData = update.entity_data as BackendNetworkNode;
              
              switch (update.update_type) {
                case 'created':
                  newState.nodes = [...prevState.nodes, nodeData];
                  break;
                  
                case 'updated':
                  newState.nodes = prevState.nodes.map(node =>
                    node.id === nodeData.id ? nodeData : node
                  );
                  break;
                  
                case 'deleted':
                  newState.nodes = prevState.nodes.filter(node => node.id !== nodeData.id);
                  // Also remove any edges connected to this node
                  newState.edges = prevState.edges.filter(edge => 
                    edge.source !== nodeData.id && edge.target !== nodeData.id
                  );
                  break;
              }
            } else if (update.entity_type === 'edge') {
              const edgeData = update.entity_data as BackendNetworkEdge;
              
              switch (update.update_type) {
                case 'created':
                  newState.edges = [...prevState.edges, edgeData];
                  break;
                  
                case 'updated':
                  newState.edges = prevState.edges.map(edge =>
                    edge.id === edgeData.id ? edgeData : edge
                  );
                  break;
                  
                case 'deleted':
                  newState.edges = prevState.edges.filter(edge => edge.id !== edgeData.id);
                  break;
              }
            }

            newState.lastUpdated = update.timestamp;
            return newState;
          }
          return prevState;

        case 'ping':
          // Respond to ping with pong
          if (wsManagerRef.current) {
            wsManagerRef.current.send({ type: 'pong', timestamp: new Date().toISOString() });
          }
          return prevState;

        case 'pong':
          // Server responded to our ping
          return prevState;

        default:
          return prevState;
      }
    });
  }, []);

  const connect = useCallback(async () => {
    if (wsManagerRef.current || state.isConnecting) return;

    setState(prev => ({ ...prev, isConnecting: true, connectionError: null }));

    try {
      wsManagerRef.current = new WebSocketManager(sessionId);
      wsManagerRef.current.addMessageHandler(handleGraphUpdate);
      await wsManagerRef.current.connect();
      
      setState(prev => ({
        ...prev,
        isConnected: true,
        isConnecting: false,
        connectionError: null,
      }));
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setState(prev => ({
        ...prev,
        isConnected: false,
        isConnecting: false,
        connectionError: error instanceof Error ? error.message : 'Connection failed',
      }));
      wsManagerRef.current = null;
    }
  }, [sessionId, handleGraphUpdate, state.isConnecting]);

  const disconnect = useCallback(() => {
    if (wsManagerRef.current) {
      wsManagerRef.current.removeMessageHandler(handleGraphUpdate);
      wsManagerRef.current.disconnect();
      wsManagerRef.current = null;
    }
    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
    }));
  }, [handleGraphUpdate]);

  const requestGraphState = useCallback(() => {
    if (wsManagerRef.current) {
      wsManagerRef.current.requestGraphState();
    }
  }, []);

  const ping = useCallback(() => {
    if (wsManagerRef.current) {
      wsManagerRef.current.ping();
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // Auto-connect on mount
  useEffect(() => {
    connect();
  }, [connect]);

  // 5-second sync updates
  useEffect(() => {
    if (!state.isConnected) return;

    const interval = setInterval(() => {
      if (wsManagerRef.current && state.isConnected) {
        wsManagerRef.current.requestGraphState();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [state.isConnected]);

  const actions: RealtimeGraphActions = {
    connect,
    disconnect,
    requestGraphState,
    ping,
  };

  return [state, actions];
} 