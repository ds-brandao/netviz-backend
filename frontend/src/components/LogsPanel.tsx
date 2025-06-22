import React, { useState, useEffect, useCallback } from 'react';
import { FileText, AlertTriangle, XCircle, RefreshCw, Search } from 'lucide-react';
import { ApiService, LogEntry } from '../services/api';
import { useTheme } from '../contexts/ThemeContext';

interface LogsPanelProps {
  className?: string;
  focusedNodeId?: string;
}

const LogsPanel: React.FC<LogsPanelProps> = ({ className = '', focusedNodeId }) => {
  const { theme } = useTheme();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'errors' | 'recent'>('recent');

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      let logData: LogEntry[];
      
      // If a device is focused, get logs only for that device
      if (focusedNodeId) {
        const requestId = Date.now();
        console.log(`=== DEVICE FOCUS DEBUG [${requestId}] ===`);
        console.log('focusedNodeId received:', focusedNodeId);
        console.log('focusedNodeId type:', typeof focusedNodeId);
        console.log('focusedNodeId length:', focusedNodeId?.length);
        console.log('filter:', filter);
        
        // Try exact match first, then fallbacks
        const deviceName = focusedNodeId;
        
        console.log('Using device name for logs:', deviceName);
        
        // Use the AI query endpoint for device-specific logs
        const response = await fetch('/ai/query-logs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            device_name: deviceName,
            time_range: filter === 'errors' ? 24 : 2,
            size: 50,
            log_level: filter === 'errors' ? 'ERROR' : undefined
          })
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('Failed to fetch device logs:', response.status, errorText);
          throw new Error(`Failed to fetch device logs: ${response.status}`);
        }
        
        const data = await response.json();
        console.log(`[${requestId}] Device-specific logs received:`, data.logs.length, 'logs');
        console.log(`[${requestId}] Sample log services:`, data.logs.slice(0, 3).map(log => log.service));
        logData = data.logs;
      } else {
        // Get logs from all devices
        switch (filter) {
          case 'errors':
            logData = await ApiService.fetchErrorLogs(24, 20);
            break;
          case 'recent':
            logData = await ApiService.fetchRecentLogs(30, 20);
            break;
          default:
            logData = await ApiService.fetchLogs({ size: 20 });
        }
      }
      
      setLogs(logData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch logs');
    } finally {
      setLoading(false);
    }
  }, [filter, focusedNodeId]);

  useEffect(() => {
    fetchLogs();
  }, [filter, focusedNodeId]);

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR': return 'text-red-500';
      case 'WARN': return 'text-yellow-500';
      case 'INFO': return 'text-blue-500';
      default: return 'text-gray-500';
    }
  };


  return (
    <div className={`rounded-lg border ${
      theme === 'light' 
        ? 'bg-white border-gray-200' 
        : 'bg-gray-900 border-gray-700'
    } ${className}`}>
      {/* Header */}
      <div className={`p-4 border-b ${
        theme === 'light' ? 'border-gray-200' : 'border-gray-700'
      }`}>
        <div className="flex items-center justify-between mb-3">
          <h3 className={`font-semibold flex items-center gap-2 ${
            theme === 'light' ? 'text-gray-900' : 'text-white'
          }`}>
            <FileText className="w-5 h-5" />
            {focusedNodeId ? `${focusedNodeId} Logs` : 'System Logs'}
          </h3>
          <button
            onClick={fetchLogs}
            disabled={loading}
            className={`p-2 rounded-lg transition-colors disabled:opacity-50 ${
              theme === 'light'
                ? 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                : 'text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Filter Tabs */}
        <div className={`flex space-x-1 rounded-lg p-1 ${
          theme === 'light' ? 'bg-gray-100' : 'bg-gray-800'
        }`}>
          {[
            { id: 'recent', label: 'Recent', count: logs.length },
            { id: 'errors', label: 'Errors', count: logs.filter(log => ['ERROR', 'WARN'].includes(log.level)).length },
            { id: 'all', label: 'All', count: logs.length }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id as 'all' | 'errors' | 'recent')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                filter === tab.id
                  ? 'bg-blue-600 text-white'
                  : theme === 'light'
                  ? 'text-gray-600 hover:text-gray-900 hover:bg-gray-200'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className={`ml-1 text-xs px-1 rounded ${
                  theme === 'light' ? 'bg-gray-300' : 'bg-gray-600'
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Log Entries - Compact Layout */}
      <div className="max-h-80 overflow-y-auto overflow-x-auto">
        {error && (
          <div className={`px-2 py-1 text-xs ${
            theme === 'light' 
              ? 'text-red-600 bg-red-50 border-b border-red-100' 
              : 'text-red-400 bg-red-900/20'
          }`}>
            Error: {error}
          </div>
        )}

        {loading ? (
          <div className={`p-4 text-center text-sm ${
            theme === 'light' ? 'text-gray-600' : 'text-gray-400'
          }`}>
            <RefreshCw className="w-4 h-4 animate-spin mx-auto mb-2" />
            Loading logs...
          </div>
        ) : logs.length === 0 ? (
          <div className={`p-4 text-center text-sm ${
            theme === 'light' ? 'text-gray-600' : 'text-gray-400'
          }`}>
            <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No logs found</p>
            <p className="text-xs">
              {filter === 'errors' ? 'No errors or warnings' : 'No recent activity'}
            </p>
          </div>
        ) : (
          <div className="font-mono text-xs">
            {logs.slice(0, 20).map((log) => (
              <div 
                key={log.id} 
                className={`px-2 py-0.5 whitespace-nowrap border-b ${
                  theme === 'light'
                    ? 'hover:bg-gray-50 border-gray-200'
                    : 'hover:bg-gray-800/50 border-gray-700'
                }`}
                style={{ minWidth: 'max-content' }}
              >
                <span className={`mr-2 ${
                  theme === 'light' ? 'text-gray-500' : 'text-gray-500'
                }`}>
                  {formatTimestamp(log.timestamp)}
                </span>
                <span className={`mr-2 ${getLevelColor(log.level)}`}>
                  [{log.level}]
                </span>
                <span className="text-blue-400 mr-2">
                  {log.service}:
                </span>
                <span className={theme === 'light' ? 'text-gray-900' : 'text-gray-300'}>
                  {log.message}
                </span>
                {log.metadata.filename && typeof log.metadata.filename === 'string' && (
                  <span className={`ml-2 ${
                    theme === 'light' ? 'text-gray-500' : 'text-gray-600'
                  }`}>
                    ({String(log.metadata.filename)})
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {logs.length > 10 && (
        <div className={`p-3 border-t text-center ${
          theme === 'light' ? 'border-gray-200' : 'border-gray-700'
        }`}>
          <button className={`text-sm flex items-center gap-1 mx-auto transition-colors ${
            theme === 'light'
              ? 'text-blue-600 hover:text-blue-800'
              : 'text-blue-400 hover:text-blue-300'
          }`}>
            <Search className="w-4 h-4" />
            View all {logs.length} logs
          </button>
        </div>
      )}
    </div>
  );
};

export default LogsPanel; 