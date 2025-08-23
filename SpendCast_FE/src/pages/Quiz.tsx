import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { CheckCircle, XCircle, Brain, ArrowRight } from 'lucide-react';

interface Question {
  id: number;
  question: string;
  options: string[];
  correctAnswer: number;
  explanation: string;
}

function Quiz() {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState(false);

  const questions: Question[] = [
    {
      id: 1,
      question: 'What percentage of your income should ideally go to savings?',
      options: ['5-10%', '20-30%', '40-50%', '60-70%'],
      correctAnswer: 1,
      explanation:
        'Financial experts recommend saving 20-30% of your income for a healthy financial future.',
    },
    {
      id: 2,
      question:
        'Which expense category typically takes the largest portion of a household budget?',
      options: ['Food', 'Transportation', 'Housing', 'Entertainment'],
      correctAnswer: 2,
      explanation:
        'Housing costs (rent/mortgage, utilities, maintenance) typically account for 25-30% of household income.',
    },
    {
      id: 3,
      question: 'What is the 50/30/20 budgeting rule?',
      options: [
        '50% needs, 30% wants, 20% savings',
        '50% savings, 30% needs, 20% wants',
        '50% wants, 30% savings, 20% needs',
        '50% housing, 30% food, 20% other',
      ],
      correctAnswer: 0,
      explanation:
        'The 50/30/20 rule suggests allocating 50% for needs, 30% for wants, and 20% for savings and debt repayment.',
    },
  ];

  const handleAnswerSelect = (answerIndex: number) => {
    if (answered) return;

    setSelectedAnswer(answerIndex);
    setAnswered(true);

    if (answerIndex === questions[currentQuestion].correctAnswer) {
      setScore(score + 1);
    }
  };

  const handleNextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
      setSelectedAnswer(null);
      setAnswered(false);
    } else {
      setShowResult(true);
    }
  };

  const resetQuiz = () => {
    setCurrentQuestion(0);
    setSelectedAnswer(null);
    setShowResult(false);
    setScore(0);
    setAnswered(false);
  };

  const getScoreMessage = () => {
    const percentage = (score / questions.length) * 100;
    if (percentage >= 80) return "Excellent! You're a spending expert! 🎉";
    if (percentage >= 60)
      return 'Good job! You have solid financial knowledge! 👍';
    if (percentage >= 40)
      return 'Not bad! Keep learning about personal finance! 📚';
    return 'Keep studying! Financial literacy is a journey! 💪';
  };

  if (showResult) {
    return (
      <>
        <main className="px-4 py-8 pb-24">
          <div className="max-w-2xl mx-auto text-center">
            <div className="mb-8">
              <Brain className="h-16 w-16 text-brand-primary mx-auto mb-4" />
              <h2 className="text-3xl font-bold text-brand-secondary mb-4">
                Quiz Complete!
              </h2>
            </div>

            <div className="bg-brand-tertiary p-8 rounded-xl mb-8">
              <div className="text-6xl font-bold text-brand-secondary mb-2">
                {score}/{questions.length}
              </div>
              <div className="text-xl text-brand-secondary/70 mb-4">
                {Math.round((score / questions.length) * 100)}% Correct
              </div>
              <p className="text-lg text-brand-secondary">
                {getScoreMessage()}
              </p>
            </div>

            <Button
              onClick={resetQuiz}
              className="bg-brand-primary text-brand-secondary hover:bg-brand-primary/90 px-8 py-3"
            >
              Take Quiz Again
            </Button>
          </div>
        </main>
      </>
    );
  }

  const currentQ = questions[currentQuestion];

  return (
    <>
      <main className="px-4 py-8 pb-24">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-semibold text-brand-secondary mb-4">
              Financial Knowledge Quiz
            </h2>
            <p className="text-brand-secondary/70 mb-6">
              Test your understanding of personal finance and spending habits
            </p>

            {/* Progress Bar */}
            <div className="mb-6">
              <div className="flex justify-between text-sm text-brand-secondary/70 mb-2">
                <span>
                  Question {currentQuestion + 1} of {questions.length}
                </span>
                <span>
                  {Math.round(((currentQuestion + 1) / questions.length) * 100)}
                  %
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-brand-primary h-2 rounded-full transition-all duration-300"
                  style={{
                    width: `${
                      ((currentQuestion + 1) / questions.length) * 100
                    }%`,
                  }}
                ></div>
              </div>
            </div>
          </div>

          {/* Question */}
          <div className="bg-brand-tertiary p-6 rounded-xl mb-6">
            <h3 className="text-xl font-semibold text-brand-secondary mb-6">
              {currentQ.question}
            </h3>

            <div className="space-y-3">
              {currentQ.options.map((option, index) => {
                let buttonStyle =
                  'w-full p-4 text-left border-2 rounded-lg transition-all duration-200 ';

                if (!answered) {
                  buttonStyle +=
                    'border-gray-200 hover:border-brand-primary hover:bg-brand-primary/5';
                } else {
                  if (index === currentQ.correctAnswer) {
                    buttonStyle +=
                      'border-green-500 bg-green-50 text-green-700';
                  } else if (
                    index === selectedAnswer &&
                    index !== currentQ.correctAnswer
                  ) {
                    buttonStyle += 'border-red-500 bg-red-50 text-red-700';
                  } else {
                    buttonStyle += 'border-gray-200 text-gray-500';
                  }
                }

                return (
                  <button
                    key={index}
                    onClick={() => handleAnswerSelect(index)}
                    className={buttonStyle}
                    disabled={answered}
                  >
                    <div className="flex items-center justify-between">
                      <span>{option}</span>
                      {answered && index === currentQ.correctAnswer && (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      )}
                      {answered &&
                        index === selectedAnswer &&
                        index !== currentQ.correctAnswer && (
                          <XCircle className="h-5 w-5 text-red-600" />
                        )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Explanation */}
          {answered && (
            <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg mb-6">
              <h4 className="font-semibold text-blue-800 mb-2">Explanation:</h4>
              <p className="text-blue-700">{currentQ.explanation}</p>
            </div>
          )}

          {/* Next Button */}
          {answered && (
            <div className="text-center">
              <Button
                onClick={handleNextQuestion}
                className="bg-brand-secondary text-white hover:bg-brand-secondary/90 px-6 py-3"
              >
                {currentQuestion < questions.length - 1 ? (
                  <>
                    Next Question
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                ) : (
                  'See Results'
                )}
              </Button>
            </div>
          )}
        </div>
      </main>
    </>
  );
}

export default Quiz;
