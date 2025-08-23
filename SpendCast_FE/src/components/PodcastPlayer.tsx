import { useState } from 'react';
import Lottie from 'lottie-react';
import AudioPlayer from './AudioPlayer';

interface PodcastPlayerProps {
  animationData: object; // Lottie animation JSON
  title?: string;
  description?: string;
  playingTitle?: string;
  playingDescription?: string;
  audioUrl?: string;
  base64Audio?: string;
  className?: string;
}

function PodcastPlayer({
  animationData,
  title = 'Ready to Listen',
  description = 'Press play to start your personalized podcast',
  playingTitle = 'Now Playing',
  playingDescription = 'Enjoying your audio content',
  audioUrl,
  base64Audio,
  className = '',
}: PodcastPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <div
      className={`flex flex-col justify-center items-center space-y-8 ${className}`}
    >
      {/* Lottie Animation */}
      <div className="relative">
        <div
          className={`transform transition-all duration-500 ${
            isPlaying ? 'scale-110 rotate-3' : 'scale-100'
          }`}
        >
          <Lottie
            animationData={animationData}
            loop={isPlaying}
            autoplay={isPlaying}
            style={{
              width: 300,
              height: 300,
              filter: isPlaying ? 'brightness(1.2)' : 'brightness(0.8)',
            }}
          />
        </div>

        {/* Pulse effect when playing */}
        {isPlaying && (
          <div className="absolute inset-0 rounded-full border-4 border-green-400 animate-ping opacity-30" />
        )}
      </div>

      {/* Podcast info */}
      <div className="text-center max-w-md">
        <h3 className="text-xl font-semibold text-white mb-2">
          {isPlaying ? playingTitle : title}
        </h3>
        <p className="text-gray-400 text-sm">
          {isPlaying ? playingDescription : description}
        </p>
      </div>

      {/* Audio Player */}
      <div className="w-full max-w-2xl">
        <AudioPlayer
          audioUrl={audioUrl}
          base64Audio={base64Audio}
          onPlayStateChange={setIsPlaying}
        />
      </div>
    </div>
  );
}

export default PodcastPlayer;
