"""
Generate sample heat equation data for testing PhysForge
"""
import numpy as np
import pandas as pd

def generate_heat_equation_data(nx=50, nt=50, L=1.0, T=0.5, alpha=0.01):
    """Generate data from 1D heat equation"""
    x = np.linspace(0, L, nx)
    t = np.linspace(0, T, nt)
    dx = L / (nx - 1)
    dt = T / (nt - 1)
    
    # Initial condition: Gaussian pulse
    u = np.zeros((nt, nx))
    u[0, :] = np.exp(-100 * (x - 0.5)**2)
    
    # Solve using explicit finite difference
    r = alpha * dt / dx**2
    for n in range(nt - 1):
        for i in range(1, nx - 1):
            u[n+1, i] = u[n, i] + r * (u[n, i+1] - 2*u[n, i] + u[n, i-1])
    
    # Create dataset
    X, T = np.meshgrid(x, t)
    data = pd.DataFrame({
        'x': X.flatten(),
        't': T.flatten(),
        'u': u.flatten()
    })
    
    return data

if __name__ == "__main__":
    print("Generating sample heat equation data...")
    data = generate_heat_equation_data()
    data.to_csv("sample_heat_equation.csv", index=False)
    print(f"✓ Generated {len(data)} data points")
    print(f"  Saved to: sample_heat_equation.csv")
    print(f"\nYou can now upload this file to PhysForge!")
