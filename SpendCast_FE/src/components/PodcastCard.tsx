import { Play } from 'lucide-react';
import Lottie from 'lottie-react';
import podcastCardAnimation from '../assets/podcast_card_1.json';

interface PodcastCardProps {
  title: string;
  image?: string;
  isComingSoon?: boolean;
  onClick?: () => void;
}

function PodcastCard({
  title,
  image,
  isComingSoon = false,
  onClick,
}: PodcastCardProps) {
  return (
    <div
      className={`
        relative bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20 
        transition-all duration-300 hover:bg-white/15 hover:scale-105 hover:shadow-xl
        flex flex-col h-64
        ${!isComingSoon ? 'cursor-pointer' : 'cursor-default opacity-60'}
      `}
      onClick={!isComingSoon ? onClick : undefined}
    >
      {/* Coming Soon Badge */}
      {isComingSoon && (
        <div className="absolute top-3 right-3 bg-yellow-500/80 text-black text-xs px-2 py-1 rounded-full font-semibold">
          Coming Soon
        </div>
      )}

      {/* Large Lottie Animation */}
      <div className="relative flex-1 bg-gradient-to-br from-purple-500/30 to-blue-500/30 rounded-lg flex items-center justify-center overflow-hidden mb-3">
        {image ? (
          <img
            src={image}
            alt={title}
            className="w-full h-full object-cover rounded-lg"
          />
        ) : (
          <div className="relative w-full h-full flex items-center justify-center">
            {/* Lottie Animation - Full Size */}
            <Lottie
              animationData={podcastCardAnimation}
              loop={true}
              autoplay={true}
              style={{
                width: '100%',
                height: '100%',
              }}
            />
            {/* Subtle Play icon overlay */}
            <div className="absolute bottom-3 right-3">
              <div className="bg-black/40 backdrop-blur-sm rounded-full p-2">
                <Play size={18} className="text-white/90" fill="currentColor" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Minimal Content - Only Title */}
      <div className="relative z-10 text-center">
        <h3 className="text-lg font-semibold text-white line-clamp-2">
          {title}
        </h3>
      </div>

      {/* Hover Effect */}
      {!isComingSoon && (
        <div className="absolute inset-0 bg-gradient-to-t from-green-400/10 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-300 rounded-xl" />
      )}
    </div>
  );
}

export default PodcastCard;
