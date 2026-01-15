"""
PhysForge - Simplified Full Stack Application

A working end-to-end application for:
1. Uploading datasets (CSV)
2. Training Physics-Informed Neural Networks
3. Discovering governing equations

Single-service architecture using FastAPI + SQLite
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import numpy as np
import torch
import torch.nn as nn
import pandas as pd
import sys
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import sqlite3
import json
import io
import os
from datetime import datetime
import uuid

# Create necessary directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("results", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Global status tracker for real-time progress
processing_status = {}

app = FastAPI(title="PhysForge", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_PATH = "physforge.db"

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            status TEXT,
            dataset_name TEXT,
            created_at TEXT,
            completed_at TEXT,
            error TEXT,
            result_data TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# PINN Model
class PINN(nn.Module):
    """Physics-Informed Neural Network"""
    
    def __init__(self, layers=[2, 32, 32, 32, 1]):
        super().__init__()
        self.layers = nn.ModuleList()
        for i in range(len(layers) - 1):
            self.layers.append(nn.Linear(layers[i], layers[i+1]))
    
    def forward(self, x, t):
        inputs = torch.cat([x, t], dim=1)
        for i, layer in enumerate(self.layers[:-1]):
            inputs = torch.tanh(layer(inputs))
        return self.layers[-1](inputs)

def compute_derivatives(model, x, t):
    """Compute derivatives using automatic differentiation
    
    Returns comprehensive set of derivatives for equation discovery:
    - First derivatives: u_x, u_t
    - Second derivatives: u_xx, u_tt, u_xt
    - Third derivatives: u_xxx
    """
    x.requires_grad_(True)
    t.requires_grad_(True)
    
    u = model(x, t)
    
    # First derivatives
    u_t = torch.autograd.grad(u, t, torch.ones_like(u), create_graph=True, retain_graph=True)[0]
    u_x = torch.autograd.grad(u, x, torch.ones_like(u), create_graph=True, retain_graph=True)[0]
    
    # Second derivatives
    u_xx = torch.autograd.grad(u_x, x, torch.ones_like(u_x), create_graph=True, retain_graph=True)[0]
    u_tt = torch.autograd.grad(u_t, t, torch.ones_like(u_t), create_graph=True, retain_graph=True)[0]
    u_xt = torch.autograd.grad(u_x, t, torch.ones_like(u_x), create_graph=True, retain_graph=True)[0]
    
    # Third derivative (for KdV, etc.)
    u_xxx = torch.autograd.grad(u_xx, x, torch.ones_like(u_xx), create_graph=True, retain_graph=True)[0]
    
    return {
        'u': u,
        'u_x': u_x,
        'u_t': u_t,
        'u_xx': u_xx,
        'u_tt': u_tt,
        'u_xt': u_xt,
        'u_xxx': u_xxx
    }

def train_pinn_on_data(x_data, t_data, u_data, epochs=1000, job_id=None):
    """Train PINN on provided data with equation-agnostic physics loss
    
    Uses weak-form physics loss that doesn't assume specific equation.
    The physics is discovered after training via sparse regression.
    """
    model = PINN(layers=[2, 32, 32, 32, 1])  # Larger network for better convergence
    optimizer = torch.optim.Adam(model.parameters(), lr=0.0005)
    
    x_tensor = torch.tensor(x_data, dtype=torch.float32).reshape(-1, 1)
    t_tensor = torch.tensor(t_data, dtype=torch.float32).reshape(-1, 1)
    u_tensor = torch.tensor(u_data, dtype=torch.float32).reshape(-1, 1)
    
    losses = []
    
    print(f"Starting PINN training: {epochs} epochs, {len(x_data)} data points", flush=True)
    if job_id:
        processing_status[job_id] = {
            "stage": "training",
            "progress": f"0/{epochs}",
            "message": f"🚀 Starting PINN training with {len(x_data)} data points..."
        }
    
    for epoch in range(epochs):
        optimizer.zero_grad()
        
        # Data loss (primary objective)
        u_pred = model(x_tensor, t_tensor)
        data_loss = torch.mean((u_pred - u_tensor)**2)
        
        # Smoothness regularization (lightweight - only compute what we need)
        # Encourages smooth solutions without assuming specific equation
        x_tensor.requires_grad_(True)
        t_tensor.requires_grad_(True)
        u = model(x_tensor, t_tensor)
        
        # Only compute the derivatives we actually use (u_t and u_xx)
        u_t = torch.autograd.grad(u, t_tensor, torch.ones_like(u), create_graph=True, retain_graph=True)[0]
        u_x = torch.autograd.grad(u, x_tensor, torch.ones_like(u), create_graph=True, retain_graph=True)[0]
        u_xx = torch.autograd.grad(u_x, x_tensor, torch.ones_like(u_x), create_graph=True, retain_graph=True)[0]
        
        # Penalize extreme derivatives (helps numerical stability)
        smoothness_loss = (
            0.001 * torch.mean(u_xx**2) +  # Spatial smoothness
            0.001 * torch.mean(u_t**2)     # Temporal smoothness
        )
        
        loss = data_loss + smoothness_loss
        loss.backward()
        optimizer.step()
        
        losses.append(loss.item())
        
        # Progress logging and memory cleanup
        if epoch % 200 == 0:
            print(f"  Epoch {epoch}/{epochs}, Loss: {loss.item():.6f}", flush=True)
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        # Update progress more frequently for UI (every 20 epochs or first epoch)
        if job_id and (epoch % 20 == 0 or epoch == 1):
            percent = (epoch / epochs) * 100
            processing_status[job_id] = {
                "stage": "training",
                "progress": f"{epoch}/{epochs}",
                "message": f"⚡ Epoch {epoch}/{epochs} ({percent:.1f}%) - Loss: {loss.item():.6f}"
            }
    
    print(f"Training complete. Final loss: {losses[-1]:.6f}", flush=True)
    if job_id:
        processing_status[job_id] = {
            "stage": "training_complete",
            "progress": f"{epochs}/{epochs}",
            "message": f"✅ Training complete! Final loss: {losses[-1]:.6f}"
        }
    
    return model, losses

def discover_equation(model, x_data, t_data, threshold: float = 0.05, job_id: Optional[str] = None,
                      bootstrap_samples: int = 10, sample_ratio: float = 0.7) -> tuple:
    """
    Discover PDE equation from a trained PINN using an iterative sparse regression (STLSQ) with bootstrap
    stability analysis. Compared to the original single-pass thresholded regression, this method
    iteratively refits the model after removing small coefficients and estimates the stability of
    discovered terms via random subsampling.

    Args:
        model: Trained PINN model.
        x_data, t_data: Arrays of space/time coordinates (1D).
        threshold: Coefficient threshold relative to the largest coefficient.
        job_id: Optional job identifier for UI progress updates.
        bootstrap_samples: Number of bootstrap runs for stability estimation.
        sample_ratio: Fraction of data points used in each bootstrap resample.

    Returns:
        equation_str: Human-readable PDE (e.g., "u_t = 0.010*u_xx - 0.100*u*u_x").
        coefficients: Dictionary of active terms and their coefficients.
        r_squared: Goodness of fit on full data.
        term_names: List of all candidate terms considered.
        stability_freq: Dict mapping term name to selection frequency across bootstraps (0-1).
        coeff_std: Dict mapping term name to standard deviation of coefficients across bootstraps.
        derivative_stable: Optional boolean indicating whether autograd derivatives agree with
                          finite-difference approximations (True => derivatives reliable).
    """
    print(f"Starting equation discovery using all {len(x_data)} data points", flush=True)
    if job_id:
        processing_status[job_id] = {
            "stage": "discovery",
            "progress": "0%",
            "message": f"🔬 Computing derivatives on {len(x_data)} data points..."
        }

    # Convert inputs to tensors for autograd
    x_tensor = torch.tensor(x_data, dtype=torch.float32).reshape(-1, 1)
    t_tensor = torch.tensor(t_data, dtype=torch.float32).reshape(-1, 1)

    # Compute derivatives via autograd
    derivs = compute_derivatives(model, x_tensor, t_tensor)

    # Flatten target and u for convenience
    u_t_np = derivs['u_t'].detach().numpy().flatten()
    u_np = derivs['u'].detach().numpy().flatten()

    # ------------------------------------------------------------------
    # Finite difference derivative sanity check on a regular grid
    derivative_stable = None
    try:
        # Check if the dataset forms a complete grid (n_x * n_t)
        xs = np.unique(x_data)
        ts = np.unique(t_data)
        if len(xs) * len(ts) == len(u_np):
            # Reshape predictions into grid
            with torch.no_grad():
                u_pred = model(x_tensor, t_tensor).numpy().flatten()
            u_pred_grid = u_pred.reshape(len(ts), len(xs))
            # Finite difference along x and t (interior points)
            dx = xs[1] - xs[0] if len(xs) > 1 else 1.0
            dt = ts[1] - ts[0] if len(ts) > 1 else 1.0
            # Compute FD derivatives on grid (central difference)
            fd_u_x = (u_pred_grid[:, 2:] - u_pred_grid[:, :-2]) / (2 * dx)
            fd_u_t = (u_pred_grid[2:, :] - u_pred_grid[:-2, :]) / (2 * dt)
            # Autograd derivatives on matching interior points
            u_x_autograd = derivs['u_x'].detach().numpy().flatten().reshape(len(ts), len(xs))
            u_t_autograd = derivs['u_t'].detach().numpy().flatten().reshape(len(ts), len(xs))
            u_x_autograd_int = u_x_autograd[:, 1:-1]
            u_t_autograd_int = u_t_autograd[1:-1, :]
            # Compute relative errors
            err_x = np.linalg.norm(fd_u_x - u_x_autograd_int) / (np.linalg.norm(u_x_autograd_int) + 1e-12)
            err_t = np.linalg.norm(fd_u_t - u_t_autograd_int) / (np.linalg.norm(u_t_autograd_int) + 1e-12)
            derivative_stable = (max(err_x, err_t) < 0.5)
        else:
            derivative_stable = None
    except Exception:
        derivative_stable = None

    # ------------------------------------------------------------------
    # Candidate library (restricted by default to avoid overfitting)
    if job_id:
        processing_status[job_id] = {
            "stage": "discovery",
            "progress": "40%",
            "message": "📚 Building candidate term library..."
        }

    library = {}
    # Base terms
    library['u'] = u_np
    library['u_x'] = derivs['u_x'].detach().numpy().flatten()
    library['u_xx'] = derivs['u_xx'].detach().numpy().flatten()
    library['u_xxx'] = derivs['u_xxx'].detach().numpy().flatten()
    # Nonlinear terms
    library['u*u_x'] = u_np * library['u_x']
    # Optional higher-order nonlinearities (commented for now)
    library['u²'] = u_np ** 2
    # library['u³'] = u_np ** 3

    # Names and full design matrix
    term_names = list(library.keys())
    X_full = np.column_stack([library[name] for name in term_names])

    if job_id:
        processing_status[job_id] = {
            "stage": "discovery",
            "progress": "50%",
            "message": f"📊 Running sparse regression on {len(term_names)} candidate terms..."
        }

    # ------------------------------------------------------------------
    # Helper: iterative thresholded least squares (STLSQ)
    def stlsq(X, y, thr):
        # Normalize columns
        X_std = np.std(X, axis=0)
        X_std[X_std < 1e-10] = 1.0
        X_norm = X / X_std
        # Active mask (all terms start active)
        active = np.ones(X_norm.shape[1], dtype=bool)
        coeffs = np.zeros(X_norm.shape[1])
        while True:
            # Fit only on active columns
            Xa = X_norm[:, active]
            # Solve least squares
            try:
                coeffs_norm, *_ = np.linalg.lstsq(Xa, y, rcond=None)
            except np.linalg.LinAlgError:
                coeffs_norm = np.zeros(Xa.shape[1])
            # Un-normalize
            coeffs_full = np.zeros_like(coeffs)
            coeffs_full[active] = coeffs_norm / X_std[active]
            # Threshold
            max_c = np.max(np.abs(coeffs_full)) if coeffs_full.size else 0.0
            # Avoid division by zero
            if max_c == 0:
                break
            new_active = np.abs(coeffs_full) >= thr * max_c
            # If no change, stop
            if np.array_equal(new_active, active):
                coeffs = coeffs_full
                break
            # If all dropped, keep at least the largest term
            if np.sum(new_active) == 0:
                idx_max = np.argmax(np.abs(coeffs_full))
                new_active[idx_max] = True
            active = new_active
        return coeffs

    # ------------------------------------------------------------------
    # Bootstrap stability analysis
    rng = np.random.default_rng()
    n = len(u_t_np)
    selection_counts = {name: 0 for name in term_names}
    coeff_hist = {name: [] for name in term_names}
    for b in range(max(1, bootstrap_samples)):
        # Random subset indices
        idx = rng.choice(n, size=int(sample_ratio * n), replace=False)
        X_sub = X_full[idx]
        y_sub = u_t_np[idx]
        coeffs_b = stlsq(X_sub, y_sub, threshold)
        # Record selections and values
        for name, coeff in zip(term_names, coeffs_b):
            if coeff != 0:
                selection_counts[name] += 1
                coeff_hist[name].append(coeff)

    stability_freq = {name: selection_counts[name] / max(1, bootstrap_samples) for name in term_names}
    coeff_std = {name: (float(np.std(coeff_hist[name])) if len(coeff_hist[name]) > 1 else 0.0)
                 for name in term_names}

    # ------------------------------------------------------------------
    # Final coefficients using all data
    final_coeffs = stlsq(X_full, u_t_np, threshold)
    final_active_coeffs = {}
    active_terms_list = []
    for name, coeff in zip(term_names, final_coeffs):
        if coeff != 0:
            final_active_coeffs[name] = float(coeff)
            sign = "+" if coeff > 0 else ""
            active_terms_list.append(f"{sign}{coeff:.6f}*{name}")

    if active_terms_list:
        equation_str = "u_t = " + " ".join(active_terms_list).replace("+ -", "- ")
    else:
        equation_str = "u_t = 0 (no significant terms found)"

    # ------------------------------------------------------------------
    # Compute R² on full data using only active terms
    if len(final_active_coeffs) > 0:
        active_idx = [i for i, name in enumerate(term_names) if name in final_active_coeffs]
        X_active = X_full[:, active_idx]
        coeffs_vec = np.array([final_active_coeffs[term_names[i]] for i in active_idx])
        u_t_pred = X_active @ coeffs_vec
    else:
        u_t_pred = np.zeros_like(u_t_np)
    ss_res = np.sum((u_t_np - u_t_pred)**2)
    ss_tot = np.sum((u_t_np - np.mean(u_t_np))**2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    if job_id:
        message = "";
        active_count = len(final_active_coeffs)
        if active_count == 0:
            message = "⚠️ No significant terms found - data may be too noisy"
        elif active_count > 8:
            message = f"⚠️ Found {active_count} terms - equation may be overfitting"
        else:
            message = f"🎯 Equation discovered! Found {active_count} active term{'s' if active_count != 1 else ''}"
        processing_status[job_id] = {
            "stage": "discovery",
            "progress": "100%",
            "message": message
        }

    return equation_str, final_active_coeffs, r_squared, term_names, stability_freq, coeff_std, derivative_stable

def create_visualization(model, x_data, t_data, u_data, losses, 
                        equation_str, coefficients, r_squared, job_id):
    """Create visualization of results with discovered equation"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Training loss
    axes[0, 0].plot(losses)
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Loss')
    axes[0, 0].set_title('Training Loss')
    axes[0, 0].set_yscale('log')
    axes[0, 0].grid(True)
    
    # True solution
    x_unique = np.unique(x_data)
    t_unique = np.unique(t_data)
    u_true = u_data.reshape(len(t_unique), len(x_unique))
    
    im1 = axes[0, 1].contourf(x_unique, t_unique, u_true, levels=50, cmap='hot')
    axes[0, 1].set_xlabel('x')
    axes[0, 1].set_ylabel('t')
    axes[0, 1].set_title('Input Data')
    plt.colorbar(im1, ax=axes[0, 1])
    
    # PINN prediction
    x_tensor = torch.tensor(x_data, dtype=torch.float32).reshape(-1, 1)
    t_tensor = torch.tensor(t_data, dtype=torch.float32).reshape(-1, 1)
    
    with torch.no_grad():
        u_pred = model(x_tensor, t_tensor).numpy().flatten()
    
    u_pred_grid = u_pred.reshape(len(t_unique), len(x_unique))
    im2 = axes[1, 0].contourf(x_unique, t_unique, u_pred_grid, levels=50, cmap='hot')
    axes[1, 0].set_xlabel('x')
    axes[1, 0].set_ylabel('t')
    axes[1, 0].set_title('PINN Prediction')
    plt.colorbar(im2, ax=axes[1, 0])
    
    # Discovered equation
    axes[1, 1].axis('off')
    
    # Format equation nicely
    eq_display = equation_str.replace('u_t', '∂u/∂t')
    eq_display = eq_display.replace('u_xx', '∂²u/∂x²')
    eq_display = eq_display.replace('u_xxx', '∂³u/∂x³')
    eq_display = eq_display.replace('u_tt', '∂²u/∂t²')
    eq_display = eq_display.replace('u_xt', '∂²u/∂x∂t')
    eq_display = eq_display.replace('u_x', '∂u/∂x')
    eq_display = eq_display.replace('*', '·')
    
    # Build coefficient table
    coeff_lines = []
    for term, coeff in sorted(coefficients.items(), key=lambda x: abs(x[1]), reverse=True):
        coeff_lines.append(f"  {term:8s} = {coeff:+.6f}")
    
    coeff_text = "\n".join(coeff_lines[:5])  # Show top 5 terms
    if len(coefficients) > 5:
        coeff_text += f"\n  ... and {len(coefficients) - 5} more"
    
    equation_text = f"""
DISCOVERED EQUATION
{'='*45}

{eq_display}

R² Score: {r_squared:.6f}

Active Coefficients:
{coeff_text}

{'✓ Equation discovered!' if coefficients else '⚠ No significant terms'}
    """
    
    axes[1, 1].text(0.05, 0.5, equation_text, fontsize=11, family='monospace',
                     verticalalignment='center', wrap=True)
    
    plt.tight_layout()
    output_path = f"results/{job_id}.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path

# API Models
class JobStatus(BaseModel):
    id: str
    status: str
    dataset_name: str
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result: Optional[dict] = None

# Background task for training
def process_job(job_id: str, filepath: str):
    """Background task to process uploaded data"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Update status to processing
        c.execute("UPDATE jobs SET status = 'processing' WHERE id = ?", (job_id,))
        conn.commit()
        
        # Load data
        df = pd.read_csv(filepath)
        
        # Expect columns: x, t, u
        if not all(col in df.columns for col in ['x', 't', 'u']):
            raise ValueError("CSV must contain columns: x, t, u")
        
        x_data = df['x'].values
        t_data = df['t'].values
        u_data = df['u'].values
        
        # Train PINN
        model, losses = train_pinn_on_data(x_data, t_data, u_data, epochs=1000, job_id=job_id)
        
        # Discover equation (using all available data)
        # The discover_equation function returns additional stability information in this version:
        # equation_str: string representation of the PDE
        # coefficients: dictionary of active term coefficients
        # r_squared: goodness of fit
        # all_terms: list of all candidate terms considered
        # stability_freq: selection frequency of each term across bootstrap samples
        # coeff_std: standard deviation of coefficients across bootstrap samples
        # derivative_stable: boolean indicating whether finite difference derivatives agree with autograd
        equation_str, coefficients, r_squared, all_terms, stability_freq, coeff_std, derivative_stable = discover_equation(
            model, x_data, t_data, job_id=job_id
        )
        
        # Create visualization
        viz_path = create_visualization(model, x_data, t_data, u_data, losses, 
                                       equation_str, coefficients, r_squared, job_id)
        
        # Compute final error
        x_tensor = torch.tensor(x_data, dtype=torch.float32).reshape(-1, 1)
        t_tensor = torch.tensor(t_data, dtype=torch.float32).reshape(-1, 1)
        with torch.no_grad():
            u_pred = model(x_tensor, t_tensor).numpy().flatten()
        mse = np.mean((u_data - u_pred)**2)
        
        # Assess quality of discovered equation.
        # Base classification on r_squared and number of active terms. We further penalize if the
        # derivative stability check fails or if many active terms have low bootstrap frequency.
        num_terms = len(coefficients)
        # Start with a base quality determined by fit and sparsity
        if r_squared > 0.95 and num_terms <= 3:
            quality = "excellent"
        elif r_squared > 0.85 and num_terms <= 5:
            quality = "good"
        elif r_squared > 0.70:
            quality = "fair"
        else:
            quality = "poor"

        # Penalize quality if derivatives appear unstable
        if derivative_stable is False:
            # degrade by one level
            if quality == "excellent":
                quality = "good"
            elif quality == "good":
                quality = "fair"
            else:
                quality = "poor"

        # Penalize if active terms have low bootstrap selection frequency (<0.6)
        unstable_terms = [name for name in coefficients.keys() if stability_freq.get(name, 1.0) < 0.6]
        if unstable_terms:
            # degrade by one level
            if quality == "excellent":
                quality = "good"
            elif quality == "good":
                quality = "fair"
            else:
                quality = "poor"

        # Assemble result dictionary with extended metrics
        result = {
            "equation": equation_str,
            "coefficients": coefficients,
            "r_squared": float(r_squared),
            "mse": float(mse),
            "final_loss": float(losses[-1]),
            "epochs": len(losses),
            "terms_tested": all_terms,
            "visualization": viz_path,
            "quality": quality,
            "num_terms": num_terms,
            "stability_freq": stability_freq,
            "coeff_std": coeff_std,
            "derivative_stable": derivative_stable
        }
        
        result_json = json.dumps(result)
        print(f"Storing result (length: {len(result_json)} chars): {result_json[:200]}...", flush=True)
        
        c.execute("""
            UPDATE jobs 
            SET status = 'completed', 
                completed_at = ?,
                result_data = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), result_json, job_id))
        conn.commit()
        
        print(f"✅ Job {job_id} completed successfully", flush=True)
        print(f"   Equation: {equation_str}", flush=True)
        print(f"   R²: {r_squared:.6f}", flush=True)
        print(f"   Active terms: {len(coefficients)}", flush=True)
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"❌ Job {job_id} failed: {error_msg}", flush=True)
        import traceback
        traceback.print_exc()
        
        try:
            c.execute("""
                UPDATE jobs 
                SET status = 'failed', 
                    error = ?,
                    completed_at = ?
                WHERE id = ?
            """, (error_msg, datetime.now().isoformat(), job_id))
            conn.commit()
        except Exception as db_error:
            print(f"❌ Failed to update job status: {db_error}", flush=True)
    
    finally:
        conn.close()

# API Endpoints
# Serve the main web interface. We deliver the top-level index.html from the root of the repository rather than
# relying on a static directory that may not exist in this simplified deployment.
@app.get("/")
async def root():
    """Serve the main web interface"""
    return FileResponse("index.html")

@app.post("/api/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a dataset and start training"""
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    filepath = f"uploads/{job_id}.csv"
    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)
    
    # Create job record
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO jobs (id, status, dataset_name, created_at)
        VALUES (?, ?, ?, ?)
    """, (job_id, "queued", file.filename, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    # Start background processing
    background_tasks.add_task(process_job, job_id, filepath)
    
    return {"job_id": job_id, "status": "queued"}

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a training job"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    
    result_data = json.loads(row[6]) if row[6] else None
    
    # Add real-time processing status if available
    processing_info = processing_status.get(job_id, None)
    
    return {
        "id": row[0],
        "status": row[1],
        "dataset_name": row[2],
        "created_at": row[3],
        "completed_at": row[4],
        "error": row[5],
        "result": result_data,
        "processing": processing_info  # Real-time progress
    }

@app.get("/api/jobs/{job_id}/progress")
async def get_job_progress(job_id: str):
    """Get real-time processing progress for a job"""
    if job_id in processing_status:
        return processing_status[job_id]
    return {"stage": "unknown", "progress": "N/A", "message": "No progress data available"}

@app.get("/api/jobs")
async def list_jobs():
    """List all jobs"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, status, dataset_name, created_at, completed_at FROM jobs ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    
    jobs = []
    for row in rows:
        jobs.append({
            "id": row[0],
            "status": row[1],
            "dataset_name": row[2],
            "created_at": row[3],
            "completed_at": row[4]
        })
    
    return jobs

@app.get("/api/results/{job_id}/visualization")
async def get_visualization(job_id: str):
    """Get visualization image for a completed job"""
    viz_path = f"results/{job_id}.png"
    if not os.path.exists(viz_path):
        raise HTTPException(status_code=404, detail="Visualization not found")
    return FileResponse(viz_path, media_type="image/png")

# Removed duplicate root endpoint. The main UI is served by the root() function defined above.

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print("="*60)
    print("Starting PhysForge...")
    print("="*60)
    print(f"Open your browser to: http://localhost:{port}")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=port)
