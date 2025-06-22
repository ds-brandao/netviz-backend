import React, { useState } from 'react';
import { SimpleLiquidGlass } from './SimpleLiquidGlass/SimpleLiquidGlass';
import { useTheme } from '../contexts/ThemeContext';
import { 
  Settings, 
  MessageSquare, 
  Info, 
  Layout, 
  Layers,
  Search,
  RotateCcw,
  Zap,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronUp,
  Network,
  Cog
} from 'lucide-react';
import { NetworkNode, LayoutMode, FilterLayer } from '../types/network';
import { NodeInfoPanel } from './NodeInfoPanel';
import { ChatPanel } from './ChatPanel';

interface ControlPanelProps {
  focusedNode: NetworkNode | null;
  onLayoutChange: (layout: LayoutMode) => void;
  onFilterChange: (layers: FilterLayer[]) => void;
  onResetView: () => void;
  activeLayers: FilterLayer[];
  currentLayout: LayoutMode;
  onOpenSettings: () => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  focusedNode,
  onLayoutChange,
  onFilterChange,
  onResetView,
  activeLayers,
  currentLayout,
  onOpenSettings
}) => {
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState<'info' | 'chat' | 'controls'>('controls');
  const [isExpanded, setIsExpanded] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const layouts: { key: LayoutMode; label: string; icon: React.ReactNode }[] = [
    { key: 'force', label: 'Force Directed', icon: <Zap className="w-4 h-4" /> },
    { key: 'hierarchical', label: 'Hierarchical', icon: <Layout className="w-4 h-4" /> },
    { key: 'circular', label: 'Circular', icon: <RotateCcw className="w-4 h-4" /> },
    { key: 'grid', label: 'Grid', icon: <Settings className="w-4 h-4" /> }
  ];

  const layers: { key: FilterLayer; label: string; color: string }[] = [
    { key: 'physical', label: 'Physical', color: 'bg-red-500' },
    { key: 'datalink', label: 'Data Link', color: 'bg-orange-500' },
    { key: 'network', label: 'Network', color: 'bg-yellow-500' },
    { key: 'transport', label: 'Transport', color: 'bg-green-500' },
    { key: 'application', label: 'Application', color: 'bg-blue-500' }
  ];

  const toggleLayer = (layer: FilterLayer) => {
    const newLayers = activeLayers.includes(layer)
      ? activeLayers.filter(l => l !== layer)
      : [...activeLayers, layer];
    onFilterChange(newLayers);
  };

  const tabs = [
    { key: 'controls' as const, label: 'Controls', icon: Settings },
    { key: 'info' as const, label: 'Node Info', icon: Info, disabled: !focusedNode },
    { key: 'chat' as const, label: 'AI Assistant', icon: MessageSquare }
  ];

  return (
    <SimpleLiquidGlass
      padding="0"
      textColor={theme === 'light' ? '#1f2937' : 'white'}
    >
        <div className="w-80 bg-transparent">
          {/* Header */}
          <div className={`flex items-center justify-between p-4 border-b ${theme === 'light' ? 'border-gray-200' : 'border-white/10'}`}>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Network className="w-4 h-4 text-white" />
              </div>
              <div>
                <h2 className={`font-semibold text-sm ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>Network Control</h2>
                <p className={`text-xs ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`}>
                  {focusedNode ? `Focused: ${focusedNode.label}` : 'Network Overview'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={onOpenSettings}
                className={`p-1 rounded-lg transition-colors ${theme === 'light' ? 'hover:bg-gray-100' : 'hover:bg-white/10'}`}
                title="Settings"
              >
                <Cog className={`w-4 h-4 ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`} />
              </button>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className={`p-1 rounded-lg transition-colors ${theme === 'light' ? 'hover:bg-gray-100' : 'hover:bg-white/10'}`}
              >
                {isExpanded ? (
                  <ChevronUp className={`w-4 h-4 ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`} />
                ) : (
                  <ChevronDown className={`w-4 h-4 ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`} />
                )}
              </button>
            </div>
          </div>

          {isExpanded && (
            <>
              {/* Tab Navigation */}
              <div className={`flex border-b ${theme === 'light' ? 'border-gray-200' : 'border-white/10'}`}>
                {tabs.map(tab => {
                  const IconComponent = tab.icon;
                  return (
                    <button
                      key={tab.key}
                      onClick={() => !tab.disabled && setActiveTab(tab.key)}
                      disabled={tab.disabled}
                      className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium transition-colors ${
                        activeTab === tab.key
                          ? 'text-blue-400 bg-blue-500/20 border-b-2 border-blue-500'
                          : tab.disabled
                          ? `${theme === 'light' ? 'text-gray-400' : 'text-gray-600'} cursor-not-allowed`
                          : `${theme === 'light' ? 'text-gray-600 hover:text-gray-900 hover:bg-gray-100' : 'text-gray-400 hover:text-white hover:bg-white/5'}`
                      }`}
                    >
                      <IconComponent className="w-3 h-3" />
                      {tab.label}
                    </button>
                  );
                })}
              </div>

              {/* Content */}
              <div className="p-4 max-h-96 overflow-y-auto">
                {activeTab === 'controls' && (
                  <div className="space-y-4">
                    {/* Search */}
                    <div className="relative">
                      <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 ${theme === 'light' ? 'text-gray-500' : 'text-gray-400'}`} />
                      <input
                        type="text"
                        placeholder="Search network..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className={`w-full pl-10 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:border-blue-500 transition-colors ${
                          theme === 'light'
                            ? 'border-gray-300 bg-gray-50 text-gray-900 placeholder-gray-500'
                            : 'border-white/20 bg-white/5 text-white placeholder-gray-400'
                        }`}
                      />
                    </div>

                    {/* Layout Controls */}
                    <div>
                      <h3 className={`font-medium text-sm mb-2 flex items-center gap-2 ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>
                        <Layout className="w-4 h-4 text-blue-400" />
                        Layout Mode
                      </h3>
                      <div className="grid grid-cols-2 gap-2">
                        {layouts.map(layout => (
                          <button
                            key={layout.key}
                            onClick={() => onLayoutChange(layout.key)}
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all border ${
                              currentLayout === layout.key
                                ? 'bg-blue-500/80 text-white border-blue-500'
                                : theme === 'light'
                                ? 'bg-gray-100 text-gray-700 hover:bg-gray-200 border-gray-300'
                                : 'bg-white/10 text-gray-300 hover:bg-white/20 border-white/20'
                            }`}
                          >
                            {layout.icon}
                            {layout.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Layer Filters */}
                    <div>
                      <h3 className={`font-medium text-sm mb-2 flex items-center gap-2 ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>
                        <Layers className="w-4 h-4 text-purple-400" />
                        Network Layers
                      </h3>
                      <div className="space-y-2">
                        {layers.map(layer => {
                          const isActive = activeLayers.includes(layer.key);
                          return (
                            <button
                              key={layer.key}
                              onClick={() => toggleLayer(layer.key)}
                              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-all border ${
                                isActive
                                  ? theme === 'light'
                                    ? 'bg-blue-50 border-blue-300 shadow-sm'
                                    : 'bg-white/15 border border-white/30'
                                  : theme === 'light'
                                  ? 'bg-gray-50 hover:bg-gray-100 border-gray-200 hover:border-gray-300'
                                  : 'bg-white/5 hover:bg-white/10 border-white/10'
                              }`}
                            >
                              <div className="flex items-center gap-2">
                                <div className={`w-3 h-3 rounded-full ${layer.color}`} />
                                <span className={`text-sm ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>{layer.label}</span>
                              </div>
                              {isActive ? (
                                <Eye className="w-4 h-4 text-green-500" />
                              ) : (
                                <EyeOff className={`w-4 h-4 ${theme === 'light' ? 'text-gray-400' : 'text-gray-500'}`} />
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {/* Reset Button */}
                    <button
                      onClick={onResetView}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg transition-all duration-200 font-medium text-sm"
                    >
                      <RotateCcw className="w-4 h-4" />
                      Reset View
                    </button>
                  </div>
                )}

                {activeTab === 'info' && focusedNode && (
                  <NodeInfoPanel node={focusedNode} />
                )}

                {activeTab === 'chat' && (
                  <ChatPanel focusedNode={focusedNode} />
                )}
              </div>
            </>
          )}
                          </div>
    </SimpleLiquidGlass>
  );
};