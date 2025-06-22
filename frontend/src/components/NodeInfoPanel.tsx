import React from 'react';
import { 
  Router, 
  Network, 
  Shield, 
  Server, 
  Monitor,
  MapPin,
  Clock,
  Cpu,
  HardDrive,
  Cable,
  Activity,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Info
} from 'lucide-react';
import { NetworkNode } from '../types/network';
import { formatMetadataForDisplay, getDisplayFieldName, isEmpty } from '../utils/dataAdapter';

interface NodeInfoPanelProps {
  node: NetworkNode;
}

export const NodeInfoPanel: React.FC<NodeInfoPanelProps> = ({ node }) => {
  const getNodeIcon = (type: NetworkNode['type']) => {
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
      default:
        return Network;
    }
  };

  const getStatusIcon = (status: NetworkNode['status']) => {
    switch (status) {
      case 'online':
        return { icon: CheckCircle, color: 'text-green-400' };
      case 'warning':
        return { icon: AlertTriangle, color: 'text-yellow-400' };
      case 'error':
        return { icon: XCircle, color: 'text-red-400' };
      case 'offline':
        return { icon: XCircle, color: 'text-gray-400' };
      default:
        return { icon: XCircle, color: 'text-gray-400' };
    }
  };

  const IconComponent = getNodeIcon(node.type);
  const statusInfo = getStatusIcon(node.status);
  const StatusIcon = statusInfo.icon;

  // Format metadata for display, filtering out empty fields
  const displayMetadata = formatMetadataForDisplay(node.metadata || {});

  // Categorize metadata fields
  const hardwareFields = ['vendor', 'model', 'version', 'ports'];
  const performanceFields = ['cpu', 'memory'];
  const locationFields = ['location', 'uptime'];
  
  const hardwareInfo = Object.fromEntries(
    Object.entries(displayMetadata).filter(([key]) => hardwareFields.includes(key))
  );
  
  const performanceInfo = Object.fromEntries(
    Object.entries(displayMetadata).filter(([key]) => performanceFields.includes(key))
  );
  
  const locationInfo = Object.fromEntries(
    Object.entries(displayMetadata).filter(([key]) => locationFields.includes(key))
  );
  
  const otherInfo = Object.fromEntries(
    Object.entries(displayMetadata).filter(([key]) => 
      !hardwareFields.includes(key) && 
      !performanceFields.includes(key) && 
      !locationFields.includes(key)
    )
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3 p-3 bg-gray-800/30 rounded-lg border border-gray-700/50">
        <div className="p-2 bg-blue-500/20 rounded-lg">
          <IconComponent className="w-5 h-5 text-blue-400" />
        </div>
        <div className="flex-1">
          <h3 className="text-white font-semibold">{node.label}</h3>
          <div className="flex items-center gap-2 text-sm">
            <StatusIcon className={`w-3 h-3 ${statusInfo.color}`} />
            <span className={`capitalize ${statusInfo.color}`}>{node.status}</span>
            <span className="text-gray-400">•</span>
            <span className="text-gray-400 capitalize">{node.type}</span>
          </div>
        </div>
      </div>

      {/* Basic Info */}
      <div className="space-y-3">
        {/* Only show IP if it exists and is not empty */}
        {!isEmpty(node.ip) && (
          <div className="flex items-center gap-2 text-sm">
            <Cable className="w-4 h-4 text-gray-400" />
            <span className="text-gray-400">IP Address:</span>
            <span className="text-white font-mono">{node.ip}</span>
          </div>
        )}

        {/* Location info from metadata */}
        {locationInfo.location && (
          <div className="flex items-center gap-2 text-sm">
            <MapPin className="w-4 h-4 text-gray-400" />
            <span className="text-gray-400">Location:</span>
            <span className="text-white">{locationInfo.location}</span>
          </div>
        )}

        {locationInfo.uptime && (
          <div className="flex items-center gap-2 text-sm">
            <Clock className="w-4 h-4 text-gray-400" />
            <span className="text-gray-400">Uptime:</span>
            <span className="text-white font-mono">{locationInfo.uptime}</span>
          </div>
        )}
      </div>

      {/* Hardware Info - Only show if there are hardware fields */}
      {Object.keys(hardwareInfo).length > 0 && (
        <div className="p-3 bg-gray-800/30 rounded-lg border border-gray-700/50">
          <h4 className="text-white font-medium mb-2 flex items-center gap-2">
            <Server className="w-4 h-4 text-purple-400" />
            Hardware
          </h4>
          <div className="space-y-2 text-sm">
            {Object.entries(hardwareInfo).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="text-gray-400">{getDisplayFieldName(key)}:</span>
                <span className={`text-white ${key === 'version' ? 'font-mono' : ''}`}>
                  {value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Performance Metrics - Only show if there are performance fields */}
      {Object.keys(performanceInfo).length > 0 && (
        <div className="p-3 bg-gray-800/30 rounded-lg border border-gray-700/50">
          <h4 className="text-white font-medium mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4 text-green-400" />
            Performance
          </h4>
          <div className="space-y-3">
            {performanceInfo.cpu && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-3 h-3 text-gray-400" />
                    <span className="text-gray-400 text-sm">CPU Usage</span>
                  </div>
                  <span className="text-white text-sm font-medium">{performanceInfo.cpu}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-500 ${
                      parseFloat(performanceInfo.cpu) > 80 ? 'bg-red-500' : 
                      parseFloat(performanceInfo.cpu) > 60 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${Math.min(parseFloat(performanceInfo.cpu), 100)}%` }}
                  />
                </div>
              </div>
            )}

            {performanceInfo.memory && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <HardDrive className="w-3 h-3 text-gray-400" />
                    <span className="text-gray-400 text-sm">Memory Usage</span>
                  </div>
                  <span className="text-white text-sm font-medium">{performanceInfo.memory}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-500 ${
                      parseFloat(performanceInfo.memory) > 80 ? 'bg-red-500' : 
                      parseFloat(performanceInfo.memory) > 60 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${Math.min(parseFloat(performanceInfo.memory), 100)}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Additional Metadata - Only show if there are other fields */}
      {Object.keys(otherInfo).length > 0 && (
        <div className="p-3 bg-gray-800/30 rounded-lg border border-gray-700/50">
          <h4 className="text-white font-medium mb-2 flex items-center gap-2">
            <Info className="w-4 h-4 text-blue-400" />
            Additional Info
          </h4>
          <div className="space-y-2 text-sm">
            {Object.entries(otherInfo).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="text-gray-400">{getDisplayFieldName(key)}:</span>
                <span className="text-white break-all max-w-32 text-right">
                  {value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Layer Info */}
      <div className="p-3 bg-gray-800/30 rounded-lg border border-gray-700/50">
        <h4 className="text-white font-medium mb-2">Network Layer</h4>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${
            node.layer === 'physical' ? 'bg-red-500' :
            node.layer === 'datalink' ? 'bg-orange-500' :
            node.layer === 'network' ? 'bg-yellow-500' :
            node.layer === 'transport' ? 'bg-green-500' :
            'bg-blue-500'
          }`} />
          <span className="text-white capitalize text-sm">{node.layer}</span>
        </div>
      </div>
    </div>
  );
};