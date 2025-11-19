import numpy as np
from typing import Dict, List, Tuple
from itertools import combinations_with_replacement
import logging

from .schemas import FeatureLibraryConfig

logger = logging.getLogger(__name__)

class FeatureGenerator:
    def __init__(self, independent_variables: List[str], dependent_variable: str):
        self.independent_variables = independent_variables
        self.dependent_variable = dependent_variable

    def generate_features(self,
                              data: Dict[str, np.ndarray],
                              config: FeatureLibraryConfig) -> Dict[str, np.ndarray]:
        """
        Generates a library of candidate features from input data (u and its derivatives, and independent variables).
        data: Dictionary where keys are flattened arrays for 'u', 'du_dx', 'd2u_dxdt', 'x', 't', etc.
              All arrays must have the same number of samples.
        config: FeatureLibraryConfig instance.
        """
        features = {}
        if not data or 'u' not in data:
            logger.warning("Input data is empty or 'u' (dependent variable) is missing. Cannot generate features.")
            return features

        num_samples = data['u'].shape[0]

        # Collect all available base features (independent vars, dependent var, derivatives)
        all_base_features_map = {}

        # 1. Independent variables
        if config.include_independent_variables:
            for var_name in self.independent_variables:
                if var_name in data:
                    all_base_features_map[var_name] = data[var_name]
                    features[var_name] = data[var_name]
                else:
                    logger.warning(f"Independent variable '{var_name}' not found in data for feature generation.")

        # 2. Dependent variable (u)
        if config.include_dependent_variable and 'u' in data:
            all_base_features_map['u'] = data['u']
            features['u'] = data['u']

        # 3. Derivatives
        if config.include_derivatives:
            for key, value in data.items():
                if key.startswith('d') and key != 'u' and not key.startswith('grid_'): # All derivatives
                    all_base_features_map[key] = value
                    features[key] = value

        # Ensure all feature arrays have the same shape (num_samples,)
        for key, value in features.items():
            if value.ndim > 1 and value.shape[1] == 1:
                features[key] = value.squeeze()
            elif value.ndim == 0: # Scalar values, expand to array of num_samples
                features[key] = np.full(num_samples, value)

        # 4. Polynomial features and Cross-products
        base_feature_names_for_products = list(all_base_features_map.keys())
        base_feature_values_for_products = list(all_base_features_map.values())

        if base_feature_names_for_products:
            # Polynomials of individual features (degree 2 up to polynomial_degree)
            for i, name in enumerate(base_feature_names_for_products):
                for degree in range(2, config.polynomial_degree + 1):
                    feature_name = f"({name})^{degree}"
                    features[feature_name] = base_feature_values_for_products[i] ** degree

            # Cross-products (total degree up to cross_product_degree)
            if config.cross_product_degree >= 2:
                # Generate combinations of feature names for cross-products
                for r in range(2, config.cross_product_degree + 1):
                    for combo_names_tuple in combinations_with_replacement(base_feature_names_for_products, r):
                        # Sort the combo names to ensure canonical naming (e.g., u*du_dx is same as du_dx*u)
                        sorted_combo_names = tuple(sorted(combo_names_tuple))
                        feature_name = "*".join(sorted_combo_names)
                        
                        # Avoid re-adding if it's just a higher power of a single term already covered by polynomial_degree
                        if len(set(sorted_combo_names)) == 1 and config.polynomial_degree >= r:
                            continue # Already covered by individual polynomial terms

                        # Compute product
                        product_val = np.ones(num_samples)
                        for name in sorted_combo_names:
                            product_val *= all_base_features_map[name]
                        
                        features[feature_name] = product_val

        # Ensure all feature arrays are 1D (num_samples,)
        for key, value in features.items():
            if value.ndim > 1:
                features[key] = value.squeeze()

        logger.info(f"Generated {len(features)} candidate features.")
        return features
