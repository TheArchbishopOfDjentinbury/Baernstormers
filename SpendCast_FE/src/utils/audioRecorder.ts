import RecordRTC from 'recordrtc';

export class WebMAudioRecorder {
  private recorder: RecordRTC | null = null;
  private stream: MediaStream | null = null;

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
        numberOfAudioChannels: 1,
        audioBitsPerSecond: 128000,
        timeSlice: 1000,
      });

      this.recorder.startRecording();
    } catch (error) {
      console.error('Error starting WebM recording:', error);
      throw new Error('Failed to start recording');
    }
  }

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

  static async blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result as string;
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  static async blobToDataURL(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  static async recordToBase64(): Promise<{
    base64: string;
    dataURL: string;
    blob: Blob;
  }> {
    const recorder = new WebMAudioRecorder();

    await recorder.startRecording();

    throw new Error('Use startRecording() and stopRecording() separately');
  }

  private cleanup(): void {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }
    this.recorder = null;
  }

  isRecording(): boolean {
    return this.recorder?.getState() === 'recording';
  }

  getDuration(): number {
    if (this.recorder?.getState() === 'recording') {
      const recordRTCInstance = this.recorder as RecordRTC & {
        getStartTime(): number;
      };
      return Date.now() - recordRTCInstance.getStartTime();
    }
    return 0;
  }
}

export const audioUtils = {
  createRecorder: () => new WebMAudioRecorder(),

  toBase64: WebMAudioRecorder.blobToBase64,

  toDataURL: WebMAudioRecorder.blobToDataURL,

  checkSupport: () => {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
  },

  base64ToBlob: (base64: string, mimeType = 'audio/webm'): Blob => {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  },

  base64ToAudioURL: (base64: string, mimeType = 'audio/webm'): string => {
    const blob = audioUtils.base64ToBlob(base64, mimeType);
    return URL.createObjectURL(blob);
  },
};
