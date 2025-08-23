import { useState } from 'react';
import {
  animationStyles,
  FloatingIcons,
  QuizProgress,
  QuizQuestion,
  QuizExplanation,
  QuizNextButton,
  QuizResults,
  quizQuestions,
  type QuizState,
} from '../components/Quiz';

export default function Quiz() {
  const [quizState, setQuizState] = useState<QuizState>({
    currentQuestion: 0,
    selectedAnswer: null,
    showResult: false,
    score: 0,
    answered: false,
    isTransitioning: false,
  });

  const handleAnswerSelect = (answerIndex: number) => {
    if (quizState.answered) return;

    setQuizState(prev => {
      const newScore = answerIndex === quizQuestions[prev.currentQuestion].correctAnswer 
        ? prev.score + 1 
        : prev.score;
      
      return {
        ...prev,
        selectedAnswer: answerIndex,
        answered: true,
        score: newScore,
      };
    });

    // Scroll to next button after answer is selected
    setTimeout(() => {
      const nextButton = document.querySelector('.next-button-container');
      if (nextButton) {
        nextButton.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center' 
        });
      }
    }, 500); // Delay to let explanation animate in
  };

  const handleNextQuestion = () => {
    setQuizState(prev => ({ ...prev, isTransitioning: true }));
    
    // Fade out current question
    setTimeout(() => {
      if (quizState.currentQuestion < quizQuestions.length - 1) {
        setQuizState(prev => ({
          ...prev,
          currentQuestion: prev.currentQuestion + 1,
          selectedAnswer: null,
          answered: false,
        }));
      } else {
        setQuizState(prev => ({ ...prev, showResult: true }));
      }
      
      // Fade in new question
      setTimeout(() => {
        setQuizState(prev => ({ ...prev, isTransitioning: false }));
      }, 50);
    }, 300);
  };

  if (quizState.showResult) {
    return (
      <>
        <style>{animationStyles}</style>
        <QuizResults score={quizState.score} totalQuestions={quizQuestions.length} />
      </>
    );
  }

  const currentQ = quizQuestions[quizState.currentQuestion];

  return (
    <>
      <style>{animationStyles}</style>
      <FloatingIcons />
      <main className="px-4 py-8 pb-24">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-8 animate-fade-in">
            <h2 className="text-2xl font-semibold text-brand-secondary mb-4 animate-slide-down">
              Your July 2024 Financial Story
            </h2>
            <p className="text-brand-secondary/70 mb-6 animate-fade-in-delay">
              SpendCast analyzed your spending patterns and found something inspiring. Let's discover your financial personality together!
            </p>

            <QuizProgress 
              currentQuestion={quizState.currentQuestion}
              totalQuestions={quizQuestions.length}
            />
          </div>

          <QuizQuestion
            question={currentQ}
            selectedAnswer={quizState.selectedAnswer}
            answered={quizState.answered}
            isTransitioning={quizState.isTransitioning}
            onAnswerSelect={handleAnswerSelect}
          />

          {quizState.answered && (
            <QuizExplanation
              explanation={currentQ.explanation}
              isTransitioning={quizState.isTransitioning}
            />
          )}

          {quizState.answered && (
            <QuizNextButton
              currentQuestion={quizState.currentQuestion}
              totalQuestions={quizQuestions.length}
              isTransitioning={quizState.isTransitioning}
              onNext={handleNextQuestion}
            />
          )}
        </div>
      </main>
    </>
  );
}
