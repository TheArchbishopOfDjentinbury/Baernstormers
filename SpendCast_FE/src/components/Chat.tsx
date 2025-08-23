import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Mic } from 'lucide-react';

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

  const handleRightButton = () => {
    if (message.trim()) {
      handleSend({ preventDefault: () => {} } as React.FormEvent);
    } else {
      toggleRecording();
    }
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50">
      {/* Simple yellow background */}
      <div className="bg-brand-primary border-t border-brand-secondary/20 shadow-lg">
        {/* Recording indicator */}
        {isRecording && (
          <div className="flex items-center justify-center py-2 text-sm text-brand-secondary">
            <div className="flex space-x-1 mr-2">
              <div className="w-2 h-2 bg-brand-secondary rounded-full animate-bounce"></div>
              <div
                className="w-2 h-2 bg-brand-secondary rounded-full animate-bounce"
                style={{ animationDelay: '0.1s' }}
              ></div>
              <div
                className="w-2 h-2 bg-brand-secondary rounded-full animate-bounce"
                style={{ animationDelay: '0.2s' }}
              ></div>
            </div>
            <span>Recording...</span>
          </div>
        )}

        {/* Chat input area */}
        <div className="px-4 py-4 pb-safe-area-inset-bottom">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto">
            <div className="flex items-end gap-3">
              {/* Message input - LEFT (takes most space) */}
              <div className="flex-1">
                <Textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder={
                    isRecording ? 'Recording...' : 'Ask about your spending...'
                  }
                  disabled={isRecording}
                  className="resize-none min-h-[48px] max-h-32 rounded-xl border border-brand-secondary/30 shadow-sm transition-all duration-200 focus:border-brand-secondary focus:shadow-md text-base px-4 py-3"
                  style={{
                    background: isRecording ? 'rgba(255,255,255,0.7)' : 'white',
                    color: '#004b5a',
                  }}
                  rows={1}
                />
              </div>

              {/* Send/Mic button - RIGHT */}
              <Button
                type="button"
                onClick={handleRightButton}
                size="icon"
                className="shrink-0 rounded-xl h-12 w-12 shadow-sm transition-all duration-200 hover:shadow-md"
                style={{
                  background: message.trim()
                    ? '#004b5a' // Dark teal for send
                    : isRecording
                    ? '#006b7a' // Lighter teal for recording
                    : '#004b5a', // Dark teal for mic
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
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Chat;
