import { useState } from 'react';
import PodcastPlayer from '../components/Podcast/PodcastPlayer';
import PodcastList from '@/components/Podcast/PodcastList';
import podcastAnimation from '../assets/podcast.json';

interface Podcast {
  id: string;
  title: string;
  description: string;
  duration?: string;
  image?: string;
  isComingSoon?: boolean;
  animationData?: unknown;
  audioUrl?: string;
}

function Podcast() {
  const [selectedPodcast, setSelectedPodcast] = useState<Podcast | null>(null);

  const podcasts: Podcast[] = [
    {
      id: 'yearly',
      title: 'Generate Yearly Podcast',
      description:
        'Get comprehensive insights about your annual spending patterns, trends, and financial habits.',
      duration: '~7 min',
      animationData: podcastAnimation,
    },
  ];

  const handlePodcastSelect = (podcast: Podcast) => {
    if (!podcast.isComingSoon) {
      setSelectedPodcast(podcast);
    }
  };

  return (
    <div className="h-full overflow-y-auto touch-scroll bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      <div className="min-h-full">
        <main className="px-4 py-8 pb-24">
          <div className="max-w-6xl mx-auto">
            <div className="text-center py-6">
              <p className="text-gray-300 text-lg">
                Discover insights through audio stories
              </p>
            </div>

            <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
              {selectedPodcast ? (
                <PodcastPlayer
                  animationData={
                    selectedPodcast.animationData || podcastAnimation
                  }
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
        </main>
      </div>
    </div>
  );
}

export default Podcast;
