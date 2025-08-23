import RecordRTC from 'recordrtc';

export class WebMAudioRecorder {
  private recorder: RecordRTC | null = null;
  private stream: MediaStream | null = null;

  /**
   * Start recording audio in WebM format
   */
  async startRecording(): Promise<void> {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      this.recorder = new RecordRTC(this.stream, {
        type: 'audio',
        mimeType: 'audio/webm',
        recorderType: RecordRTC.MediaStreamRecorder,
        numberOfAudioChannels: 1, // Mono for smaller file size
        audioBitsPerSecond: 128000, // 128 kbps
        timeSlice: 1000, // Get data every second
      });

      this.recorder.startRecording();
    } catch (error) {
      console.error('Error starting WebM recording:', error);
      throw new Error('Failed to start recording');
    }
  }

  /**
   * Stop recording and get WebM blob
   */
  async stopRecording(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.recorder) {
        reject(new Error('No active recording'));
        return;
      }

      this.recorder.stopRecording(() => {
        if (this.recorder) {
          const blob = this.recorder.getBlob();
          this.cleanup();
          resolve(blob);
        } else {
          reject(new Error('Recorder became null during stop'));
        }
      });
    });
  }

  /**
   * Convert blob to Base64 string
   */
  static async blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result as string;
        // Remove the data URL prefix to get pure Base64
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  /**
   * Get full data URL (with mime type)
   */
  static async blobToDataURL(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  /**
   * Record audio and convert to Base64 in one go
   */
  static async recordToBase64(): Promise<{
    base64: string;
    dataURL: string;
    blob: Blob;
  }> {
    const recorder = new WebMAudioRecorder();

    await recorder.startRecording();

    // Auto-stop after some time or let user control it
    // For demo, we'll need to call stopRecording manually

    throw new Error('Use startRecording() and stopRecording() separately');
  }

  /**
   * Cleanup resources
   */
  private cleanup(): void {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }
    this.recorder = null;
  }

  /**
   * Check if recording is active
   */
  isRecording(): boolean {
    return this.recorder?.getState() === 'recording';
  }

  /**
   * Get recording duration
   */
  getDuration(): number {
    if (this.recorder?.getState() === 'recording') {
      // RecordRTC doesn't expose getStartTime in types, but it exists at runtime
      const recordRTCInstance = this.recorder as RecordRTC & {
        getStartTime(): number;
      };
      return Date.now() - recordRTCInstance.getStartTime();
    }
    return 0;
  }
}

// Helper functions for easy use
export const audioUtils = {
  /**
   * Create WebM recorder instance
   */
  createRecorder: () => new WebMAudioRecorder(),

  /**
   * Convert any blob to Base64
   */
  toBase64: WebMAudioRecorder.blobToBase64,

  /**
   * Convert any blob to data URL
   */
  toDataURL: WebMAudioRecorder.blobToDataURL,

  /**
   * Check browser support for WebM recording
   */
  checkSupport: () => {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  },

  /**
   * Convert Base64 string to Blob
   */
  base64ToBlob: (base64: string, mimeType = 'audio/webm'): Blob => {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  },

  /**
   * Convert Base64 string to audio URL for playback
   */
  base64ToAudioURL: (base64: string, mimeType = 'audio/webm'): string => {
    const blob = audioUtils.base64ToBlob(base64, mimeType);
    return URL.createObjectURL(blob);
  },
};
