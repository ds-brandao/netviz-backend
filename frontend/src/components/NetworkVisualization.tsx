import React, { useState, useCallback, useMemo } from 'react';
import ReactFlow, {
  Node,
  addEdge,
  useNodesState,
  useEdgesState,
  Connection,
  Controls,
  Background,
  ReactFlowProvider,
  NodeTypes,
  Viewport,
  BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useTheme } from '../contexts/ThemeContext';

import { NetworkNode } from './NetworkNode';
import { NetworkEdge } from './NetworkEdge';
import { EnhancedCombinedControlPanel } from './EnhancedCombinedControlPanel';
import { EnhancedSettingsModal } from './EnhancedSettingsModal';
import { useNetworkLayout } from '../hooks/useNetworkLayout';
import { useNetworkData } from '../hooks/useNetworkData';
import { NetworkNode as NetworkNodeType, LayoutMode, FilterLayer } from '../types/network';

const nodeTypes: NodeTypes = {
  networkNode: NetworkNode,
};

const edgeTypes = {
  networkEdge: NetworkEdge,
};

const NetworkVisualizationContent: React.FC = () => {
  const { theme } = useTheme();
  const [focusedNode, setFocusedNode] = useState<NetworkNodeType | null>(null);
  const [currentLayout, setCurrentLayout] = useState<LayoutMode>('hierarchical');
  const [activeLayers, setActiveLayers] = useState<FilterLayer[]>(['physical', 'datalink', 'network', 'transport', 'application']);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const { applyLayout } = useNetworkLayout();

  // Use network data (either real-time or fake)
  const [networkState] = useNetworkData();

  // Get nodes and edges from the network data
  const frontendNodes = useMemo(() => {
    return networkState.nodes;
  }, [networkState.nodes]);

  const frontendEdges = useMemo(() => {
    return networkState.edges;
  }, [networkState.edges]);

  // Filter nodes based on active layers
  const filteredNodes = useMemo(() => {
    return frontendNodes.filter(node => activeLayers.includes(node.layer));
  }, [frontendNodes, activeLayers]);

  // Filter edges based on visible nodes
  const filteredEdges = useMemo(() => {
    const nodeIds = new Set(filteredNodes.map(node => node.id));
    return frontendEdges.filter(edge => nodeIds.has(edge.source) && nodeIds.has(edge.target));
  }, [filteredNodes, frontendEdges]);

  // Apply layout to nodes
  const layoutedNodes = useMemo(() => {
    return applyLayout(filteredNodes, filteredEdges, currentLayout);
  }, [filteredNodes, filteredEdges, currentLayout, applyLayout]);

  // Convert edges to React Flow format
  const layoutedEdges = useMemo(() => {
    return filteredEdges.map(edge => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: 'networkEdge',
      data: edge,
      animated: edge.status === 'active' && (edge.utilization || 0) > 50,
    }));
  }, [filteredEdges]);

  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges);

  // Update nodes and edges when layout changes
  React.useEffect(() => {
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [layoutedNodes, layoutedEdges, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    const networkNode = node.data as NetworkNodeType;
    setFocusedNode(networkNode);
  }, []);

  const onPaneClick = useCallback(() => {
    setFocusedNode(null);
  }, []);

  const handleLayoutChange = useCallback((layout: LayoutMode) => {
    setCurrentLayout(layout);
  }, []);

  const handleFilterChange = useCallback((layers: FilterLayer[]) => {
    setActiveLayers(layers);
  }, []);

  const handleResetView = useCallback(() => {
    setFocusedNode(null);
  }, []);

  const defaultViewport: Viewport = {
    x: 0,
    y: 0,
    zoom: 0.8
  };

  // Calculate network stats from real-time data
  const networkStats = useMemo(() => {
    const totalNodes = filteredNodes.length;
    const active = filteredNodes.filter(n => n.status === 'online').length;
    const issues = filteredNodes.filter(n => n.status === 'error' || n.status === 'warning').length;
    
    return { totalNodes, active, issues };
  }, [filteredNodes]);

  return (
    <div className={`w-screen h-screen overflow-hidden relative transition-colors duration-300 ${
      theme === 'light' ? 'bg-gray-100' : 'bg-gray-900'
    }`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{
          padding: 0.1,
          includeHiddenNodes: false,
          minZoom: 0.1,
          maxZoom: 2
        }}
        defaultViewport={defaultViewport}
        minZoom={0.1}
        maxZoom={2}
        className="w-full h-full"
        proOptions={{ hideAttribution: true }}
      >
        <Background 
          color={theme === 'light' ? "#a855f7" : "#8b5cf6"} 
          gap={20} 
          size={2}
          variant={BackgroundVariant.Dots}
        />
        
        <Controls 
          className="!bottom-4 !left-1/2 !transform !-translate-x-1/2"
          showZoom={true}
          showFitView={true}
          showInteractive={true}
        />
      </ReactFlow>

      {/* Combined Control Panel - Left */}
      <div className="absolute top-0 left-0 p-4">
        <div className="pointer-events-auto">
                      <EnhancedCombinedControlPanel
            focusedNode={focusedNode}
            currentLayout={currentLayout}
            activeLayers={activeLayers}
            onLayoutChange={handleLayoutChange}
            onFilterChange={handleFilterChange}
            onResetView={handleResetView}
            onOpenSettings={() => setIsSettingsOpen(true)}
            networkStats={networkStats}
          />
        </div>
      </div>

      {/* Connection status indicator */}
      <div className="absolute top-4 right-4 pointer-events-auto">
        <div className={`px-3 py-2 rounded-lg text-sm font-medium ${
          networkState.isConnected 
            ? 'bg-green-100 text-green-800 border border-green-200' 
            : networkState.isConnecting
            ? 'bg-yellow-100 text-yellow-800 border border-yellow-200'
            : 'bg-red-100 text-red-800 border border-red-200'
        }`}>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              networkState.isConnected ? 'bg-green-500' : 
              networkState.isConnecting ? 'bg-yellow-500' : 'bg-red-500'
            }`} />
            <span>
              {networkState.dataMode === 'fake' ? 'Fake Data' :
               networkState.isConnected ? 'Live' : 
               networkState.isConnecting ? 'Connecting...' : 'Disconnected'}
            </span>
          </div>
          {networkState.lastUpdated && (
            <div className="text-xs opacity-75 mt-1">
              Last update: {new Date(networkState.lastUpdated).toLocaleTimeString()}
            </div>
          )}
          {networkState.connectionError && (
            <div className="text-xs text-red-600 mt-1">
              {networkState.connectionError}
            </div>
          )}
        </div>
      </div>

      {/* Settings Modal */}
      {isSettingsOpen && (
      <EnhancedSettingsModal 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
      />
      )}
    </div>
  );
};

export const NetworkVisualization: React.FC = () => {
  return (
    <ReactFlowProvider>
      <NetworkVisualizationContent />
    </ReactFlowProvider>
  );
};