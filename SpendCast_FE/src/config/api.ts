export const API_CONFIG = {
  BASE_URL: 'https://spendcast-backend-647495354561.europe-west3.run.app',
  ENDPOINTS: {
    CHAT: '/api/v1/agent/chat',
    PODCAST: '/api/v1/agent/podcast',
  },
} as const;

export interface ChatRequest {
  message: string;
  include_audio: boolean;
  response_as_audio?: boolean;
}

export interface ChatResponse {
  response: string;
  success: boolean;
  error?: string;
  audio_content?: string;
}
