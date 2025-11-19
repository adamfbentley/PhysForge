import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { User } from '../api/auth';

const DashboardPage: React.FC = () => {
  const { user, loading } = useAuth();
  const [dashboardUser, setDashboardUser] = useState<User | null>(null);

  useEffect(() => {
    if (user) {
      setDashboardUser(user);
    }
  }, [user]);

  if (loading) {
    return <div className="text-center text-xl mt-8">Loading user data...</div>;
  }

  if (!dashboardUser) {
    return <div className="text-center text-xl mt-8 text-red-600">Failed to load user data. Please try logging in again.</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-4xl font-bold text-gray-800 mb-6">User Dashboard</h1>
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-2xl font-semibold text-blue-700 mb-4">User Information</h2>
        <p className="text-lg mb-2"><span className="font-medium">User ID:</span> {dashboardUser.id}</p>
        <p className="text-lg mb-2"><span className="font-medium">Email:</span> {dashboardUser.email}</p>
        <p className="text-lg mb-2"><span className="font-medium">Account Status:</span> {dashboardUser.is_active ? 'Active' : 'Inactive'}</p>
        <div className="mt-4">
          <h3 className="text-xl font-medium text-gray-700 mb-2">Roles:</h3>
          {dashboardUser.roles.length > 0 ? (
            <ul className="list-disc list-inside ml-4">
              {dashboardUser.roles.map((role) => (
                <li key={role.id} className="text-gray-600">{role.name}</li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-600">No roles assigned.</p>
          )}
        </div>
      </div>

      <div className="mt-8 bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-2xl font-semibold text-green-700 mb-4">Recent Activity</h2>
        <p className="text-gray-600">No recent activity to display yet. Start a new PINN training or PDE discovery job!</p>
      </div>
    </div>
  );
};

export default DashboardPage;
