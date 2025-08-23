import { useState, useCallback } from 'react';
import { API_CONFIG, ChatRequest } from '@/config/api';

export interface StreamingMessage {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  type: 'text' | 'voice';
  isStreaming?: boolean;
}

export interface UseStreamingResponseReturn {
  isStreaming: boolean;
  error: string | null;
  sendMessage: (message: string) => Promise<void>;
  sendAudio: (audioBlob: Blob) => Promise<void>;
}

export const useStreamingResponse = (
  onMessageUpdate: (message: StreamingMessage) => void,
  onMessageComplete: (message: StreamingMessage) => void,
  onError: (error: string) => void
): UseStreamingResponseReturn => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const makeStreamingRequest = useCallback(
    async (request: ChatRequest, messageId: string) => {
      try {
        setIsStreaming(true);
        setError(null);

        const url = `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.CHAT_STREAM}`;

        console.log('🚀 Sending request to:', url);
        console.log('📤 Request payload:', JSON.stringify(request, null, 2));
        console.log('📤 Request headers:', {
          'Content-Type': 'application/json',
        });

        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(request),
        });

        console.log('📡 Response status:', response.status);
        console.log(
          '📡 Response headers:',
          Object.fromEntries(response.headers.entries())
        );

        // Check if it's actually a streaming response
        const contentType = response.headers.get('content-type');
        const transferEncoding = response.headers.get('transfer-encoding');

        console.log('🔍 Content-Type:', contentType);
        console.log('🔍 Transfer-Encoding:', transferEncoding);
        console.log(
          '🔍 Is streaming response?',
          transferEncoding === 'chunked' || contentType?.includes('stream')
        );

        // Check for empty response
        const contentLength = response.headers.get('content-length');
        console.log('🔍 Content-Length:', contentLength);

        if (contentLength === '0') {
          console.log('⚠️ Empty response body! (content-length: 0)');
          console.log(
            '❌ API might not be working correctly or wrong endpoint'
          );
          throw new Error('API returned empty response (content-length: 0)');
        }

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        if (!response.body) {
          throw new Error('No response body');
        }

        // Check if this might be a regular JSON response instead of stream
        if (
          contentType?.includes('application/json') &&
          transferEncoding !== 'chunked'
        ) {
          console.log(
            '⚠️ This looks like a regular JSON response, not streaming!'
          );
          console.log('📄 Trying to parse as JSON...');

          try {
            const jsonResponse = await response.json();
            console.log('📄 JSON Response:', jsonResponse);

            // Handle as single complete message
            const finalMessage: StreamingMessage = {
              id: messageId,
              text: jsonResponse.response || JSON.stringify(jsonResponse),
              sender: 'bot',
              timestamp: new Date(),
              type: 'text',
              isStreaming: false,
            };
            onMessageComplete(finalMessage);
            return;
          } catch (jsonError) {
            console.log(
              '❌ Failed to parse as JSON, falling back to streaming'
            );
          }
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let accumulatedText = '';
        let chunkCount = 0;

        // Create initial streaming message
        const streamingMessage: StreamingMessage = {
          id: messageId,
          text: '',
          sender: 'bot',
          timestamp: new Date(),
          type: 'text',
          isStreaming: true,
        };

        console.log('📥 Starting to read stream...');

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            console.log('✅ Stream completed!');
            console.log('📝 Final accumulated text:', accumulatedText);
            console.log('🔢 Total chunks received:', chunkCount);

            // Mark message as complete
            const finalMessage: StreamingMessage = {
              ...streamingMessage,
              text: accumulatedText,
              isStreaming: false,
            };
            onMessageComplete(finalMessage);
            break;
          }

          const chunk = decoder.decode(value, { stream: true });
          chunkCount++;

          console.log(`📦 Chunk ${chunkCount}:`, chunk);
          console.log(`📦 Chunk ${chunkCount} (raw bytes):`, value);

          // Parse SSE format: handle multiple JSON objects in one chunk
          let newContent = '';

          // First, split by "data: " to get individual messages
          const parts = chunk.split('data: ').filter((part) => part.trim());

          for (const part of parts) {
            try {
              // Clean up the JSON string - remove newlines and extra whitespace
              const cleanJsonData = part.trim().replace(/\n/g, '');

              // Skip empty parts
              if (!cleanJsonData) continue;

              // Try to parse each JSON object
              const parsed = JSON.parse(cleanJsonData);
              console.log(`📦 Parsed SSE data:`, parsed);

              // Handle different types of SSE messages
              if (parsed.content) {
                // Direct content field
                newContent += parsed.content;
              } else if (parsed.type === 'end') {
                // End of stream marker - don't add to content
                console.log('🏁 Received end of stream marker');
                continue;
              } else if (parsed.head && parsed.results) {
                // SPARQL query results
                console.log('📊 Received SPARQL results:', parsed);
                // Format SPARQL results as readable text
                if (
                  parsed.results.bindings &&
                  parsed.results.bindings.length > 0
                ) {
                  newContent += '\n\nQuery Results:\n';
                  parsed.results.bindings.forEach(
                    (binding: any, index: number) => {
                      newContent += `${index + 1}. `;
                      Object.keys(binding).forEach((key) => {
                        newContent += `${key}: ${binding[key].value} `;
                      });
                      newContent += '\n';
                    }
                  );
                } else {
                  newContent += '\n\nNo results found for your query.';
                }
              } else if (parsed.schema_summary || parsed.example_queries) {
                // Schema information - format nicely
                if (parsed.schema_summary) {
                  newContent += '\n\n📋 Schema Information:\n';
                  newContent += parsed.schema_summary;
                }
                if (parsed.description) {
                  newContent += '\n\n📝 ' + parsed.description;
                }
              } else if (parsed.error) {
                // Error messages
                newContent += `\n\n❌ Error: ${parsed.error}\n`;
                if (parsed.query) {
                  newContent += `Query: ${parsed.query}\n`;
                }
                if (parsed.validation_tips) {
                  newContent += `Tips: ${parsed.validation_tips.join(', ')}\n`;
                }
              } else {
                // Unknown JSON structure - log but don't add to content
                console.log('❓ Unknown SSE data structure:', parsed);
                // Only add to content if it seems like actual message content
                if (parsed.message || parsed.text || parsed.response) {
                  newContent +=
                    parsed.message || parsed.text || parsed.response;
                }
                // Skip other control/metadata messages
              }
            } catch (parseError) {
              console.log(`⚠️ Failed to parse JSON part:`, part, parseError);
              // If parsing fails, treat as plain text, but skip control messages
              const trimmedPart = part.trim();
              if (
                trimmedPart &&
                !trimmedPart.includes('"type"') &&
                !trimmedPart.includes('{"')
              ) {
                newContent += trimmedPart;
              }
            }
          }

          if (newContent) {
            accumulatedText += newContent;
            console.log(`📝 New content extracted:`, newContent);
            console.log(`📝 Accumulated so far:`, accumulatedText);
          } else {
            // Fallback: treat as plain text, but skip control messages
            const cleanChunk = chunk.trim();
            if (
              cleanChunk &&
              !cleanChunk.includes('data: {"type"') &&
              !cleanChunk.includes('"type": "end"') &&
              !cleanChunk.startsWith('data: {')
            ) {
              accumulatedText += chunk;
              console.log(`📝 Accumulated so far (fallback):`, accumulatedText);
            } else {
              console.log(`🚫 Skipped control chunk:`, cleanChunk);
            }
          }

          // Update the streaming message
          const updatedMessage: StreamingMessage = {
            ...streamingMessage,
            text: accumulatedText,
          };

          onMessageUpdate(updatedMessage);
        }
      } catch (err) {
        console.error('❌ Error in streaming request:', err);
        const errorMessage =
          err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        onError(errorMessage);
      } finally {
        setIsStreaming(false);
      }
    },
    [onMessageUpdate, onMessageComplete, onError]
  );

  const sendMessage = useCallback(
    async (message: string) => {
      const messageId = (Date.now() + 1).toString();
      const request: ChatRequest = {
        message,
        include_audio: false,
      };

      await makeStreamingRequest(request, messageId);
    },
    [makeStreamingRequest]
  );

  const sendAudio = useCallback(
    async (audioBlob: Blob) => {
      const messageId = (Date.now() + 1).toString();

      // For audio, we might need to send it differently
      // This is a simplified version - you might need to adjust based on your API
      const request: ChatRequest = {
        message: '', // Empty for audio
        include_audio: true,
      };

      await makeStreamingRequest(request, messageId);
    },
    [makeStreamingRequest]
  );

  return {
    isStreaming,
    error,
    sendMessage,
    sendAudio,
  };
};
