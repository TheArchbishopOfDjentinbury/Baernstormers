import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface ChatLoaderProps {
  className?: string;
}

const ChatLoader: React.FC<ChatLoaderProps> = ({ className = '' }) => {
  const [messageIndex, setMessageIndex] = useState(0);

  // Simple loading messages
  const loadingMessages = [
    'Looking for a smart person to answer...',
    'Analyzing your spending data...',
    'Thinking really hard...',
  ];

  // Rotate messages every 5 seconds
  useEffect(() => {
    const messageInterval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % loadingMessages.length);
    }, 5000);

    return () => clearInterval(messageInterval);
  }, [loadingMessages.length]);

  return (
    <div className={`flex justify-start ${className}`}>
      <motion.div
        className="max-w-[70%] px-4 py-2 bg-gray-100 text-gray-800 rounded-2xl rounded-tl-sm relative overflow-hidden"
        animate={{
          opacity: [1, 0.7, 1],
        }}
        transition={{
          duration: 1.5,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      >
        {/* Shimmer effect overlay */}
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/60 to-transparent"
          animate={{
            x: ['-100%', '100%'],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'linear',
          }}
        />

        {/* Message text */}
        <motion.p
          className="text-base relative z-10"
          key={messageIndex}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          {loadingMessages[messageIndex]}
        </motion.p>
      </motion.div>
    </div>
  );
};

export default ChatLoader;
