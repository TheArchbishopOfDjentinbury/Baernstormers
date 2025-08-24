import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';
import Header from './components/Header';
import Chat from './pages/Chat';
import Achievements from './pages/Achievements';
import Quiz from './pages/Quiz';
import Podcast from './pages/Podcast';
import { buildMetrics } from '@/components/achievements/metricfromData';
import type { Metrics } from '@/components/achievements/type';

const metrics = buildMetrics(); // now definitely defined

function App() {
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
            <Route path="/achievements" element={<Achievements metrics={metrics} />} />
            <Route path="/quiz" element={<Quiz />} />
            <Route path="/podcast" element={<Podcast />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
