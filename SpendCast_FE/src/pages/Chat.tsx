import ChatComponent from '@/components/Chat';

function Chat() {
  return (
    <>
      {/* Main Content */}
      <main className="px-4 py-8 pb-24">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-semibold text-brand-secondary mb-4">
              Chat with SpendCast
            </h2>
            <p className="text-brand-secondary/70">
              Ask questions about your spending patterns and get AI-powered
              insights
            </p>
          </div>
        </div>
      </main>

      <ChatComponent />
    </>
  );
}

export default Chat;
