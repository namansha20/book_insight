import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Navbar() {
  const location = useLocation();
  
  return (
    <nav className="bg-gray-800 border-b border-gray-700 shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-2">
            <span className="text-2xl">📚</span>
            <span className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              Book Insight
            </span>
          </Link>
          <div className="flex space-x-1">
            <Link
              to="/"
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                location.pathname === '/'
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              📖 Library
            </Link>
            <Link
              to="/qa"
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                location.pathname === '/qa'
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              🤖 Ask AI
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
