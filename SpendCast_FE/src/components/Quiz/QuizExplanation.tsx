interface QuizExplanationProps {
  explanation: string;
  isTransitioning: boolean;
}

const QuizExplanation = ({ explanation, isTransitioning }: QuizExplanationProps) => {
  return (
    <div className={`relative bg-gradient-to-r from-blue-50 to-indigo-50 p-6 mb-6 overflow-hidden ${
      isTransitioning ? 'question-transition-out' : 'question-transition-in animate-slide-up'
    }`}>
      <div className="absolute top-0 right-0 w-20 h-20 bg-brand-primary/5 rounded-full -translate-y-4 translate-x-4"></div>
      <div className="absolute bottom-0 left-0 w-16 h-16 bg-indigo-200/20 rounded-full translate-y-4 -translate-x-4"></div>
      <div className="relative z-10">
        <div className="flex items-center mb-3">
          <div className="w-2 h-2 bg-brand-primary rounded-full mr-2 animate-pulse"></div>
          <h4 className="font-semibold text-brand-secondary text-lg animate-fade-in">Why this matters:</h4>
        </div>
        <p className="text-brand-secondary/80 leading-relaxed text-base animate-fade-in-delay">
          {explanation}
        </p>
      </div>
    </div>
  );
};

export default QuizExplanation;
