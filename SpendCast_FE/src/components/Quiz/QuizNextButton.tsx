import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowRight } from '@fortawesome/free-solid-svg-icons';
import { Button } from '@/components/ui/button';

interface QuizNextButtonProps {
  currentQuestion: number;
  totalQuestions: number;
  isTransitioning: boolean;
  onNext: () => void;
}

const QuizNextButton = ({ 
  currentQuestion, 
  totalQuestions, 
  isTransitioning, 
  onNext 
}: QuizNextButtonProps) => {
  return (
    <div className={`text-center next-button-container ${
      isTransitioning ? 'question-transition-out' : 'question-transition-in animate-fade-in-delay'
    }`}>
      <Button
        onClick={onNext}
        className="bg-brand-secondary text-white hover:bg-brand-secondary/90 px-6 py-3 transform hover:scale-105 transition-all duration-200 shadow-md hover:shadow-lg animate-bounce-gentle"
      >
        {currentQuestion < totalQuestions - 1 ? (
          <>
            Next Question
            <FontAwesomeIcon icon={faArrowRight} className="ml-2 h-4 w-4" />
          </>
        ) : (
          'See Results'
        )}
      </Button>
    </div>
  );
};

export default QuizNextButton;
