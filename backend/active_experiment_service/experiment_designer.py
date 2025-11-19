import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Callable
import logging
from scipy.stats import qmc # For Latin Hypercube Sampling
from scipy.optimize import minimize
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern

from .schemas import ParameterSpaceDefinition, LHSConfig, BayesianOptimizationConfig, OptimizationHistoryEntry

logger = logging.getLogger(__name__)

class LatinHypercubeSampler:
    def __init__(self, config: LHSConfig):
        self.config = config

    def generate_samples(self) -> pd.DataFrame:
        """
        Generates samples using Latin Hypercube Sampling (STORY-602).
        Returns a pandas DataFrame of proposed parameters.
        """
        logger.info(f"Generating {self.config.num_samples} samples using LHS.")

        continuous_bounds = []
        continuous_param_names = []
        for param_name, bounds in self.config.parameter_space.continuous_params.items():
            continuous_bounds.append(bounds)
            continuous_param_names.append(param_name)
        
        # Handle continuous parameters
        if continuous_bounds:
            sampler = qmc.LatinHypercube(d=len(continuous_bounds))
            lhs_samples_unit = sampler.random(n=self.config.num_samples)
            
            # Scale samples to actual bounds
            lhs_samples_scaled = qmc.scale(lhs_samples_unit, np.array(continuous_bounds)[:, 0], np.array(continuous_bounds)[:, 1])
            proposed_df = pd.DataFrame(lhs_samples_scaled, columns=continuous_param_names)
        else:
            proposed_df = pd.DataFrame(index=range(self.config.num_samples))

        # Handle categorical parameters (randomly sample from allowed values)
        for param_name, values in self.config.parameter_space.categorical_params.items():
            proposed_df[param_name] = np.random.choice(values, size=self.config.num_samples)
        
        logger.info(f"Generated {self.config.num_samples} LHS samples.")
        return proposed_df

class BayesianOptimizer:
    def __init__(self, config: BayesianOptimizationConfig, pde_discovery_result: Dict[str, Any]):
        self.config = config
        self.pde_discovery_result = pde_discovery_result
        self.optimization_history: List[OptimizationHistoryEntry] = []

        self.continuous_param_names = list(self.config.parameter_space.continuous_params.keys())
        self.continuous_bounds = np.array([self.config.parameter_space.continuous_params[name] for name in self.continuous_param_names])
        self.categorical_param_names = list(self.config.parameter_space.categorical_params.keys())

        # Initialize Gaussian Process Regressor
        # A simple Matern kernel is often a good default for BO
        self.kernel = Matern(length_scale=1.0, nu=2.5)
        self.gp_model = GaussianProcessRegressor(kernel=self.kernel, alpha=1e-6, normalize_y=True, n_restarts_optimizer=10)

        self.objective_function = self._placeholder_objective_function

    def _placeholder_objective_function(self, params: Dict[str, Any]) -> float:
        """
        A placeholder objective function for Bayesian Optimization.
        """
        score = 0.0
        for i, name in enumerate(self.continuous_param_names):
            val = params[name]
            # Normalize value to [0, 1] range for consistent scoring
            min_val, max_val = self.config.parameter_space.continuous_params[name]
            normalized_val = (val - min_val) / (max_val - min_val)
            score += (normalized_val - 0.5)**2 # Penalize values far from center
        
        for name in self.categorical_param_names:
            # Simple penalty for specific categorical values
            if params[name] == self.config.parameter_space.categorical_params[name][0]: # First category is 'bad'
                score += 0.1
        
        # Add a component based on PDE uncertainty if available
        # This is a highly simplified heuristic
        if self.pde_discovery_result and self.config.target_metric_key in self.pde_discovery_result.get('equation_metrics', {}):
            pde_metric = self.pde_discovery_result['equation_metrics'][self.config.target_metric_key]
            score += pde_metric * 0.1 # Incorporate PDE metric, assuming lower is better

        return score

    def _expected_improvement(self, X: np.ndarray, gp_model: GaussianProcessRegressor, xi: float = 0.01) -> np.ndarray:
        """
        Expected Improvement acquisition function.
        X: Points at which to calculate EI.
        gp_model: Gaussian Process model.
        xi: Exploration-exploitation trade-off parameter.
        """
        mu, sigma = gp_model.predict(X, return_std=True)
        mu_sample_opt = np.max(gp_model.y_train_)

        with np.errstate(divide='warn'):
            imp = mu - mu_sample_opt - xi
            Z = imp / sigma
            ei = imp * qmc.stats.norm.cdf(Z) + sigma * qmc.stats.norm.pdf(Z)
            ei[sigma == 0.0] = 0.0
        return ei

    def _propose_single_point(self, acquisition_function: Callable, X_sample: np.ndarray, Y_sample: np.ndarray) -> Dict[str, Any]:
        """
        Proposes a single new point by maximizing the acquisition function.
        """
        dim = self.continuous_bounds.shape[0]
        min_val, max_val = self.continuous_bounds[:, 0], self.continuous_bounds[:, 1]

        # Find the best point by optimizing the acquisition function
        # We'll use a multi-start optimization to avoid local optima
        n_restarts = 20
        best_x = None
        best_ei = -np.inf

        for _ in range(n_restarts):
            # Randomly initialize optimization starting points within bounds
            x0 = np.random.uniform(min_val, max_val, size=dim)
            
            res = minimize(lambda x: -acquisition_function(x.reshape(1, -1)), 
                           x0=x0, 
                           bounds=self.continuous_bounds, 
                           method='L-BFGS-B')
            
            if -res.fun > best_ei:
                best_ei = -res.fun
                best_x = res.x
        
        if best_x is None:
            # Fallback to random if optimization fails
            best_x = np.random.uniform(min_val, max_val, size=dim)

        proposed_point_dict = dict(zip(self.continuous_param_names, best_x.tolist()))

        # For categorical parameters, randomly select one for the proposed point
        for param_name, values in self.config.parameter_space.categorical_params.items():
            proposed_point_dict[param_name] = np.random.choice(values)

        return proposed_point_dict

    def propose_next_points(self, current_data: pd.DataFrame, iteration: int) -> List[Dict[str, Any]]:
        """
        Proposes new experiment parameters using Bayesian Optimization (STORY-603).
        current_data: DataFrame with 'observed_metric' and parameter columns.
        iteration: Current iteration number.
        Returns a list of dictionaries, each representing a proposed parameter set.
        """
        logger.info(f"Bayesian Optimization: Proposing points for iteration {iteration}.")

        # Prepare training data for GP model
        X_train_continuous = current_data[self.continuous_param_names].values
        Y_train = current_data['observed_metric'].values

        if self.categorical_param_names:
            logger.warning("Categorical parameters are present but not fully integrated into GP model for BO. They will be randomly sampled.")

        # Fit GP model
        self.gp_model.fit(X_train_continuous, Y_train)

        # Define acquisition function
        if self.config.acquisition_function == "EI":
            acquisition_func = lambda X: self._expected_improvement(X, self.gp_model)
        elif self.config.acquisition_function == "UCB":
            # UCB acquisition function (beta parameter for exploration-exploitation trade-off)
            beta = 2.0 # Can be made configurable
            acquisition_func = lambda X: self.gp_model.predict(X, return_std=True)[0] + beta * self.gp_model.predict(X, return_std=True)[1]
        else:
            raise ValueError(f"Unsupported acquisition function: {self.config.acquisition_function}")

        # Propose a single new point (for simplicity, BO typically proposes one point at a time)
        proposed_point_dict = self._propose_single_point(acquisition_func, X_train_continuous, Y_train)
        
        # Estimate uncertainty and expected improvement at the proposed point
        X_proposed_continuous = np.array([proposed_point_dict[name] for name in self.continuous_param_names]).reshape(1, -1)
        mu_proposed, sigma_proposed = self.gp_model.predict(X_proposed_continuous, return_std=True)
        ei_proposed = acquisition_func(X_proposed_continuous)[0] if self.config.acquisition_function == "EI" else None

        # Store in history (observed_metric will be None initially, filled by external feedback)
        self.optimization_history.append(OptimizationHistoryEntry(
            iteration=iteration,
            proposed_point=proposed_point_dict,
            observed_metric=None,
            model_uncertainty=sigma_proposed[0] if sigma_proposed is not None else None,
            expected_improvement=ei_proposed
        ).model_dump())

        logger.info(f"Proposed new point: {proposed_point_dict}")
        return [proposed_point_dict]

    def get_optimization_history(self) -> List[Dict[str, Any]]:
        return self.optimization_history
