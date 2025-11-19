from sympy import sympify, symbols, Eq, solve, simplify, collect
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

def canonicalize_equation(equation_str: str, independent_variables: List[str], dependent_variable: str) -> Optional[str]:
    """
    Parses an equation string, simplifies it, and expresses it in a canonical form.
    For PDEs, it attempts to express the highest order derivative of the dependent variable
    with respect to one of the independent variables on one side.
    """
    if not equation_str:
        return None

    try:
        # Define symbols
        all_symbols = symbols(independent_variables + [dependent_variable])
        u = symbols(dependent_variable)

        # Parse the equation string. Assume it's an equality, e.g., "du/dt + u*du/dx = 0"
        # If it's already an equality, Eq(lhs, rhs), sympify will parse it.
        # If it's just an expression, it assumes expression = 0.
        expr = sympify(equation_str, evaluate=False)

        # If it's an equality, convert to an expression equal to zero
        if isinstance(expr, Eq):
            expr = expr.lhs - expr.rhs
        
        # Simplify the expression
        simplified_expr = simplify(expr)

        # Attempt to find the highest order derivative of the dependent variable
        # with respect to one of the independent variables. This is a heuristic for canonical form.
        
        # Collect all derivatives of 'u'
        u_derivatives = []
        for s in simplified_expr.atoms(symbols):
            if isinstance(s, symbols) and s.name.startswith('d') and s.name.endswith(dependent_variable):
                u_derivatives.append(s)
        
        # Sort derivatives by order (heuristic: count 'd's) and then by variable
        u_derivatives.sort(key=lambda s: (s.name.count('d'), s.name))

        if u_derivatives:
            # Try to solve for the highest order derivative
            highest_deriv = u_derivatives[-1]
            
            # Ensure the highest_deriv is not zero in the expression
            if simplified_expr.has(highest_deriv):
                # Solve for highest_deriv = ...
                solutions = solve(simplified_expr, highest_deriv)
                if solutions:
                    # Take the first solution and express it as an equation
                    canonical_eq = Eq(highest_deriv, solutions[0])
                    return str(canonical_eq)
            
        # If no clear highest derivative or solving fails, try to collect terms
        # and set the expression to zero.
        canonical_expr = collect(simplified_expr, all_symbols)
        return str(Eq(canonical_expr, 0))

    except Exception as e:
        logger.warning(f"Failed to canonicalize equation '{equation_str}': {e}")
        return equation_str # Return original if canonicalization fails
