"""
PySR Symbolic Regression for PDE Discovery

Simplified version adapted from production backend.
Discovers equations with transcendental functions: sin, cos, exp, log, sqrt
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Check if PySR is available
try:
    import pysr
    PYSR_AVAILABLE = True
except ImportError:
    PYSR_AVAILABLE = False
    logger.warning("PySR not installed. Symbolic regression will be unavailable. Install with: pip install pysr")


class PySRDiscoverer:
    """Discover PDEs using PySR symbolic regression"""
    
    def __init__(
        self,
        binary_operators: List[str] = ["+", "-", "*", "/"],
        unary_operators: List[str] = ["sin", "cos", "exp", "log", "sqrt"],
        populations: int = 15,
        population_size: int = 33,
        timeout_seconds: int = 120,  # 2 minutes default
        max_complexity: int = 20,
        procs: int = 4
    ):
        """
        Initialize PySR discoverer
        
        Args:
            binary_operators: Operations between terms (e.g., +, -, *, /)
            unary_operators: Functions of single terms (e.g., sin, exp, log)
            populations: Number of evolutionary populations
            population_size: Size of each population
            timeout_seconds: Max time for search
            max_complexity: Maximum equation complexity
            procs: Number of parallel processes
        """
        if not PYSR_AVAILABLE:
            raise ImportError("PySR not installed. Install with: pip install pysr")
            
        self.binary_operators = binary_operators
        self.unary_operators = unary_operators
        self.populations = populations
        self.population_size = population_size
        self.timeout_seconds = timeout_seconds
        self.max_complexity = max_complexity
        self.procs = procs
        
    def discover(
        self,
        feature_matrix: np.ndarray,
        feature_names: List[str],
        target: np.ndarray
    ) -> Dict:
        """
        Discover equation using symbolic regression
        
        Args:
            feature_matrix: Matrix of candidate terms [n_samples, n_features]
            feature_names: Names of features (e.g., ['u', 'u_x', 'u_xx'])
            target: Target to fit (e.g., u_t values)
            
        Returns:
            Dictionary with discovered equations and metrics
        """
        logger.info(f"Starting PySR discovery with {len(feature_names)} features")
        logger.info(f"Timeout: {self.timeout_seconds}s, Populations: {self.populations}")
        
        # Ensure target is 1D
        if target.ndim > 1:
            target = target.squeeze()
            
        # Create PySR model
        model = pysr.PySRRegressor(
            binary_operators=self.binary_operators,
            unary_operators=self.unary_operators,
            populations=self.populations,
            population_size=self.population_size,
            timeout_in_seconds=self.timeout_seconds,
            maxsize=self.max_complexity,
            procs=self.procs,
            verbosity=0,  # Quiet output
            progress=False,  # No progress bar (messes with web logs)
            temp_equation_file=True,
        )
        
        # Fit model
        try:
            model.fit(feature_matrix, target, variable_names=feature_names)
        except Exception as e:
            logger.error(f"PySR fitting failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "best_equation": None,
                "all_equations": []
            }
        
        # Extract results
        equations_df = model.equations_
        
        if equations_df.empty:
            logger.warning("PySR found no equations")
            return {
                "success": False,
                "error": "No equations found",
                "best_equation": None,
                "all_equations": []
            }
        
        # Get all equations sorted by loss
        equations_df = equations_df.sort_values(by='loss')
        
        # Parse results
        all_equations = []
        for idx, row in equations_df.iterrows():
            eq_dict = {
                "equation": row['equation'],
                "loss": float(row['loss']),
                "complexity": int(row['complexity']),
                "score": float(row.get('score', 0.0))
            }
            
            # Calculate R² if possible
            try:
                predictions = model.predict(feature_matrix, index=idx)
                ss_res = np.sum((target - predictions) ** 2)
                ss_tot = np.sum((target - np.mean(target)) ** 2)
                r_squared = 1 - (ss_res / ss_tot)
                eq_dict["r_squared"] = float(r_squared)
                eq_dict["rmse"] = float(np.sqrt(row['loss']))
            except:
                eq_dict["r_squared"] = None
                eq_dict["rmse"] = float(np.sqrt(row['loss']))
            
            # Calculate AIC/BIC
            n = len(target)
            k = row['complexity']  # Use complexity as proxy for parameters
            mse = row['loss']
            
            # AIC = n·ln(MSE) + 2k
            # BIC = n·ln(MSE) + k·ln(n)
            if mse > 0:
                eq_dict["aic"] = n * np.log(mse) + 2 * k
                eq_dict["bic"] = n * np.log(mse) + k * np.log(n)
            else:
                eq_dict["aic"] = None
                eq_dict["bic"] = None
            
            all_equations.append(eq_dict)
        
        # Best equation is first (lowest loss)
        best = all_equations[0]
        
        logger.info(f"PySR found {len(all_equations)} equations")
        logger.info(f"Best equation: {best['equation']} (R²={best.get('r_squared', 'N/A')})")
        
        return {
            "success": True,
            "best_equation": best,
            "all_equations": all_equations[:10],  # Return top 10
            "model": model  # Keep model for predictions if needed
        }


def discover_with_pysr(
    x_data: np.ndarray,
    t_data: np.ndarray,
    u_data: np.ndarray,
    derivs: Dict[str, np.ndarray],
    timeout_seconds: int = 120
) -> Dict:
    """
    Convenient wrapper for PySR discovery from raw data
    
    Args:
        x_data: Spatial coordinates
        t_data: Time coordinates
        u_data: Solution values
        derivs: Dictionary of derivatives from PINN
        timeout_seconds: Max search time
        
    Returns:
        Discovery results dictionary
    """
    if not PYSR_AVAILABLE:
        return {
            "success": False,
            "error": "PySR not installed",
            "best_equation": None
        }
    
    # Sample for efficiency (PySR is slow on large datasets)
    max_samples = 500
    if len(u_data) > max_samples:
        indices = np.random.choice(len(u_data), size=max_samples, replace=False)
    else:
        indices = np.arange(len(u_data))
    
    # Build feature library (same as sparse regression)
    u = u_data[indices]
    u_x = derivs['u_x'][indices]
    u_xx = derivs['u_xx'][indices]
    u_xxx = derivs['u_xxx'][indices]
    u_tt = derivs['u_tt'][indices]
    u_xt = derivs['u_xt'][indices]
    u_t = derivs['u_t'][indices]  # Target
    
    # Feature matrix (candidate terms for right-hand side)
    features = {
        'u': u,
        'u_x': u_x,
        'u_xx': u_xx,
        'u_xxx': u_xxx,
        'u_tt': u_tt,
        'u_xt': u_xt,
        'u_squared': u ** 2,
        'u_cubed': u ** 3,
        'u_u_x': u * u_x,
        'u_u_xx': u * u_xx,
        'u_x_squared': u_x ** 2,
    }
    
    feature_names = list(features.keys())
    feature_matrix = np.column_stack([features[name] for name in feature_names])
    
    # Discover
    discoverer = PySRDiscoverer(timeout_seconds=timeout_seconds)
    results = discoverer.discover(feature_matrix, feature_names, u_t)
    
    return results
