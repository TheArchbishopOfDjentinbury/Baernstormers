import { API_CONFIG } from '@/config/api';

export const usePodcastResponse = () => {
  const generatePodcast = async (): Promise<string> => {
    const url = `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.PODCAST}`;

    console.log('🎙️ Making podcast request:', {
      url,
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      console.log('📡 Podcast response received:', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
      });

      if (!response.ok) {
        console.error('❌ Podcast request failed:', {
          status: response.status,
          statusText: response.statusText,
        });
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      console.log('📦 Podcast response data:', {
        success: data.success,
        hasResponse: !!data.response,
        responseLength: data.response?.length || 0,
        fullData: data,
      });

      if (!data.success) {
        console.error('❌ Podcast generation failed:', {
          error: data.error,
          fullData: data,
        });
        throw new Error(data.error || 'Failed to generate podcast');
      }

      const audioContent = data.response || '';
      console.log('✅ Podcast generated successfully:', {
        audioContentLength: audioContent.length,
        audioContentPreview: audioContent.substring(0, 100) + '...',
      });

      return audioContent;
    } catch (error) {
      console.error('💥 Error generating podcast:', error);
      throw error;
    }
  };

  return { generatePodcast };
};
