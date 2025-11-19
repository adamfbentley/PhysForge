import torch
import torch.nn as nn
import torch.nn.functional as F # For huber_loss
import numpy as np
from typing import Dict, Any, Callable, List, Optional
from sympy import symbols, sympify, diff, lambdify, sin, cos, exp, log, Abs, pi # SEC-QA-001: Explicitly import allowed sympy functions
import re

from .pinn_config import PinnTrainingConfig, PhysicsLossConfig, Condition
from .pinn_model import MLP, DeepONet # Import DeepONet for type checking

import logging
logger = logging.getLogger(__name__)

class PinnSolver:
    def __init__(self, model: nn.Module, config: PinnTrainingConfig, device: str = 'cpu'): # CQ-QA-003: Changed type hint from MLP to nn.Module
        self.model = model.to(device)
        self.config = config
        self.device = device
        self.training_params = config.training_parameters
        self.physics_config = config.physics_loss_config

        self.optimizer = self._get_optimizer()
        self.loss_fn = nn.MSELoss()

        self.independent_vars = []
        self.dependent_vars = []
        self.pde_expr = None
        self.pde_func = None
        self.pde_args = [] # Store the ordered arguments for lambdified PDE function

        # CQ-QA-003: Store DeepONet specific dimensions
        self.branch_input_dim = None
        self.trunk_input_dim = None
        if isinstance(self.model, DeepONet):
            self.branch_input_dim = self.model.branch_input_dim
            self.trunk_input_dim = self.model.trunk_input_dim

        if self.physics_config:
            self.independent_vars = [symbols(v) for v in self.physics_config.independent_variables]
            self.dependent_vars = [symbols(v) for v in self.physics_config.dependent_variables]
            self._prepare_pde_function()
        
        # CQ-QA-006: Custom loss function registry
        self._custom_loss_functions = {
            "weighted_mse": self._weighted_mse_loss,
            "huber_loss": self._huber_loss,
        }

    def _get_optimizer(self):
        if self.training_params.optimizer == "Adam":
            return torch.optim.Adam(self.model.parameters(), lr=self.training_params.learning_rate)
        elif self.training_params.optimizer == "LBFGS":
            return torch.optim.LBFGS(self.model.parameters(), lr=self.training_params.learning_rate, 
                                     max_iter=50000, max_eval=50000, history_size=50, 
                                     tolerance_grad=1e-5, tolerance_change=1e-9, line_search_fn="strong_wolfe")
        else:
            raise ValueError(f"Unsupported optimizer: {self.training_params.optimizer}")

    # SEC-QA-001: Added basic keyword filtering and complexity check for PDE equation
    def _validate_pde_equation(self, pde_equation: str):
        dangerous_keywords = ['import', 'os', 'sys', 'eval', 'exec', 'lambda', 'def', 'class', 'while', 'for', 'if', 'try', 'except', 'with', 'open']
        for keyword in dangerous_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', pde_equation):
                raise ValueError(f"PDE equation contains a forbidden keyword: '{keyword}'. This is a security risk.")
        if '__' in pde_equation:
            raise ValueError("PDE equation contains forbidden '__' sequence. This is a security risk.")
        
        # SEC-QA-001: Basic complexity check: limit length of the PDE string
        MAX_PDE_EQUATION_LENGTH = 500 # Arbitrary limit, can be tuned
        if len(pde_equation) > MAX_PDE_EQUATION_LENGTH:
            raise ValueError(f"PDE equation exceeds maximum allowed length of {MAX_PDE_EQUATION_LENGTH} characters. Please simplify the expression.")

    def _prepare_pde_function(self):
        """Prepares a callable function for the PDE residual using sympy and lambdify."""
        if not self.physics_config or not self.physics_config.pde_equation:
            return

        # SEC-QA-001: Validate PDE equation before sympify
        self._validate_pde_equation(self.physics_config.pde_equation)

        # Assume the model output is the first dependent variable for simplicity
        u = self.dependent_vars[0]

        # Collect all symbols involved in the PDE expression
        all_symbols = list(self.independent_vars) + self.dependent_vars

        # Create a dictionary to map derivatives to symbolic placeholders
        derivative_map = {}
        # CQ-PTS-001: Support for cross-derivatives
        for var1 in self.independent_vars:
            # First derivatives
            derivative_map[diff(u, var1)] = symbols(f'd{u}d{var1}')
            # Second derivatives (pure and cross)
            for var2 in self.independent_vars:
                # Ensure unique placeholder for d2u/dxdy vs d2u/dydx
                # Sympy treats diff(u,x,y) as diff(u,y,x), so we only need one placeholder for cross-derivatives
                # Use a canonical representation for the key to avoid duplicates
                key_tuple = tuple(sorted((var1, var2), key=str))
                if (u, key_tuple) not in derivative_map:
                    if var1 == var2:
                        derivative_map[diff(u, var1, var2)] = symbols(f'd2{u}d{var1}d{var2}')
                    else:
                        derivative_map[diff(u, var1, var2)] = symbols(f'd2{u}d{key_tuple[0]}d{key_tuple[1]}')
            # CQ-QA-004: Third derivatives
            for var2 in self.independent_vars:
                for var3 in self.independent_vars:
                    key_tuple = tuple(sorted((var1, var2, var3), key=str))
                    if (u, key_tuple) not in derivative_map:
                        derivative_map[diff(u, var1, var2, var3)] = symbols(f'd3{u}d{key_tuple[0]}d{key_tuple[1]}d{key_tuple[2]}')

        # SEC-QA-001: Restrict sympify's environment with a whitelist of allowed functions
        safe_dict = {s.name: s for s in all_symbols} # Include independent and dependent variables
        safe_dict.update({
            'sin': sin, 'cos': cos, 'exp': exp, 'log': log, # Sympy math functions
            'Abs': Abs, 'diff': diff, 'pi': pi, # Sympy functions and constant
            **{str(s): s for s in self.independent_vars}, # Ensure independent vars are available as symbols
            **{str(s): s for s in self.dependent_vars} # Ensure dependent vars are available as symbols
        })

        # Replace derivatives in the PDE expression with placeholders
        pde_with_placeholders = sympify(self.physics_config.pde_equation, locals=safe_dict, globals=safe_dict)
        for d_sym, d_placeholder in derivative_map.items():
            pde_with_placeholders = pde_with_placeholders.subs(d_sym, d_placeholder)

        # The arguments for the lambdified function will be independent vars, dependent vars, and their derivatives
        # The order matters for lambdify
        self.pde_args = list(self.independent_vars) + list(self.dependent_vars) + list(derivative_map.values())
        self.pde_func = lambdify(self.pde_args, pde_with_placeholders, 'numpy')

    # CQ-QA-004: Extended _compute_derivatives to support 3rd order
    def _compute_derivatives(self, y: torch.Tensor, x_input: torch.Tensor, order: int = 1) -> torch.Tensor:
        """Computes derivatives of y with respect to x_input using torch.autograd.grad."""
        if order == 1:
            return torch.autograd.grad(y, x_input, grad_outputs=torch.ones_like(y), create_graph=True, retain_graph=True)[0]
        elif order == 2:
            first_deriv = self._compute_derivatives(y, x_input, order=1)
            return torch.autograd.grad(first_deriv, x_input, grad_outputs=torch.ones_like(first_deriv), create_graph=True, retain_graph=True)[0]
        elif order == 3:
            first_deriv = self._compute_derivatives(y, x_input, order=1)
            second_deriv = self._compute_derivatives(first_deriv, x_input, order=1)
            return torch.autograd.grad(second_deriv, x_input, grad_outputs=torch.ones_like(second_deriv), create_graph=True, retain_graph=True)[0]
        else:
            raise ValueError(f"Unsupported derivative order: {order}. Max 3rd order supported.")

    # CQ-QA-003: Helper to get model output, handling DeepONet's separate inputs
    def _get_model_output(self, x_input: torch.Tensor, branch_x_input: Optional[torch.Tensor] = None) -> torch.Tensor:
        if isinstance(self.model, DeepONet):
            if branch_x_input is None:
                # For physics loss, assume x_input represents the trunk input (spatial/temporal coordinates)
                # and branch input is a constant (e.g., zeros) as the PDE itself doesn't depend on a specific function input here.
                branch_x = torch.zeros(x_input.shape[0], self.branch_input_dim, device=self.device, requires_grad=x_input.requires_grad)
            else:
                branch_x = branch_x_input
            return self.model(branch_x, x_input)
        else:
            return self.model(x_input)

    def _compute_pde_loss(self, x_pde: torch.Tensor) -> torch.Tensor:
        if not self.physics_config or not self.pde_func:
            return torch.tensor(0.0, device=self.device)

        x_pde.requires_grad_(True)
        u_pred = self._get_model_output(x_pde) # CQ-QA-003: Use helper function for model output

        # Prepare arguments for the PDE function
        pde_input_values = []
        # Independent variables
        for i, var_sym in enumerate(self.independent_vars):
            pde_input_values.append(x_pde[:, i])
        # Dependent variables (model output)
        u = self.dependent_vars[0] # Assuming single output u
        pde_input_values.append(u_pred.squeeze())

        # Derivatives (CQ-PTS-001: Handle cross-derivatives)
        # Map independent variable symbols to their indices in x_pde
        var_to_idx = {str(var_sym): i for i, var_sym in enumerate(self.independent_vars)}
        
        # Collect all required derivatives based on self.pde_args (which includes placeholders)
        # This ensures we compute derivatives in the order expected by self.pde_func
        computed_derivatives = {}
        for arg_sym in self.pde_args:
            if arg_sym in self.independent_vars or arg_sym in self.dependent_vars: # Already added
                continue
            
            # Parse derivative placeholder name, e.g., 'd2udxdy'
            match = re.match(r'd(\d?)u?d([a-zA-Z]+)(?:d([a-zA-Z]+))?(?:d([a-zA-Z]+))?', str(arg_sym)) # Extended for 3rd order
            if not match:
                logger.warning(f"Could not parse derivative symbol: {arg_sym}")
                continue
            
            order_str, var1_name, var2_name, var3_name = match.groups()
            order = int(order_str) if order_str else 1

            if order == 1:
                var_idx = var_to_idx[var1_name]
                deriv = self._compute_derivatives(u_pred, x_pde[:, var_idx].unsqueeze(-1), order=1)
                computed_derivatives[arg_sym] = deriv.squeeze()
            elif order == 2:
                var1_idx = var_to_idx[var1_name]
                if var2_name: # Cross-derivative or pure second derivative
                    var2_idx = var_to_idx[var2_name]
                    if var1_name == var2_name: # Pure second derivative
                        first_deriv = self._compute_derivatives(u_pred, x_pde[:, var1_idx].unsqueeze(-1), order=1)
                        second_deriv = self._compute_derivatives(first_deriv, x_pde[:, var1_idx].unsqueeze(-1), order=1)
                        computed_derivatives[arg_sym] = second_deriv.squeeze()
                    else: # Cross-derivative d2u/dvar1dvar2
                        # Compute d/dvar2 (du/dvar1)
                        du_dvar1 = self._compute_derivatives(u_pred, x_pde[:, var1_idx].unsqueeze(-1), order=1)
                        d2u_dvar1dvar2 = self._compute_derivatives(du_dvar1, x_pde[:, var2_idx].unsqueeze(-1), order=1)
                        computed_derivatives[arg_sym] = d2u_dvar1dvar2.squeeze()
                else: # Should not happen if parsing is correct for d2u/dx2
                    logger.warning(f"Unexpected derivative symbol format for order 2: {arg_sym}")
                    continue
            elif order == 3: # CQ-QA-004: Third order derivatives
                var1_idx = var_to_idx[var1_name]
                var2_idx = var_to_idx[var2_name]
                var3_idx = var_to_idx[var3_name]

                # Compute d3u/dvar1dvar2dvar3
                du_dvar1 = self._compute_derivatives(u_pred, x_pde[:, var1_idx].unsqueeze(-1), order=1)
                d2u_dvar1dvar2 = self._compute_derivatives(du_dvar1, x_pde[:, var2_idx].unsqueeze(-1), order=1)
                d3u_dvar1dvar2dvar3 = self._compute_derivatives(d2u_dvar1dvar2, x_pde[:, var3_idx].unsqueeze(-1), order=1)
                computed_derivatives[arg_sym] = d3u_dvar1dvar2dvar3.squeeze()
            else:
                raise ValueError(f"Unsupported derivative order {order} for symbol {arg_sym}")

        # Append computed derivatives in the correct order as per self.pde_args
        for arg_sym in self.pde_args[len(self.independent_vars) + len(self.dependent_vars):]:
            pde_input_values.append(computed_derivatives[arg_sym])

        # Convert to numpy for lambdified function, then back to torch
        pde_residual_np = self.pde_func(*[arg.detach().cpu().numpy() for arg in pde_input_values])
        pde_residual = torch.tensor(pde_residual_np, dtype=torch.float32, device=self.device).unsqueeze(-1)

        return self.loss_fn(pde_residual, torch.zeros_like(pde_residual))

    def _generate_collocation_points(self, bounds: Dict[str, List[float]], num_points: int) -> torch.Tensor:
        """Generates random collocation points within the given bounds."""
        points = []
        for var in self.physics_config.independent_variables:
            lower, upper = bounds[var]
            points.append(torch.rand(num_points, 1) * (upper - lower) + lower)
        return torch.cat(points, dim=1).to(self.device)

    def _compute_boundary_loss(self) -> torch.Tensor:
        if not self.physics_config or not self.physics_config.boundary_conditions:
            return torch.tensor(0.0, device=self.device)

        total_bc_loss = torch.tensor(0.0, device=self.device)
        for bc in self.physics_config.boundary_conditions:
            # Generate points for this specific boundary
            bc_points_list = []
            for var_idx, var_name in enumerate(self.physics_config.independent_variables):
                if var_name in bc.location:
                    # Fixed boundary value
                    bc_points_list.append(torch.full((self.physics_config.num_boundary_points, 1), float(bc.location[var_name]), device=self.device))
                else:
                    # Randomly sample within domain bounds for other dimensions
                    lower, upper = self.physics_config.domain_bounds[var_name]
                    bc_points_list.append(torch.rand(self.physics_config.num_boundary_points, 1, device=self.device) * (upper - lower) + lower)
            x_bc = torch.cat(bc_points_list, dim=1)
            x_bc.requires_grad_(True)
            u_pred_bc = self._get_model_output(x_bc) # CQ-QA-003: Use helper function for model output

            if bc.type == "Dirichlet":
                target_value = float(bc.value) # Assuming scalar for now
                total_bc_loss += self.loss_fn(u_pred_bc, torch.full_like(u_pred_bc, target_value))
            elif bc.type == "Neumann":
                # CQ-QA-005: Raise ValueError for Neumann condition with multiple fixed locations
                if len(bc.location) != 1:
                    raise ValueError(f"Neumann condition '{bc.name}' has multiple fixed locations. Only single variable Neumann supported for now.")
                
                fixed_var_name = list(bc.location.keys())[0]
                fixed_var_idx = self.physics_config.independent_variables.index(fixed_var_name)
                
                du_d_fixed_var = self._compute_derivatives(u_pred_bc, x_bc[:, fixed_var_idx].unsqueeze(-1), order=1)
                target_value = float(bc.value)
                total_bc_loss += self.loss_fn(du_d_fixed_var, torch.full_like(du_d_fixed_var, target_value))
            else:
                logger.warning(f"Unsupported boundary condition type: {bc.type}")

        return total_bc_loss

    def _compute_initial_loss(self) -> torch.Tensor:
        if not self.physics_config or not self.physics_config.initial_conditions:
            return torch.tensor(0.0, device=self.device)

        total_ic_loss = torch.tensor(0.0, device=self.device)
        for ic in self.physics_config.initial_conditions:
            # Assuming initial condition is typically at t=0
            # Generate points for this specific initial condition
            ic_points_list = []
            for var_idx, var_name in enumerate(self.physics_config.independent_variables):
                if var_name in ic.location:
                    ic_points_list.append(torch.full((self.physics_config.num_initial_points, 1), float(ic.location[var_name]), device=self.device))
                else:
                    lower, upper = self.physics_config.domain_bounds[var_name]
                    ic_points_list.append(torch.rand(self.physics_config.num_initial_points, 1, device=self.device) * (upper - lower) + lower)
            x_ic = torch.cat(ic_points_list, dim=1)
            x_ic.requires_grad_(True)
            u_pred_ic = self._get_model_output(x_ic) # CQ-QA-003: Use helper function for model output

            target_value = float(ic.value) # Assuming scalar for now
            total_ic_loss += self.loss_fn(u_pred_ic, torch.full_like(u_pred_ic, target_value))

        return total_ic_loss

    def _compute_regularization_loss(self) -> torch.Tensor:
        """Computes L1 or L2 regularization loss (STORY-205)."""
        if not self.training_params.regularization_type or self.training_params.regularization_weight == 0.0:
            return torch.tensor(0.0, device=self.device)

        reg_loss = torch.tensor(0.0, device=self.device)
        for param in self.model.parameters():
            if param.requires_grad: # Only regularize trainable parameters
                if self.training_params.regularization_type == "L1":
                    reg_loss += torch.norm(param, p=1)
                elif self.training_params.regularization_type == "L2":
                    reg_loss += torch.norm(param, p=2)**2
        return reg_loss * self.training_params.regularization_weight

    # CQ-QA-006: Static methods for custom loss functions
    @staticmethod
    def _weighted_mse_loss(y_pred: torch.Tensor, y_true: torch.Tensor, params: Optional[Dict[str, Any]]) -> torch.Tensor:
        weights = params.get("weights", 1.0) if params else 1.0
        return torch.mean(weights * (y_pred - y_true)**2)

    @staticmethod
    def _huber_loss(y_pred: torch.Tensor, y_true: torch.Tensor, params: Optional[Dict[str, Any]]) -> torch.Tensor:
        delta = params.get("delta", 1.0) if params else 1.0
        return F.huber_loss(y_pred, y_true, reduction='mean', delta=delta)

    # CQ-QA-006: Uses the custom loss function registry
    def _compute_custom_loss(self, y_pred: torch.Tensor, y_true: torch.Tensor) -> torch.Tensor:
        """Computes a custom loss function based on configuration (STORY-205)."""
        if not self.training_params.custom_loss_function_name:
            return torch.tensor(0.0, device=self.device)

        loss_name = self.training_params.custom_loss_function_name
        if loss_name in self._custom_loss_functions:
            custom_loss_func = self._custom_loss_functions[loss_name]
            return custom_loss_func(y_pred, y_true, self.training_params.custom_loss_params)
        else:
            logger.warning(f"Unsupported custom loss function: {loss_name}. Falling back to default MSE.")
            return self.loss_fn(y_pred, y_true) # Fallback to MSE

    def train(self, data: Optional[Dict[str, torch.Tensor]], update_callback: Callable[[int, str, Optional[str]], None]):
        logger.info(f"Starting PINN training for {self.config.output_name}...")
        self.model.train()

        x_pde = None
        if self.physics_config:
            x_pde = self._generate_collocation_points(self.physics_config.domain_bounds, self.physics_config.num_domain_points)

        for epoch in range(self.training_params.epochs):
            self.optimizer.zero_grad()
            
            loss_data = torch.tensor(0.0, device=self.device)
            if data and self.config.dataset_ref:
                x_data = data['x'].to(self.device)
                y_data = data['y'].to(self.device)
                
                # CQ-QA-003: Handle DeepONet specific input if applicable
                if isinstance(self.model, DeepONet):
                    # Split x_data into branch and trunk inputs based on configured dimensions
                    branch_x_data = x_data[:, :self.branch_input_dim]
                    trunk_x_data = x_data[:, self.branch_input_dim:]
                    y_pred_data = self.model(branch_x_data, trunk_x_data) 
                else:
                    y_pred_data = self.model(x_data)

                if self.training_params.custom_loss_function_name:
                    loss_data = self._compute_custom_loss(y_pred_data, y_data) * self.training_params.loss_weights.get("data", 1.0)
                else:
                    loss_data = self.loss_fn(y_pred_data, y_data) * self.training_params.loss_weights.get("data", 1.0)

            loss_pde = self._compute_pde_loss(x_pde) * self.training_params.loss_weights.get("pde", 1.0) if x_pde is not None else torch.tensor(0.0, device=self.device)
            loss_bc = self._compute_boundary_loss() * self.training_params.loss_weights.get("bc", 1.0)
            loss_ic = self._compute_initial_loss() * self.training_params.loss_weights.get("ic", 1.0)
            
            # STORY-205: Add regularization loss
            loss_regularization = self._compute_regularization_loss()

            total_loss = loss_data + loss_pde + loss_bc + loss_ic + loss_regularization
            total_loss.backward()

            if self.training_params.optimizer == "LBFGS":
                def closure():
                    self.optimizer.zero_grad()
                    loss_data_closure = torch.tensor(0.0, device=self.device)
                    if data and self.config.dataset_ref:
                        x_data = data['x'].to(self.device)
                        y_data = data['y'].to(self.device)
                        
                        # CQ-QA-003: Handle DeepONet specific input in closure
                        if isinstance(self.model, DeepONet):
                            branch_x_data = x_data[:, :self.branch_input_dim]
                            trunk_x_data = x_data[:, self.branch_input_dim:]
                            y_pred_data = self.model(branch_x_data, trunk_x_data)
                        else:
                            y_pred_data = self.model(x_data)

                        if self.training_params.custom_loss_function_name:
                            loss_data_closure = self._compute_custom_loss(y_pred_data, y_data) * self.training_params.loss_weights.get("data", 1.0)
                        else:
                            loss_data_closure = self.loss_fn(y_pred_data, y_data) * self.training_params.loss_weights.get("data", 1.0)

                    loss_pde_closure = self._compute_pde_loss(x_pde) * self.training_params.loss_weights.get("pde", 1.0) if x_pde is not None else torch.tensor(0.0, device=self.device)
                    loss_bc_closure = self._compute_boundary_loss() * self.training_params.loss_weights.get("bc", 1.0)
                    loss_ic_closure = self._compute_initial_loss() * self.training_params.loss_weights.get("ic", 1.0)
                    loss_regularization_closure = self._compute_regularization_loss() # Recalculate regularization

                    total_loss_closure = loss_data_closure + loss_pde_closure + loss_bc_closure + loss_ic_closure + loss_regularization_closure
                    total_loss_closure.backward()
                    return total_loss_closure
                self.optimizer.step(closure)
            else:
                self.optimizer.step()

            if (epoch + 1) % 100 == 0 or epoch == 0:
                progress = int(((epoch + 1) / self.training_params.epochs) * 100)
                message = f"Epoch {epoch+1}/{self.training_params.epochs}, Total Loss: {total_loss.item():.6f}, Data Loss: {loss_data.item():.6f}, PDE Loss: {loss_pde.item():.6f}, BC Loss: {loss_bc.item():.6f}, IC Loss: {loss_ic.item():.6f}, Reg Loss: {loss_regularization.item():.6f}"
                logger.info(message)
                update_callback(progress, "RUNNING", message)

        logger.info("PINN training completed.")
        update_callback(100, "COMPLETED", "PINN training finished successfully.")

        return {
            "final_loss": total_loss.item(),
            "data_loss": loss_data.item(),
            "pde_loss": loss_pde.item(),
            "bc_loss": loss_bc.item(),
            "ic_loss": loss_ic.item(),
            "regularization_loss": loss_regularization.item() # Add regularization loss to metrics
        }
