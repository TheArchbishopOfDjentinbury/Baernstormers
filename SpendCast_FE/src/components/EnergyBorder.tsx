import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface EnergyBorderProps {
  children: ReactNode;
  type: 'good' | 'medium' | 'bad';
  isActive?: boolean;
}

const EnergyBorder: React.FC<EnergyBorderProps> = ({
  children,
  type,
  isActive = true,
}) => {
  // Energy colors based on achievement type
  const energyColors = {
    good: {
      primary: '#10B981', // Green
      secondary: '#34D399',
      glow: '#6EE7B7',
    },
    medium: {
      primary: '#F59E0B', // Orange
      secondary: '#FBBF24',
      glow: '#FCD34D',
    },
    bad: {
      primary: '#EF4444', // Red
      secondary: '#F87171',
      glow: '#FCA5A5',
    },
  };

  const colors = energyColors[type];

  return (
    <div className="relative inline-block">
      {isActive && (
        <>
          {/* Primary energy flow */}
          <motion.div
            className="absolute rounded-full"
            style={{
              inset: '-5px',
              background: `conic-gradient(from 0deg, 
                ${colors.primary}ff 0%, 
                ${colors.secondary}ff 25%, 
                ${colors.primary}ff 50%, 
                ${colors.secondary}ff 75%, 
                ${colors.primary}ff 100%)`,
              filter: `blur(0.5px) brightness(1.3)`,
            }}
            animate={{
              rotate: [0, 360],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: 'linear',
            }}
          />

          {/* Secondary counter-rotating energy */}
          <motion.div
            className="absolute rounded-full"
            style={{
              inset: '-3px',
              background: `conic-gradient(from 180deg, 
                transparent 0%, 
                ${colors.glow}cc 20%, 
                ${colors.primary}ff 40%, 
                ${colors.glow}cc 60%, 
                transparent 80%)`,
              filter: `blur(1px)`,
            }}
            animate={{
              rotate: [360, 0],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'linear',
            }}
          />

          {/* Intense inner glow */}
          <motion.div
            className="absolute rounded-full border-2"
            style={{
              inset: '-2px',
              borderColor: colors.primary,
              background: `radial-gradient(circle, transparent 60%, ${colors.primary}30 100%)`,
              boxShadow: `
                0 0 10px ${colors.primary}ff,
                0 0 20px ${colors.primary}80,
                inset 0 0 10px ${colors.primary}40
              `,
            }}
            animate={{
              boxShadow: [
                `0 0 10px ${colors.primary}ff, 0 0 20px ${colors.primary}80, inset 0 0 10px ${colors.primary}40`,
                `0 0 15px ${colors.primary}ff, 0 0 30px ${colors.primary}ff, inset 0 0 15px ${colors.primary}60`,
                `0 0 10px ${colors.primary}ff, 0 0 20px ${colors.primary}80, inset 0 0 10px ${colors.primary}40`,
              ],
            }}
            transition={{
              duration: 1,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />

          {/* Energy waves */}
          {[...Array(8)].map((_, index) => (
            <motion.div
              key={`wave-${index}`}
              className="absolute"
              style={{
                top: '50%',
                left: '50%',
                width: '2px',
                height: '8px',
                background: `linear-gradient(to top, transparent, ${colors.glow}ff, transparent)`,
                borderRadius: '2px',
                transformOrigin: '1px 50px',
                transform: `rotate(${index * 45}deg)`,
              }}
              animate={{
                scaleY: [0.5, 1.5, 0.5],
                opacity: [0.6, 1, 0.6],
              }}
              transition={{
                duration: 0.8,
                repeat: Infinity,
                delay: index * 0.1,
                ease: 'easeInOut',
              }}
            />
          ))}

          {/* Plasma crackling effect */}
          {[...Array(12)].map((_, index) => (
            <motion.div
              key={`plasma-${index}`}
              className="absolute w-0.5 h-1 rounded-full"
              style={{
                backgroundColor: colors.secondary,
                top: '50%',
                left: '50%',
                transformOrigin: `0.25px ${45 + Math.random() * 10}px`,
                transform: `rotate(${index * 30}deg)`,
              }}
              animate={{
                scaleY: [0, 2, 0],
                opacity: [0, 1, 0],
                rotate: [index * 30, index * 30 + 360],
              }}
              transition={{
                duration: 1.2,
                repeat: Infinity,
                delay: index * 0.05,
                ease: 'easeOut',
              }}
            />
          ))}
        </>
      )}

      {/* Achievement content */}
      <div className="relative z-10">{children}</div>
    </div>
  );
};

export default EnergyBorder;
