import React from 'react';
import Navigation from './Navigation';

const Header: React.FC = () => {
  return (
    <header className="bg-brand-primary w-full">
      <div className="px-4 py-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-brand-secondary text-center">
            SpendCast
          </h1>
        </div>
      </div>

      <Navigation />
    </header>
  );
};

export default Header;
