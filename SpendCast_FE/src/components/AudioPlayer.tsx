import { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import { Play, Pause, SkipBack, SkipForward, Volume2 } from 'lucide-react';

interface AudioPlayerProps {
  audioUrl?: string;
  base64Audio?: string;
  onPlayStateChange?: (isPlaying: boolean) => void;
  minimal?: boolean;
}

const AudioPlayer = ({
  audioUrl,
  base64Audio,
  onPlayStateChange,
  minimal = false,
}: AudioPlayerProps) => {
  const waveformRef = useRef<HTMLDivElement>(null);
  const wavesurfer = useRef<WaveSurfer | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.5);

  const base64ToBlob = (
    base64: string,
    mimeType: string = 'audio/mp3'
  ): Blob => {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  };

  useEffect(() => {
    if (!waveformRef.current) return;

    wavesurfer.current = WaveSurfer.create({
      container: waveformRef.current,
      waveColor: minimal ? '#6b7280' : '#4ade80',
      progressColor: minimal ? '#374151' : '#16a34a',
      cursorColor: '#ffffff',
      barWidth: minimal ? 2 : 3,
      barRadius: minimal ? 2 : 3,
      height: minimal ? 40 : 60,
      normalize: true,
      backend: 'WebAudio',
      mediaControls: false,
    });

    if (base64Audio) {
      const audioBlob = base64ToBlob(base64Audio);
      wavesurfer.current.loadBlob(audioBlob);
    } else if (audioUrl) {
      wavesurfer.current.load(audioUrl);
    } else {
      wavesurfer.current.loadBlob(createDemoBlob());
    }

    wavesurfer.current.on('play', () => {
      setIsPlaying(true);
      onPlayStateChange?.(true);
    });

    wavesurfer.current.on('pause', () => {
      setIsPlaying(false);
      onPlayStateChange?.(false);
    });

    wavesurfer.current.on('timeupdate', (time: number) => {
      setCurrentTime(time);
    });

    wavesurfer.current.on('ready', () => {
      setDuration(wavesurfer.current?.getDuration() || 0);
    });

    return () => {
      if (wavesurfer.current) {
        wavesurfer.current.destroy();
      }
    };
  }, [audioUrl, base64Audio, onPlayStateChange, minimal]);

  const createDemoBlob = () => {
    const AudioContextClass =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext })
        .webkitAudioContext;
    const audioContext = new AudioContextClass();
    const sampleRate = audioContext.sampleRate;
    const duration = 30;
    const buffer = audioContext.createBuffer(
      1,
      sampleRate * duration,
      sampleRate
    );
    const data = buffer.getChannelData(0);

    for (let i = 0; i < data.length; i++) {
      const time = i / sampleRate;
      data[i] =
        Math.sin(440 * 2 * Math.PI * time) * 0.1 * (1 + Math.sin(time * 0.5));
    }

    const arrayBuffer = new ArrayBuffer(44 + data.length * 2);
    const view = new DataView(arrayBuffer);

    const writeString = (offset: number, string: string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };

    writeString(0, 'RIFF');
    view.setUint32(4, 36 + data.length * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, data.length * 2, true);

    let offset = 44;
    for (let i = 0; i < data.length; i++) {
      view.setInt16(offset, data[i] * 0x7fff, true);
      offset += 2;
    }

    return new Blob([arrayBuffer], { type: 'audio/wav' });
  };

  const togglePlayPause = () => {
    if (wavesurfer.current) {
      wavesurfer.current.playPause();
    }
  };

  const skipBackward = () => {
    if (wavesurfer.current) {
      const currentTime = wavesurfer.current.getCurrentTime();
      wavesurfer.current.seekTo(Math.max(0, (currentTime - 10) / duration));
    }
  };

  const skipForward = () => {
    if (wavesurfer.current) {
      const currentTime = wavesurfer.current.getCurrentTime();
      wavesurfer.current.seekTo(Math.min(1, (currentTime + 10) / duration));
    }
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (wavesurfer.current) {
      wavesurfer.current.setVolume(newVolume);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (minimal) {
    return (
      <div className="w-full bg-gray-50 rounded-lg p-2 border border-gray-200 mt-1">
        <div ref={waveformRef} className="mb-2" />

        <div className="flex items-center gap-2">
          <button
            onClick={togglePlayPause}
            className="p-1.5 bg-brand-secondary hover:bg-brand-secondary/80 rounded-full text-white transition-colors flex-shrink-0"
          >
            {isPlaying ? <Pause size={14} /> : <Play size={14} />}
          </button>

          <div className="text-gray-500 text-xs font-mono">
            {formatTime(currentTime)} / {formatTime(duration)}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-gray-900/90 backdrop-blur-sm rounded-lg p-6 border border-gray-700">
      <div ref={waveformRef} className="mb-4" />

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={skipBackward}
            className="p-2 text-white hover:text-green-400 transition-colors"
            title="Skip back 10s"
          >
            <SkipBack size={20} />
          </button>

          <button
            onClick={togglePlayPause}
            className="p-3 bg-green-500 hover:bg-green-600 rounded-full text-white transition-colors"
          >
            {isPlaying ? <Pause size={24} /> : <Play size={24} />}
          </button>

          <button
            onClick={skipForward}
            className="p-2 text-white hover:text-green-400 transition-colors"
            title="Skip forward 10s"
          >
            <SkipForward size={20} />
          </button>
        </div>

        <div className="text-white text-sm">
          {formatTime(currentTime)} / {formatTime(duration)}
        </div>

        <div className="flex items-center space-x-2">
          <Volume2 size={20} className="text-white" />
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={volume}
            onChange={handleVolumeChange}
            className="w-20 accent-green-500"
          />
        </div>
      </div>
    </div>
  );
};

export default AudioPlayer;
