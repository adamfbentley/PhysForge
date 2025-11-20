"""
Generate sample data from Korteweg-de Vries (KdV) Equation

KdV equation: ∂u/∂t = -α·u·∂u/∂x - β·∂³u/∂x³

This equation models:
- Shallow water waves
- Plasma waves
- Soliton propagation

The KdV equation has exact soliton solutions that maintain their shape.
"""

import numpy as np
import pandas as pd
from scipy.integrate import odeint

def kdv_pde(u, x, t, alpha=1.0, beta=0.01):
    """
    Compute spatial derivatives for KdV equation
    
    du/dt = -alpha * u * du/dx - beta * d³u/dx³
    """
    n = len(u)
    dx = x[1] - x[0]
    
    # First derivative (central difference)
    u_x = np.zeros_like(u)
    u_x[1:-1] = (u[2:] - u[:-2]) / (2 * dx)
    u_x[0] = (u[1] - u[-1]) / (2 * dx)  # Periodic
    u_x[-1] = (u[0] - u[-2]) / (2 * dx)  # Periodic
    
    # Third derivative (using 5-point stencil)
    u_xxx = np.zeros_like(u)
    for i in range(n):
        # Use periodic boundary conditions
        im2 = (i - 2) % n
        im1 = (i - 1) % n
        ip1 = (i + 1) % n
        ip2 = (i + 2) % n
        
        u_xxx[i] = (u[ip2] - 2*u[ip1] + 2*u[im1] - u[im2]) / (2 * dx**3)
    
    # KdV equation: du/dt = -alpha * u * u_x - beta * u_xxx
    du_dt = -alpha * u * u_x - beta * u_xxx
    
    return du_dt

def kdv_soliton_solution(x, t, c=1.0, x0=0.5):
    """
    Exact soliton solution to KdV equation
    
    u(x,t) = (c/2) * sech²((sqrt(c)/2) * (x - ct - x0))
    """
    amplitude = c / 2
    width = np.sqrt(c) / 2
    position = x - c * t - x0
    
    # sech(z) = 1/cosh(z)
    u = amplitude / (np.cosh(width * position))**2
    
    return u

def solve_kdv_equation(x, t, alpha=1.0, beta=0.01, c=1.0):
    """
    Solve KdV equation using method of lines
    
    Parameters:
    -----------
    x : array, spatial grid
    t : array, time grid
    alpha : float, nonlinear coefficient
    beta : float, dispersion coefficient
    c : float, wave speed for initial soliton
    
    Returns:
    --------
    u : array, solution at each (x, t)
    """
    # Initial condition: soliton
    u0 = kdv_soliton_solution(x, 0, c=c, x0=0.3)
    
    # Solve ODE in time
    def rhs(u, t_val):
        return kdv_pde(u, x, t_val, alpha, beta)
    
    # Integrate in time
    u_all = odeint(rhs, u0, t)
    
    return u_all

def generate_kdv_data(nx=50, nt=50, alpha=1.0, beta=0.01):
    """
    Generate KdV equation dataset
    
    Parameters:
    -----------
    nx : int, number of spatial points
    nt : int, number of time points
    alpha : float, nonlinear coefficient
    beta : float, dispersion coefficient
    
    Returns:
    --------
    DataFrame with columns: x, t, u
    """
    # Create grid
    x = np.linspace(0, 1, nx)
    t = np.linspace(0, 0.5, nt)  # Shorter time to keep soliton in domain
    
    # Solve KdV equation
    print(f"Solving KdV equation (α={alpha}, β={beta})...")
    print("  This includes third-order dispersion: ∂³u/∂x³")
    u_solution = solve_kdv_equation(x, t, alpha, beta, c=1.0)
    
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
    
    return df, alpha, beta

if __name__ == "__main__":
    print("Generating Korteweg-de Vries (KdV) equation dataset...")
    print("="*60)
    
    # Generate data
    df, alpha, beta = generate_kdv_data(nx=50, nt=50, alpha=1.0, beta=0.01)
    
    # Save to CSV
    output_file = "sample_kdv_equation.csv"
    df.to_csv(output_file, index=False)
    
    print(f"✓ Generated {len(df)} data points")
    print(f"  Nonlinear coefficient (α): {alpha}")
    print(f"  Dispersion coefficient (β): {beta}")
    print(f"  Spatial domain: [0, 1]")
    print(f"  Time domain: [0, 0.5]")
    print(f"  Saved to: {output_file}")
    print()
    print("Expected equation to discover:")
    print(f"  ∂u/∂t = -{alpha:.6f}·u·∂u/∂x - {beta:.6f}·∂³u/∂x³")
    print()
    print("Expected terms:")
    print(f"  ✓ u*u_x with coefficient ≈ -{alpha:.6f} (nonlinear advection)")
    print(f"  ✓ u_xxx with coefficient ≈ -{beta:.6f} (dispersion)")
    print()
    print("Note: This is a soliton solution - a wave that maintains its shape!")
    print("Upload this file to PhysForge to test third-order derivative discovery!")
