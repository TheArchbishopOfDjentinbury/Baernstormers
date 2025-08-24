import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Send, Mic, MicOff } from 'lucide-react';
import ChatLoader from '@/components/Chat/ChatLoader';
import AudioPlayer from '@/components/AudioPlayer';
import { WebMAudioRecorder, audioUtils } from '@/utils/audioRecorder';
import { useChatResponse, type ChatMessage } from '@/hooks/useChatResponse';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  type: 'text' | 'voice';
  audioContent?: string;
}

const Chat: React.FC = () => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingError, setRecordingError] = useState<string | null>(null);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [responseAsAudio, setResponseAsAudio] = useState(true);
  const mp3RecorderRef = useRef<WebMAudioRecorder | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const gifs = ['crying_1.gif', 'crying_2.gif', 'crying_3.gif'];
  const [randomGif] = useState(
    () => gifs[Math.floor(Math.random() * gifs.length)]
  );

  const { sendMessage: sendChatMessage } = useChatResponse(
    (chatMessage: ChatMessage) => {
      setIsWaitingForResponse(false);

      const message: Message = {
        id: chatMessage.id,
        text: chatMessage.text,
        sender: chatMessage.sender,
        timestamp: chatMessage.timestamp,
        type: chatMessage.type,
        audioContent: chatMessage.audioContent,
      };

      setMessages((prev) => [...prev, message]);
    },
    (error: string) => {
      setIsWaitingForResponse(false);

      const errorMessage: Message = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        text: `Error: ${error}`,
        sender: 'bot',
        timestamp: new Date(),
        type: 'text',
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  );

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    return () => {
      if (mp3RecorderRef.current) {
        mp3RecorderRef.current.stopRecording();
      }
    };
  }, []);

  const addUserMessage = (text: string, type: 'text' | 'voice' = 'text') => {
    const newMessage: Message = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      text,
      sender: 'user',
      timestamp: new Date(),
      type,
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isWaitingForResponse) {
      const messageText = message.trim();
      addUserMessage(messageText);
      setMessage('');
      setIsWaitingForResponse(true);
      await sendChatMessage(messageText, false, responseAsAudio);
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

      if (!audioUtils.checkSupport()) {
        throw new Error('Audio recording not supported');
      }

      const recorder = new WebMAudioRecorder();
      mp3RecorderRef.current = recorder;

      await recorder.startRecording();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting MP3 recording:', error);
      setRecordingError('Failed to start recording');
    }
  };

  const stopRecording = async () => {
    try {
      if (!mp3RecorderRef.current || !isRecording) {
        return;
      }

      setIsRecording(false);

      const mp3Blob = await mp3RecorderRef.current.stopRecording();

      const base64Audio = await audioUtils.toBase64(mp3Blob);

      console.log('🎤 MP3 recorded:', {
        size: mp3Blob.size,
        type: mp3Blob.type,
        base64Length: base64Audio.length,
      });

      console.log('🔊 Voice message settings:', {
        responseAsAudio: responseAsAudio,
        includeAudio: true,
        messageType: 'voice',
      });

      console.log('📤 Sending voice message to backend:', {
        messageType: 'base64 audio',
        includeAudio: true,
        responseAsAudio: responseAsAudio,
        audioDataPreview: base64Audio.substring(0, 100) + '...',
        fullAudioLength: base64Audio.length,
      });

      addUserMessage('🎤 Voice message (MP3)', 'voice');

      setIsWaitingForResponse(true);

      await sendChatMessage(base64Audio, true, responseAsAudio);
    } catch (error) {
      console.error('Error processing MP3 audio:', error);
      setRecordingError('Failed to process recording');

      const errorMessage: Message = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        text: 'Sorry, I could not process your voice message.',
        sender: 'bot',
        timestamp: new Date(),
        type: 'text',
      };
      setMessages((prev) => [...prev, errorMessage]);
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
    const cleanText = exampleText.replace(/"/g, '');
    setMessage(cleanText);
  };

  return (
    <>
      <div className="h-full overflow-y-auto p-4 pb-32">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-8 px-4">
              <h3 className="text-xl font-semibold text-brand-secondary mb-6">
                Let's talk about your spending!
              </h3>

              <div className="mb-6">
                <img
                  src={`/${randomGif}`}
                  alt="Welcome"
                  className="w-full max-w-md mx-auto h-48 object-cover rounded-lg shadow-lg"
                />
              </div>

              <div className="space-y-4">
                <p className="text-brand-secondary/70 text-base max-w-md mx-auto">
                  I'm here to help you understand your spending habits. Ask me
                  anything about your spending patterns and expenses!
                </p>
                <div className="flex flex-wrap justify-center gap-2 text-sm text-brand-secondary/60 mt-6">
                  <button
                    onClick={() =>
                      handleExampleClick(
                        'How much did I spend on coffee in 2025?'
                      )
                    }
                    className="bg-gray-100 px-3 py-1 rounded-full hover:bg-gray-200 transition-colors cursor-pointer"
                  >
                    "How much did I spend on coffee in 2025?"
                  </button>
                  <button
                    onClick={() =>
                      handleExampleClick('Show my monthly spending in 2025')
                    }
                    className="bg-gray-100 px-3 py-1 rounded-full hover:bg-gray-200 transition-colors cursor-pointer"
                  >
                    "Show my monthly spending in 2025"
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
                    <p className="text-base">{msg.text}</p>

                    {msg.audioContent && (
                      <div className="mt-2">
                        <AudioPlayer
                          base64Audio={msg.audioContent}
                          minimal={true}
                        />
                      </div>
                    )}
                    <p className="text-xs opacity-70 mt-1">
                      {msg.timestamp.toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                </div>
              ))}

              {isWaitingForResponse && <ChatLoader className="mb-4" />}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      <div className="fixed bottom-0 left-0 right-0 z-50 bg-brand-primary border-t border-brand-secondary/20 shadow-lg">
        {recordingError && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 mx-4 rounded mb-2">
            {recordingError}
          </div>
        )}

        <div className="bg-white px-4 py-3">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <span className="text-base text-gray-700">
              Response me as audio
            </span>
            <Switch
              checked={responseAsAudio}
              onCheckedChange={setResponseAsAudio}
            />
          </div>
        </div>

        <div className="bg-brand-primary border-t border-brand-secondary/20 shadow-lg">
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

          <div className="px-4 py-4 pb-safe-area-inset-bottom">
            <form onSubmit={handleSend} className="max-w-4xl mx-auto">
              <div className="flex items-end gap-3">
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

                <Button
                  type="button"
                  onClick={handleRightButton}
                  size="icon"
                  className="shrink-0 rounded-xl h-12 w-12 shadow-sm transition-all duration-200 hover:shadow-md"
                  style={{
                    background: message.trim()
                      ? '#004b5a'
                      : isRecording
                      ? '#006b7a'
                      : '#004b5a',
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
