import { useState, useCallback } from 'react';
import { API_CONFIG, type ChatRequest, type ChatResponse } from '@/config/api';

export interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  type: 'text' | 'voice';
  audioContent?: string;
}

export interface UseChatResponseReturn {
  isLoading: boolean;
  error: string | null;
  sendMessage: (
    message: string,
    includeAudio?: boolean,
    responseAsAudio?: boolean
  ) => Promise<void>;
}

export const useChatResponse = (
  onMessageComplete: (message: ChatMessage) => void,
  onError: (error: string) => void
): UseChatResponseReturn => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const makeRequest = useCallback(
    async (request: ChatRequest, messageId: string) => {
      try {
        setIsLoading(true);
        setError(null);

        const url = `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.CHAT}`;

        console.log('🚀 Sending request to:', url);

        if (request.include_audio) {
          const messageSizeKB = (request.message.length / 1024).toFixed(2);
          const messageSizeMB = (
            request.message.length /
            (1024 * 1024)
          ).toFixed(2);

          console.log('🎤 Voice message request details:', {
            url,
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            include_audio: request.include_audio,
            response_as_audio: request.response_as_audio,
            messageLength: request.message.length,
            messageSizeKB: `${messageSizeKB} KB`,
            messageSizeMB: `${messageSizeMB} MB`,
            messageIsBase64:
              request.message.startsWith('data:') ||
              request.message.length > 1000,
          });

          if (request.message.length > 5 * 1024 * 1024) {
            console.warn(
              '⚠️ Large audio file detected! Size:',
              messageSizeMB,
              'MB'
            );
          }
          console.log('📤 Voice message payload (truncated):', {
            ...request,
            message: request.message.substring(0, 100) + '...(truncated)',
          });
        } else {
          console.log(
            '📤 Text message payload:',
            JSON.stringify(request, null, 2)
          );
        }

        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(request),
        });

        console.log('📡 Response status:', response.status);

        if (!response.ok) {
          let errorDetails = '';
          try {
            const errorText = await response.text();
            console.error('❌ Server error response:', errorText);
            errorDetails = errorText;
          } catch (e) {
            console.error('❌ Could not read error response:', e);
          }

          throw new Error(
            `HTTP error! status: ${response.status}. Details: ${errorDetails}`
          );
        }

        const jsonResponse: ChatResponse = await response.json();
        console.log('📄 Chat Response:', jsonResponse);

        if (!jsonResponse.success) {
          throw new Error(jsonResponse.error || 'Unknown error from server');
        }

        const finalMessage: ChatMessage = {
          id: messageId,
          text: jsonResponse.response,
          sender: 'bot',
          timestamp: new Date(),
          type: jsonResponse.audio_content ? 'voice' : 'text',
          audioContent: jsonResponse.audio_content,
        };

        onMessageComplete(finalMessage);
      } catch (err) {
        console.error('❌ Error in chat request:', err);
        const errorMessage =
          err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        onError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    },
    [onMessageComplete, onError]
  );

  const sendMessage = useCallback(
    async (message: string, includeAudio = false, responseAsAudio = false) => {
      const messageId = Date.now().toString();

      if (includeAudio) {
        console.log('🚀 useChatResponse: Preparing voice message request:', {
          messageId,
          messageType: 'voice/audio',
          includeAudio,
          responseAsAudio,
          messageLength: message.length,
          messagePreview: message.substring(0, 50) + '...',
        });
      } else {
        console.log('📝 useChatResponse: Preparing text message request:', {
          messageId,
          messageType: 'text',
          includeAudio,
          responseAsAudio,
          message,
        });
      }

      const request: ChatRequest = {
        message,
        include_audio: includeAudio,
        response_as_audio: responseAsAudio,
      };

      console.log('📦 useChatResponse: Final request object:', request);

      await makeRequest(request, messageId);
    },
    [makeRequest]
  );

  return {
    isLoading,
    error,
    sendMessage,
  };
};
