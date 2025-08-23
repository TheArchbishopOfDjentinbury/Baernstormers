import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Mic, Plus } from 'lucide-react';

const Chat: React.FC = () => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      // Handle sending message
      setMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(e);
    }
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50">
      {/* Glassmorphism background with gradient */}
      <div
        className="backdrop-blur-xl border-t border-brand-secondary/20 shadow-2xl"
        style={{
          background:
            'linear-gradient(to top, rgba(238,246,246,0.95), rgba(238,246,246,0.90), transparent)',
        }}
      >
        {/* Safe area padding for mobile */}
        <div className="px-4 pt-3 pb-safe-area-inset-bottom">
          <form
            onSubmit={handleSend}
            className="flex items-end gap-3 max-w-4xl mx-auto"
          >
            {/* Attachment button */}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="shrink-0 rounded-full h-11 w-11 border border-brand-secondary/20 shadow-lg transition-all duration-200 hover:scale-105"
              style={{
                background: 'rgba(238,246,246,0.8)',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(238,246,246,1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(238,246,246,0.8)';
              }}
            >
              <Plus className="h-5 w-5 text-brand-secondary" />
            </Button>

            {/* Message input container */}
            <div className="flex-1 relative">
              <Textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask about your spending..."
                className="resize-none min-h-[44px] max-h-32 rounded-2xl border-brand-secondary/30 shadow-lg backdrop-blur-sm transition-all duration-200 focus:border-brand-primary focus:shadow-xl pr-12"
                style={{
                  background: 'rgba(255,255,255,0.9)',
                  color: '#004b5a',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.background = 'rgba(255,255,255,1)';
                  e.currentTarget.style.borderColor = '#ffcc00';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.9)';
                  e.currentTarget.style.borderColor = 'rgba(0,75,90,0.3)';
                }}
                rows={1}
              />

              {/* Character counter for mobile UX */}
              {message.length > 100 && (
                <div className="absolute -top-6 right-2 text-xs text-brand-secondary/60">
                  {message.length}/500
                </div>
              )}
            </div>

            {/* Voice/Send button */}
            <Button
              type={message.trim() ? 'submit' : 'button'}
              onClick={message.trim() ? undefined : toggleRecording}
              size="icon"
              className="shrink-0 rounded-full h-11 w-11 shadow-lg transition-all duration-300 hover:scale-105"
              style={{
                background: message.trim()
                  ? 'linear-gradient(135deg, #ffcc00, #004b5a)' // Yellow to dark teal
                  : isRecording
                  ? 'linear-gradient(135deg, #ef4444, #ec4899)' // Keep red for recording
                  : 'linear-gradient(135deg, #004b5a, #eef6f6)', // Dark teal to light mint
                animation: isRecording
                  ? 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite'
                  : 'none',
              }}
              onMouseEnter={(e) => {
                if (message.trim()) {
                  e.currentTarget.style.background =
                    'linear-gradient(135deg, #e6b800, #003a47)'; // Darker brand colors
                } else if (isRecording) {
                  e.currentTarget.style.background =
                    'linear-gradient(135deg, #dc2626, #db2777)';
                } else {
                  e.currentTarget.style.background =
                    'linear-gradient(135deg, #003a47, #d9eded)'; // Darker teal to lighter mint
                }
              }}
              onMouseLeave={(e) => {
                if (message.trim()) {
                  e.currentTarget.style.background =
                    'linear-gradient(135deg, #ffcc00, #004b5a)';
                } else if (isRecording) {
                  e.currentTarget.style.background =
                    'linear-gradient(135deg, #ef4444, #ec4899)';
                } else {
                  e.currentTarget.style.background =
                    'linear-gradient(135deg, #004b5a, #eef6f6)';
                }
              }}
            >
              {message.trim() ? (
                <Send className="h-5 w-5 text-white" />
              ) : (
                <Mic
                  className={`h-5 w-5 text-white ${
                    isRecording ? 'animate-pulse' : ''
                  }`}
                />
              )}
            </Button>
          </form>

          {/* Recording indicator */}
          {isRecording && (
            <div className="flex items-center justify-center mt-2 text-sm text-brand-secondary/70">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-bounce"></div>
                <div
                  className="w-2 h-2 bg-red-500 rounded-full animate-bounce"
                  style={{ animationDelay: '0.1s' }}
                ></div>
                <div
                  className="w-2 h-2 bg-red-500 rounded-full animate-bounce"
                  style={{ animationDelay: '0.2s' }}
                ></div>
              </div>
              <span className="ml-2">Recording...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Chat;
