import numpy as np
from typing import Dict, List, Any, Optional
import pysr
from .schemas import PySRConfig
import logging
from scipy.stats import t # For confidence intervals
from .symbolic_utils import canonicalize_equation # STORY-503
from .metrics_utils import calculate_pysr_aic_bic # CQ-PDE-004

logger = logging.getLogger(__name__)

class PySRDiscoverer:
    def __init__(self, config: PySRConfig, independent_variables: List[str], dependent_variable: str):
        self.config = config
        self.independent_variables = independent_variables
        self.dependent_variable = dependent_variable

    def _perform_bootstrapping(self, feature_matrix: np.ndarray, target_derivative: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
        """
        For PySR, uncertainty quantification is primarily handled by its internal confidence metrics
        (e.g., `weighted_avg_std`, `bayes_factor`) which are extracted in `discover_pde`.
        Direct bootstrapping of coefficients for symbolic regression is computationally intensive
        and less straightforward than for linear models like SINDy.
        """
        logger.info("PySR provides internal confidence metrics for uncertainty quantification. Direct coefficient bootstrapping is not performed.")
        return {"message": "PySR provides internal confidence metrics. Bootstrapping for coefficients not performed."}


    def discover_pde(self,
                         feature_matrix: np.ndarray,
                         feature_names: List[str],
                         target_derivative: np.ndarray,
                         canonicalize_equation_flag: bool = True) -> Dict[str, Any]:
        """
        Discovers PDE using PySR (STORY-403, STORY-404, STORY-405, STORY-501, STORY-503).
        """
        logger.info(f"Starting PySR PDE discovery with {self.config.populations} populations.")

        # PySR expects X (feature matrix) and y (target vector).
        # Ensure target_derivative is 1D for PySR
        if target_derivative.ndim > 1:
            target_derivative = target_derivative.squeeze()

        model = pysr.PySRRegressor(
            n_features_to_test=self.config.n_features_to_test,
            binary_operators=self.config.binary_operators,
            unary_operators=self.config.unary_operators,
            complexity_of_operators=self.config.complexity_of_operators,
            max_depth=self.config.max_depth,
            populations=self.config.populations,
            timeout_in_seconds=self.config.timeout_in_seconds,
            output_jax_code=False,
            temp_equation_file=True,
            procs=self.config.procs,
            # STORY-404: PySR's internal validation is controlled by `procs` and `populations`
            # and it generates multiple equations with different complexities/losses.
            # We will select the best one based on loss.
        )

        model.fit(feature_matrix, target_derivative, X_columns=feature_names)

        best_equation_df = model.equations_
        discovered_equation = "No equation found by PySR."
        equation_metrics = {}
        uncertainty_metrics = {}
        canonical_equation = None
        model_selection_metrics = {}

        if not best_equation_df.empty:
            # STORY-501: Model selection criteria (RMSE, R-squared, complexity are directly available)
            # PySR's 'loss' is typically MSE.
            best_eq_row = best_equation_df.sort_values(by='loss').iloc[0]
            discovered_equation = best_eq_row['equation']
            
            # Extract relevant metrics
            rmse = np.sqrt(best_eq_row['loss']) # Assuming loss is MSE
            r_squared = best_eq_row.get('r2', None) # PySR might provide R2
            complexity = best_eq_row['complexity']

            equation_metrics = {
                "rmse": rmse,
                "r_squared": r_squared,
                "complexity": complexity,
                "equation_string": discovered_equation # Store the raw equation string
            }

            # Calculate AIC/BIC (STORY-501)
            n_samples = feature_matrix.shape[0]
            # For PySR, k (number of parameters) is often related to complexity.
            # A simple heuristic is to count the number of operators + constants.
            # For now, let's use complexity as a proxy for k.
            aic_bic_metrics = calculate_pysr_aic_bic(n_samples, best_eq_row['loss'] * n_samples, complexity) # CQ-PDE-004
            equation_metrics.update(aic_bic_metrics)
            logger.info(f"PySR discovered equation: {discovered_equation}")
            logger.info(f"Equation metrics: {equation_metrics}")

            # STORY-405: Uncertainty Quantification
            if self.config.uncertainty_quantification_method == "bootstrap":
                uncertainty_metrics = self._perform_bootstrapping(feature_matrix, target_derivative, feature_names)
            # PySR also provides 'weighted_avg_std' and 'bayes_factor' in its equations_ dataframe
            # which can be used for uncertainty.
            if 'weighted_avg_std' in best_eq_row:
                uncertainty_metrics['pysr_weighted_avg_std'] = best_eq_row['weighted_avg_std']
            if 'bayes_factor' in best_eq_row:
                uncertainty_metrics['pysr_bayes_factor'] = best_eq_row['bayes_factor']
            logger.info(f"Uncertainty metrics: {uncertainty_metrics}")

            # STORY-503: Canonicalize equation
            if canonicalize_equation_flag and discovered_equation != "No equation found by PySR.":
                canonical_equation = canonicalize_equation(discovered_equation, self.independent_variables, self.dependent_variable)
                logger.info(f"Canonicalized equation: {canonical_equation}")
        
        return {
            "discovered_equation": discovered_equation,
            "canonical_equation": canonical_equation,
            "equation_metrics": equation_metrics,
            "uncertainty_metrics": uncertainty_metrics,
            "all_pysr_equations": best_equation_df.to_dict(orient='records') # Return all equations for ranking
        }
