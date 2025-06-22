import React from 'react';
import { Handle, Position } from 'reactflow';
import { 
  Router, 
  Network, 
  Shield, 
  Server, 
  Monitor,
  Laptop,
  HardDrive,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react';
import { NetworkNode as NetworkNodeType } from '../types/network';
import { useTheme } from '../contexts/ThemeContext';

export interface NetworkNodeProps {
  data: NetworkNodeType;
  isConnectable: boolean;
  selected: boolean;
}

const getNodeIcon = (type: NetworkNodeType['type']) => {
  switch (type) {
    case 'router':
      return Router;
    case 'switch':
      return Network;
    case 'firewall':
      return Shield;
    case 'server':
      return Server;
    case 'endpoint':
      return Monitor;
    case 'client':
      return Laptop;
    case 'host':
      return HardDrive;
    default:
      return Network;
  }
};

const getStatusColor = (status: NetworkNodeType['status']) => {
  switch (status) {
    case 'online':
      return 'text-green-400 bg-green-400/20';
    case 'warning':
      return 'text-yellow-400 bg-yellow-400/20';
    case 'error':
      return 'text-red-400 bg-red-400/20';
    case 'offline':
      return 'text-gray-400 bg-gray-400/20';
    default:
      return 'text-gray-400 bg-gray-400/20';
  }
};

const getStatusIcon = (status: NetworkNodeType['status']) => {
  switch (status) {
    case 'online':
      return CheckCircle;
    case 'warning':
      return AlertTriangle;
    case 'error':
      return XCircle;
    case 'offline':
      return Clock;
    default:
      return Clock;
  }
};

export const NetworkNode: React.FC<NetworkNodeProps> = ({ data, isConnectable, selected }) => {
  const { theme } = useTheme();
  const IconComponent = getNodeIcon(data.type);
  const StatusIcon = getStatusIcon(data.status);
  const statusColor = getStatusColor(data.status);

  return (
    <div className={`relative min-w-[180px] backdrop-blur-sm border rounded-xl p-4 shadow-2xl transition-all duration-300 hover:shadow-blue-500/20 hover:border-blue-500/50 ${
      theme === 'light' 
        ? 'bg-white/90 text-gray-900' 
        : 'bg-gray-900/90 text-white'
    } ${
      selected ? 'border-blue-500 shadow-blue-500/30 scale-105' : 'border-gray-700'
    }`}>
      <Handle
        type="target"
        position={Position.Top}
        isConnectable={isConnectable}
        className="!w-3 !h-3 !bg-blue-500 !border-2 !border-gray-900"
      />
      
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2 rounded-lg ${statusColor}`}>
          <IconComponent className="w-5 h-5" />
        </div>
        <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs ${statusColor}`}>
          <StatusIcon className="w-3 h-3" />
          <span className="capitalize">{data.status}</span>
        </div>
      </div>

      <div className="space-y-2">
        <div>
          <h3 className={`font-semibold text-sm truncate ${
            theme === 'light' ? 'text-gray-900' : 'text-white'
          }`}>{data.label}</h3>
          {data.ip && <p className={`text-xs font-mono ${
            theme === 'light' ? 'text-gray-600' : 'text-gray-400'
          }`}>{data.ip}</p>}
        </div>
        
        <div className={`text-xs ${
          theme === 'light' ? 'text-gray-500' : 'text-gray-500'
        }`}>
          <p className="capitalize">{data.type} • {data.layer}</p>
          {data.metadata.location && (
            <p className="truncate">{data.metadata.location}</p>
          )}
        </div>

        {(data.metadata.cpu !== undefined || data.metadata.memory !== undefined) && (
          <div className="flex gap-2 text-xs">
            {data.metadata.cpu !== undefined && (
              <div className="flex-1">
                <div className="flex justify-between mb-1">
                  <span className={theme === 'light' ? 'text-gray-600' : 'text-gray-400'}>CPU</span>
                  <span className={theme === 'light' ? 'text-gray-900' : 'text-white'}>{data.metadata.cpu}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-1">
                  <div 
                    className={`h-1 rounded-full transition-all duration-300 ${
                      data.metadata.cpu > 80 ? 'bg-red-500' : 
                      data.metadata.cpu > 60 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${data.metadata.cpu}%` }}
                  />
                </div>
              </div>
            )}
            {data.metadata.memory !== undefined && (
              <div className="flex-1">
                <div className="flex justify-between mb-1">
                  <span className={theme === 'light' ? 'text-gray-600' : 'text-gray-400'}>MEM</span>
                  <span className={theme === 'light' ? 'text-gray-900' : 'text-white'}>{data.metadata.memory}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-1">
                  <div 
                    className={`h-1 rounded-full transition-all duration-300 ${
                      data.metadata.memory > 80 ? 'bg-red-500' : 
                      data.metadata.memory > 60 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${data.metadata.memory}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        isConnectable={isConnectable}
        className="!w-3 !h-3 !bg-blue-500 !border-2 !border-gray-900"
      />
    </div>
  );
};