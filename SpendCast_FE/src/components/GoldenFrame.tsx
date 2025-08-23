import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface MetalFrameProps {
  children: ReactNode;
  className?: string;
}

const MetalFrame: React.FC<MetalFrameProps> = ({
  children,
  className = '',
}) => {
  return (
    <div className={`relative inline-block ${className}`}>
      {/* Outer metallic ring */}
      <motion.div
        className="absolute inset-0 rounded-full"
        style={{
          background: `conic-gradient(from 0deg, 
            #C0C0C0 0%, 
            #808080 25%, 
            #E8E8E8 50%, 
            #A0A0A0 75%, 
            #C0C0C0 100%)`,
          padding: '3px',
        }}
        animate={{
          rotate: [0, 360],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: 'linear',
        }}
      >
        <div className="w-full h-full rounded-full bg-white" />
      </motion.div>

      {/* Inner metallic border */}
      <motion.div
        className="absolute inset-0 rounded-full border-2"
        style={{
          borderColor: '#C0C0C0',
          boxShadow: `
            0 0 8px #C0C0C060,
            inset 0 0 8px #80808030,
            0 2px 4px #00000020
          `,
        }}
        animate={{
          boxShadow: [
            '0 0 8px #C0C0C060, inset 0 0 8px #80808030, 0 2px 4px #00000020',
            '0 0 12px #E8E8E8aa, inset 0 0 12px #A0A0A050, 0 4px 8px #00000030',
            '0 0 8px #C0C0C060, inset 0 0 8px #80808030, 0 2px 4px #00000020',
          ],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      />

      {/* Metallic shine effect */}
      <motion.div
        className="absolute inset-0 rounded-full"
        style={{
          background: `linear-gradient(120deg, 
            transparent 0%, 
            transparent 40%, 
            #FFFFFF60 50%, 
            transparent 60%, 
            transparent 100%)`,
        }}
        animate={{
          rotate: [0, 360],
        }}
        transition={{
          duration: 6,
          repeat: Infinity,
          ease: 'linear',
        }}
      />

      {/* Secondary shine */}
      <motion.div
        className="absolute inset-0 rounded-full"
        style={{
          background: `linear-gradient(60deg, 
            transparent 0%, 
            transparent 70%, 
            #FFFFFF30 75%, 
            transparent 80%, 
            transparent 100%)`,
        }}
        animate={{
          rotate: [360, 0],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: 'linear',
        }}
      />

      {/* Achievement content */}
      <div className="relative z-10">{children}</div>
    </div>
  );
};

export default MetalFrame;
