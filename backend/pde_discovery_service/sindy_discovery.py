import numpy as np
from typing import Dict, List, Any, Optional
import pysindy as ps
from .schemas import SindyConfig
import logging
from scipy.stats import t # For confidence intervals
from sklearn.model_selection import KFold # For cross-validation
from .symbolic_utils import canonicalize_equation # STORY-503
from .metrics_utils import calculate_sindy_aic_bic # CQ-PDE-004

logger = logging.getLogger(__name__)

class SindyDiscoverer:
    def __init__(self, config: SindyConfig, independent_variables: List[str], dependent_variable: str):
        self.config = config
        self.independent_variables = independent_variables
        self.dependent_variable = dependent_variable

    def _perform_bootstrapping(self, feature_matrix: np.ndarray, target_derivative: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
        """
        Performs bootstrapping to quantify uncertainty in SINDy coefficients (STORY-405).
        Returns mean coefficients and confidence intervals.
        """
        logger.info(f"Performing bootstrapping with {self.config.bootstrap_samples} samples.")
        n_samples = feature_matrix.shape[0]
        all_coefficients = []

        for _ in range(self.config.bootstrap_samples):
            # Resample with replacement
            indices = np.random.choice(n_samples, n_samples, replace=True)
            X_resampled = feature_matrix[indices]
            y_resampled = target_derivative[indices]

            optimizer = ps.STLSQ(threshold=self.config.threshold, alpha=self.config.alpha, max_iter=self.config.max_iter)
            model = ps.SINDy(optimizer=optimizer, feature_library=ps.IdentityLibrary(), feature_names=feature_names)
            
            try:
                model.fit(X_resampled, x_dot=y_resampled)
                all_coefficients.append(model.coefficients().flatten())
            except Exception as e:
                logger.warning(f"Bootstrapping sample failed: {e}")
                continue
        
        if not all_coefficients:
            return {"message": "Bootstrapping failed to produce any valid coefficient sets."}

        all_coefficients = np.array(all_coefficients)
        mean_coefficients = np.mean(all_coefficients, axis=0)
        std_coefficients = np.std(all_coefficients, axis=0)

        # Calculate 95% confidence intervals (assuming t-distribution for small samples, Z for large)
        confidence_level = 0.95
        alpha = 1.0 - confidence_level
        
        # Degrees of freedom for t-distribution (n_samples - k, where k is number of non-zero coeffs)
        # This is an approximation as k varies per bootstrap sample. Using n_samples-1 for simplicity.
        df = n_samples - 1 
        if df <= 0: df = 1 # Ensure df is positive

        t_critical = t.ppf(1 - alpha / 2, df)
        margin_of_error = t_critical * (std_coefficients / np.sqrt(self.config.bootstrap_samples))

        lower_bound = mean_coefficients - margin_of_error
        upper_bound = mean_coefficients + margin_of_error

        coeff_ci = []
        for i, name in enumerate(feature_names):
            coeff_ci.append({
                "feature": name,
                "mean_coefficient": mean_coefficients[i],
                "std_dev": std_coefficients[i],
                "ci_lower": lower_bound[i],
                "ci_upper": upper_bound[i]
            })

        return {
            "method": "bootstrap",
            "bootstrap_samples": self.config.bootstrap_samples,
            "coefficient_confidence_intervals": coeff_ci
        }


    def discover_pde(self,
                         feature_matrix: np.ndarray,
                         feature_names: List[str],
                         target_derivative: np.ndarray,
                         canonicalize_equation_flag: bool = True) -> Dict[str, Any]:
        """
        Discovers PDE using SINDy (STORY-402, STORY-404, STORY-405, STORY-501, STORY-503).
        """
        logger.info(f"Starting SINDy PDE discovery with optimizer: {self.config.optimizer}")

        if target_derivative.ndim == 1:
            target_derivative = target_derivative.reshape(-1, 1)

        optimizer = ps.STLSQ(threshold=self.config.threshold, alpha=self.config.alpha, max_iter=self.config.max_iter)
        
        model_selection_metrics = {}
        uncertainty_metrics = {}
        discovered_equation = "No equation found"
        equation_metrics = {}
        canonical_equation = None

        if self.config.cross_validation_folds: # STORY-404: Cross-validation
            logger.info(f"Performing {self.config.cross_validation_folds}-fold cross-validation.")
            cv = KFold(n_splits=self.config.cross_validation_folds, shuffle=True, random_state=42)
            
            # SINDyCV requires a feature library, even if it's IdentityLibrary
            feature_library = ps.IdentityLibrary()
            
            sindy_cv_model = ps.SINDy(optimizer=optimizer, feature_library=feature_library, feature_names=feature_names)
            
            # SINDyCV expects X and X_dot
            sindy_cv_model.fit(feature_matrix, x_dot=target_derivative, cv=cv)
            
            # The best model from CV is stored in sindy_cv_model.model
            model = sindy_cv_model.model
            
            # Extract CV metrics
            cv_scores = sindy_cv_model.get_metrics()
            model_selection_metrics["cross_validation_scores"] = cv_scores.tolist() if isinstance(cv_scores, np.ndarray) else cv_scores
            logger.info(f"Cross-validation completed. Best model found.")
        else:
            model = ps.SINDy(optimizer=optimizer, feature_library=ps.IdentityLibrary(), feature_names=feature_names)
            model.fit(feature_matrix, x_dot=target_derivative)
        
        # Get the discovered equation string
        equation_string_list = model.equations(precision=5)
        discovered_equation = equation_string_list[0] if equation_string_list else "No equation found"
        logger.info(f"SINDy discovered equation: {discovered_equation}")

        # Evaluate metrics (RMSE, AIC/BIC) (STORY-501)
        predicted_derivative = model.predict(feature_matrix)
        rmse = np.sqrt(np.mean((target_derivative - predicted_derivative)**2))
        
        # Get coefficients
        coefficients = model.coefficients()
        
        equation_metrics = {
            "rmse": rmse,
            "coefficients": coefficients.tolist() if coefficients is not None else [],
            "num_terms": np.count_nonzero(coefficients) # Complexity
        }
        
        aic_bic_metrics = calculate_sindy_aic_bic(model, feature_matrix, target_derivative) # CQ-PDE-004
        equation_metrics.update(aic_bic_metrics)
        logger.info(f"Equation metrics: {equation_metrics}")

        # STORY-405: Uncertainty Quantification
        if self.config.uncertainty_quantification_method == "bootstrap":
            uncertainty_metrics = self._perform_bootstrapping(feature_matrix, target_derivative, feature_names)
            logger.info(f"Uncertainty metrics: {uncertainty_metrics}")

        # STORY-503: Canonicalize equation
        if canonicalize_equation_flag and discovered_equation != "No equation found":
            canonical_equation = canonicalize_equation(discovered_equation, self.independent_variables, self.dependent_variable)
            logger.info(f"Canonicalized equation: {canonical_equation}")

        return {
            "discovered_equation": discovered_equation,
            "canonical_equation": canonical_equation,
            "equation_metrics": equation_metrics,
            "uncertainty_metrics": uncertainty_metrics,
            "model_selection_metrics": model_selection_metrics # For CV scores
        }
