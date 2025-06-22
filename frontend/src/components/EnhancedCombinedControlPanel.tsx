import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { SimpleLiquidGlass } from './SimpleLiquidGlass/SimpleLiquidGlass';
import { useTheme } from '../contexts/ThemeContext';
import { useDataMode } from '../contexts/DataModeContext';
import LogsPanel from './LogsPanel';
import { 
  Settings, 
  MessageSquare, 
  ChevronDown,
  ChevronUp,
  Network,
  Cog,
  Send,
  Loader2,
  X,
  Activity,
  Plus,
  StopCircle,
  Database,
  Wifi,
  Info,
  Layout,
  Search,
  RotateCcw,
  Zap,
  Terminal,
  Code,
  FileText,
  Play,
  Copy,
  Download
} from 'lucide-react';
import { NetworkNode, LayoutMode, FilterLayer } from '../types/network';
import { ApiService } from '../services/api';

interface ChatSession {
  id: string;
  name: string;
  messages: Message[];
  isActive: boolean;
  abortController?: AbortController;
}

interface EnhancedCombinedControlPanelProps {
  focusedNode: NetworkNode | null;
  onLayoutChange: (layout: LayoutMode) => void;
  onFilterChange: (layers: FilterLayer[]) => void;
  onResetView: () => void;
  activeLayers: FilterLayer[];
  currentLayout: LayoutMode;
  onOpenSettings: () => void;
  networkStats: {
    totalNodes: number;
    active: number;
    issues: number;
  };
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'tool' | 'thinking' | 'ssh' | 'code' | 'markdown';
  content: string;
  toolCalls?: Array<{
    id: string;
    name: string;
    args: Record<string, unknown>;
    result?: Record<string, unknown>;
  }>;
  tool_name?: string;
  tool_args?: Record<string, unknown>;
  thinking?: string;
  timestamp: Date;
  // Rich content types
  contentType?: 'text' | 'markdown' | 'code' | 'ssh_session' | 'ansible_playbook';
  language?: string; // For code syntax highlighting
  ssh_session?: {
    host: string;
    status: 'connecting' | 'connected' | 'disconnected' | 'error';
    output: string[];
    current_command?: string;
  };
  metadata?: Record<string, unknown>;
}

export const EnhancedCombinedControlPanel: React.FC<EnhancedCombinedControlPanelProps> = ({
  focusedNode,
  onLayoutChange,
  onFilterChange,
  onResetView,
  activeLayers,
  currentLayout,
  onOpenSettings,
  networkStats
}) => {
  const { theme } = useTheme();
  const { setDataMode, isUsingFakeData } = useDataMode();

  // Rich content renderer component
  const RichContentRenderer: React.FC<{ message: Message }> = ({ message }) => {
    const syntaxTheme = theme === 'light' ? vs : vscDarkPlus;
    
    // Handle SSH session display
    if (message.contentType === 'ssh_session' && message.ssh_session) {
      const { host, status, output, current_command } = message.ssh_session;
      const statusColors = {
        connecting: 'text-yellow-400',
        connected: 'text-green-400',
        disconnected: 'text-gray-400',
        error: 'text-red-400'
      };
      
      return (
        <div className={`border rounded-lg p-4 ${theme === 'light' ? 'bg-gray-50 border-gray-300' : 'bg-gray-800 border-gray-600'}`}>
          <div className="flex items-center gap-2 mb-3">
            <Terminal className="w-4 h-4" />
            <span className="font-mono text-sm">{host}</span>
            <div className={`flex items-center gap-1 ${statusColors[status]}`}>
              <div className={`w-2 h-2 rounded-full ${status === 'connected' ? 'bg-green-400' : status === 'connecting' ? 'bg-yellow-400 animate-pulse' : status === 'error' ? 'bg-red-400' : 'bg-gray-400'}`} />
              <span className="text-xs uppercase">{status}</span>
            </div>
          </div>
          
          <div className={`font-mono text-sm max-h-64 overflow-y-auto ${theme === 'light' ? 'bg-white text-gray-800' : 'bg-black text-green-400'} p-3 rounded border`}>
            {output.map((line, idx) => (
              <div key={idx} className="whitespace-pre-wrap">{line}</div>
            ))}
            {current_command && (
              <div className="flex items-center gap-1 mt-2">
                <span className="text-blue-400">$</span>
                <span className="text-blue-400">{current_command}</span>
                <div className="w-2 h-4 bg-blue-400 animate-pulse ml-1" />
              </div>
            )}
          </div>
          
          <div className="flex gap-2 mt-3">
            <button className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${theme === 'light' ? 'bg-gray-200 hover:bg-gray-300' : 'bg-gray-700 hover:bg-gray-600'}`}>
              <Copy className="w-3 h-3" />
              Copy
            </button>
            <button className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${theme === 'light' ? 'bg-gray-200 hover:bg-gray-300' : 'bg-gray-700 hover:bg-gray-600'}`}>
              <Download className="w-3 h-3" />
              Export
            </button>
          </div>
        </div>
      );
    }
    
    // Handle code blocks (including Ansible playbooks)
    if (message.contentType === 'code' || message.contentType === 'ansible_playbook') {
      const language = message.language || (message.contentType === 'ansible_playbook' ? 'yaml' : 'text');
      const isPlaybook = message.contentType === 'ansible_playbook';
      
      return (
        <div className={`border rounded-lg overflow-hidden ${theme === 'light' ? 'border-gray-300' : 'border-gray-600'}`}>
          <div className={`flex items-center justify-between px-4 py-2 ${theme === 'light' ? 'bg-gray-100' : 'bg-gray-700'}`}>
            <div className="flex items-center gap-2">
              {isPlaybook ? <Play className="w-4 h-4" /> : <Code className="w-4 h-4" />}
              <span className="text-sm font-medium">
                {isPlaybook ? 'Ansible Playbook' : 'Code Block'}
                {language && ` (${language})`}
              </span>
            </div>
            <div className="flex gap-2">
              <button className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${theme === 'light' ? 'bg-gray-200 hover:bg-gray-300' : 'bg-gray-600 hover:bg-gray-500'}`}>
                <Copy className="w-3 h-3" />
                Copy
              </button>
              {isPlaybook && (
                <button className={`flex items-center gap-1 px-2 py-1 rounded text-xs bg-blue-600 hover:bg-blue-500 text-white`}>
                  <Play className="w-3 h-3" />
                  Run
                </button>
              )}
            </div>
          </div>
          
          <SyntaxHighlighter
            language={language}
            style={syntaxTheme as { [key: string]: React.CSSProperties }}
            wrapLongLines
          >
            {message.content}
          </SyntaxHighlighter>
        </div>
      );
    }
    
    // Handle markdown content
    if (message.contentType === 'markdown') {
      return (
        <div className={`border rounded-lg p-4 ${theme === 'light' ? 'bg-gray-50 border-gray-300' : 'bg-gray-800 border-gray-600'}`}>
          <div className={`flex items-center gap-2 mb-3 ${theme === 'light' ? 'text-gray-600' : 'text-gray-300'}`}>
            <FileText className="w-4 h-4" />
            <span className="text-sm font-medium">Markdown Document</span>
          </div>
          
          <div className={`prose ${theme === 'light' ? '' : 'prose-invert'} max-w-none`}>
            <ReactMarkdown
              components={{
                code: ({ className, children, ...props }) => {
                  const match = /language-(\w+)/.exec(className || '');
                  const language = match ? match[1] : '';
                  
                  if (language) {
                    return (
                      <SyntaxHighlighter
                        language={language}
                        style={syntaxTheme as { [key: string]: React.CSSProperties }}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    );
                  }
                  
                  return (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                }
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        </div>
      );
    }
    
    // Default text content
    return <div className="whitespace-pre-wrap">{message.content}</div>;
  };

  const [activeTab, setActiveTab] = useState<'overview' | 'controls' | 'logs' | 'info' | 'chat'>('controls');
  const [isExpanded, setIsExpanded] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Chat sessions state
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([
    {
      id: 'session-1',
      name: 'General Chat',
      messages: [
        {
          id: '1',
          role: 'assistant',
          content: focusedNode 
            ? `I'm here to help you with ${focusedNode.label}. I can check its status, run SSH commands, or create Ansible playbooks.`
            : "Hello! I'm your network infrastructure assistant. I can help you monitor devices, run SSH commands, and create Ansible playbooks.",
          timestamp: new Date()
        }
      ],
      isActive: false
    }
  ]);
  
  const [activeChatSession, setActiveChatSession] = useState<string>('session-1');
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatSessions]);

  // Load chat history when component mounts or active session changes
  useEffect(() => {
    if (activeChatSession) {
      loadChatHistory(activeChatSession);
    }
  }, [activeChatSession]);

  // Load available sessions on component mount
  useEffect(() => {
    const loadExistingSessions = async () => {
      try {
        // For now, we'll just ensure the default session has proper history
        // In a real app, you might want to load a list of all sessions
        if (chatSessions.length === 1 && chatSessions[0].messages.length === 1) {
          await loadChatHistory(chatSessions[0].id);
        }
      } catch (error) {
        console.error('Failed to load existing sessions:', error);
      }
    };

    loadExistingSessions();
  }, []); // Only run on mount

  const getCurrentSession = () => {
    return chatSessions.find(session => session.id === activeChatSession);
  };

  // Load chat history from backend
  const loadChatHistory = async (sessionId: string) => {
    try {
      const response = await fetch(`http://localhost:3001/chats/${sessionId}`);
      if (response.ok) {
        const history = await response.json();
        
        // Convert backend format to frontend Message format
        const messages: Message[] = [];
        history.forEach((item: { message: string; response: string; timestamp: string }) => {
          // Add user message
          messages.push({
            id: `user-${Date.now()}-${Math.random()}`,
            role: 'user',
            content: item.message,
            timestamp: new Date(item.timestamp)
          });
          
          // Add assistant message
          messages.push({
            id: `assistant-${Date.now()}-${Math.random()}`,
            role: 'assistant',
            content: item.response,
            timestamp: new Date(item.timestamp)
          });
        });
        
        // Update the session with loaded messages
        setChatSessions(prev =>
          prev.map(session =>
            session.id === sessionId
              ? { ...session, messages }
              : session
          )
        );
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };

  // Placeholder for future message update functionality
  // const updateSessionMessages = (sessionId: string, newMessages: Message[]) => {
  //   setChatSessions(prev => 
  //     prev.map(session => 
  //       session.id === sessionId 
  //         ? { ...session, messages: newMessages }
  //         : session
  //     )
  //   );
  // };

  const stopCurrentWorkflow = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    
    const currentSession = getCurrentSession();
    if (currentSession?.abortController) {
      currentSession.abortController.abort();
      setChatSessions(prev => 
        prev.map(session => 
          session.id === activeChatSession 
            ? { ...session, isActive: false, abortController: undefined }
            : session
        )
      );
    }
    setIsLoading(false);
  };

    const handleChatSubmit = async (message: string) => {
    if (!message.trim() || isLoading) return;

    const currentSession = getCurrentSession();
    if (!currentSession) return;

    // Add user message immediately
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: message.trim(),
      timestamp: new Date()
    };

    setChatSessions(prev =>
      prev.map(session =>
        session.id === activeChatSession
          ? { ...session, messages: [...session.messages, userMessage] }
          : session
      )
    );

    setInputValue('');
    setIsLoading(true);

    // Create abort controller for this request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: '',
        timestamp: new Date()
      };

      // Add empty assistant message
      setChatSessions(prev =>
        prev.map(session =>
          session.id === activeChatSession
            ? { ...session, messages: [...session.messages, assistantMessage] }
            : session
        )
      );

      // Use the API service for streaming
      const chatRequest = {
        message: message.trim(),
        session_id: activeChatSession,
        context: focusedNode ? {
          focused_device: focusedNode.id,
          focused_node: {
            id: focusedNode.id,
            label: focusedNode.label,
            type: focusedNode.type,
            status: focusedNode.status,
            ip: focusedNode.ip
          }
        } : undefined
      };

             for await (const chunk of ApiService.streamChatMessage(chatRequest)) {
         if (abortController.signal.aborted) {
           break;
         }

         if (chunk.type === 'thinking' && chunk.thinking) {
           // Create a separate thinking message
           const thinkingMessage: Message = {
             id: `thinking-${Date.now()}`,
             role: 'thinking',
             content: chunk.thinking,
             timestamp: new Date()
           };

           setChatSessions(prev =>
             prev.map(session =>
               session.id === activeChatSession
                 ? { ...session, messages: [...session.messages, thinkingMessage] }
                 : session
             )
           );

         } else if (chunk.type === 'tool_call' && chunk.tool_name) {
           // Create a separate tool call message
           const toolCallMessage: Message = {
             id: `tool-call-${Date.now()}`,
             role: 'tool',
             content: chunk.thinking || `Using ${chunk.tool_name} tool...`,
             tool_name: chunk.tool_name,
             tool_args: chunk.tool_args,
             timestamp: new Date()
           };

           setChatSessions(prev =>
             prev.map(session =>
               session.id === activeChatSession
                 ? { ...session, messages: [...session.messages, toolCallMessage] }
                 : session
             )
           );

         } else if (chunk.type === 'tool_result' && chunk.content) {
           // Create a separate tool result message
           const toolResultMessage: Message = {
             id: `tool-result-${Date.now()}`,
             role: 'tool',
             content: chunk.content,
             timestamp: new Date()
           };

           setChatSessions(prev =>
             prev.map(session =>
               session.id === activeChatSession
                 ? { ...session, messages: [...session.messages, toolResultMessage] }
                 : session
             )
           );

         } else if (chunk.type === 'text' && chunk.content) {
           assistantMessage.content += chunk.content;
           
           // Update the assistant message
           setChatSessions(prev =>
             prev.map(session =>
               session.id === activeChatSession
                 ? {
                     ...session,
                     messages: session.messages.map(msg =>
                       msg.id === assistantMessage.id
                         ? { ...assistantMessage }
                         : msg
                     )
                   }
                 : session
             )
           );
         } else if (chunk.type === 'error') {
           throw new Error(chunk.error || 'Unknown error occurred');
         }
         // 'done' type is handled by the generator ending
       }

    } catch (error: unknown) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Chat request was aborted');
        return;
      }

      console.error('Chat error:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date()
      };

      setChatSessions(prev =>
        prev.map(session =>
          session.id === activeChatSession
            ? { ...session, messages: [...session.messages, errorMessage] }
            : session
        )
      );
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const createNewChatSession = () => {
    const newSessionId = `session-${Date.now()}`;
    const newSession: ChatSession = {
      id: newSessionId,
      name: `Chat ${chatSessions.length + 1}`,
      messages: [
        {
          id: '1',
          role: 'assistant',
          content: `Hello! I'm your network infrastructure assistant with **real-time access** to live network data. I can help you with:

🔍 **Log Analysis** (using live OpenSearch data):
• Get recent logs from any device
• Search for specific errors or patterns  
• Filter by log level (ERROR, WARN, INFO)

📊 **Device Monitoring** (using live MetricBeat data):
• Check device status and health metrics
• View CPU, memory, and system performance
• Get comprehensive device reports

🔧 **Network Automation**:
• Create and execute Ansible playbooks
• Run SSH commands on remote devices
• Automate network management tasks

💬 **I use real tools** - no simulated data! Try asking:
• "Get logs for switch2"
• "Show me device info for frr-router"  
• "Create an ansible playbook for nginx"
• "What are the recent errors?"

How can I help you today?`,
          timestamp: new Date()
        }
      ],
      isActive: false
    };
    
    setChatSessions(prev => [...prev, newSession]);
    setActiveChatSession(newSessionId);
  };

  const addDemoContent = (type: 'ssh' | 'ansible' | 'markdown' | 'code') => {
    const currentSession = getCurrentSession();
    if (!currentSession) return;

    let demoMessage: Message;

    switch (type) {
      case 'ssh':
        demoMessage = {
          id: `demo-ssh-${Date.now()}`,
          role: 'assistant',
          content: '',
          contentType: 'ssh_session',
          ssh_session: {
            host: '192.168.1.10',
            status: 'connected',
            output: [
              'Last login: Wed Dec 11 10:30:15 2024 from 192.168.1.100',
              'admin@router:~$ ps aux | grep nginx',
              'root      1234  0.1  0.5  12345  6789 ?        Ss   10:25   0:01 nginx: master process',
              'www-data  1235  0.0  0.3   8901  2345 ?        S    10:25   0:00 nginx: worker process',
              'admin@router:~$ systemctl status nginx',
              '● nginx.service - A high performance web server',
              '   Loaded: loaded (/lib/systemd/system/nginx.service; enabled)',
              '   Active: active (running) since Wed 2024-12-11 10:25:30 UTC; 5min ago',
              'admin@router:~$ '
            ],
            current_command: 'top'
          },
          timestamp: new Date()
        };
        break;

      case 'ansible':
        demoMessage = {
          id: `demo-ansible-${Date.now()}`,
          role: 'assistant',
          content: `---
- name: Install and configure Nginx
  hosts: webservers
  become: yes
  vars:
    nginx_port: 80
    server_name: example.com
    
  tasks:
    - name: Install Nginx
      package:
        name: nginx
        state: present
        
    - name: Start and enable Nginx
      systemd:
        name: nginx
        state: started
        enabled: yes
        
    - name: Create custom nginx config
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/sites-available/{{ server_name }}
        backup: yes
      notify: restart nginx
      
    - name: Enable site
      file:
        src: /etc/nginx/sites-available/{{ server_name }}
        dest: /etc/nginx/sites-enabled/{{ server_name }}
        state: link
      notify: restart nginx
        
  handlers:
    - name: restart nginx
      systemd:
        name: nginx
        state: restarted`,
          contentType: 'ansible_playbook',
          language: 'yaml',
          timestamp: new Date()
        };
        break;

      case 'markdown':
        demoMessage = {
          id: `demo-markdown-${Date.now()}`,
          role: 'assistant',
          content: `# Network Troubleshooting Guide

## Overview
This guide covers common network troubleshooting steps for enterprise environments.

## Quick Diagnostics

### 1. Connectivity Tests
\`\`\`bash
# Basic ping test
ping -c 4 8.8.8.8

# Trace route to destination
traceroute google.com

# Check DNS resolution
nslookup example.com
\`\`\`

### 2. Interface Status
\`\`\`bash
# Check interface status
ip link show

# View IP configuration
ip addr show

# Check routing table
ip route show
\`\`\`

## Common Issues

| Issue | Symptoms | Solution |
|-------|----------|----------|
| DNS Resolution | Can ping IPs but not domains | Check \`/etc/resolv.conf\` |
| Slow Connection | High latency, packet loss | Check bandwidth usage |
| No Internet | Local network OK, no external access | Check default gateway |

> **Note**: Always check physical connections first before diving into software troubleshooting.`,
          contentType: 'markdown',
          timestamp: new Date()
        };
        break;

      case 'code':
        demoMessage = {
          id: `demo-code-${Date.now()}`,
          role: 'assistant',
          content: `#!/usr/bin/env python3
"""
Network Device Monitor
Monitors network devices and sends alerts for issues.
"""

import subprocess
import time
from datetime import datetime

class NetworkMonitor:
    def __init__(self, devices):
        self.devices = devices
        self.failed_devices = set()
        
    def ping_device(self, ip):
        """Ping a device and return True if reachable"""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '1', ip],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error pinging {ip}: {e}")
            return False
            
    def monitor_loop(self, interval=60):
        """Main monitoring loop"""
        print("Starting network monitoring...")
        
        while True:
            for device in self.devices:
                if self.ping_device(device):
                    if device in self.failed_devices:
                        print(f"✅ {device} is back online")
                        self.failed_devices.remove(device)
                else:
                    if device not in self.failed_devices:
                        print(f"❌ {device} is unreachable")
                        self.failed_devices.add(device)
                        
            time.sleep(interval)

if __name__ == "__main__":
    devices = ["192.168.1.1", "192.168.1.10", "8.8.8.8"]
    monitor = NetworkMonitor(devices)
    monitor.monitor_loop(interval=30)`,
          contentType: 'code',
          language: 'python',
          timestamp: new Date()
        };
        break;
    }

    setChatSessions(prev =>
      prev.map(session =>
        session.id === activeChatSession
          ? { ...session, messages: [...session.messages, demoMessage] }
          : session
      )
    );
  };

  const deleteChatSession = (sessionId: string) => {
    if (chatSessions.length <= 1) return; // Don't delete the last session
    
    setChatSessions(prev => prev.filter(session => session.id !== sessionId));
    
    if (activeChatSession === sessionId) {
      setActiveChatSession(chatSessions[0].id);
    }
  };

  const switchChatSession = (sessionId: string) => {
    // Stop current workflow if switching sessions
    stopCurrentWorkflow();
    setActiveChatSession(sessionId);
    // History will be loaded by the useEffect hook
  };

  // Layout and layer configurations
  const layouts: { key: LayoutMode; label: string; icon: React.ReactNode }[] = [
    { key: 'force', label: 'Force Directed', icon: <Zap className="w-4 h-4" /> },
    { key: 'hierarchical', label: 'Vertical', icon: <Layout className="w-4 h-4" /> },
    { key: 'hierarchical-horizontal', label: 'Horizontal', icon: <Layout className="w-4 h-4 rotate-90" /> },
    { key: 'circular', label: 'Circular', icon: <RotateCcw className="w-4 h-4" /> },
    { key: 'grid', label: 'Grid', icon: <Settings className="w-4 h-4" /> }
  ];


  const tabs = [
    { key: 'overview' as const, label: 'Overview', icon: Activity },
    { key: 'controls' as const, label: 'Controls', icon: Settings },
    { key: 'logs' as const, label: 'Logs', icon: FileText },
    { key: 'info' as const, label: 'Node Info', icon: Info, disabled: !focusedNode },
    { key: 'chat' as const, label: 'AI Assistant', icon: MessageSquare }
  ];

  const currentSession = getCurrentSession();

  // Determine panel size based on active tab
  const isAIChatActive = activeTab === 'chat';
  const isLogsActive = activeTab === 'logs';
  const panelWidth = isAIChatActive ? 'w-[500px]' : isLogsActive ? 'w-[600px]' : 'w-80';
  const maxHeight = isAIChatActive ? 'max-h-[90vh]' : isLogsActive ? 'max-h-[70vh]' : 'max-h-[80vh]';

  // Regular panel with expandable AI chat
  return (
    <SimpleLiquidGlass
      padding="0"
      textColor={theme === 'light' ? '#1f2937' : 'white'}
    >
      <div className={`${panelWidth} bg-transparent ${maxHeight} flex flex-col transition-all duration-300`}>
        {/* Header */}
        <div className={`flex items-center justify-between p-3 border-b ${theme === 'light' ? 'border-gray-200' : 'border-white/10'}`}>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Network className="w-3 h-3 text-white" />
            </div>
            <div>
              <h2 className={`font-semibold text-xs ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>Network Control</h2>
              <p className={`text-xs ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`}>
                {focusedNode ? `Focused: ${focusedNode.label}` : 'Network Overview'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setDataMode(isUsingFakeData ? 'realtime' : 'fake')}
              className={`p-1 rounded-lg transition-colors ${theme === 'light' ? 'hover:bg-gray-100' : 'hover:bg-white/10'}`}
              title={isUsingFakeData ? 'Switch to Real-time Data' : 'Switch to Fake Data (BAU)'}
            >
              {isUsingFakeData ? (
                <Wifi className={`w-3 h-3 ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`} />
              ) : (
                <Database className={`w-3 h-3 ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`} />
              )}
            </button>
            <button
              onClick={onOpenSettings}
              className={`p-1 rounded-lg transition-colors ${theme === 'light' ? 'hover:bg-gray-100' : 'hover:bg-white/10'}`}
              title="Settings"
            >
              <Cog className={`w-3 h-3 ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`} />
            </button>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className={`p-1 rounded-lg transition-colors ${theme === 'light' ? 'hover:bg-gray-100' : 'hover:bg-white/10'}`}
            >
              {isExpanded ? (
                <ChevronUp className={`w-3 h-3 ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`} />
              ) : (
                <ChevronDown className={`w-3 h-3 ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`} />
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
                    className={`flex-1 flex items-center justify-center gap-1 px-2 py-2 text-xs font-medium transition-colors ${
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
            <div className="flex-1 overflow-hidden">
              {activeTab === 'overview' && (
                <div className="p-3 space-y-3">
                  <div className={`p-3 rounded-lg border ${
                    theme === 'light' ? 'bg-gray-50 border-gray-200' : 'bg-gray-800/50 border-white/10'
                  }`}>
                    <h3 className={`text-sm font-medium mb-2 ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>
                      Data Source
                    </h3>
                    <div className="flex items-center gap-2">
                      {isUsingFakeData ? (
                        <Database className="w-4 h-4 text-blue-500" />
                      ) : (
                        <Wifi className="w-4 h-4 text-green-500" />
                      )}
                      <span className={`text-sm ${theme === 'light' ? 'text-gray-700' : 'text-gray-300'}`}>
                        {isUsingFakeData ? 'Fake Data (BAU Testing)' : 'Real-time Data'}
                      </span>
                    </div>
                    <p className={`text-xs mt-1 ${theme === 'light' ? 'text-gray-500' : 'text-gray-400'}`}>
                      {isUsingFakeData 
                        ? 'Using mock network data for business-as-usual testing'
                        : 'Connected to live network infrastructure'
                      }
                    </p>
                  </div>

                  {/* Network Stats */}
                  <div className={`p-3 rounded-lg border ${
                    theme === 'light' ? 'bg-gray-50 border-gray-200' : 'bg-gray-800/50 border-white/10'
                  }`}>
                    <h3 className={`text-sm font-medium mb-2 ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>
                      Network Statistics
                    </h3>
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div>
                        <div className={`text-lg font-bold ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>
                          {networkStats.totalNodes}
                        </div>
                        <div className={`text-xs ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`}>
                          Total Nodes
                        </div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-green-500">
                          {networkStats.active}
                        </div>
                        <div className={`text-xs ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`}>
                          Active
                        </div>
                      </div>
                      <div>
                        <div className="text-lg font-bold text-red-500">
                          {networkStats.issues}
                        </div>
                        <div className={`text-xs ${theme === 'light' ? 'text-gray-600' : 'text-gray-400'}`}>
                          Issues
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'logs' && (
                <div className="h-96 overflow-hidden">
                  <LogsPanel 
                    className="h-full border-0 bg-transparent" 
                    focusedNodeId={focusedNode?.id}
                  />
                </div>
              )}

              {activeTab === 'controls' && (
                <div className="p-3 space-y-4 max-h-96 overflow-y-auto">
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
                <div className="p-3 space-y-3">
                  <div className={`p-3 rounded-lg border ${
                    theme === 'light' ? 'bg-gray-50 border-gray-200' : 'bg-gray-800/50 border-white/10'
                  }`}>
                    <h3 className={`text-sm font-medium mb-2 ${theme === 'light' ? 'text-gray-900' : 'text-white'}`}>
                      {focusedNode.label}
                    </h3>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className={theme === 'light' ? 'text-gray-600' : 'text-gray-400'}>Type:</span>
                        <span className={theme === 'light' ? 'text-gray-900' : 'text-white'}>{focusedNode.type}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className={theme === 'light' ? 'text-gray-600' : 'text-gray-400'}>Status:</span>
                        <span className={`font-medium ${
                          focusedNode.status === 'online' ? 'text-green-500' :
                          focusedNode.status === 'warning' ? 'text-yellow-500' :
                          focusedNode.status === 'error' ? 'text-red-500' : 'text-gray-500'
                        }`}>{focusedNode.status}</span>
                      </div>
                      {focusedNode.ip && (
                        <div className="flex justify-between">
                          <span className={theme === 'light' ? 'text-gray-600' : 'text-gray-400'}>IP:</span>
                          <span className={theme === 'light' ? 'text-gray-900' : 'text-white'}>{focusedNode.ip}</span>
                        </div>
                      )}
                      <div className="flex justify-between">
                        <span className={theme === 'light' ? 'text-gray-600' : 'text-gray-400'}>Layer:</span>
                        <span className={theme === 'light' ? 'text-gray-900' : 'text-white'}>{focusedNode.layer}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'chat' && (
                <div className="flex flex-col h-[70vh] min-h-[500px]">
                  {/* Chat Sessions Tabs */}
                  <div className={`flex overflow-x-auto border-b ${theme === 'light' ? 'border-gray-200' : 'border-white/10'} p-2`}>
                    {chatSessions.map(session => (
                      <div key={session.id} className="flex items-center min-w-0">
                        <button
                          onClick={() => switchChatSession(session.id)}
                          className={`flex items-center gap-1 px-2 py-1 text-xs font-medium transition-colors border-r ${
                            activeChatSession === session.id
                              ? 'text-blue-400 bg-blue-500/20 border-b-2 border-blue-500'
                              : `${theme === 'light' ? 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 border-gray-200' : 'text-gray-400 hover:text-white hover:bg-white/5 border-white/10'}`
                          }`}
                        >
                          {session.isActive && <Loader2 className="w-2 h-2 animate-spin" />}
                          <span className="truncate max-w-20">{session.name}</span>
                        </button>
                        {chatSessions.length > 1 && (
                          <button
                            onClick={() => deleteChatSession(session.id)}
                            className={`p-1 hover:bg-red-500/20 transition-colors ${theme === 'light' ? 'text-gray-400 hover:text-red-600' : 'text-gray-500 hover:text-red-400'}`}
                          >
                            <X className="w-2 h-2" />
                          </button>
                        )}
                      </div>
                    ))}
                    <button
                      onClick={createNewChatSession}
                      className={`flex items-center justify-center w-6 h-6 m-1 rounded transition-colors ${theme === 'light' ? 'hover:bg-gray-100' : 'hover:bg-white/10'}`}
                      title="New Chat"
                    >
                      <Plus className="w-3 h-3" />
                    </button>
                  </div>

                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto p-3 space-y-2">
                    {currentSession?.messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div className={`max-w-[90%] ${message.role === 'assistant' ? 'space-y-1' : ''}`}>
                          {message.content && (
                            <div
                              className={`p-2 rounded-lg text-xs ${
                                message.role === 'user'
                                  ? theme === 'light'
                                    ? 'bg-blue-500 text-white'
                                    : 'bg-blue-600/30 text-blue-100'
                                  : message.role === 'thinking'
                                  ? theme === 'light'
                                    ? 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                                    : 'bg-yellow-900/30 text-yellow-200 border border-yellow-600/30'
                                  : message.role === 'tool'
                                  ? theme === 'light'
                                    ? 'bg-purple-100 text-purple-800 border border-purple-300'
                                    : 'bg-purple-900/30 text-purple-200 border border-purple-600/30'
                                  : theme === 'light'
                                  ? 'bg-gray-200 text-gray-800'
                                  : 'bg-gray-700/50 text-gray-100'
                              }`}
                            >
                              {/* Tool call header */}
                              {message.role === 'tool' && message.tool_name && (
                                <div className={`flex items-center gap-2 mb-1 pb-1 border-b ${
                                  theme === 'light' ? 'border-purple-200' : 'border-purple-600/30'
                                }`}>
                                  <Settings className="w-3 h-3" />
                                  <span className="font-medium">{message.tool_name}</span>
                                  {message.tool_args && (
                                    <span className={`text-xs ${
                                      theme === 'light' ? 'text-purple-600' : 'text-purple-300'
                                    }`}>
                                      ({Object.keys(message.tool_args).join(', ')})
                                    </span>
                                  )}
                                </div>
                              )}
                              
                              {/* Thinking indicator */}
                              {message.role === 'thinking' && (
                                <div className={`flex items-center gap-2 mb-1 ${
                                  theme === 'light' ? 'text-yellow-700' : 'text-yellow-300'
                                }`}>
                                  <Loader2 className="w-3 h-3 animate-spin" />
                                  <span className="font-medium">Thinking...</span>
                                </div>
                              )}
                              
                              <RichContentRenderer message={message} />
                              
                              {/* Tool arguments display */}
                              {message.role === 'tool' && message.tool_args && (
                                <div className={`mt-2 pt-2 border-t text-xs ${
                                  theme === 'light' ? 'border-purple-200 text-purple-600' : 'border-purple-600/30 text-purple-300'
                                }`}>
                                  <strong>Arguments:</strong>
                                  <pre className="mt-1 text-xs overflow-x-auto">
                                    {JSON.stringify(message.tool_args, null, 2)}
                                  </pre>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                    {isLoading && (
                      <div className="flex justify-start">
                        <div className={`p-2 rounded-lg ${
                          theme === 'light' ? 'bg-gray-200' : 'bg-gray-700/50'
                        }`}>
                          <Loader2 className="w-3 h-3 animate-spin text-blue-400" />
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Demo buttons */}
                  <div className={`p-2 border-t ${theme === 'light' ? 'border-gray-200' : 'border-white/10'}`}>
                    <div className="text-xs mb-2 text-center opacity-75">Rich Content Demos:</div>
                    <div className="grid grid-cols-4 gap-1">
                      <button
                        onClick={() => addDemoContent('ssh')}
                        className={`flex items-center justify-center p-1 rounded text-xs ${theme === 'light' ? 'bg-gray-100 hover:bg-gray-200' : 'bg-gray-700 hover:bg-gray-600'}`}
                        title="SSH Session Demo"
                      >
                        <Terminal className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => addDemoContent('ansible')}
                        className={`flex items-center justify-center p-1 rounded text-xs ${theme === 'light' ? 'bg-gray-100 hover:bg-gray-200' : 'bg-gray-700 hover:bg-gray-600'}`}
                        title="Ansible Playbook Demo"
                      >
                        <Play className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => addDemoContent('markdown')}
                        className={`flex items-center justify-center p-1 rounded text-xs ${theme === 'light' ? 'bg-gray-100 hover:bg-gray-200' : 'bg-gray-700 hover:bg-gray-600'}`}
                        title="Markdown Documentation Demo"
                      >
                        <FileText className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => addDemoContent('code')}
                        className={`flex items-center justify-center p-1 rounded text-xs ${theme === 'light' ? 'bg-gray-100 hover:bg-gray-200' : 'bg-gray-700 hover:bg-gray-600'}`}
                        title="Python Code Demo"
                      >
                        <Code className="w-3 h-3" />
                      </button>
                    </div>
                  </div>

                  {/* Input */}
                  <div className={`p-3 border-t ${
                    theme === 'light' ? 'border-gray-200' : 'border-white/10'
                  }`}>
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        if (isLoading) {
                          stopCurrentWorkflow();
                        } else {
                          handleChatSubmit(inputValue);
                        }
                      }}
                      className="flex gap-1"
                    >
                      <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder={focusedNode ? `Ask about ${focusedNode.label}...` : 'Ask about the network...'}
                        className={`flex-1 px-2 py-1 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 ${
                          theme === 'light'
                            ? 'bg-gray-100 text-gray-900 placeholder-gray-500'
                            : 'bg-gray-800/50 text-white placeholder-gray-400'
                        }`}
                        disabled={isLoading}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            if (isLoading) {
                              stopCurrentWorkflow();
                            } else {
                              handleChatSubmit(inputValue);
                            }
                          }
                        }}
                      />
                      <button
                        type="submit"
                        disabled={!inputValue.trim() && !isLoading}
                        className={`px-2 py-1 rounded transition-all text-xs ${
                          isLoading
                            ? 'bg-red-500 hover:bg-red-600 text-white'
                            : theme === 'light'
                            ? 'bg-blue-500 hover:bg-blue-600 text-white disabled:bg-gray-300'
                            : 'bg-blue-600/40 hover:bg-blue-600/60 text-white disabled:bg-gray-700/50'
                        }`}
                      >
                        {isLoading ? (
                          <StopCircle className="w-3 h-3" />
                        ) : (
                          <Send className="w-3 h-3" />
                        )}
                      </button>
                    </form>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </SimpleLiquidGlass>
  );
};
