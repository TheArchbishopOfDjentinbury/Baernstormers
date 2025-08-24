import { useState } from 'react';
import PodcastPlayer from '../components/Podcast/PodcastPlayer';
import PodcastList from '@/components/Podcast/PodcastList';
import podcastAnimation from '../assets/podcast.json';
import { usePodcastResponse } from '@/hooks/usePodcastResponse';

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
  const [generatedAudio, setGeneratedAudio] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { generatePodcast } = usePodcastResponse();

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

  const handlePodcastSelect = async (podcast: Podcast) => {
    if (!podcast.isComingSoon) {
      setSelectedPodcast(podcast);
      setIsGenerating(true);
      setError(null);

      try {
        const audioContent = await generatePodcast();
        setGeneratedAudio(audioContent);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : 'Failed to generate podcast'
        );
      } finally {
        setIsGenerating(false);
      }
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
                <>
                  {error && (
                    <div className="text-center mb-4">
                      <p className="text-red-400 text-sm">{error}</p>
                      <button
                        onClick={() => setSelectedPodcast(null)}
                        className="mt-2 text-blue-400 hover:text-blue-300 text-sm"
                      >
                        Back to Podcasts
                      </button>
                    </div>
                  )}
                  <PodcastPlayer
                    animationData={
                      selectedPodcast.animationData || podcastAnimation
                    }
                    title={
                      isGenerating ? 'Generating Podcast...' : 'Ready to Listen'
                    }
                    description={
                      isGenerating
                        ? 'Please wait while we create your personalized podcast'
                        : `Your ${selectedPodcast.title.toLowerCase()} is ready`
                    }
                    playingTitle="Now Playing"
                    playingDescription={selectedPodcast.description}
                    audioUrl={selectedPodcast.audioUrl}
                    base64Audio={generatedAudio}
                    className="h-full"
                    isLoading={isGenerating}
                  />
                </>
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
