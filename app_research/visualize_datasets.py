"""
Visualize all three physics datasets side-by-side
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

def visualize_datasets():
    """Create side-by-side visualization of all three datasets"""
    
    # Load datasets
    heat_df = pd.read_csv('sample_heat_equation.csv')
    burgers_df = pd.read_csv('sample_burgers_equation.csv')
    kdv_df = pd.read_csv('sample_kdv_equation.csv')
    
    # Reshape data
    datasets = [
        ('Heat Equation\n∂u/∂t = 0.01·∂²u/∂x²', heat_df),
        ('Burgers Equation\n∂u/∂t = 0.01·∂²u/∂x² - u·∂u/∂x', burgers_df),
        ('KdV Equation\n∂u/∂t = -1.0·u·∂u/∂x - 0.01·∂³u/∂x³', kdv_df)
    ]
    
    # Create figure
    fig = plt.figure(figsize=(18, 6))
    gs = GridSpec(2, 3, figure=fig, height_ratios=[1, 0.3], hspace=0.4, wspace=0.3)
    
    for idx, (title, df) in enumerate(datasets):
        # Get unique values
        x_unique = np.sort(df['x'].unique())
        t_unique = np.sort(df['t'].unique())
        
        # Reshape u values
        u_grid = df.pivot(index='t', columns='x', values='u').values
        
        # Main plot
        ax = fig.add_subplot(gs[0, idx])
        im = ax.contourf(x_unique, t_unique, u_grid, levels=50, cmap='RdBu_r')
        ax.set_xlabel('x (space)', fontsize=11)
        ax.set_ylabel('t (time)', fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        plt.colorbar(im, ax=ax, label='u')
        
        # Statistics panel
        ax_stats = fig.add_subplot(gs[1, idx])
        ax_stats.axis('off')
        
        stats_text = f"""
        Data Points: {len(df):,}
        x range: [{df['x'].min():.2f}, {df['x'].max():.2f}]
        t range: [{df['t'].min():.2f}, {df['t'].max():.2f}]
        u range: [{df['u'].min():.3f}, {df['u'].max():.3f}]
        """
        
        ax_stats.text(0.1, 0.5, stats_text, fontsize=9, family='monospace',
                     verticalalignment='center',
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.suptitle('PhysForge Test Datasets - Three Physics Regimes', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    plt.savefig('datasets_comparison.png', dpi=150, bbox_inches='tight')
    print("✓ Saved visualization to: datasets_comparison.png")
    plt.close()

if __name__ == "__main__":
    print("Creating datasets comparison visualization...")
    visualize_datasets()
    print()
    print("Upload these datasets to PhysForge to test:")
    print("  1. sample_heat_equation.csv      → Should find: u_xx")
    print("  2. sample_burgers_equation.csv   → Should find: u_xx, u*u_x")
    print("  3. sample_kdv_equation.csv       → Should find: u*u_x, u_xxx")
