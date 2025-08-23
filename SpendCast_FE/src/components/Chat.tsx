import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Mic, MicOff } from 'lucide-react';
import ChatLoader from '@/components/ChatLoader';
import {
  useStreamingResponse,
  type StreamingMessage,
} from '@/hooks/useStreamingResponse';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  type: 'text' | 'voice';
  isStreaming?: boolean;
}

const Chat: React.FC = () => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingError, setRecordingError] = useState<string | null>(null);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Random GIF selection
  const gifs = ['crying_1.gif', 'crying_2.gif', 'crying_3.gif'];
  const [randomGif] = useState(
    () => gifs[Math.floor(Math.random() * gifs.length)]
  );

  // Streaming response hook
  const {
    isStreaming,
    sendMessage: sendStreamingMessage,
    sendAudio: sendStreamingAudio,
  } = useStreamingResponse(
    // onMessageUpdate - called for each chunk
    (streamingMessage: StreamingMessage) => {
      // Hide loader when first chunk arrives
      setIsWaitingForResponse(false);

      setMessages((prev) => {
        const existingIndex = prev.findIndex(
          (msg) => msg.id === streamingMessage.id
        );
        if (existingIndex >= 0) {
          // Update existing streaming message
          const updated = [...prev];
          updated[existingIndex] = streamingMessage;
          return updated;
        } else {
          // Add new streaming message
          return [...prev, streamingMessage];
        }
      });
    },
    // onMessageComplete - called when streaming is done
    (finalMessage: StreamingMessage) => {
      setMessages((prev) => {
        const existingIndex = prev.findIndex(
          (msg) => msg.id === finalMessage.id
        );
        if (existingIndex >= 0) {
          const updated = [...prev];
          updated[existingIndex] = finalMessage;
          return updated;
        }
        return prev;
      });
    },
    // onError - called on error
    (error: string) => {
      // Hide loader on error
      setIsWaitingForResponse(false);

      const errorMessage: Message = {
        id: Date.now().toString(),
        text: `Error: ${error}`,
        sender: 'bot',
        timestamp: new Date(),
        type: 'text',
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  );

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop();
      }
    };
  }, [isRecording]);

  const addUserMessage = (text: string, type: 'text' | 'voice' = 'text') => {
    const newMessage: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
      timestamp: new Date(),
      type,
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isStreaming && !isWaitingForResponse) {
      const messageText = message.trim();
      // Add user message immediately
      addUserMessage(messageText);
      // Clear input
      setMessage('');
      // Show loader
      setIsWaitingForResponse(true);
      // Send to backend with streaming
      await sendStreamingMessage(messageText);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(e);
    }
  };

  const startRecording = async () => {
    try {
      setRecordingError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        try {
          const audioBlob = new Blob(audioChunksRef.current, {
            type: 'audio/wav',
          });

          // Add placeholder message for user
          addUserMessage('🎤 Voice message (recorded)', 'voice');

          // Show loader
          setIsWaitingForResponse(true);

          // Send audio to backend with streaming
          await sendStreamingAudio(audioBlob);
        } catch (error) {
          console.error('Error processing audio:', error);
          const errorMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: 'Sorry, I could not process your voice message.',
            sender: 'bot',
            timestamp: new Date(),
            type: 'text',
          };
          setMessages((prev) => [...prev, errorMessage]);
        }

        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      setRecordingError('Не удалось получить доступ к микрофону');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleRightButton = () => {
    if (message.trim()) {
      handleSend({ preventDefault: () => {} } as React.FormEvent);
    } else {
      toggleRecording();
    }
  };

  const handleExampleClick = (exampleText: string) => {
    // Remove quotes from the example text and set it in the input
    const cleanText = exampleText.replace(/"/g, '');
    setMessage(cleanText);
  };

  return (
    <>
      {/* Scrollable Messages area - with bottom padding for fixed input */}
      <div className="h-full overflow-y-auto p-4 pb-32">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-8 px-4">
              {/* Welcome title first */}
              <h3 className="text-xl font-semibold text-brand-secondary mb-6">
                Let's talk about your spending!
              </h3>

              {/* Random GIF - full width */}
              <div className="mb-6">
                <img
                  src={`/${randomGif}`}
                  alt="Welcome"
                  className="w-full max-w-md mx-auto h-48 object-cover rounded-lg shadow-lg"
                />
              </div>

              {/* Description and examples */}
              <div className="space-y-4">
                <p className="text-brand-secondary/70 text-base max-w-md mx-auto">
                  I'm here to help you understand your spending habits. Ask me
                  anything about your spending patterns and expenses!
                </p>
                <div className="flex flex-wrap justify-center gap-2 text-sm text-brand-secondary/60 mt-6">
                  <button
                    onClick={() =>
                      handleExampleClick('How much did I spend on coffee?')
                    }
                    className="bg-gray-100 px-3 py-1 rounded-full hover:bg-gray-200 transition-colors cursor-pointer"
                  >
                    "How much did I spend on coffee?"
                  </button>
                  <button
                    onClick={() =>
                      handleExampleClick('Show my monthly spending')
                    }
                    className="bg-gray-100 px-3 py-1 rounded-full hover:bg-gray-200 transition-colors cursor-pointer"
                  >
                    "Show my monthly spending"
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${
                    msg.sender === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-[70%] px-4 py-2 ${
                      msg.sender === 'user'
                        ? 'bg-brand-secondary text-white rounded-2xl rounded-tr-sm'
                        : 'bg-gray-100 text-gray-800 rounded-2xl rounded-tl-sm'
                    }`}
                  >
                    <p className="text-base">
                      {msg.text}
                      {msg.isStreaming && (
                        <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse">
                          |
                        </span>
                      )}
                    </p>
                    <p className="text-xs opacity-70 mt-1">
                      {msg.timestamp.toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                      {msg.isStreaming && (
                        <span className="ml-2 text-blue-500">typing...</span>
                      )}
                    </p>
                  </div>
                </div>
              ))}

              {/* Chat Loader */}
              {isWaitingForResponse && <ChatLoader className="mb-4" />}

              {/* Invisible element to scroll to */}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Fixed chat input at bottom of viewport */}
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-brand-primary border-t border-brand-secondary/20 shadow-lg">
        {/* Error message */}
        {recordingError && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 mx-4 rounded mb-2">
            {recordingError}
          </div>
        )}

        {/* Chat input container */}
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
                      isRecording
                        ? 'Recording...'
                        : 'Ask about your spending...'
                    }
                    disabled={isRecording}
                    className="resize-none min-h-[48px] max-h-32 rounded-xl border border-brand-secondary/30 shadow-sm transition-all duration-200 focus:border-brand-secondary focus:shadow-md text-base px-4 py-3"
                    style={{
                      background: isRecording
                        ? 'rgba(255,255,255,0.7)'
                        : 'white',
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
                  ) : isRecording ? (
                    <MicOff className="h-5 w-5 text-white animate-pulse" />
                  ) : (
                    <Mic className="h-5 w-5 text-white" />
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
};

export default Chat;
