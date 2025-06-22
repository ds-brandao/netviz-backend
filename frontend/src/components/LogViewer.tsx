import React, { useState, useEffect } from 'react';
import { ApiService, LogEntry, LogStats } from '../services/api';

interface LogViewerProps {
  nodeId?: string;
  className?: string;
}

const LogViewer: React.FC<LogViewerProps> = ({ nodeId, className = '' }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [stats, setStats] = useState<LogStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState({
    level: '',
    timeRange: '1h',
    size: 50,
    search: ''
  });

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let logData: LogEntry[];
      
      if (nodeId) {
        // Fetch logs for specific node
        const hours = filter.timeRange === '1h' ? 1 : 
                     filter.timeRange === '6h' ? 6 :
                     filter.timeRange === '24h' ? 24 : 1;
        logData = await ApiService.fetchNodeLogs(nodeId, hours, filter.size);
      } else {
        // Fetch general logs with filters
        const params: {
          size: number;
          time_range: string;
          level?: string;
          search?: string;
        } = {
          size: filter.size,
          time_range: filter.timeRange
        };
        
        if (filter.level) {
          params.level = filter.level;
        }
        
        if (filter.search) {
          params.search = filter.search;
        }
        
        logData = await ApiService.fetchLogs(params);
      }
      
      setLogs(logData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch logs');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const statsData = await ApiService.fetchLogStats();
      setStats(statsData);
    } catch (err) {
      console.error('Failed to fetch log stats:', err);
    }
  };

  useEffect(() => {
    fetchLogs();
    fetchStats();
  }, [nodeId, filter]);

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR': return 'text-red-600 bg-red-50';
      case 'WARN': return 'text-yellow-600 bg-yellow-50';
      case 'INFO': return 'text-blue-600 bg-blue-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };


  return (
    <div className={`bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {nodeId ? `Logs for ${nodeId}` : 'System Logs'}
          </h3>
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {/* Stats */}
        {stats && (
          <div className="flex space-x-4 text-sm text-gray-600 mb-4">
            <span>Total: {stats.total_logs}</span>
            {Object.entries(stats.level_counts).map(([level, count]) => (
              <span key={level} className={getLevelColor(level).split(' ')[0]}>
                {level}: {count}
              </span>
            ))}
            <span className={stats.opensearch_available ? 'text-green-600' : 'text-red-600'}>
              OpenSearch: {stats.opensearch_available ? 'Available' : 'Unavailable'}
            </span>
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-wrap gap-2">
          <select
            value={filter.level}
            onChange={(e) => setFilter(prev => ({ ...prev, level: e.target.value }))}
            className="px-2 py-1 border border-gray-300 rounded text-sm"
          >
            <option value="">All Levels</option>
            <option value="ERROR">ERROR</option>
            <option value="WARN">WARN</option>
            <option value="INFO">INFO</option>
          </select>

          <select
            value={filter.timeRange}
            onChange={(e) => setFilter(prev => ({ ...prev, timeRange: e.target.value }))}
            className="px-2 py-1 border border-gray-300 rounded text-sm"
          >
            <option value="1h">Last Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
          </select>

          <select
            value={filter.size}
            onChange={(e) => setFilter(prev => ({ ...prev, size: parseInt(e.target.value) }))}
            className="px-2 py-1 border border-gray-300 rounded text-sm"
          >
            <option value="25">25 logs</option>
            <option value="50">50 logs</option>
            <option value="100">100 logs</option>
            <option value="200">200 logs</option>
          </select>

          <input
            type="text"
            placeholder="Search logs..."
            value={filter.search}
            onChange={(e) => setFilter(prev => ({ ...prev, search: e.target.value }))}
            className="px-2 py-1 border border-gray-300 rounded text-sm flex-1 min-w-0"
          />
        </div>
      </div>

      {/* Log Entries - Compact Layout */}
      <div className="max-h-96 overflow-y-auto">
        {error && (
          <div className="px-2 py-1 text-red-600 bg-red-50 text-xs">
            Error: {error}
          </div>
        )}

        {loading ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            Loading logs...
          </div>
        ) : logs.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            No logs found for the selected criteria.
          </div>
        ) : (
          <div className="font-mono text-xs overflow-x-auto">
            {logs.map((log) => (
              <div 
                key={log.id} 
                className="px-2 py-0.5 hover:bg-gray-50 whitespace-nowrap border-b border-gray-100"
                style={{ minWidth: 'max-content' }}
              >
                <span className="text-gray-500 mr-2">
                  {formatTimestamp(log.timestamp)}
                </span>
                <span className={`mr-2 ${getLevelColor(log.level).split(' ')[0]}`}>
                  [{log.level}]
                </span>
                <span className="text-blue-600 mr-2">
                  {log.service}:
                </span>
                <span className="text-gray-900">
                  {log.message}
                </span>
                {log.metadata.filename && typeof log.metadata.filename === 'string' && (
                  <span className="text-gray-400 ml-2">
                    ({log.metadata.filename})
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LogViewer; 