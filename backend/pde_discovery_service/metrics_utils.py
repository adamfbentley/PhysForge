import numpy as np
from typing import Dict, Any, List
import pysindy as ps

def calculate_sindy_aic_bic(model: ps.SINDy, feature_matrix: np.ndarray, target_derivative: np.ndarray) -> Dict[str, float]:
    """Calculate AIC and BIC for a SINDy model (STORY-501, CQ-PDE-004)."""
    n = feature_matrix.shape[0] # Number of samples
    k = np.count_nonzero(model.coefficients()) # Number of non-zero coefficients (parameters)
    
    if k == 0: # Avoid division by zero or log(0)
        return {"aic": np.inf, "bic": np.inf}

    predicted_derivative = model.predict(feature_matrix)
    residuals = target_derivative - predicted_derivative
    rss = np.sum(residuals**2) # Residual sum of squares

    if rss == 0: # Perfect fit, log(0) is undefined
        return {"aic": -np.inf, "bic": -np.inf}

    # AIC = n * log(RSS/n) + 2k
    aic = n * np.log(rss / n) + 2 * k
    # BIC = n * log(RSS/n) + k * log(n)
    bic = n * np.log(rss / n) + k * np.log(n)
    
    return {"aic": aic, "bic": bic}

def calculate_pysr_aic_bic(n_samples: int, rss: float, k_params: int) -> Dict[str, float]:
    """Calculate AIC and BIC for a PySR model (STORY-501, CQ-PDE-004)."""
    if k_params == 0: # Avoid division by zero or log(0)
        return {"aic": np.inf, "bic": np.inf}
    if rss == 0: # Perfect fit, log(0) is undefined
        return {"aic": -np.inf, "bic": -np.inf}
    
    aic = n_samples * np.log(rss / n_samples) + 2 * k_params
    bic = n_samples * np.log(rss / n_samples) + k_params * np.log(n_samples)
    return {"aic": aic, "bic": bic}
