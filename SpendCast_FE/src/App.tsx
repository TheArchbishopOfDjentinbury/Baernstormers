import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';
import { useState } from 'react';
import Header from './components/Header';
import Chat from './pages/Chat';
import Achievements from './pages/Achievements';
import Quiz from './pages/Quiz';
import Podcast from './pages/Podcast';

function App() {
  const [hasCompletedQuiz, setHasCompletedQuiz] = useState(false);

  // Start with July, switch to August after quiz completion
  const currentMonth = hasCompletedQuiz ? '2024-08' : '2024-07';

  const handleQuizCompletion = () => {
    setHasCompletedQuiz(true);
  };

  return (
    <Router>
      <div className="h-screen bg-white flex flex-col overflow-hidden">
        {/* Fixed Header */}
        <div className="flex-shrink-0">
          <Header />
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-hidden">
          <Routes>
            <Route path="/" element={<Navigate to="/chat" replace />} />
            <Route path="/chat" element={<Chat />} />
            <Route
              path="/achievements"
              element={<Achievements selectedMonth={currentMonth} />}
            />
            <Route
              path="/quiz"
              element={<Quiz onQuizComplete={handleQuizCompletion} />}
            />
            <Route path="/podcast" element={<Podcast />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
