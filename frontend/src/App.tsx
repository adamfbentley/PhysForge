import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { AuthGuard } from './components/AuthGuard';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import DashboardPage from './pages/dashboard/DashboardPage';
import PdeComparisonPage from './pages/PdeComparisonPage';
import HomePage from './pages/HomePage';
import JobsPage from './pages/jobs/JobsPage';
import PinnJobPage from './pages/jobs/PinnJobPage';
import PdeDiscoveryPage from './pages/jobs/PdeDiscoveryPage';
import JobResultsPage from './pages/jobs/JobResultsPage';
import DatasetsPage from './pages/datasets/DatasetsPage';

function App() {
  return (
    <MantineProvider
      theme={{
        colorScheme: 'light',
        colors: {
          brand: ['#e3f2fd', '#bbdefb', '#90caf9', '#64b5f6', '#42a5f5', '#2196f3', '#1e88e5', '#1976d2', '#1565c0', '#0d47a1'],
        },
        primaryColor: 'brand',
      }}
      withGlobalStyles
      withNormalizeCSS
    >
      <Notifications />
      <Router>
        <Routes>
          {/* Public routes */}
          <Route
            path="/auth/login"
            element={
              <AuthGuard requireAuth={false}>
                <LoginPage />
              </AuthGuard>
            }
          />
          <Route
            path="/auth/register"
            element={
              <AuthGuard requireAuth={false}>
                <RegisterPage />
              </AuthGuard>
            }
          />

          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={
              <AuthGuard>
                <DashboardPage />
              </AuthGuard>
            }
          />
          <Route
            path="/jobs"
            element={
              <AuthGuard>
                <JobsPage />
              </AuthGuard>
            }
          />
          <Route
            path="/jobs/new/pinn"
            element={
              <AuthGuard>
                <PinnJobPage />
              </AuthGuard>
            }
          />
          <Route
            path="/jobs/new/pde"
            element={
              <AuthGuard>
                <PdeDiscoveryPage />
              </AuthGuard>
            }
          />
          <Route
            path="/jobs/:jobId/results"
            element={
              <AuthGuard>
                <JobResultsPage />
              </AuthGuard>
            }
          />
          <Route
            path="/datasets"
            element={
              <AuthGuard>
                <DatasetsPage />
              </AuthGuard>
            }
          />
          <Route
            path="/pde-comparison"
            element={
              <AuthGuard>
                <PdeComparisonPage />
              </AuthGuard>
            }
          />

          {/* Default route */}
          <Route
            path="/"
            element={
              <AuthGuard requireAuth={false}>
                <HomePage />
              </AuthGuard>
            }
          />
        </Routes>
      </Router>
    </MantineProvider>
  );
}

export default App;);

export default App;
