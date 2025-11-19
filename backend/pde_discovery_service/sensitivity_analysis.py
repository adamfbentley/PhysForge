import numpy as np
from typing import Dict, List, Any, Optional
from sympy import sympify, symbols, diff, lambdify, Eq
import logging

logger = logging.getLogger(__name__)

def perform_sensitivity_analysis(
    equation_str: str,
    independent_variables: List[str],
    dependent_variable: str,
    feature_data: Dict[str, np.ndarray], # Flattened data for features and target
    analysis_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Performs sensitivity analysis on a discovered PDE (STORY-504).
    
    This implementation focuses on symbolic differentiation of the PDE with respect to its
    coefficients or input variables, and can also perform numerical perturbation.
    
    equation_str: The discovered PDE equation string (e.g., "du_dt = 0.1*u + 0.5*du_dx").
    independent_variables: List of independent variables (e.g., ['x', 't']).
    dependent_variable: The main dependent variable (e.g., 'u').
    feature_data: Dictionary of flattened numpy arrays for all features and target derivative.
                  Used for numerical evaluation.
    analysis_config: Configuration for the analysis, e.g., {'perturbation_magnitude': 0.01, 'variables_to_perturb': ['u', 'du_dx']}.
    """
    logger.info(f"Performing sensitivity analysis for equation: {equation_str}")
    results = {"equation": equation_str}

    if not equation_str or equation_str == "No equation found":
        results["error"] = "Cannot perform sensitivity analysis on an empty or unfound equation."
        return results

    try:
        # Define symbols for independent, dependent variables, and their derivatives
        all_symbols_list = independent_variables + [dependent_variable]
        # Dynamically add symbols for derivatives present in the equation string
        # This is a heuristic and might need refinement for complex equations
        for key in feature_data.keys():
            if key.startswith('d') and key not in all_symbols_list and not key.startswith('grid_'):
                all_symbols_list.append(key)
        
        # Add any coefficients if they are explicitly named in the equation
        # This is a simplification; a more robust approach would extract coefficients from SINDy/PySR results
        # For now, we assume coefficients are numerical constants or implicitly handled by sympy.
        
        all_sympy_symbols = symbols(all_symbols_list)
        
        # Parse the equation. Assume it's in the form `LHS = RHS` or `Expression = 0`.
        # We need to convert it to an expression for differentiation.
        expr = sympify(equation_str, evaluate=False)
        if isinstance(expr, Eq):
            expr_to_analyze = expr.rhs - expr.lhs # Analyze the residual
        else:
            expr_to_analyze = expr # Assume it's already an expression = 0

        # 1. Symbolic Sensitivity to input variables/features
        symbolic_sensitivities = {}
        for var_name in all_symbols_list:
            var_sym = symbols(var_name)
            if expr_to_analyze.has(var_sym):
                partial_deriv = diff(expr_to_analyze, var_sym)
                symbolic_sensitivities[f"d_residual_d_{var_name}"] = str(partial_deriv)
        results["symbolic_sensitivities"] = symbolic_sensitivities
        logger.info(f"Symbolic sensitivities computed: {symbolic_sensitivities}")

        # 2. Numerical Perturbation Analysis (if configured)
        if analysis_config and analysis_config.get("perform_numerical_perturbation", False):
            perturbation_magnitude = analysis_config.get("perturbation_magnitude", 0.01)
            variables_to_perturb = analysis_config.get("variables_to_perturb", [])

            numerical_sensitivities = {}
            
            # Create a callable function from the expression
            # Need to map all symbols in expr_to_analyze to arguments of the lambdified function
            all_expr_symbols = list(expr_to_analyze.free_symbols)
            if not all_expr_symbols:
                logger.warning("Equation has no free symbols for numerical perturbation.")
                results["numerical_sensitivities"] = {"message": "Equation has no free symbols for numerical perturbation."}
                return results

            # Ensure all required data for evaluation is present
            missing_data = [str(s) for s in all_expr_symbols if str(s) not in feature_data]
            if missing_data:
                logger.warning(f"Missing data for numerical perturbation: {missing_data}")
                results["numerical_sensitivities"] = {"error": f"Missing data for symbols: {missing_data}"}
                return results

            # Create a dictionary of numerical arrays for evaluation
            eval_data = {str(s): feature_data[str(s)] for s in all_expr_symbols}
            
            # Lambdify the expression
            f_expr = lambdify(all_expr_symbols, expr_to_analyze, 'numpy')
            
            # Calculate baseline residual
            baseline_residual = f_expr(*[eval_data[str(s)] for s in all_expr_symbols])
            baseline_mean_abs_residual = np.mean(np.abs(baseline_residual))

            for var_name in variables_to_perturb:
                if var_name not in eval_data: # Check if the variable exists in the data
                    logger.warning(f"Variable '{var_name}' not found in feature data for perturbation.")
                    continue

                perturbed_data = eval_data.copy()
                original_values = perturbed_data[var_name]
                
                # Perturb by adding a small amount
                perturbed_values = original_values * (1 + perturbation_magnitude)
                perturbed_data[var_name] = perturbed_values

                perturbed_residual = f_expr(*[perturbed_data[str(s)] for s in all_expr_symbols])
                perturbed_mean_abs_residual = np.mean(np.abs(perturbed_residual))

                # Calculate sensitivity as change in mean absolute residual
                # Normalize by the magnitude of perturbation and original values to get a relative sensitivity
                if np.mean(np.abs(original_values)) != 0:
                    sensitivity = (perturbed_mean_abs_residual - baseline_mean_abs_residual) / (perturbation_magnitude * np.mean(np.abs(original_values)))
                else:
                    sensitivity = (perturbed_mean_abs_residual - baseline_mean_abs_residual) / perturbation_magnitude # Absolute change if original is zero
                numerical_sensitivities[f"sensitivity_to_{var_name}"] = float(sensitivity)
            
            results["numerical_sensitivities"] = numerical_sensitivities
            logger.info(f"Numerical sensitivities computed: {numerical_sensitivities}")

    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}", exc_info=True)
        results["error"] = f"Failed to perform sensitivity analysis: {e}"
    
    return results
