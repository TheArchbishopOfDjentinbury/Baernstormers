// Animation styles for Quiz components
export const animationStyles = `
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  @keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  @keyframes slideDown {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  @keyframes slideRight {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
  }
  
  @keyframes slideLeft {
    from { opacity: 0; transform: translateX(20px); }
    to { opacity: 1; transform: translateX(0); }
  }
  
  @keyframes scaleIn {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
  }
  
  @keyframes pulseGentle {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
  }
  
  @keyframes bounceGentle {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-3px); }
  }
  
  @keyframes successPulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.03); }
    100% { transform: scale(1); }
  }
  
  @keyframes errorShake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-3px); }
    75% { transform: translateX(3px); }
  }
  
  .animate-fade-in { animation: fadeIn 0.6s ease-out; }
  .animate-fade-in-delay { animation: fadeIn 0.6s ease-out 0.2s both; }
  .animate-fade-in-delay-2 { animation: fadeIn 0.6s ease-out 0.4s both; }
  .animate-fade-in-delay-3 { animation: fadeIn 0.6s ease-out 0.6s both; }
  .animate-slide-up { animation: slideUp 0.6s ease-out; }
  .animate-slide-down { animation: slideDown 0.6s ease-out; }
  .animate-slide-right { animation: slideRight 0.6s ease-out; }
  .animate-slide-left { animation: slideLeft 0.6s ease-out; }
  .animate-scale-in { animation: scaleIn 0.5s ease-out; }
  .animate-pulse-gentle { animation: pulseGentle 3s ease-in-out infinite; }
  .animate-bounce-gentle { animation: bounceGentle 2s ease-in-out infinite; }
  .animate-success-pulse { animation: successPulse 0.5s ease-out; }
  .animate-error-shake { animation: errorShake 0.5s ease-out; }
  .animate-fade-out-partial { opacity: 0.6; }
  .animate-count-up { animation: scaleIn 0.8s ease-out; }
  .animate-fade-in-stagger { animation: fadeIn 0.4s ease-out; }
  
  .animate-fade-in-stagger:nth-child(1) { animation-delay: 0s; }
  .animate-fade-in-stagger:nth-child(2) { animation-delay: 0.1s; }
  .animate-fade-in-stagger:nth-child(3) { animation-delay: 0.2s; }
  .animate-fade-in-stagger:nth-child(4) { animation-delay: 0.3s; }
  
  .question-transition-out {
    opacity: 0;
    transform: translateX(-20px);
    transition: all 0.3s ease-in-out;
  }
  
  .question-transition-in {
    opacity: 1;
    transform: translateX(0);
    transition: all 0.4s ease-out;
  }
  
  @keyframes floatUp {
    0% { 
      transform: translateY(100vh) rotate(0deg);
      opacity: 0;
    }
    10% { opacity: 0.7; }
    90% { opacity: 0.7; }
    100% { 
      transform: translateY(-100px) rotate(360deg);
      opacity: 0;
    }
  }
  
  @keyframes floatDiagonal {
    0% { 
      transform: translate(100vw, 100vh) rotate(0deg);
      opacity: 0;
    }
    10% { opacity: 0.6; }
    90% { opacity: 0.6; }
    100% { 
      transform: translate(-100px, -100px) rotate(-180deg);
      opacity: 0;
    }
  }
  
  @keyframes floatSlow {
    0% { 
      transform: translate(-100px, 100vh) rotate(0deg);
      opacity: 0;
    }
    10% { opacity: 0.5; }
    90% { opacity: 0.5; }
    100% { 
      transform: translate(100vw, -100px) rotate(180deg);
      opacity: 0;
    }
  }
  
  .floating-icon {
    position: fixed;
    pointer-events: none;
    z-index: 1;
    opacity: 0;
  }
  
  .float-1 { 
    animation: floatUp 8s linear infinite;
    animation-fill-mode: forwards;
  }
  .float-2 { 
    animation: floatDiagonal 12s linear infinite;
    animation-fill-mode: forwards;
  }
  .float-3 { 
    animation: floatSlow 10s linear infinite;
    animation-fill-mode: forwards;
  }
`;
