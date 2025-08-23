import { Play } from 'lucide-react';

interface PodcastCardProps {
  title: string;
  description?: string;
  duration?: string;
  image?: string;
  isComingSoon?: boolean;
  onClick?: () => void;
}

function PodcastCard({
  title,
  description,
  duration = '~5 min',
  image,
  isComingSoon = false,
  onClick,
}: PodcastCardProps) {
  return (
    <div
      className={`
        relative bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20 
        transition-all duration-300 hover:bg-white/15 hover:scale-105 hover:shadow-xl
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

      {/* Image or Placeholder */}
      <div className="mb-4 h-32 bg-gradient-to-br from-purple-500/30 to-blue-500/30 rounded-lg flex items-center justify-center">
        {image ? (
          <img
            src={image}
            alt={title}
            className="w-full h-full object-cover rounded-lg"
          />
        ) : (
          <Play size={40} className="text-white/70" />
        )}
      </div>

      {/* Content */}
      <div className="space-y-2">
        <h3 className="text-lg font-semibold text-white line-clamp-2">
          {title}
        </h3>

        {description && (
          <p className="text-gray-300 text-sm line-clamp-3">{description}</p>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-2">
          <span className="text-gray-400 text-xs">{duration}</span>

          {!isComingSoon && (
            <div className="flex items-center space-x-1 text-green-400 text-sm">
              <Play size={16} />
              <span>Listen</span>
            </div>
          )}
        </div>
      </div>

      {/* Hover Effect */}
      {!isComingSoon && (
        <div className="absolute inset-0 bg-gradient-to-t from-green-400/10 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-300 rounded-xl" />
      )}
    </div>
  );
}

export default PodcastCard;
