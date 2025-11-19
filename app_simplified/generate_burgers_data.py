"""
Generate sample data from Burgers Equation

Burgers equation: ∂u/∂t = ν∇²u - u·∇u
In 1D: ∂u/∂t = ν∂²u/∂x² - u·∂u/∂x

This is a fundamental equation in fluid dynamics that models:
- Viscous diffusion (ν∂²u/∂x²)
- Nonlinear convection (-u·∂u/∂x)

The equation can develop shock waves when viscosity is small.
"""

import numpy as np
import pandas as pd
from scipy.integrate import odeint

def burgers_pde(u, x, t, nu=0.01):
    """
    Compute spatial derivatives for Burgers equation
    
    du/dt = nu * d²u/dx² - u * du/dx
    """
    # Periodic boundary conditions
    n = len(u)
    dx = x[1] - x[0]
    
    # First derivative (central difference)
    u_x = np.zeros_like(u)
    u_x[1:-1] = (u[2:] - u[:-2]) / (2 * dx)
    u_x[0] = (u[1] - u[-1]) / (2 * dx)  # Periodic
    u_x[-1] = (u[0] - u[-2]) / (2 * dx)  # Periodic
    
    # Second derivative (central difference)
    u_xx = np.zeros_like(u)
    u_xx[1:-1] = (u[2:] - 2*u[1:-1] + u[:-2]) / (dx**2)
    u_xx[0] = (u[1] - 2*u[0] + u[-1]) / (dx**2)  # Periodic
    u_xx[-1] = (u[0] - 2*u[-1] + u[-2]) / (dx**2)  # Periodic
    
    # Burgers equation: du/dt = nu * u_xx - u * u_x
    du_dt = nu * u_xx - u * u_x
    
    return du_dt

def solve_burgers_equation(x, t, nu=0.01):
    """
    Solve Burgers equation using method of lines
    
    Parameters:
    -----------
    x : array, spatial grid
    t : array, time grid
    nu : float, viscosity coefficient (default 0.01)
    
    Returns:
    --------
    u : array, solution at each (x, t)
    """
    # Initial condition: smooth wave
    u0 = np.sin(2 * np.pi * x) + 0.5 * np.sin(4 * np.pi * x)
    
    # Solve ODE in time for each spatial point
    def rhs(u, t_val):
        return burgers_pde(u, x, t_val, nu)
    
    # Integrate in time
    u_all = odeint(rhs, u0, t)
    
    return u_all

def generate_burgers_data(nx=50, nt=50, nu=0.01):
    """
    Generate Burgers equation dataset
    
    Parameters:
    -----------
    nx : int, number of spatial points
    nt : int, number of time points
    nu : float, viscosity (default 0.01)
    
    Returns:
    --------
    DataFrame with columns: x, t, u
    """
    # Create grid
    x = np.linspace(0, 1, nx)
    t = np.linspace(0, 2.0, nt)
    
    # Solve Burgers equation
    print(f"Solving Burgers equation (ν={nu})...")
    print("  This includes nonlinear convection: u·∂u/∂x")
    u_solution = solve_burgers_equation(x, t, nu)
    
    # Create meshgrid
    X, T = np.meshgrid(x, t)
    
    # Flatten arrays
    x_flat = X.flatten()
    t_flat = T.flatten()
    u_flat = u_solution.flatten()
    
    # Create DataFrame
    df = pd.DataFrame({
        'x': x_flat,
        't': t_flat,
        'u': u_flat
    })
    
    return df, nu

if __name__ == "__main__":
    print("Generating Burgers equation dataset...")
    print("="*60)
    
    # Generate data
    df, nu = generate_burgers_data(nx=50, nt=50, nu=0.01)
    
    # Save to CSV
    output_file = "sample_burgers_equation.csv"
    df.to_csv(output_file, index=False)
    
    print(f"✓ Generated {len(df)} data points")
    print(f"  Viscosity (ν): {nu}")
    print(f"  Spatial domain: [0, 1]")
    print(f"  Time domain: [0, 2.0]")
    print(f"  Saved to: {output_file}")
    print()
    print("Expected equation to discover:")
    print(f"  ∂u/∂t = {nu:.6f}·∂²u/∂x² - u·∂u/∂x")
    print()
    print("Expected terms:")
    print(f"  ✓ u_xx with coefficient ≈ +{nu:.6f} (diffusion)")
    print(f"  ✓ u*u_x with coefficient ≈ -1.0 (nonlinear convection)")
    print()
    print("Upload this file to PhysForge to test nonlinear discovery!")
