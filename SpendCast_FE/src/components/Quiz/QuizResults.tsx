import { useNavigate } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBrain } from '@fortawesome/free-solid-svg-icons';
import { Button } from '@/components/ui/button';

interface QuizResultsProps {
  score: number;
  totalQuestions: number;
}

const QuizResults = ({ score, totalQuestions }: QuizResultsProps) => {
  const navigate = useNavigate();

  const getScoreMessage = () => {
    const percentage = (score / totalQuestions) * 100;
    if (percentage >= 80) return "You truly understand your financial story! SpendCast sees a conscious consumer with amazing values!";
    if (percentage >= 60)
      return 'Great insights! You\'re connecting with your spending patterns in a meaningful way!';
    if (percentage >= 40)
      return 'Your financial journey is unique! SpendCast is here to help you discover more insights!';
    return 'Every financial story is worth telling! Let SpendCast help you uncover the patterns in your spending!';
  };

  return (
    <main className="px-4 py-8 pb-24">
      <div className="max-w-2xl mx-auto text-center">
        <div className="mb-8 animate-fade-in">
          <FontAwesomeIcon icon={faBrain} className="text-brand-primary mx-auto mb-8 animate-pulse-gentle" style={{width: '8rem', height: '8rem'}} />
          <h2 className="text-3xl font-bold text-brand-secondary mb-4 animate-slide-up">
            Your Financial Story Revealed!
          </h2>
        </div>

        <div className="bg-brand-tertiary p-8 rounded-xl mb-8 animate-scale-in transition-all duration-300">
          <div className="text-6xl font-bold text-brand-secondary mb-2 animate-count-up">
            {score}/{totalQuestions}
          </div>
          <div className="text-xl text-brand-secondary/70 mb-4 animate-fade-in-delay">
            {Math.round((score / totalQuestions) * 100)}% Correct
          </div>
          <p className="text-lg text-brand-secondary animate-fade-in-delay-2">
            {getScoreMessage()}
          </p>
        </div>

        <Button
          onClick={() => navigate('/achievements')}
          className="bg-brand-primary text-brand-secondary hover:bg-brand-primary/90 px-8 py-3 animate-fade-in-delay-3 transform hover:scale-105 transition-all duration-200 shadow-md hover:shadow-lg"
        >
          Go to Achievements
        </Button>
      </div>
    </main>
  );
};

export default QuizResults;
