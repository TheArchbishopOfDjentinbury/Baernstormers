import { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import PodcastPlayer from '../components/PodcastPlayer';
import PodcastList from '../components/PodcastList';
import podcastAnimation from '../assets/podcast.json';

interface Podcast {
  id: string;
  title: string;
  description: string;
  duration?: string;
  image?: string;
  isComingSoon?: boolean;
  animationData?: object;
  audioUrl?: string;
}

function Podcast() {
  const [selectedPodcast, setSelectedPodcast] = useState<Podcast | null>(null);

  // Available podcasts data
  const podcasts: Podcast[] = [
    {
      id: 'yearly',
      title: 'Generate Yearly Podcast',
      description:
        'Get comprehensive insights about your annual spending patterns, trends, and financial habits.',
      duration: '~7 min',
      animationData: podcastAnimation,
    },
    {
      id: 'healthy',
      title: 'Generate Healthy Food Podcast',
      description:
        'Discover your healthy eating habits and learn how your food spending aligns with wellness goals.',
      duration: '~5 min',
      animationData: podcastAnimation,
    },
    {
      id: 'tbd',
      title: 'TBD',
      description:
        'More exciting podcast categories coming soon. Stay tuned for updates!',
      duration: '~? min',
      isComingSoon: true,
    },
  ];

  const handlePodcastSelect = (podcast: Podcast) => {
    if (!podcast.isComingSoon) {
      setSelectedPodcast(podcast);
    }
  };

  const handleBackToList = () => {
    setSelectedPodcast(null);
  };

  return (
    <div className="h-full p-4 bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      <div className="max-w-6xl mx-auto h-full flex flex-col">
        {/* Header */}
        <div className="text-center py-6">
          {selectedPodcast && (
            <button
              onClick={handleBackToList}
              className="absolute left-4 top-6 flex items-center space-x-2 text-gray-300 hover:text-white transition-colors"
            >
              <ArrowLeft size={20} />
              <span>Back to Podcasts</span>
            </button>
          )}

          <p className="text-gray-300 text-lg">
            Discover insights through audio stories
          </p>
        </div>

        {/* Main content area */}
        <div className="flex-1 flex items-center justify-center">
          {selectedPodcast ? (
            <PodcastPlayer
              animationData={selectedPodcast.animationData}
              title="Ready to Listen"
              description={`Generate your ${selectedPodcast.title.toLowerCase()}`}
              playingTitle="Now Playing"
              playingDescription={selectedPodcast.description}
              audioUrl={selectedPodcast.audioUrl}
              className="h-full"
            />
          ) : (
            <PodcastList
              podcasts={podcasts}
              onPodcastSelect={handlePodcastSelect}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default Podcast;
