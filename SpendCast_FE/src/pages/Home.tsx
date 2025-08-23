import Chat from '@/components/Chat';

function Home() {
  return (
    <div className="min-h-screen bg-white">
      {/* Yellow Header */}
      <header className="bg-brand-primary px-4 py-6 mb-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-brand-secondary text-center">
            SpendCast
          </h1>
          <p className="text-lg text-brand-secondary/80 text-center mt-2">
            Smart spending insights and analysis
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="px-4 pb-24">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-semibold text-brand-secondary mb-4">
              Welcome to SpendCast
            </h2>
            <p className="text-brand-secondary/70">
              Start a conversation to analyze your spending patterns
            </p>
          </div>
        </div>
      </main>

      <Chat />
    </div>
  );
}

export default Home;
