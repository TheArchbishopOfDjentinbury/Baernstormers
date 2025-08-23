interface QuizProgressProps {
  currentQuestion: number;
  totalQuestions: number;
}

const QuizProgress = ({ currentQuestion, totalQuestions }: QuizProgressProps) => {
  const progressPercentage = ((currentQuestion + 1) / totalQuestions) * 100;

  return (
    <div className="mb-6 animate-fade-in-delay-2">
      <div className="flex justify-between text-sm text-brand-secondary/70 mb-2">
        <span className="animate-slide-right">
          Question {currentQuestion + 1} of {totalQuestions}
        </span>
        <span className="animate-slide-left">
          {Math.round(progressPercentage)}%
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-brand-primary h-2 rounded-full transition-all duration-500 ease-out"
          style={{
            width: `${progressPercentage}%`,
          }}
        ></div>
      </div>
    </div>
  );
};

export default QuizProgress;
