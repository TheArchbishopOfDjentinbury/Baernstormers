import PodcastCard from './PodcastCard';

interface Podcast {
  id: string;
  title: string;
  description: string;
  duration?: string;
  image?: string;
  isComingSoon?: boolean;
  animationData?: any;
  audioUrl?: string;
}

interface PodcastListProps {
  podcasts: Podcast[];
  onPodcastSelect?: (podcast: Podcast) => void;
}

function PodcastList({ podcasts, onPodcastSelect }: PodcastListProps) {
  return (
    <div className="w-full max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h3 className="text-2xl font-semibold text-white mb-3">
          Available Podcasts
        </h3>
        <p className="text-gray-300 text-lg">
          Choose a podcast to generate your personalized audio insights
        </p>
      </div>

      {/* Podcasts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {podcasts.map((podcast) => (
          <PodcastCard
            key={podcast.id}
            title={podcast.title}
            description={podcast.description}
            duration={podcast.duration}
            image={podcast.image}
            isComingSoon={podcast.isComingSoon}
            onClick={() => onPodcastSelect?.(podcast)}
          />
        ))}
      </div>

      {/* Bottom spacing */}
      <div className="mt-12" />
    </div>
  );
}

export default PodcastList;
