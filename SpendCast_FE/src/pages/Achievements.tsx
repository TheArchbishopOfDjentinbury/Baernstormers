import Achievement from '@/components/Achievement';
import { useState, useEffect, useMemo } from 'react';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { buildMetrics } from '@/components/achievements/metricfromData';
import type { Metrics } from '@/components/achievements/type';
import Footer from '@/components/Footer';

// Import Lottie animations
import coffeeAnimation from '@/assets/coffee.json';
import healthyAnimation from '@/assets/healthy-food.json';
import transportAnimation from '@/assets/transport.json';
import swissAnimation from '@/assets/swiss.json';
import beerAnimation from '@/assets/beer.json';
import moneyAnimation from '@/assets/money.json';

import { ShinyLedFrame } from '@/components/achievements/shiny-buttons';

type AchievementCalc = {
  id: number;
  title: string;
  description: string;
  icon: unknown;
  type: 'good' | 'medium' | 'bad';
  category: string;
  compute: (m: Metrics) => { progress: number; unlocked: boolean };
};

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const pct = (num: number, den: number) => (den > 0 ? num / den : 0);

const ACHIEVEMENTS: AchievementCalc[] = [
  {
    id: 1,
    title: 'No Coffee',
    description: 'Spent over 100 CHF on coffee this month',
    icon: coffeeAnimation,
    type: 'good',
    category: 'Spending Habits',
    compute: (m) => {
      // If your Metrics uses coffeeSpendThisMonth, keep that name.
      const spend = m.coffeeSpend;
      const ratio = clamp01(spend / 100);
      const p = (1 - ratio) * 100; // inverse progress
      return { progress: Math.round(p), unlocked: spend === 0 };
    },
  },
  {
    id: 2,
    title: 'Health Conscious',
    description: 'Spent 30% of food budget on healthy items',
    icon: healthyAnimation,
    type: 'good',
    category: 'Lifestyle',
    compute: (m) => {
      const target = 0.3;
      const share = pct(
        m.healthyFoodSpend,
        m.healthyFoodSpend + m.unhealthyFoodSpend
      );
      const p = clamp01(share / target) * 100;
      return { progress: Math.round(p), unlocked: share >= target };
    },
  },
  {
    id: 3,
    title: 'Transport Spender',
    description: 'High transport costs - over budget limit',
    icon: transportAnimation,
    type: 'bad',
    category: 'Budget Alert',
    compute: (m) => {
      const transportBudget = 200; // TODO: from settings
      const ratio =
        transportBudget > 0 ? m.transportSpend / transportBudget : 0;
      const p = clamp01(ratio) * 100;
      return { progress: Math.round(p), unlocked: ratio >= 1.0 };
    },
  },
  {
    id: 4,
    title: 'Swiss Quality',
    description: 'Preferred Swiss-made products',
    icon: swissAnimation,
    type: 'medium',
    category: 'Quality Choice',
    compute: (m) => {
      const share = pct(
        m.swissMadeSpend,
        m.swissMadeSpend + m.nonswissMadeSpend
      );
      const p = clamp01(share) * 100;
      return { progress: Math.round(p), unlocked: share >= 0.5 };
    },
  },
  {
    id: 5,
    title: 'Social Drinker',
    description: 'Moderate alcohol spending - within limits',
    icon: beerAnimation,
    type: 'medium',
    category: 'Entertainment',
    compute: (m) => {
      const alcoholBudget = 100; // or m.alcoholMonthlyLimit
      const ratio = alcoholBudget > 0 ? m.alcoholSpend / alcoholBudget : 0;
      // 100 at/below limit; drops to 0 at 2x limit
      const p = (1 - clamp01((ratio - 1) / 1)) * 100;
      return { progress: Math.round(p), unlocked: ratio <= 1.0 };
    },
  },
  {
    id: 6,
    title: 'Budget Master',
    description: 'Stayed under budget for 3 months',
    icon: moneyAnimation,
    type: 'good',
    category: 'Financial Goal',
    compute: (m) => {
      const p = clamp01(m.consecutiveMonthsUnderBudget / 3) * 100;
      return {
        progress: Math.round(p),
        unlocked: m.consecutiveMonthsUnderBudget >= 3,
      };
    },
  },
];

type Props = {
  selectedMonth?: string; // Format: "2024-07"
};

function Achievements({ selectedMonth }: Props) {
  const [animationsLoaded, setAnimationsLoaded] = useState(false);

  useEffect(() => setAnimationsLoaded(true), []);

  // Build metrics for the selected month
  const metrics = useMemo(() => buildMetrics(selectedMonth), [selectedMonth]);

  const computed = useMemo(
    () =>
      ACHIEVEMENTS.map((a) => {
        const { progress, unlocked } = a.compute(metrics);
        return { ...a, progress, unlocked };
      }),
    [metrics]
  );

  // Get month label for display
  const monthLabel = useMemo(() => {
    const date = new Date(selectedMonth + '-01');
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
  }, [selectedMonth]);

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-semibold text-brand-secondary mb-4">
              Your Achievements
            </h2>
            <p className="text-brand-secondary/70 mb-4">
              Track your progress and unlock rewards as you improve your
              spending habits
            </p>

            {/* Current Month Display */}
            <div className="mt-2">
              <span className="text-sm text-brand-secondary/60">
                Showing achievements for:{' '}
                <span className="font-semibold">{monthLabel}</span>
              </span>
            </div>

            {/* Special notification for August achievements */}
            {selectedMonth === '2024-08' && (
              <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-2 text-green-700">
                  <span className="text-lg">🎉</span>
                  <span className="text-sm font-medium">
                    Congratulations! You've unlocked August achievements by
                    completing the quiz!
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className="grid gap-6 grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {computed.map((achievement) => {
              const typeStyles = {
                good: {
                  led: '#22c55e',
                  accent: 'text-green-600',
                  progress: 'bg-green-500',
                  border: 'border-green-200',
                  background: 'bg-green-50',
                },
                medium: {
                  led: '#f59e0b',
                  accent: 'text-orange-600',
                  progress: 'bg-orange-500',
                  border: 'border-orange-200',
                  background: 'bg-orange-50',
                },
                bad: {
                  led: '#ef4444',
                  accent: 'text-red-600',
                  progress: 'bg-red-500',
                  border: 'border-red-200',
                  background: 'bg-red-50',
                },
              } as const;
              const styles = typeStyles[achievement.type];

              return (
                <div key={achievement.id} className="text-center">
                  <Popover>
                    <PopoverTrigger asChild>
                      <button
                        className="group cursor-pointer focus:outline-none transition-all duration-300 mb-2
                                hover:scale-105 active:scale-95 rounded-full"
                      >
                        {' '}
                        {animationsLoaded ? (
                          <ShinyLedFrame ledColor={styles.led} size={96}>
                            <Achievement
                              icon={achievement.icon}
                              type={achievement.type}
                              size="lg"
                              unlocked={achievement.unlocked}
                            />
                          </ShinyLedFrame>
                        ) : (
                          <div className="w-24 h-24 bg-gray-200 rounded-full mx-auto animate-pulse" />
                        )}
                      </button>
                    </PopoverTrigger>

                    <PopoverContent
                      className="w-80 bg-white border border-gray-200 shadow-lg"
                      side="top"
                      align="center"
                    >
                      <div className="space-y-3">
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
                          {achievement.unlocked && (
                            <div className="flex items-center gap-1 text-xs text-green-600 font-medium">
                              <span>✨</span> Achieved!
                            </div>
                          )}
                        </div>

                        <p className="text-sm text-gray-600">
                          {achievement.description}
                        </p>

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
                            />
                          </div>
                        </div>
                      </div>
                    </PopoverContent>
                  </Popover>

                  <h3 className="text-sm font-bold text-gray-800">
                    {achievement.title}
                  </h3>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}

export default Achievements;
