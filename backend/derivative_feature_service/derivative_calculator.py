import torch
import numpy as np
from typing import Dict, List, Tuple, Any
from sympy import symbols, sympify, diff, lambdify
import logging
from itertools import combinations_with_replacement

from .schemas import OutputGridConfig
from backend.pinn_training_service.pinn_model import MLP # Re-use MLP model

logger = logging.getLogger(__name__)

class DerivativeCalculator:
    def __init__(self, model: MLP, device: str = 'cpu'):
        self.model = model.to(device)
        self.model.eval() # Set model to evaluation mode
        self.device = device

    def _compute_single_derivative(self, y: torch.Tensor, x_input: torch.Tensor, order: int = 1) -> torch.Tensor:
        """Computes derivatives of y with respect to x_input using torch.autograd.grad."""
        if order == 1:
            return torch.autograd.grad(y, x_input, grad_outputs=torch.ones_like(y), create_graph=True, retain_graph=True)[0]
        elif order == 2:
            first_deriv = self._compute_single_derivative(y, x_input, order=1)
            return torch.autograd.grad(first_deriv, x_input, grad_outputs=torch.ones_like(first_deriv), create_graph=True, retain_graph=True)[0]
        elif order == 3: # STORY-301: Third order derivatives
            first_deriv = self._compute_single_derivative(y, x_input, order=1)
            second_deriv = self._compute_single_derivative(first_deriv, x_input, order=1)
            return torch.autograd.grad(second_deriv, x_input, grad_outputs=torch.ones_like(second_deriv), create_graph=True, retain_graph=True)[0]
        else:
            raise ValueError(f"Unsupported derivative order: {order}. Max 3rd order supported.")

    def generate_grid_points(self, grid_config: OutputGridConfig) -> Tuple[torch.Tensor, Dict[str, np.ndarray]]:
        """Generates meshgrid points and returns them as a flattened tensor and original meshgrid axes."""
        coords = []
        mesh_grids_np_axes = {}
        for var_name in grid_config.independent_variables:
            lower, upper = grid_config.domain_bounds[var_name]
            resolution = grid_config.grid_resolution[var_name]
            points = np.linspace(lower, upper, resolution)
            coords.append(points)
            mesh_grids_np_axes[var_name] = points

        # Create N-D meshgrid
        mesh_grids = np.meshgrid(*coords, indexing='ij')
        
        # Flatten meshgrid to (num_points, input_dim) tensor
        flat_points = np.vstack([grid.ravel() for grid in mesh_grids]).T
        
        return torch.tensor(flat_points, dtype=torch.float32, device=self.device), mesh_grids_np_axes

    @torch.no_grad()
    def compute_derivatives_on_grid(self, grid_config: OutputGridConfig, max_order: int) -> Dict[str, np.ndarray]:
        """
        Computes PINN output and its derivatives on a specified grid.
        Returns a dictionary where keys are derivative names (e.g., 'u', 'du_dx', 'd2u_dxdt')
        and values are numpy arrays of the derivatives, reshaped to the original grid shape.
        """
        self.model.eval() # Ensure model is in evaluation mode

        # Generate grid points
        x_grid_tensor, mesh_grids_np_axes = self.generate_grid_points(grid_config)
        original_grid_shape = tuple(grid_config.grid_resolution[var] for var in grid_config.independent_variables)
        
        # Make a copy for derivative computation that requires grad
        x_grid_tensor_grad = x_grid_tensor.clone().detach().requires_grad_(True)

        # Predict output (u)
        u_pred = self.model(x_grid_tensor_grad)
        
        results = {
            'u': u_pred.cpu().numpy().reshape(original_grid_shape + (self.model.output_dim,))
        }

        # Store the grid axes themselves
        for var_name, axis_data in mesh_grids_np_axes.items():
            results[f'grid_{var_name}'] = axis_data

        # Map independent variable names to their indices in the input tensor
        var_to_idx = {var_name: i for i, var_name in enumerate(grid_config.independent_variables)}

        # Iterate through all combinations of derivatives up to max_order
        for order in range(1, max_order + 1):
            # Generate all unique combinations of variables for this order
            # e.g., for order 2 and vars [x, t]: (x,x), (x,t), (t,t)
            var_combinations = list(combinations_with_replacement(grid_config.independent_variables, order))

            for combo in var_combinations:
                # Sort the combo to ensure canonical naming (e.g., (x,y) not (y,x))
                sorted_combo = tuple(sorted(combo))
                
                # CQ-QA-002: Complete the f-string to correctly construct derivative names
                # Count occurrences of each variable in the combo for powers (e.g., dx2)
                var_counts = {var: sorted_combo.count(var) for var in set(sorted_combo)}
                
                deriv_suffix_parts = []
                for var_name in grid_config.independent_variables: # Maintain consistent order
                    if var_name in var_counts:
                        count = var_counts[var_name]
                        if count == 1:
                            deriv_suffix_parts.append(f"d{var_name}")
                        else:
                            deriv_suffix_parts.append(f"d{var_name}{count}")
                
                deriv_name = f"d{order}u_" + "_".join(deriv_suffix_parts)

                # Compute the derivative
                current_deriv = u_pred
                for var_name in sorted_combo:
                    var_idx = var_to_idx[var_name]
                    current_deriv = self._compute_single_derivative(current_deriv, x_grid_tensor_grad[:, var_idx].unsqueeze(-1), order=1)
                
                results[deriv_name] = current_deriv.cpu().numpy().reshape(original_grid_shape + (self.model.output_dim,))

        return results
