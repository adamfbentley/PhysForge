import React, { useEffect, useState } from 'react';
import { fetchPdeDiscoveryResults, PdeDiscoveryResultResponse } from '../api/pdeDiscoveryApi';
import EquationEditor from '../components/EquationEditor'; // Assuming EquationEditor is in components

const PdeComparisonPage: React.FC = () => {
  const [pdeResults, setPdeResults] = useState<PdeDiscoveryResultResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortConfig, setSortConfig] = useState<{ key: keyof PdeDiscoveryResultResponse | string; direction: 'ascending' | 'descending' } | null>(null);
  const [selectedEquation, setSelectedEquation] = useState<string>('');

  // SECURITY FIX: Removed hardcoded authentication token and owner ID.
  // Data fetching is temporarily disabled until a secure authentication mechanism is implemented.
  // In a real application, ownerId and token would be obtained securely from an authentication context.
  // const MOCK_OWNER_ID = 1; 
  // const MOCK_AUTH_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzFAZXhhbXBsZS5jb20iLCJ1c2VyX2lkIjoxLCJleHAiOjE3MTk5OTk5OTl9.some_mock_jwt_token_for_testing';

  useEffect(() => {
    // Temporarily disable data fetching due to missing secure authentication implementation.
    // Re-enable and implement secure token retrieval when authentication is ready.
    // const getPdeResults = async () => {
    //   try {
    //     const data = await fetchPdeDiscoveryResults(MOCK_OWNER_ID, MOCK_AUTH_TOKEN);
    //     setPdeResults(data);
    //   } catch (err: any) {
    //     setError(err.message || 'An unknown error occurred');
    //   } finally {
    //     setLoading(false);
    //   }
    // };

    // getPdeResults();
    setLoading(false); // Set loading to false to display the 'no data' message
    setError('Data fetching is disabled. Implement secure authentication to load PDE results.');
  }, []);

  const sortedPdeResults = React.useMemo(() => {
    let sortableItems = [...pdeResults];
    if (sortConfig !== null) {
      sortableItems.sort((a, b) => {
        let aValue: any;
        let bValue: any;

        // Handle nested metrics for sorting
        if (sortConfig.key === 'rmse' || sortConfig.key === 'aic' || sortConfig.key === 'bic' || sortConfig.key === 'complexity') {
          aValue = a.equation_metrics?.[sortConfig.key];
          bValue = b.equation_metrics?.[sortConfig.key];
        } else {
          aValue = a[sortConfig.key as keyof PdeDiscoveryResultResponse];
          bValue = b[sortConfig.key as keyof PdeDiscoveryResultResponse];
        }

        if (aValue === undefined || aValue === null) return 1; // Push undefined/null to end
        if (bValue === undefined || bValue === null) return -1; // Push undefined/null to end

        if (aValue < bValue) {
          return sortConfig.direction === 'ascending' ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === 'ascending' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableItems;
  }, [pdeResults, sortConfig]);

  const requestSort = (key: keyof PdeDiscoveryResultResponse | string) => {
    let direction: 'ascending' | 'descending' = 'ascending';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

  const getClassNamesFor = (name: keyof PdeDiscoveryResultResponse | string) => {
    if (!sortConfig) {
      return;
    }
    return sortConfig.key === name ? sortConfig.direction : undefined;
  };

  if (loading) {
    return <div className="flex justify-center items-center h-screen text-lg text-gray-600 dark:text-gray-400">Loading PDE results...</div>;
  }

  if (error) {
    return <div className="text-red-500 text-center p-4">Error: {error}</div>;
  }

  return (
    <div className="container mx-auto p-6 bg-white dark:bg-gray-900 text-gray-900 dark:text-white min-h-screen">
      <h1 className="text-3xl font-bold mb-6 text-center">PDE Comparison & Equation Editor</h1>

      <div className="mb-8 p-4 border rounded-lg shadow-md bg-gray-50 dark:bg-gray-800">
        <h2 className="text-2xl font-semibold mb-4">Equation Editor</h2>
        <EquationEditor
          value={selectedEquation}
          onChange={setSelectedEquation}
          label="Edit Equation"
          placeholder="Enter your PDE equation here..."
        />
        <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
          Current Equation: <code className="bg-gray-200 dark:bg-gray-700 p-1 rounded text-sm">{
            selectedEquation || 'No equation entered.'
          }</code>
        </p>
      </div>

      <h2 className="text-2xl font-semibold mb-4">Discovered PDE Equations</h2>
      {sortedPdeResults.length === 0 ? (
        <p className="text-center text-gray-600 dark:text-gray-400">No PDE discovery results found. {error}</p>
      ) : (
        <div className="overflow-x-auto shadow-md rounded-lg">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-100 dark:bg-gray-800">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Job ID
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Algorithm
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  <button type="button" onClick={() => requestSort('discovered_equation')} className={`flex items-center ${getClassNamesFor('discovered_equation') === 'ascending' ? 'sort-asc' : getClassNamesFor('discovered_equation') === 'descending' ? 'sort-desc' : ''}`}>
                    Discovered Equation
                  </button>
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  <button type="button" onClick={() => requestSort('canonical_equation')} className={`flex items-center ${getClassNamesFor('canonical_equation') === 'ascending' ? 'sort-asc' : getClassNamesFor('canonical_equation') === 'descending' ? 'sort-desc' : ''}`}>
                    Canonical Form
                  </button>
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  <button type="button" onClick={() => requestSort('rmse')} className={`flex items-center ${getClassNamesFor('rmse') === 'ascending' ? 'sort-asc' : getClassNamesFor('rmse') === 'descending' ? 'sort-desc' : ''}`}>
                    RMSE
                  </button>
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  <button type="button" onClick={() => requestSort('aic')} className={`flex items-center ${getClassNamesFor('aic') === 'ascending' ? 'sort-asc' : getClassNamesFor('aic') === 'descending' ? 'sort-desc' : ''}`}>
                    AIC
                  </button>
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  <button type="button" onClick={() => requestSort('bic')} className={`flex items-center ${getClassNamesFor('bic') === 'ascending' ? 'sort-asc' : getClassNamesFor('bic') === 'descending' ? 'sort-desc' : ''}`}>
                    BIC
                  </button>
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  <button type="button" onClick={() => requestSort('model_ranking_score')} className={`flex items-center ${getClassNamesFor('model_ranking_score') === 'ascending' ? 'sort-asc' : getClassNamesFor('model_ranking_score') === 'descending' ? 'sort-desc' : ''}`}>
                    Rank Score
                  </button>
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Uncertainty
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Sensitivity
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Created At
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              {sortedPdeResults.map((result) => (
                <tr key={result.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">{result.job_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{result.discovery_algorithm}</td>
                  <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-300 max-w-xs truncate">{result.discovered_equation || 'N/A'}</td>
                  <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-300 max-w-xs truncate">{result.canonical_equation || 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{result.equation_metrics?.rmse?.toFixed(4) || 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{result.equation_metrics?.aic?.toFixed(2) || 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{result.equation_metrics?.bic?.toFixed(2) || 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{result.model_ranking_score?.toFixed(2) || 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{result.uncertainty_metrics ? 'Available' : 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{result.sensitivity_analysis_results_path ? 'Available' : 'N/A'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">{new Date(result.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default PdeComparisonPage;
