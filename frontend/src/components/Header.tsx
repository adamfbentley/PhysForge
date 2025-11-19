import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Header: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header className="bg-blue-800 text-white p-4 shadow-md flex justify-between items-center">
      <Link to="/" className="text-2xl font-bold hover:text-blue-200">
        Physics-Informed Platform
      </Link>
      <nav>
        {isAuthenticated ? (
          <div className="flex items-center space-x-4">
            <span className="text-lg">Welcome, {user?.email}</span>
            <button
              onClick={logout}
              className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
            >
              Logout
            </button>
          </div>
        ) : (
          <div className="space-x-4">
            <Link to="/login" className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
              Login
            </Link>
            <Link to="/register" className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded">
              Register
            </Link>
          </div>
        )}
      </nav>
    </header>
  );
};

export default Header;
