import { Trophy, Star, Target, Award } from 'lucide-react';

function Achievements() {
  const achievements = [
    {
      id: 1,
      title: 'First Conversation',
      description: 'Started your first chat with SpendCast',
      icon: Star,
      progress: 100,
      unlocked: true,
      color: 'bg-yellow-100 text-yellow-600',
    },
    {
      id: 2,
      title: 'Budget Tracker',
      description: 'Tracked expenses for 7 consecutive days',
      icon: Target,
      progress: 60,
      unlocked: false,
      color: 'bg-blue-100 text-blue-600',
    },
    {
      id: 3,
      title: 'Spending Analyst',
      description: 'Analyzed 100+ transactions',
      icon: Award,
      progress: 25,
      unlocked: false,
      color: 'bg-green-100 text-green-600',
    },
    {
      id: 4,
      title: 'Master Saver',
      description: 'Saved 20% of monthly income',
      icon: Trophy,
      progress: 0,
      unlocked: false,
      color: 'bg-purple-100 text-purple-600',
    },
  ];

  return (
    <>
      {/* Main Content */}
      <main className="px-4 py-8 pb-24">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-semibold text-brand-secondary mb-4">
              Your Achievements
            </h2>
            <p className="text-brand-secondary/70">
              Track your progress and unlock rewards as you improve your
              spending habits
            </p>
          </div>

          {/* Achievements Grid */}
          <div className="grid gap-6 md:grid-cols-2">
            {achievements.map((achievement) => {
              const IconComponent = achievement.icon;
              return (
                <div
                  key={achievement.id}
                  className={`p-6 rounded-xl border-2 transition-all duration-200 ${
                    achievement.unlocked
                      ? 'border-brand-primary bg-brand-primary/5 shadow-lg'
                      : 'border-gray-200 bg-gray-50'
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <div
                      className={`p-3 rounded-full ${
                        achievement.unlocked
                          ? achievement.color
                          : 'bg-gray-200 text-gray-400'
                      }`}
                    >
                      <IconComponent className="h-6 w-6" />
                    </div>

                    <div className="flex-1">
                      <h3
                        className={`text-lg font-semibold mb-2 ${
                          achievement.unlocked
                            ? 'text-brand-secondary'
                            : 'text-gray-500'
                        }`}
                      >
                        {achievement.title}
                      </h3>
                      <p
                        className={`text-sm mb-4 ${
                          achievement.unlocked
                            ? 'text-brand-secondary/70'
                            : 'text-gray-400'
                        }`}
                      >
                        {achievement.description}
                      </p>

                      {/* Progress Bar */}
                      <div className="mb-2">
                        <div className="flex justify-between text-xs mb-1">
                          <span
                            className={
                              achievement.unlocked
                                ? 'text-brand-secondary'
                                : 'text-gray-400'
                            }
                          >
                            Progress
                          </span>
                          <span
                            className={
                              achievement.unlocked
                                ? 'text-brand-secondary'
                                : 'text-gray-400'
                            }
                          >
                            {achievement.progress}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full transition-all duration-500 ${
                              achievement.unlocked
                                ? 'bg-brand-primary'
                                : 'bg-gray-300'
                            }`}
                            style={{ width: `${achievement.progress}%` }}
                          ></div>
                        </div>
                      </div>

                      {achievement.unlocked && (
                        <div className="inline-flex items-center gap-1 text-xs text-brand-secondary font-medium">
                          <Trophy className="h-3 w-3" />
                          Unlocked!
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </main>
    </>
  );
}

export default Achievements;
