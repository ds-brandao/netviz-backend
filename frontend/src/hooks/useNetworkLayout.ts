import { useCallback } from 'react';
import dagre from 'dagre';
import { Node, Position } from 'reactflow';
import { NetworkNode, NetworkEdge, LayoutMode } from '../types/network';

export const useNetworkLayout = () => {
  const applyLayout = useCallback((
    nodes: NetworkNode[],
    edges: NetworkEdge[],
    layout: LayoutMode
  ): Node[] => {
    switch (layout) {
      case 'hierarchical':
        return applyHierarchicalLayout(nodes, edges);
      case 'circular':
        return applyCircularLayout(nodes);
      case 'grid':
        return applyGridLayout(nodes);
      case 'force':
      default:
        return applyForceLayout(nodes);
    }
  }, []);

  return { applyLayout };
};

const applyHierarchicalLayout = (nodes: NetworkNode[], edges: NetworkEdge[]): Node[] => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ 
    rankdir: 'TB', 
    ranksep: 150, 
    nodesep: 120,
    marginx: 50,
    marginy: 50
  });

  nodes.forEach(node => {
    dagreGraph.setNode(node.id, { width: 220, height: 140 });
  });

  edges.forEach(edge => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  return nodes.map(node => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      id: node.id,
      type: 'networkNode',
      position: {
        x: nodeWithPosition.x - 110,
        y: nodeWithPosition.y - 70,
      },
      data: node,
      targetPosition: Position.Top,
      sourcePosition: Position.Bottom,
    };
  });
};

const applyCircularLayout = (nodes: NetworkNode[]): Node[] => {
  const center = { x: 400, y: 300 };
  const baseRadius = 200;
  
  // Group nodes by layer for better organization
  const layerGroups: { [key: string]: NetworkNode[] } = {};
  nodes.forEach(node => {
    if (!layerGroups[node.layer]) {
      layerGroups[node.layer] = [];
    }
    layerGroups[node.layer].push(node);
  });

  const layerOrder = ['physical', 'datalink', 'network', 'transport', 'application'];
  
  return nodes.map((node) => {
    const layerIndex = layerOrder.indexOf(node.layer);
    const radius = baseRadius + (layerIndex * 80);
    const nodesInLayer = layerGroups[node.layer].length;
    const indexInLayer = layerGroups[node.layer].indexOf(node);
    
    const angle = (indexInLayer / nodesInLayer) * 2 * Math.PI;
    const x = center.x + radius * Math.cos(angle);
    const y = center.y + radius * Math.sin(angle);
    
    return {
      id: node.id,
      type: 'networkNode',
      position: { x, y },
      data: node,
      targetPosition: Position.Top,
      sourcePosition: Position.Bottom,
    };
  });
};

const applyGridLayout = (nodes: NetworkNode[]): Node[] => {
  const spacing = { x: 280, y: 200 };
  const startPos = { x: 100, y: 100 };
  
  let currentRow = 0;
  let currentCol = 0;
  const maxCols = 4;

  return nodes.map((node) => {
    const position = {
      x: startPos.x + (currentCol * spacing.x),
      y: startPos.y + (currentRow * spacing.y)
    };

    currentCol++;
    if (currentCol >= maxCols) {
      currentCol = 0;
      currentRow++;
    }

    return {
      id: node.id,
      type: 'networkNode',
      position,
      data: node,
      targetPosition: Position.Top,
      sourcePosition: Position.Bottom,
    };
  });
};

const applyForceLayout = (nodes: NetworkNode[]): Node[] => {
  // Create a more organized force layout based on network topology
  const center = { x: 400, y: 300 };
  
  // Group nodes by type and layer for logical positioning
  const coreNodes = nodes.filter(n => n.type === 'router' || n.type === 'firewall');
  const distributionNodes = nodes.filter(n => n.type === 'switch' && n.layer === 'datalink');
  const accessNodes = nodes.filter(n => n.type === 'switch' && n.layer !== 'datalink');
  const serverNodes = nodes.filter(n => n.type === 'server');
  const endpointNodes = nodes.filter(n => n.type === 'endpoint');

  const result: Node[] = [];

  // Position core nodes in the center
  coreNodes.forEach((node, index) => {
    const angle = (index / coreNodes.length) * 2 * Math.PI;
    const radius = 80;
    result.push({
      id: node.id,
      type: 'networkNode',
      position: {
        x: center.x + radius * Math.cos(angle),
        y: center.y + radius * Math.sin(angle)
      },
      data: node,
      targetPosition: Position.Top,
      sourcePosition: Position.Bottom,
    });
  });

  // Position distribution nodes around core
  distributionNodes.forEach((node, index) => {
    const angle = (index / distributionNodes.length) * 2 * Math.PI;
    const radius = 200;
    result.push({
      id: node.id,
      type: 'networkNode',
      position: {
        x: center.x + radius * Math.cos(angle),
        y: center.y + radius * Math.sin(angle)
      },
      data: node,
      targetPosition: Position.Top,
      sourcePosition: Position.Bottom,
    });
  });

  // Position access nodes in outer ring
  accessNodes.forEach((node, index) => {
    const angle = (index / accessNodes.length) * 2 * Math.PI;
    const radius = 320;
    result.push({
      id: node.id,
      type: 'networkNode',
      position: {
        x: center.x + radius * Math.cos(angle),
        y: center.y + radius * Math.sin(angle)
      },
      data: node,
      targetPosition: Position.Top,
      sourcePosition: Position.Bottom,
    });
  });

  // Position servers
  serverNodes.forEach((node, index) => {
    const angle = (index / serverNodes.length) * 2 * Math.PI + Math.PI / 4;
    const radius = 280;
    result.push({
      id: node.id,
      type: 'networkNode',
      position: {
        x: center.x + radius * Math.cos(angle),
        y: center.y + radius * Math.sin(angle)
      },
      data: node,
      targetPosition: Position.Top,
      sourcePosition: Position.Bottom,
    });
  });

  // Position endpoints
  endpointNodes.forEach((node, index) => {
    const angle = (index / endpointNodes.length) * 2 * Math.PI;
    const radius = 420;
    result.push({
      id: node.id,
      type: 'networkNode',
      position: {
        x: center.x + radius * Math.cos(angle),
        y: center.y + radius * Math.sin(angle)
      },
      data: node,
      targetPosition: Position.Top,
      sourcePosition: Position.Bottom,
    });
  });

  return result;
};