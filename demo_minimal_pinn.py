"""
Minimal PhysForge Demo: PINN Training for PDE Discovery

This script demonstrates the core concept of PhysForge:
1. Generate synthetic data from a known PDE (heat equation)
2. Train a Physics-Informed Neural Network (PINN) 
3. Show that the PINN learned the underlying physics

Equation: ∂u/∂t = α∇²u (1D heat equation, α=0.01)
"""

import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
from typing import Tuple

# Set random seeds for reproducibility
np.random.seed(42)
torch.manual_seed(42)

class PINN(nn.Module):
    """Simple Physics-Informed Neural Network"""
    
    def __init__(self, layers=[2, 32, 32, 32, 1]):
        super().__init__()
        self.layers = nn.ModuleList()
        for i in range(len(layers) - 1):
            self.layers.append(nn.Linear(layers[i], layers[i+1]))
    
    def forward(self, x, t):
        """Forward pass: inputs (x, t) -> output u(x,t)"""
        inputs = torch.cat([x, t], dim=1)
        for i, layer in enumerate(self.layers[:-1]):
            inputs = torch.tanh(layer(inputs))
        return self.layers[-1](inputs)


def generate_heat_equation_data(nx=50, nt=50, L=1.0, T=0.5, alpha=0.01) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate training data from 1D heat equation using finite differences
    
    ∂u/∂t = α∂²u/∂x²
    
    Returns:
        x_data: spatial coordinates
        t_data: temporal coordinates
        u_data: solution values
    """
    x = np.linspace(0, L, nx)
    t = np.linspace(0, T, nt)
    dx = L / (nx - 1)
    dt = T / (nt - 1)
    
    # Initial condition: Gaussian pulse
    u = np.zeros((nt, nx))
    u[0, :] = np.exp(-100 * (x - 0.5)**2)
    
    # Boundary conditions: u(0,t) = u(L,t) = 0
    
    # Solve using explicit finite difference
    r = alpha * dt / dx**2
    for n in range(nt - 1):
        for i in range(1, nx - 1):
            u[n+1, i] = u[n, i] + r * (u[n, i+1] - 2*u[n, i] + u[n, i-1])
    
    # Create meshgrid for training data
    X, T = np.meshgrid(x, t)
    x_data = X.flatten()
    t_data = T.flatten()
    u_data = u.flatten()
    
    return x_data, t_data, u_data


def compute_pde_residual(model, x, t):
    """
    Compute PDE residual: ∂u/∂t - α∇²u
    
    Uses automatic differentiation to compute derivatives
    """
    x.requires_grad_(True)
    t.requires_grad_(True)
    
    u = model(x, t)
    
    # First derivatives
    u_t = torch.autograd.grad(u, t, torch.ones_like(u), create_graph=True)[0]
    u_x = torch.autograd.grad(u, x, torch.ones_like(u), create_graph=True)[0]
    
    # Second derivative
    u_xx = torch.autograd.grad(u_x, x, torch.ones_like(u_x), create_graph=True)[0]
    
    # PDE residual (alpha = 0.01)
    alpha = 0.01
    residual = u_t - alpha * u_xx
    
    return residual


def train_pinn(model, x_train, t_train, u_train, epochs=5000, lr=0.001):
    """Train the PINN using both data loss and physics loss"""
    
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    # Convert to tensors
    x_tensor = torch.tensor(x_train, dtype=torch.float32).reshape(-1, 1)
    t_tensor = torch.tensor(t_train, dtype=torch.float32).reshape(-1, 1)
    u_tensor = torch.tensor(u_train, dtype=torch.float32).reshape(-1, 1)
    
    losses = []
    
    print("Training PINN...")
    for epoch in range(epochs):
        optimizer.zero_grad()
        
        # Data loss: match the training data
        u_pred = model(x_tensor, t_tensor)
        data_loss = torch.mean((u_pred - u_tensor)**2)
        
        # Physics loss: satisfy PDE at collocation points
        residual = compute_pde_residual(model, x_tensor, t_tensor)
        physics_loss = torch.mean(residual**2)
        
        # Total loss
        loss = data_loss + physics_loss
        
        loss.backward()
        optimizer.step()
        
        losses.append(loss.item())
        
        if (epoch + 1) % 1000 == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.6f}, "
                  f"Data Loss: {data_loss.item():.6f}, Physics Loss: {physics_loss.item():.6f}")
    
    return losses


def visualize_results(model, x_data, t_data, u_data, losses):
    """Create visualization of training and predictions"""
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    # Plot 1: Training loss
    axes[0].plot(losses)
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Training Loss')
    axes[0].set_yscale('log')
    axes[0].grid(True)
    
    # Plot 2: True solution
    x_unique = np.unique(x_data)
    t_unique = np.unique(t_data)
    u_true = u_data.reshape(len(t_unique), len(x_unique))
    
    im1 = axes[1].contourf(x_unique, t_unique, u_true, levels=50, cmap='hot')
    axes[1].set_xlabel('x')
    axes[1].set_ylabel('t')
    axes[1].set_title('True Solution u(x,t)')
    plt.colorbar(im1, ax=axes[1])
    
    # Plot 3: PINN prediction
    x_tensor = torch.tensor(x_data, dtype=torch.float32).reshape(-1, 1)
    t_tensor = torch.tensor(t_data, dtype=torch.float32).reshape(-1, 1)
    
    with torch.no_grad():
        u_pred = model(x_tensor, t_tensor).numpy().flatten()
    
    u_pred_grid = u_pred.reshape(len(t_unique), len(x_unique))
    im2 = axes[2].contourf(x_unique, t_unique, u_pred_grid, levels=50, cmap='hot')
    axes[2].set_xlabel('x')
    axes[2].set_ylabel('t')
    axes[2].set_title('PINN Prediction')
    plt.colorbar(im2, ax=axes[2])
    
    plt.tight_layout()
    plt.savefig('demo_pinn_results.png', dpi=150, bbox_inches='tight')
    print("\nVisualization saved as 'demo_pinn_results.png'")
    
    # Compute error
    error = np.mean((u_data - u_pred)**2)
    print(f"Mean Squared Error: {error:.6e}")


def main():
    print("="*60)
    print("PhysForge Minimal Demo: PINN for Heat Equation")
    print("="*60)
    
    # 1. Generate training data
    print("\n1. Generating data from heat equation...")
    x_data, t_data, u_data = generate_heat_equation_data()
    print(f"   Generated {len(x_data)} data points")
    print(f"   Equation: ∂u/∂t = 0.01 ∂²u/∂x²")
    
    # 2. Create and train PINN
    print("\n2. Creating Physics-Informed Neural Network...")
    model = PINN(layers=[2, 32, 32, 32, 1])
    print(f"   Network: {sum(p.numel() for p in model.parameters())} parameters")
    
    print("\n3. Training...")
    losses = train_pinn(model, x_data, t_data, u_data, epochs=5000)
    
    # 3. Visualize results
    print("\n4. Creating visualization...")
    visualize_results(model, x_data, t_data, u_data, losses)
    
    print("\n" + "="*60)
    print("✓ Demo complete!")
    print("="*60)
    print("\nThis demonstrates PhysForge's core capability:")
    print("- Generate/load PDE data")
    print("- Train PINN using automatic differentiation")
    print("- Enforce physics constraints during training")
    print("- Visualize and validate results")
    print("\nThe full platform adds:")
    print("- Microservices architecture for scalability")
    print("- Job queuing and monitoring")
    print("- Symbolic regression for equation discovery")
    print("- Active learning for experimental design")
    print("="*60)


if __name__ == "__main__":
    main()
