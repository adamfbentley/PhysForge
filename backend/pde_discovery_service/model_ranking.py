import numpy as np
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def rank_models(models_with_metrics: List[Dict[str, Any]], ranking_criteria: List[str]) -> List[Dict[str, Any]]:
    """
    Ranks discovered PDE models based on a list of criteria (STORY-502).
    
    models_with_metrics: List of dictionaries, where each dict represents a discovered model
                         and contains its 'equation_metrics' (e.g., 'rmse', 'complexity', 'aic', 'bic').
    ranking_criteria: List of strings specifying criteria and their order of importance.
                      Criteria can be prefixed with '-' for descending order (e.g., '-r_squared').
                      Default criteria are 'rmse', 'complexity', 'aic'.
    
    Returns a list of models, sorted by the ranking criteria, with an added 'ranking_score'.
    """
    if not models_with_metrics:
        return []

    logger.info(f"Ranking models using criteria: {ranking_criteria}")

    # Define a scoring function for each criterion (lower is better for RMSE, AIC, BIC, complexity)
    # For R-squared, higher is better.
    def get_criterion_value(model_metrics: Dict[str, Any], criterion: str):
        is_descending = False
        if criterion.startswith('-'):
            is_descending = True
            criterion = criterion[1:] # Remove '-'

        value = model_metrics.get(criterion)
        if value is None:
            # Penalize missing values heavily
            return np.inf if not is_descending else -np.inf 

        # Invert score for descending criteria (e.g., higher R-squared is better, so we negate it for sorting ascending)
        return -value if is_descending else value

    # Sort models based on multiple criteria
    # Python's sort is stable, so later criteria break ties for earlier ones.
    # The key function generates a tuple of values for comparison.
    
    ranked_models = sorted(models_with_metrics, key=lambda model: [
        get_criterion_value(model.get('equation_metrics', {}), criterion) for criterion in ranking_criteria
    ])

    # Assign a simple ranking score (e.g., inverse of rank)
    for i, model in enumerate(ranked_models):
        model['model_ranking_score'] = len(ranked_models) - i # Higher score for better rank

    logger.info(f"Models ranked successfully. Top model: {ranked_models[0].get('discovered_equation')}")
    return ranked_models
