import { useCallback, useState } from 'react';
import {
  useExternalStoreRuntime,
  ThreadMessageLike,
  AppendMessage,
  AddToolResultOptions,
} from '@assistant-ui/react';
import { ApiService } from '../services/api';
import { NetworkNode } from '../types/network';

interface NetworkContext {
  focusedNode?: NetworkNode;
  networkStats?: {
    totalNodes: number;
    active: number;
    issues: number;
  };
}

export const useNetworkAssistantRuntime = (context?: NetworkContext) => {
  const [messages, setMessages] = useState<ThreadMessageLike[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  const onNew = useCallback(async (message: AppendMessage) => {
    if (message.content[0]?.type !== 'text') {
      throw new Error('Only text messages are supported');
    }

    const userMessage: ThreadMessageLike = {
      id: Date.now().toString(),
      role: 'user',
      content: message.content,
    };

    setMessages(prev => [...prev, userMessage]);
    setIsRunning(true);

    // Create abort controller for cancellation
    const controller = new AbortController();
    setAbortController(controller);

    // Create assistant message placeholder
    const assistantId = (Date.now() + 1).toString();
    const assistantMessage: ThreadMessageLike = {
      id: assistantId,
      role: 'assistant',
      content: [],
    };

    setMessages(prev => [...prev, assistantMessage]);

    try {
      let currentText = '';
      const toolCalls: Array<{
        type: 'tool-call';
        toolCallId: string;
        toolName: string;
        args: unknown;
        result?: unknown;
      }> = [];
      let currentToolCallIndex = 0;

      // Stream the response
      for await (const chunk of ApiService.streamChat({
        message: message.content[0].text,
        context: context ? {
          focused_node: context.focusedNode,
          network_stats: context.networkStats ? {
            total_nodes: context.networkStats.totalNodes,
            active: context.networkStats.active,
            issues: context.networkStats.issues,
          } : undefined,
        } : undefined,
        signal: controller.signal,
      })) {
        if (chunk.type === 'text') {
          currentText += chunk.content;
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantId
                ? {
                    ...m,
                    content: [
                      { type: 'text', text: currentText },
                      ...toolCalls,
                    ],
                  }
                : m
            )
          );
        } else if (chunk.type === 'tool_call') {
          const toolCall = {
            type: 'tool-call' as const,
            toolCallId: chunk.toolCallId,
            toolName: chunk.toolName,
            args: chunk.args,
          };
          toolCalls[currentToolCallIndex] = toolCall;
          currentToolCallIndex++;

          setMessages(prev =>
            prev.map(m =>
              m.id === assistantId
                ? {
                    ...m,
                    content: [
                      ...(currentText ? [{ type: 'text' as const, text: currentText }] : []),
                      ...toolCalls,
                    ],
                  }
                : m
            )
          );
        } else if (chunk.type === 'tool_stream') {
          // Handle streaming tool output (e.g., SSH output)
          // This could be used to update a specific tool UI component
          console.log('Tool stream:', chunk.content);
        } else if (chunk.type === 'tool_result') {
          // Update the tool call with its result
          const lastToolCall = toolCalls[toolCalls.length - 1];
          if (lastToolCall) {
            lastToolCall.result = chunk.result;
            setMessages(prev =>
              prev.map(m =>
                m.id === assistantId
                  ? {
                      ...m,
                      content: [
                        ...(currentText ? [{ type: 'text' as const, text: currentText }] : []),
                        ...toolCalls,
                      ],
                    }
                  : m
              )
            );
          }
        } else if (chunk.type === 'error') {
          console.error('Stream error:', chunk.error);
          // Add error to message
          setMessages(prev =>
            prev.map(m =>
              m.id === assistantId
                ? {
                    ...m,
                    content: [
                      {
                        type: 'text' as const,
                        text: currentText || `Error: ${chunk.error}`,
                      },
                    ],
                  }
                : m
            )
          );
        }
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('Chat error:', error);
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? {
                  ...m,
                  content: [
                    {
                      type: 'text' as const,
                      text: `Error: ${error.message}`,
                    },
                  ],
                }
              : m
          )
        );
      }
    } finally {
      setIsRunning(false);
      setAbortController(null);
    }
  }, [context]);

  const onCancel = useCallback(() => {
    if (abortController) {
      abortController.abort();
      setIsRunning(false);
      setAbortController(null);
    }
  }, [abortController]);

  const onAddToolResult = useCallback((options: AddToolResultOptions) => {
    setMessages(prev =>
      prev.map(message => {
        if (message.id === options.messageId) {
          return {
            ...message,
            content: message.content.map(part => {
              if (
                part.type === 'tool-call' &&
                part.toolCallId === options.toolCallId
              ) {
                return {
                  ...part,
                  result: options.result,
                };
              }
              return part;
            }),
          };
        }
        return message;
      })
    );
  }, []);

  const runtime = useExternalStoreRuntime({
    messages,
    isRunning,
    onNew,
    onCancel,
    onAddToolResult,
  });

  return runtime;
}; 