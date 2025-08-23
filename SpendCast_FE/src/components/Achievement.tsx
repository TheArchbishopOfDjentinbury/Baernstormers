import Lottie from 'lottie-react';

interface AchievementProps {
  icon: unknown;
}

const Achievement = ({ icon }: AchievementProps) => {
  return (
    <Lottie
      animationData={icon}
      loop={true}
      autoplay={true}
      style={{
        backgroundColor: '#2ECC71',
        height: '100px',
        width: '100px',
        padding: '10px',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '0 auto',
      }}
    />
  );
};

export default Achievement;
