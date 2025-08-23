import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCoins, faDollarSign, faCreditCard, faWallet } from '@fortawesome/free-solid-svg-icons';

const FloatingIcons = () => {
  const icons = [faCoins, faDollarSign, faCreditCard, faWallet];
  const colors = ['#FFD700', '#32CD32', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD'];
  const floatingIcons = [];
  
  // Shuffle icons to ensure uniqueness
  const shuffledIcons = [...icons].sort(() => Math.random() - 0.5);
  
  for (let i = 0; i < 4; i++) {
    const icon = shuffledIcons[i]; // Use unique icon for each position
    const color = colors[Math.floor(Math.random() * colors.length)];
    const animationClass = `float-${(i % 3) + 1}`;
    const size = Math.random() * 6 + 14; // 14-20px
    const delay = Math.random() * 10; // 0-10s delay
    const left = Math.random() * 100; // random horizontal position
    
    floatingIcons.push(
      <FontAwesomeIcon
        key={i}
        icon={icon}
        className={`floating-icon ${animationClass}`}
        style={{
          fontSize: `${size}px`,
          left: `${left}%`,
          animationDelay: `${delay}s`,
          color: color,
        }}
      />
    );
  }
  
  return <>{floatingIcons}</>;
};

export default FloatingIcons;
