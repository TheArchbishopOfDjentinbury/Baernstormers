import { useState } from 'react';
import Lottie from 'lottie-react';
import AudioPlayer from '../AudioPlayer';

interface PodcastPlayerProps {
  animationData: object;
  title?: string;
  description?: string;
  playingTitle?: string;
  playingDescription?: string;
  audioUrl?: string;
  base64Audio?: string;
  className?: string;
  isLoading?: boolean;
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
  isLoading = false,
}: PodcastPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <div
      className={`flex flex-col justify-center items-center space-y-8 ${className}`}
    >
      <div className="relative">
        <div
          className={`transform transition-all duration-500 ${
            isPlaying ? 'scale-110 rotate-3' : 'scale-100'
          }`}
        >
          <Lottie
            animationData={animationData}
            loop={true}
            autoplay={true}
            style={{
              width: 300,
              height: 300,
              filter: isPlaying ? 'brightness(1)' : 'brightness(0.8)',
            }}
          />
        </div>

        {isPlaying && (
          <div className="absolute inset-0 rounded-full border-4 border-green-400 animate-ping opacity-30" />
        )}
      </div>

      <div className="text-center max-w-md">
        <h3 className="text-xl font-semibold text-white mb-2">
          {isPlaying ? playingTitle : title}
        </h3>
        <p className="text-gray-400 text-sm">
          {isPlaying ? playingDescription : description}
        </p>
      </div>

      <div className="w-full max-w-2xl">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-8">
            <div className="flex space-x-2 mb-4">
              <div className="w-3 h-3 bg-brand-secondary rounded-full animate-bounce"></div>
              <div
                className="w-3 h-3 bg-brand-secondary rounded-full animate-bounce"
                style={{ animationDelay: '0.1s' }}
              ></div>
              <div
                className="w-3 h-3 bg-brand-secondary rounded-full animate-bounce"
                style={{ animationDelay: '0.2s' }}
              ></div>
            </div>
            <p className="text-gray-400 text-sm">Generating your podcast...</p>
          </div>
        ) : (
          <AudioPlayer
            audioUrl={audioUrl}
            base64Audio={base64Audio}
            onPlayStateChange={setIsPlaying}
          />
        )}
      </div>
    </div>
  );
}

export default PodcastPlayer;
