import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Terminal, FileCode, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { NetworkNode } from '../types/network';
import { ApiService } from '../services/api';
import { SimpleLiquidGlass } from './SimpleLiquidGlass/SimpleLiquidGlass';
import { useTheme } from '../contexts/ThemeContext';

interface ChatPanelProps {
  focusedNode?: NetworkNode;
  onClose?: () => void;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: Array<{
    id: string;
    name: string;
    args: Record<string, unknown>;
    result?: Record<string, unknown>;
  }>;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  focusedNode,
  onClose,
}) => {
  const { theme } = useTheme();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: focusedNode 
        ? `I'm here to help you with ${focusedNode.label}. I can check its status, run SSH commands, or create Ansible playbooks.`
        : "Hello! I'm your network infrastructure assistant. I can help you monitor devices, run SSH commands, and create Ansible playbooks.",
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    const assistantId = (Date.now() + 1).toString();
    const assistantMessage: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      toolCalls: [],
    };

    setMessages(prev => [...prev, assistantMessage]);

    // Create abort controller
    abortControllerRef.current = new AbortController();

    try {
      for await (const chunk of ApiService.streamChatMessage({
        message: userMessage.content,
        session_id: 'default',
        context: {
          focused_node: focusedNode,
        },
      })) {
        console.log('🔍 Received chunk:', chunk); // DEBUG: Log all chunks
        
        if (chunk.type === 'text') {
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantId
                ? { ...m, content: m.content + chunk.content }
                : m
            )
          );
        } else if (chunk.type === 'tool_call') {
          console.log('🔧 Processing tool_call:', chunk); // DEBUG: Log tool calls
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantId
                ? {
                    ...m,
                    toolCalls: [
                      ...(m.toolCalls || []),
                      {
                        id: chunk.toolCallId!,
                        name: chunk.toolName!,
                        args: chunk.args!,
                      },
                    ],
                  }
                : m
            )
          );
        } else if (chunk.type === 'tool_result') {
          console.log('✅ Processing tool_result:', chunk); // DEBUG: Log tool results
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantId
                ? {
                    ...m,
                    toolCalls: m.toolCalls?.map(tc =>
                      tc.id === chunk.toolCallId
                        ? { ...tc, result: chunk.result as Record<string, unknown> }
                        : tc
                    ),
                  }
                : m
            )
          );
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        console.error('Chat error:', error);
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? { ...m, content: `Error: ${error.message}` }
              : m
          )
        );
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
    }
  };

  const renderToolCall = (toolCall: NonNullable<Message['toolCalls']>[0]) => {
    if (toolCall.name === 'execute_ssh_command') {
      const args = toolCall.args as { host?: string; command?: string };
      const result = toolCall.result as { success?: boolean; output?: string; error?: string } | undefined;
      
      return (
        <div className={`rounded-lg p-2 mb-1.5 ${
          theme === 'light' ? 'bg-gray-100' : 'bg-white/5'
        }`}>
          <div className="flex items-center gap-1.5 mb-1.5">
            <Terminal className="w-3.5 h-3.5 text-green-400" />
            <span className={`text-xs font-mono ${
              theme === 'light' ? 'text-gray-700' : 'text-gray-300'
            }`}>
              SSH: {args.host || 'unknown'}
            </span>
          </div>
          <div className={`font-mono text-[11px] ${
            theme === 'light' ? 'text-gray-600' : 'text-gray-400'
          }`}>
            $ {args.command || ''}
          </div>
          {result && (
            <pre className={`mt-1.5 text-[11px] overflow-x-auto ${
              result.success ? 'text-green-400' : 'text-red-400'
            }`}>
              {result.output || result.error || ''}
            </pre>
          )}
        </div>
      );
    } else if (toolCall.name === 'run_ansible_playbook' || toolCall.name === 'create_ansible_playbook') {
      const args = toolCall.args as { playbook_content?: string };
      const result = toolCall.result as string | { output?: string } | undefined;
      
      return (
        <div className={`rounded-lg p-2 mb-1.5 ${
          theme === 'light' ? 'bg-gray-100' : 'bg-white/5'
        }`}>
          <div className="flex items-center gap-1.5 mb-1.5">
            <FileCode className="w-3.5 h-3.5 text-purple-400" />
            <span className={`text-xs ${
              theme === 'light' ? 'text-gray-700' : 'text-gray-300'
            }`}>
              Ansible Playbook
            </span>
          </div>
          {(args.playbook_content || result) && (
            <pre className={`text-[11px] overflow-x-auto ${
              theme === 'light' ? 'text-gray-600' : 'text-gray-400'
            }`}>
              {args.playbook_content || (typeof result === 'string' ? result : result?.output) || ''}
            </pre>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <SimpleLiquidGlass
      padding="0"
      textColor={theme === 'light' ? '#1f2937' : 'white'}
    >
      <div className="w-96 h-[700px] flex flex-col bg-transparent">
        {/* Header */}
        <div className={`flex items-center justify-between p-3 border-b ${
          theme === 'light' ? 'border-gray-200' : 'border-white/10'
        }`}>
          <div>
            <h3 className={`font-semibold text-xs ${
              theme === 'light' ? 'text-gray-900' : 'text-white'
            }`}>
              AI Network Assistant
            </h3>
            {focusedNode && (
              <p className={`text-[11px] ${
                theme === 'light' ? 'text-gray-600' : 'text-gray-400'
              }`}>
                Context: {focusedNode.label}
              </p>
            )}
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className={`p-1 rounded-lg transition-colors ${
                theme === 'light' ? 'hover:bg-gray-100' : 'hover:bg-white/10'
              }`}
            >
              <X className={`w-3.5 h-3.5 ${
                theme === 'light' ? 'text-gray-600' : 'text-gray-400'
              }`} />
            </button>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[85%] ${message.role === 'assistant' ? 'space-y-1.5' : ''}`}>
                {message.content && (
                  <div
                    className={`p-2.5 rounded-lg text-xs ${
                      message.role === 'user'
                        ? theme === 'light'
                          ? 'bg-blue-500 text-white'
                          : 'bg-blue-600/30 text-blue-100'
                        : theme === 'light'
                        ? 'bg-gray-200 text-gray-800'
                        : 'bg-gray-700/50 text-gray-100'
                    }`}
                  >
                    {message.role === 'assistant' ? (
                        <ReactMarkdown 
                          remarkPlugins={[remarkGfm]}
                          components={{
                            p: (props) => <p className="text-xs" {...props} />,
                            li: (props) => <li className="text-xs" {...props} />,
                            a: (props) => <a className="text-blue-400 hover:text-blue-500" {...props} />,
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      ) : (
                        <div className="whitespace-pre-wrap text-xs">{message.content}</div>
                      )}
                  </div>
                )}
                {message.toolCalls?.map((toolCall, index) => (
                  <div key={index}>{renderToolCall(toolCall)}</div>
                ))}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className={`p-2.5 rounded-lg ${
                theme === 'light' ? 'bg-gray-200' : 'bg-gray-700/50'
              }`}>
                <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className={`p-3 border-t ${
          theme === 'light' ? 'border-gray-200' : 'border-white/10'
        }`}>
          <div className="flex gap-1.5">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
              placeholder={focusedNode ? `Ask about ${focusedNode.label}...` : 'Ask about the network...'}
              className={`flex-1 px-2.5 py-1.5 rounded-lg text-xs focus:outline-none focus:ring-1.5 focus:ring-blue-500 ${
                theme === 'light'
                  ? 'bg-gray-100 text-gray-900 placeholder-gray-500'
                  : 'bg-gray-800/50 text-white placeholder-gray-400'
              }`}
              disabled={isLoading}
            />
            <button
              onClick={isLoading ? handleCancel : handleSendMessage}
              disabled={!inputValue.trim() && !isLoading}
              className={`px-2.5 py-1.5 rounded-lg transition-all ${
                isLoading
                  ? 'bg-red-500 hover:bg-red-600 text-white'
                  : theme === 'light'
                  ? 'bg-blue-500 hover:bg-blue-600 text-white disabled:bg-gray-300'
                  : 'bg-blue-600/40 hover:bg-blue-600/60 text-white disabled:bg-gray-700/50'
              }`}
            >
              {isLoading ? (
                <X className="w-3.5 h-3.5" />
              ) : (
                <Send className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </SimpleLiquidGlass>
  );
}; 