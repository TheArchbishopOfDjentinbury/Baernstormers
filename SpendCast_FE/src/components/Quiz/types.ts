export interface Question {
  id: number;
  question: string;
  options: string[];
  correctAnswer: number;
  explanation: string;
}

export interface QuizState {
  currentQuestion: number;
  selectedAnswer: number | null;
  showResult: boolean;
  score: number;
  answered: boolean;
  isTransitioning: boolean;
}
