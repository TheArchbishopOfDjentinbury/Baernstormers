export const API_CONFIG = {
  BASE_URL: 'https://spendcast-backend-647495354561.europe-west3.run.app',
  ENDPOINTS: {
    CHAT_STREAM: '/api/v1/agent/chat/stream',
  },
} as const;

export interface ChatRequest {
  message: string;
  include_audio: boolean;
}

export interface ChatResponse {
  // Define response structure based on your API
  response?: string;
  audio?: string;
  error?: string;
}
