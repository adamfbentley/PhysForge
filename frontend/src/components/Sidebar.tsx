import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Sidebar: React.FC = () => {
  const { isAuthenticated } = useAuth();

  return (
    <aside className="w-64 bg-gray-800 text-white p-4 space-y-2 shadow-lg">
      <h2 className="text-xl font-semibold mb-4">Navigation</h2>
      <nav>
        <ul className="space-y-2">
          <li>
            <Link to="/" className="block px-4 py-2 rounded hover:bg-gray-700">
              Home
            </Link>
          </li>
          {isAuthenticated && (
            <>
              <li>
                <Link to="/dashboard" className="block px-4 py-2 rounded hover:bg-gray-700">
                  Dashboard
                </Link>
              </li>
              <li>
                <Link to="/datasets" className="block px-4 py-2 rounded hover:bg-gray-700">
                  Datasets
                </Link>
              </li>
              <li>
                <Link to="/pinn-training" className="block px-4 py-2 rounded hover:bg-gray-700">
                  PINN Training
                </Link>
              </li>
              <li>
                <Link to="/pde-discovery" className="block px-4 py-2 rounded hover:bg-gray-700">
                  PDE Discovery
                </Link>
              </li>
            </>
          )}
          {!isAuthenticated && (
            <>
              <li>
                <Link to="/login" className="block px-4 py-2 rounded hover:bg-gray-700">
                  Login
                </Link>
              </li>
              <li>
                <Link to="/register" className="block px-4 py-2 rounded hover:bg-gray-700">
                  Register
                </Link>
              </li>
            </>
          )}
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;
