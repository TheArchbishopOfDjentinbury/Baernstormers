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
    <div className="border-t border-brand-secondary/20 px-4 py-3">
      <div className="max-w-4xl mx-auto flex justify-center">
        <DropdownMenu>
          <DropdownMenuTrigger className="inline-flex items-center gap-2 px-4 py-2 bg-brand-secondary text-white rounded-lg font-medium hover:bg-brand-secondary/90 transition-colors">
            {getCurrentPageName()}
            <ChevronDown className="h-4 w-4" />
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="center"
            className="w-48 bg-white border border-brand-secondary/20 shadow-lg"
          >
            <DropdownMenuItem
              className="flex items-center gap-3 px-3 py-2 hover:bg-brand-tertiary cursor-pointer"
              onClick={() => handleNavigation('/achievements')}
            >
              <Trophy className="h-4 w-4 text-brand-secondary" />
              <span className="text-brand-secondary font-medium">
                Achievements
              </span>
            </DropdownMenuItem>
            <DropdownMenuItem
              className="flex items-center gap-3 px-3 py-2 hover:bg-brand-tertiary cursor-pointer"
              onClick={() => handleNavigation('/chat')}
            >
              <MessageCircle className="h-4 w-4 text-brand-secondary" />
              <span className="text-brand-secondary font-medium">Chat</span>
            </DropdownMenuItem>
            <DropdownMenuItem
              className="flex items-center gap-3 px-3 py-2 hover:bg-brand-tertiary cursor-pointer"
              onClick={() => handleNavigation('/quiz')}
            >
              <Brain className="h-4 w-4 text-brand-secondary" />
              <span className="text-brand-secondary font-medium">Quiz</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
};

export default Navigation;
