import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ChevronDown, Trophy, MessageCircle, Brain } from 'lucide-react';

const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  const getCurrentPageName = () => {
    const path = location.pathname;
    switch (path) {
      case '/chat':
        return 'Chat';
      case '/achievements':
        return 'Achievements';
      case '/quiz':
        return 'Quiz';
      default:
        return 'Navigation';
    }
  };

  return (
    <div className="w-full bg-white border-t border-gray-200 shadow-sm">
      <DropdownMenu>
        <DropdownMenuTrigger className="w-full inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-brand-secondary border border-gray-300 font-medium hover:bg-gray-50 hover:border-brand-secondary transition-all duration-200 shadow-sm">
          {getCurrentPageName()}
          <ChevronDown className="h-4 w-4" />
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="start"
          sideOffset={0}
          className="w-screen max-w-none bg-white border border-gray-200 shadow-lg [&]:rounded-t-none [&]:rounded-b-md"
          style={{ width: '100vw', maxWidth: '100vw' }}
        >
          <DropdownMenuItem
            className="w-full flex items-center gap-3 px-4 py-3 hover:bg-brand-tertiary cursor-pointer rounded-md"
            onClick={() => handleNavigation('/achievements')}
          >
            <Trophy className="h-4 w-4 text-brand-secondary" />
            <span className="text-brand-secondary font-medium">
              Achievements
            </span>
          </DropdownMenuItem>
          <DropdownMenuItem
            className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 cursor-pointer rounded-md"
            onClick={() => handleNavigation('/chat')}
          >
            <MessageCircle className="h-4 w-4 text-brand-secondary" />
            <span className="text-brand-secondary font-medium">Chat</span>
          </DropdownMenuItem>
          <DropdownMenuItem
            className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 cursor-pointer rounded-md"
            onClick={() => handleNavigation('/quiz')}
          >
            <Brain className="h-4 w-4 text-brand-secondary" />
            <span className="text-brand-secondary font-medium">Quiz</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};

export default Navigation;
