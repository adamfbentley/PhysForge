import React from 'react';
import { Link } from 'react-router-dom';
import { AuthLayout } from '../components/layout/Layout';
import { Button } from '../components/ui/Button';
import { Card, CardBody } from '../components/ui/Card';
import {
  IconDatabase,
  IconCalculator,
  IconChartBar,
  IconTrendingUp,
  IconBrain,
  IconFileAnalytics,
  IconLogin,
  IconUserPlus
} from '@tabler/icons-react';

const HomePage: React.FC = () => {
  const features = [
    {
      icon: IconDatabase,
      title: 'Data Management',
      description: 'Securely upload, store, and manage your scientific datasets with automatic metadata extraction and versioning.',
      color: 'blue',
    },
    {
      icon: IconBrain,
      title: 'PINN Training',
      description: 'Configure and train Physics-Informed Neural Networks with custom architectures, loss functions, and boundary conditions.',
      color: 'green',
    },
    {
      icon: IconChartBar,
      title: 'PDE Discovery',
      description: 'Utilize advanced algorithms like SINDy and PySR to discover governing Partial Differential Equations from data.',
      color: 'purple',
    },
    {
      icon: IconTrendingUp,
      title: 'Derivatives & Features',
      description: 'Automated computation of high-order derivatives and generation of rich feature libraries for analysis.',
      color: 'yellow',
    },
    {
      icon: IconCalculator,
      title: 'Active Experiment Design',
      description: 'Propose new experiments or simulations to maximize information gain and refine discovered models.',
      color: 'red',
    },
    {
      icon: IconFileAnalytics,
      title: 'Reporting & Reproducibility',
      description: 'Generate comprehensive reports and reproducible analysis of your entire discovery pipeline.',
      color: 'indigo',
    },
  ];

  return (
    <AuthLayout>
      <div className="space-y-12">
        {/* Hero Section */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Physics-Informed Scientific Discovery Platform
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 mb-8 max-w-3xl mx-auto">
            Leverage Physics-Informed Neural Networks (PINNs) and advanced algorithms
            to discover new physical laws, train accurate models, and accelerate scientific research.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              component={Link}
              to="/auth/login"
              size="lg"
              leftIcon={<IconLogin size={20} />}
            >
              Sign In
            </Button>
            <Button
              component={Link}
              to="/auth/register"
              variant="outline"
              size="lg"
              leftIcon={<IconUserPlus size={20} />}
            >
              Create Account
            </Button>
          </div>
        </div>

        {/* Features Grid */}
        <div>
          <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-8">
            Powerful Features for Scientific Discovery
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <Card key={index} hover className="h-full">
                <CardBody className="text-center">
                  <div className={`inline-flex items-center justify-center w-12 h-12 rounded-lg bg-${feature.color}-100 dark:bg-${feature.color}-900 mb-4`}>
                    <feature.icon size={24} className={`text-${feature.color}-600 dark:text-${feature.color}-400`} />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    {feature.description}
                  </p>
                </CardBody>
              </Card>
            ))}
          </div>
        </div>

        {/* Call to Action */}
        <div className="text-center bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-gray-800 dark:to-gray-700 rounded-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Ready to Start Your Discovery Journey?
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-2xl mx-auto">
            Join researchers worldwide who are using PhysForge to accelerate their scientific discoveries
            and push the boundaries of physics-informed machine learning.
          </p>
          <Button
            component={Link}
            to="/auth/register"
            size="lg"
            leftIcon={<IconUserPlus size={20} />}
          >
            Get Started Free
          </Button>
        </div>
      </div>
    </AuthLayout>
  );
};

export default HomePage;
