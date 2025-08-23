import Achievement from '@/components/Achievement';
import MetalFrame from '@/components/GoldenFrame';
import { useState, useEffect } from 'react';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

// Import Lottie animations
import coffeeAnimation from '@/assets/coffee.json';
import healthyAnimation from '@/assets/healthy-food.json';
import transportAnimation from '@/assets/transport.json';
import swissAnimation from '@/assets/swiss.json';
import beerAnimation from '@/assets/beer.json';

function Achievements() {
  const [animationsLoaded, setAnimationsLoaded] = useState(false);

  useEffect(() => {
    // Simulate loading animations
    setAnimationsLoaded(true);
  }, []);

  const achievements = [
    {
      id: 1,
      title: 'Coffee Connoisseur',
      description: 'Spent over 200 CHF on coffee this month',
      icon: coffeeAnimation,
      progress: 100,
      unlocked: true,
      type: 'good' as const,
      category: 'Spending Habits',
    },
    {
      id: 2,
      title: 'Health Conscious',
      description: 'Spent 30% of food budget on healthy items',
      icon: healthyAnimation,
      progress: 75,
      unlocked: true,
      type: 'good' as const,
      category: 'Lifestyle',
    },
    {
      id: 3,
      title: 'Transport Spender',
      description: 'High transport costs - over budget limit',
      icon: transportAnimation,
      progress: 90,
      unlocked: true,
      type: 'bad' as const,
      category: 'Budget Alert',
    },
    {
      id: 4,
      title: 'Swiss Quality',
      description: 'Preferred Swiss-made products',
      icon: swissAnimation,
      progress: 60,
      unlocked: false,
      type: 'medium' as const,
      category: 'Quality Choice',
    },
    {
      id: 5,
      title: 'Social Drinker',
      description: 'Moderate alcohol spending - within limits',
      icon: beerAnimation,
      progress: 45,
      unlocked: false,
      type: 'medium' as const,
      category: 'Entertainment',
    },
    {
      id: 6,
      title: 'Budget Master',
      description: 'Stayed under budget for 3 months',
      icon: healthyAnimation, // Placeholder
      progress: 25,
      unlocked: false,
      type: 'good' as const,
      category: 'Financial Goal',
    },
  ];

  return (
    <div className="h-full overflow-y-auto p-4 pb-24">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-semibold text-brand-secondary mb-4">
            Your Achievements
          </h2>
          <p className="text-brand-secondary/70">
            Track your progress and unlock rewards as you improve your spending
            habits
          </p>
        </div>

        {/* Achievements Grid */}
        <div className="grid gap-6 grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {achievements.map((achievement) => {
            // Color schemes based on achievement type
            const typeStyles = {
              good: {
                accent: 'text-green-600',
                progress: 'bg-green-500',
                border: 'border-green-200',
                background: 'bg-green-50',
              },
              medium: {
                accent: 'text-orange-600',
                progress: 'bg-orange-500',
                border: 'border-orange-200',
                background: 'bg-orange-50',
              },
              bad: {
                accent: 'text-red-600',
                progress: 'bg-red-500',
                border: 'border-red-200',
                background: 'bg-red-50',
              },
            };

            const styles = typeStyles[achievement.type];

            return (
              <div key={achievement.id} className="text-center">
                <Popover>
                  <PopoverTrigger asChild>
                    <button className="group cursor-pointer focus:outline-none transition-all duration-300 hover:scale-105 active:scale-95 mb-2">
                      {animationsLoaded ? (
                        <MetalFrame>
                          <Achievement
                            icon={achievement.icon}
                            type={achievement.type}
                            size="lg"
                            unlocked={achievement.unlocked}
                          />
                        </MetalFrame>
                      ) : (
                        <div className="w-24 h-24 bg-gray-200 rounded-full mx-auto animate-pulse"></div>
                      )}
                    </button>
                  </PopoverTrigger>

                  <PopoverContent
                    className="w-80 bg-white border border-gray-200 shadow-lg"
                    side="top"
                    align="center"
                  >
                    {/* Detailed Info in Popover */}
                    <div className="space-y-3">
                      {/* Header */}
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="text-lg font-bold text-gray-800">
                            {achievement.title}
                          </h4>
                          <span
                            className={`inline-block text-xs px-2 py-1 rounded-full font-medium ${styles.accent} bg-white border ${styles.border} mt-1`}
                          >
                            {achievement.category}
                          </span>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-green-600 font-medium">
                          <span>✨</span>
                          Achieved!
                        </div>
                      </div>

                      {/* Description */}
                      <p className="text-sm text-gray-600">
                        {achievement.description}
                      </p>

                      {/* Progress Details */}
                      <div className="space-y-2">
                        <div className="flex justify-between text-xs">
                          <span className="text-gray-700 font-medium">
                            Progress
                          </span>
                          <span className={`${styles.accent} font-bold`}>
                            {achievement.progress}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-3">
                          <div
                            className={`h-3 rounded-full transition-all duration-700 ${styles.progress}`}
                            style={{ width: `${achievement.progress}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </PopoverContent>
                </Popover>

                {/* Achievement Title */}
                <h3 className="text-sm font-bold text-gray-800">
                  {achievement.title}
                </h3>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default Achievements;
