import { API_CONFIG, type ChatRequest, type ChatResponse } from '@/config/api';

export class ChatService {
  private static async makeRequest(
    endpoint: string,
    data: ChatRequest
  ): Promise<Response> {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response;
  }

  static async sendTextMessage(message: string): Promise<ChatResponse> {
    try {
      const request: ChatRequest = {
        message,
        include_audio: false,
      };

      const response = await this.makeRequest(
        API_CONFIG.ENDPOINTS.CHAT_STREAM,
        request
      );

      // Handle streaming response
      if (response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          fullResponse += chunk;
        }

        return { response: fullResponse };
      }

      return { response: 'No response received' };
    } catch (error) {
      console.error('Error sending text message:', error);
      return {
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  static async sendAudioMessage(audioBlob: Blob): Promise<ChatResponse> {
    try {
      // Convert audio blob to base64 or handle as needed by your API
      const formData = new FormData();
      formData.append('audio', audioBlob);

      const request: ChatRequest = {
        message: '', // Empty for audio
        include_audio: true,
      };

      const response = await this.makeRequest(
        API_CONFIG.ENDPOINTS.CHAT_STREAM,
        request
      );

      // Handle streaming response similar to text
      if (response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          fullResponse += chunk;
        }

        return { response: fullResponse };
      }

      return { response: 'No response received' };
    } catch (error) {
      console.error('Error sending audio message:', error);
      return {
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }
}
