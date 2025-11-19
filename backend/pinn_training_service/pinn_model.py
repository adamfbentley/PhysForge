import torch
import torch.nn as nn
from typing import List, Dict, Any
import math
from .pinn_config import NetworkArchitecture

class MLP(nn.Module):
    """A simple Multi-Layer Perceptron (MLP) for PINNs."""
    def __init__(self, input_dim: int, output_dim: int, layers: List[int], activation: str = 'tanh'):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.layers = layers

        if activation == 'tanh':
            self.activation = nn.Tanh()
        elif activation == 'relu':
            self.activation = nn.ReLU()
        elif activation == 'sigmoid':
            self.activation = nn.Sigmoid()
        else:
            raise ValueError(f"Unsupported activation function: {activation}")

        all_layers = [input_dim] + layers + [output_dim]
        self.net = nn.ModuleList()
        for i in range(len(all_layers) - 1):
            self.net.append(nn.Linear(all_layers[i], all_layers[i+1]))
            if i < len(all_layers) - 2: # Don't apply activation to the last layer
                self.net.append(self.activation)

    def forward(self, x):
        for layer in self.net:
            x = layer(x)
        return x

# STORY-204: Fourier Feature MLP
class FourierFeatureMLP(nn.Module):
    """MLP with Fourier Feature mapping for input."""
    def __init__(self, input_dim: int, output_dim: int, layers: List[int], activation: str = 'tanh', fourier_features_scale: float = 1.0):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.fourier_features_scale = fourier_features_scale
        
        # Generate random frequencies for Fourier features
        # We'll use a fixed number of frequencies for simplicity, e.g., 256 pairs of sin/cos
        # This means the input dimension will be expanded to input_dim * 2 * num_frequencies
        num_frequencies = 256
        self.B = nn.Parameter(fourier_features_scale * torch.randn(input_dim, num_frequencies), requires_grad=False)
        
        # The MLP will now take the expanded Fourier features as input
        fourier_output_dim = input_dim * 2 * num_frequencies
        self.mlp = MLP(fourier_output_dim, output_dim, layers, activation)

    def forward(self, x):
        # Apply Fourier Feature mapping: sin(2*pi*B*x) and cos(2*pi*B*x)
        x_proj = 2 * math.pi * x @ self.B
        fourier_features = torch.cat([torch.sin(x_proj), torch.cos(x_proj)], dim=-1)
        return self.mlp(fourier_features)

# STORY-204: DeepONet
class DeepONet(nn.Module):
    """DeepONet architecture for operator learning."""
    def __init__(self, branch_input_dim: int, trunk_input_dim: int, output_dim: int, 
                 branch_layers: List[int], trunk_layers: List[int], activation: str = 'tanh'):
        super().__init__()
        self.branch_input_dim = branch_input_dim
        self.trunk_input_dim = trunk_input_dim
        self.output_dim = output_dim

        # Branch network (for function input)
        self.branch_net = MLP(branch_input_dim, branch_layers[-1], branch_layers[:-1], activation)
        
        # Trunk network (for point input)
        self.trunk_net = MLP(trunk_input_dim, trunk_layers[-1], trunk_layers[:-1], activation)

        # Output layer (dot product + bias)
        if branch_layers[-1] != trunk_layers[-1]:
            raise ValueError("Last layer dimension of branch and trunk networks must be equal for DeepONet.")
        
        self.bias = nn.Parameter(torch.zeros(output_dim))

    def forward(self, branch_x: torch.Tensor, trunk_x: torch.Tensor):
        # CQ-QA-003: DeepONet input handling now takes separate branch and trunk inputs
        branch_output = self.branch_net(branch_x)
        trunk_output = self.trunk_net(trunk_x)
        
        output = torch.sum(branch_output * trunk_output, dim=-1, keepdim=True) + self.bias
        return output

def build_model(input_dim: int, config: NetworkArchitecture) -> nn.Module:
    """Builds a neural network model based on the provided configuration."""
    if config.network_type == "MLP":
        return MLP(
            input_dim=input_dim,
            output_dim=config.output_dim,
            layers=config.layers,
            activation=config.activation
        )
    elif config.network_type == "FourierFeatureMLP":
        if config.fourier_features_scale is None:
            raise ValueError("Fourier features scale must be provided for FourierFeatureMLP.")
        return FourierFeatureMLP(
            input_dim=input_dim,
            output_dim=config.output_dim,
            layers=config.layers,
            activation=config.activation,
            fourier_features_scale=config.fourier_features_scale
        )
    elif config.network_type == "DeepONet":
        if config.branch_input_dim is None or config.trunk_input_dim is None or config.branch_layers is None or config.trunk_layers is None:
            raise ValueError("branch_input_dim, trunk_input_dim, branch_layers, and trunk_layers must be provided for DeepONet.")
        # For DeepONet, the 'input_dim' parameter passed to build_model is effectively ignored
        # as the DeepONet class itself defines its input dimensions.
        return DeepONet(
            branch_input_dim=config.branch_input_dim,
            trunk_input_dim=config.trunk_input_dim,
            output_dim=config.output_dim,
            branch_layers=config.branch_layers,
            trunk_layers=config.trunk_layers,
            activation=config.activation
        )
    else:
        raise ValueError(f"Unsupported network type: {config.network_type}")
