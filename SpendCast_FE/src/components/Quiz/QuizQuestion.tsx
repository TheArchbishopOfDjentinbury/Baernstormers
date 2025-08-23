import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCheckCircle, faTimesCircle } from '@fortawesome/free-solid-svg-icons';
import type { Question } from './types';

interface QuizQuestionProps {
  question: Question;
  selectedAnswer: number | null;
  answered: boolean;
  isTransitioning: boolean;
  onAnswerSelect: (answerIndex: number) => void;
}

const QuizQuestion = ({
  question,
  selectedAnswer,
  answered,
  isTransitioning,
  onAnswerSelect,
}: QuizQuestionProps) => {
  return (
    <div className={`bg-brand-tertiary p-6 rounded-xl mb-6 transition-all duration-300 ${
      isTransitioning ? 'question-transition-out' : 'question-transition-in animate-slide-up'
    }`}>
      <h3 className="text-xl font-semibold text-brand-secondary mb-6 animate-fade-in">
        {question.question}
      </h3>

      <div className="space-y-3">
        {question.options.map((option, index) => {
          let buttonStyle =
            'w-full p-4 text-left border-2 rounded-lg transition-all duration-200 transform hover:scale-[1.02] ';

          if (!answered) {
            buttonStyle +=
              'border-gray-200 hover:border-brand-primary hover:bg-brand-primary/10 hover:text-brand-primary animate-fade-in-stagger';
          } else {
            if (index === question.correctAnswer) {
              buttonStyle +=
                'border-green-500 bg-green-50 text-green-700 animate-success-pulse';
            } else if (
              index === selectedAnswer &&
              index !== question.correctAnswer
            ) {
              buttonStyle += 'border-red-500 bg-red-50 text-red-700 animate-error-shake';
            } else {
              buttonStyle += 'border-gray-200 text-gray-500 animate-fade-out-partial';
            }
          }

          return (
            <button
              key={index}
              onClick={() => onAnswerSelect(index)}
              className={buttonStyle}
              disabled={answered}
            >
              <div className="flex items-center justify-between">
                <span>{option}</span>
                {answered && index === question.correctAnswer && (
                  <FontAwesomeIcon icon={faCheckCircle} className="h-5 w-5 text-green-600" />
                )}
                {answered &&
                  index === selectedAnswer &&
                  index !== question.correctAnswer && (
                    <FontAwesomeIcon icon={faTimesCircle} className="h-5 w-5 text-red-600" />
                  )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default QuizQuestion;
