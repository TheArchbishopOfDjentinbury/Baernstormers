import Lottie from 'lottie-react';

interface AchievementProps {
  icon: unknown;
  type?: 'good' | 'medium' | 'bad';
  size?: 'sm' | 'md' | 'lg';
  unlocked?: boolean;
}

const Achievement = ({
  icon,
  type = 'good',
  size = 'md',
  unlocked = false,
}: AchievementProps) => {
  // Color schemes for different achievement types
  const colorSchemes = {
    good: unlocked ? '#10B981' : '#D1FAE5', // Green
    medium: unlocked ? '#F59E0B' : '#FEF3C7', // Orange
    bad: unlocked ? '#EF4444' : '#FEE2E2', // Red
  };

  // Size configurations
  const sizes = {
    sm: { height: '60px', width: '60px', padding: '8px' },
    md: { height: '80px', width: '80px', padding: '10px' },
    lg: { height: '100px', width: '100px', padding: '12px' },
  };

  return (
    <div className="relative">
      <Lottie
        animationData={icon}
        loop={true}
        autoplay={true}
        style={{
          backgroundColor: colorSchemes[type],
          ...sizes[size],
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto',
          transition: 'all 0.3s ease',
        }}
      />
    </div>
  );
};

export default Achievement;
