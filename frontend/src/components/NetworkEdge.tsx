import React from 'react';
import { 
  BaseEdge, 
  EdgeLabelRenderer, 
  getStraightPath,
  type EdgeProps 
} from 'reactflow';
import { NetworkEdge as NetworkEdgeType } from '../types/network';

interface NetworkEdgeProps extends EdgeProps {
  data?: NetworkEdgeType;
}

export const NetworkEdge: React.FC<NetworkEdgeProps> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected
}) => {
  const [edgePath, labelX, labelY] = getStraightPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const getEdgeColor = () => {
    if (!data) return '#6B7280';
    
    switch (data.status) {
      case 'active':
        return data.utilization && data.utilization > 80 ? '#EF4444' : 
               data.utilization && data.utilization > 60 ? '#F59E0B' : '#10B981';
      case 'inactive':
        return '#6B7280';
      case 'error':
        return '#EF4444';
      default:
        return '#6B7280';
    }
  };

  const getEdgeWidth = () => {
    if (!data?.bandwidth) return 2;
    
    // Convert bandwidth to stroke width
    if (data.bandwidth.includes('100G')) return 4;
    if (data.bandwidth.includes('10G')) return 3;
    if (data.bandwidth.includes('1G')) return 2;
    return 1;
  };

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: getEdgeColor(),
          strokeWidth: getEdgeWidth(),
          strokeDasharray: data?.type === 'wireless' ? '5,5' : 
                          data?.type === 'vpn' ? '10,5' : 'none',
          opacity: selected ? 1 : 0.8,
          filter: selected ? 'drop-shadow(0 0 6px currentColor)' : 'none'
        }}
      />
      {data && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              background: 'rgba(17, 24, 39, 0.9)',
              padding: '4px 8px',
              borderRadius: '6px',
              fontSize: '11px',
              fontWeight: 500,
              color: 'white',
              border: '1px solid rgba(107, 114, 128, 0.3)',
              backdropFilter: 'blur(4px)',
              pointerEvents: 'all',
            }}
            className="nodrag nopan"
          >
            <div className="text-center">
              {data.bandwidth && (
                <div className="text-blue-300">{data.bandwidth}</div>
              )}
              {data.utilization !== undefined && (
                <div className={`text-xs ${
                  data.utilization > 80 ? 'text-red-400' : 
                  data.utilization > 60 ? 'text-yellow-400' : 'text-green-400'
                }`}>
                  {data.utilization}% util
                </div>
              )}
            </div>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
};