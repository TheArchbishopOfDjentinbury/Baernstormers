import Achievement from '@/components/Achievement';
import { useState, useEffect } from 'react';

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
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {achievements.map((achievement) => {
            // Color schemes based on achievement type
            const typeStyles = {
              good: {
                border: achievement.unlocked
                  ? 'border-green-200'
                  : 'border-gray-200',
                background: achievement.unlocked ? 'bg-green-50' : 'bg-gray-50',
                accent: 'text-green-600',
                progress: 'bg-green-500',
              },
              medium: {
                border: achievement.unlocked
                  ? 'border-orange-200'
                  : 'border-gray-200',
                background: achievement.unlocked
                  ? 'bg-orange-50'
                  : 'bg-gray-50',
                accent: 'text-orange-600',
                progress: 'bg-orange-500',
              },
              bad: {
                border: achievement.unlocked
                  ? 'border-red-200'
                  : 'border-gray-200',
                background: achievement.unlocked ? 'bg-red-50' : 'bg-gray-50',
                accent: 'text-red-600',
                progress: 'bg-red-500',
              },
            };

            const styles = typeStyles[achievement.type];

            return (
              <div
                key={achievement.id}
                className={`p-6 rounded-2xl border-2 transition-all duration-300 hover:shadow-lg ${styles.border} ${styles.background} shadow-md`}
              >
                {/* Category Badge */}
                <div className="flex justify-between items-start mb-4">
                  <span
                    className={`text-xs px-2 py-1 rounded-full font-medium ${styles.accent} bg-white/70`}
                  >
                    {achievement.category}
                  </span>
                  <div className="flex items-center gap-1 text-xs text-green-600 font-medium">
                    <span>✨</span>
                    Achieved!
                  </div>
                </div>

                {/* Achievement Animation */}
                <div className="mb-4">
                  {animationsLoaded ? (
                    <Achievement
                      icon={achievement.icon}
                      type={achievement.type}
                      size="lg"
                      unlocked={achievement.unlocked}
                    />
                  ) : (
                    <div className="w-24 h-24 bg-gray-200 rounded-full mx-auto animate-pulse"></div>
                  )}
                </div>

                {/* Achievement Info */}
                <div className="text-center">
                  <h3 className="text-lg font-bold mb-2 text-gray-800">
                    {achievement.title}
                  </h3>
                  <p className="text-sm mb-4 text-gray-600">
                    {achievement.description}
                  </p>

                  {/* Progress Bar */}
                  <div className="mb-2">
                    <div className="flex justify-between text-xs mb-2">
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
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default Achievements;
