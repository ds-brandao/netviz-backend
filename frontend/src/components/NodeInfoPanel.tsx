import React, { useState } from 'react';
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
  Info,
  FileText,
  BarChart3,
  Settings,
  Eye
} from 'lucide-react';
import { NetworkNode } from '../types/network';
import { formatMetadataForDisplay, getDisplayFieldName, isEmpty } from '../utils/dataAdapter';
import LogViewer from './LogViewer';

interface NodeInfoPanelProps {
  node: NetworkNode;
}

type TabType = 'overview' | 'logs' | 'stats' | 'config';

export const NodeInfoPanel: React.FC<NodeInfoPanelProps> = ({ node }) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');

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
  const hardwareFields = ['vendor', 'model', 'version', 'ports', 'serial_number', 'firmware'];
  const performanceFields = ['cpu', 'memory', 'bandwidth_usage', 'packet_loss', 'latency'];
  const locationFields = ['location', 'uptime', 'rack', 'datacenter', 'building'];
  const networkFields = ['vlan', 'subnet', 'gateway', 'dns', 'domain'];
  
  const hardwareInfo = Object.fromEntries(
    Object.entries(displayMetadata).filter(([key]) => hardwareFields.includes(key))
  );
  
  const performanceInfo = Object.fromEntries(
    Object.entries(displayMetadata).filter(([key]) => performanceFields.includes(key))
  );
  
  const locationInfo = Object.fromEntries(
    Object.entries(displayMetadata).filter(([key]) => locationFields.includes(key))
  );

  const networkInfo = Object.fromEntries(
    Object.entries(displayMetadata).filter(([key]) => networkFields.includes(key))
  );
  
  const otherInfo = Object.fromEntries(
    Object.entries(displayMetadata).filter(([key]) => 
      !hardwareFields.includes(key) && 
      !performanceFields.includes(key) && 
      !locationFields.includes(key) &&
      !networkFields.includes(key)
    )
  );

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Eye },
    { id: 'logs', label: 'Logs', icon: FileText },
    { id: 'stats', label: 'Stats', icon: BarChart3 },
    { id: 'config', label: 'Config', icon: Settings },
  ];

  const renderOverviewTab = () => (
    <div className="space-y-4">
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
                <span className={`text-white ${key === 'version' || key === 'serial_number' ? 'font-mono' : ''}`}>
                  {value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Network Configuration */}
      {Object.keys(networkInfo).length > 0 && (
        <div className="p-3 bg-gray-800/30 rounded-lg border border-gray-700/50">
          <h4 className="text-white font-medium mb-2 flex items-center gap-2">
            <Network className="w-4 h-4 text-blue-400" />
            Network Configuration
          </h4>
          <div className="space-y-2 text-sm">
            {Object.entries(networkInfo).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="text-gray-400">{getDisplayFieldName(key)}:</span>
                <span className="text-white font-mono">
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

            {/* Additional performance metrics */}
            {Object.entries(performanceInfo).filter(([key]) => !['cpu', 'memory'].includes(key)).map(([key, value]) => (
              <div key={key} className="flex justify-between text-sm">
                <span className="text-gray-400">{getDisplayFieldName(key)}:</span>
                <span className="text-white font-mono">{value}</span>
              </div>
            ))}
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

  const renderLogsTab = () => (
    <div className="h-full">
      <LogViewer nodeId={node.id} className="h-full" />
    </div>
  );

  const renderStatsTab = () => (
    <div className="space-y-4">
      <div className="p-3 bg-gray-800/30 rounded-lg border border-gray-700/50">
        <h4 className="text-white font-medium mb-3">Connection Statistics</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-400">Active Connections:</span>
            <div className="text-white font-mono">
              {displayMetadata.active_connections || 'N/A'}
            </div>
          </div>
          <div>
            <span className="text-gray-400">Total Packets:</span>
            <div className="text-white font-mono">
              {displayMetadata.total_packets || 'N/A'}
            </div>
          </div>
          <div>
            <span className="text-gray-400">Bytes Sent:</span>
            <div className="text-white font-mono">
              {displayMetadata.bytes_sent || 'N/A'}
            </div>
          </div>
          <div>
            <span className="text-gray-400">Bytes Received:</span>
            <div className="text-white font-mono">
              {displayMetadata.bytes_received || 'N/A'}
            </div>
          </div>
        </div>
      </div>

      <div className="p-3 bg-gray-800/30 rounded-lg border border-gray-700/50">
        <h4 className="text-white font-medium mb-3">Health Metrics</h4>
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Last Health Check:</span>
            <span className="text-white">
              {displayMetadata.last_health_check || new Date().toLocaleString()}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Response Time:</span>
            <span className="text-white font-mono">
              {displayMetadata.response_time || '<1ms'}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Availability:</span>
            <span className="text-green-400 font-mono">
              {displayMetadata.availability || '99.9%'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderConfigTab = () => (
    <div className="space-y-4">
      <div className="p-3 bg-gray-800/30 rounded-lg border border-gray-700/50">
        <h4 className="text-white font-medium mb-3">Device Configuration</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Management IP:</span>
            <span className="text-white font-mono">{node.ip || 'N/A'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">SNMP Community:</span>
            <span className="text-white font-mono">
              {displayMetadata.snmp_community || 'public'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">SSH Port:</span>
            <span className="text-white font-mono">
              {displayMetadata.ssh_port || '22'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Protocol:</span>
            <span className="text-white">
              {displayMetadata.protocol || 'SSH/SNMP'}
            </span>
          </div>
        </div>
      </div>

      <div className="p-3 bg-gray-800/30 rounded-lg border border-gray-700/50">
        <h4 className="text-white font-medium mb-3">Security Settings</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Access Control:</span>
            <span className="text-white">
              {displayMetadata.access_control || 'Enabled'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Encryption:</span>
            <span className="text-white">
              {displayMetadata.encryption || 'AES-256'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Last Security Scan:</span>
            <span className="text-white">
              {displayMetadata.last_security_scan || 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {/* Raw metadata for debugging */}
      <div className="p-3 bg-gray-800/30 rounded-lg border border-gray-700/50">
        <h4 className="text-white font-medium mb-3">Raw Metadata</h4>
        <pre className="text-xs text-gray-300 bg-gray-900 p-2 rounded overflow-auto max-h-40">
          {JSON.stringify(node.metadata, null, 2)}
        </pre>
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 p-3 bg-gray-800/30 rounded-lg border border-gray-700/50 mb-4">
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

      {/* Tabs */}
      <div className="flex space-x-1 mb-4 bg-gray-800/20 rounded-lg p-1">
        {tabs.map((tab) => {
          const TabIcon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
              }`}
            >
              <TabIcon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'logs' && renderLogsTab()}
        {activeTab === 'stats' && renderStatsTab()}
        {activeTab === 'config' && renderConfigTab()}
      </div>
    </div>
  );
};