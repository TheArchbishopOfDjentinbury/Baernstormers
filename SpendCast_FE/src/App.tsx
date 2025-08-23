import Achievement from '@/components/Achievement';
import beer from '@/assets/beer.json';
import healthyFood from '@/assets/healthy-food.json';
import transport from '@/assets/transport.json';
import coffee from '@/assets/coffee.json';
import swiss from '@/assets/swiss.json';

function App() {
  const achievements = [
    {
      id: 1,
      title: 'Alcohol Master',
      description: 'Drink 5 beers in a week',
      progress: 4,
      total: 5,
      icon: beer,
    },
    {
      id: 2,
      title: 'Healthy Eating Master',
      description: 'Complete 5 healthy meals in a week',
      progress: 4,
      total: 5,
      icon: healthyFood,
    },
    {
      id: 3,
      title: 'Transport Master',
      description: 'Travel 500 km in a week',
      progress: 4,
      total: 5,
      icon: transport,
    },
    {
      id: 4,
      title: 'Coffee Master',
      description: 'Drink 5 coffees in a week',
      progress: 4,
      total: 5,
      icon: coffee,
    },
    {
      id: 5,
      title: 'Swiss Master',
      description: 'Travel to Switzerland in a week',
      progress: 4,
      total: 5,
      icon: swiss,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-4">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-3">
          🏆 Achievement Hub
        </h1>
        <p className="text-lg text-gray-600">
          Track your progress and unlock rewards
        </p>
      </div>

      {/* Single column achievements */}
      <div className="max-w-md mx-auto space-y-6">
        {achievements.map((achievement) => (
          <Achievement key={achievement.id} icon={achievement.icon} />
        ))}
      </div>
    </div>
  );
}

export default App;
