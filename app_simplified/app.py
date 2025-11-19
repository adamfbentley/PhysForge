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

def train_pinn_on_data(x_data, t_data, u_data, epochs=3000):
    """Train PINN on provided data with equation-agnostic physics loss
    
    Uses weak-form physics loss that doesn't assume specific equation.
    The physics is discovered after training via sparse regression.
    """
    model = PINN(layers=[2, 32, 32, 32, 1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    x_tensor = torch.tensor(x_data, dtype=torch.float32).reshape(-1, 1)
    t_tensor = torch.tensor(t_data, dtype=torch.float32).reshape(-1, 1)
    u_tensor = torch.tensor(u_data, dtype=torch.float32).reshape(-1, 1)
    
    losses = []
    
    for epoch in range(epochs):
        optimizer.zero_grad()
        
        # Data loss (primary objective)
        u_pred = model(x_tensor, t_tensor)
        data_loss = torch.mean((u_pred - u_tensor)**2)
        
        # Smoothness regularization (weak physics prior)
        # Encourages smooth solutions without assuming specific equation
        derivs = compute_derivatives(model, x_tensor, t_tensor)
        
        # Penalize extreme derivatives (helps numerical stability)
        smoothness_loss = (
            0.001 * torch.mean(derivs['u_xx']**2) +  # Spatial smoothness
            0.001 * torch.mean(derivs['u_t']**2)     # Temporal smoothness
        )
        
        loss = data_loss + smoothness_loss
        loss.backward()
        optimizer.step()
        
        losses.append(loss.item())
    
    return model, losses

def discover_equation(model, x_data, t_data, sample_size=500, threshold=0.01):
    """Discover PDE equation from trained PINN using sparse regression
    
    Builds a library of candidate terms and uses least squares with
    thresholding (simplified SINDy approach) to find active terms.
    
    Returns:
        equation_str: Human-readable equation (e.g., "u_t = 0.010*u_xx + 0.002*u*u_x")
        coefficients: Dict of non-zero coefficients
        r_squared: Goodness of fit
        terms_tested: All terms that were considered
    """
    # Sample random points for discovery
    indices = np.random.choice(len(x_data), size=min(sample_size, len(x_data)), replace=False)
    x_sample = x_data[indices]
    t_sample = t_data[indices]
    
    x_tensor = torch.tensor(x_sample, dtype=torch.float32).reshape(-1, 1)
    t_tensor = torch.tensor(t_sample, dtype=torch.float32).reshape(-1, 1)
    
    # Compute all derivatives
    derivs = compute_derivatives(model, x_tensor, t_tensor)
    
    # Target: u_t (left-hand side of PDE)
    u_t_np = derivs['u_t'].detach().numpy().flatten()
    u_np = derivs['u'].detach().numpy().flatten()
    
    # Build library of candidate terms (right-hand side)
    library = {}
    
    # Linear terms
    library['u'] = u_np
    library['u_x'] = derivs['u_x'].detach().numpy().flatten()
    
    # Second derivatives
    library['u_xx'] = derivs['u_xx'].detach().numpy().flatten()
    library['u_tt'] = derivs['u_tt'].detach().numpy().flatten()
    library['u_xt'] = derivs['u_xt'].detach().numpy().flatten()
    
    # Third derivative
    library['u_xxx'] = derivs['u_xxx'].detach().numpy().flatten()
    
    # Nonlinear terms
    library['u²'] = u_np ** 2
    library['u³'] = u_np ** 3
    library['u*u_x'] = u_np * library['u_x']
    library['u*u_xx'] = u_np * library['u_xx']
    library['u_x²'] = library['u_x'] ** 2
    
    # Stack into feature matrix
    term_names = list(library.keys())
    X = np.column_stack([library[name] for name in term_names])
    
    # Normalize columns for numerical stability
    X_std = np.std(X, axis=0)
    X_std[X_std < 1e-10] = 1.0  # Avoid division by zero
    X_normalized = X / X_std
    
    # Least squares fit
    coeffs_normalized, residuals, rank, s = np.linalg.lstsq(X_normalized, u_t_np, rcond=None)
    
    # Un-normalize coefficients
    coeffs = coeffs_normalized / X_std
    
    # Threshold small coefficients (sparsity)
    max_coeff = np.max(np.abs(coeffs))
    coeffs[np.abs(coeffs) < threshold * max_coeff] = 0
    
    # Build equation string
    active_terms = []
    active_coeffs = {}
    
    for name, coeff in zip(term_names, coeffs):
        if coeff != 0:
            active_coeffs[name] = float(coeff)
            sign = "+" if coeff > 0 else ""
            active_terms.append(f"{sign}{coeff:.6f}*{name}")
    
    if active_terms:
        equation_str = "u_t = " + " ".join(active_terms).replace("+ -", "- ")
    else:
        equation_str = "u_t = 0 (no significant terms found)"
    
    # R² score
    u_t_pred = X @ coeffs
    ss_res = np.sum((u_t_np - u_t_pred)**2)
    ss_tot = np.sum((u_t_np - np.mean(u_t_np))**2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    
    return equation_str, active_coeffs, r_squared, term_names

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
        model, losses = train_pinn_on_data(x_data, t_data, u_data, epochs=3000)
        
        # Discover equation
        equation_str, coefficients, r_squared, all_terms = discover_equation(model, x_data, t_data)
        
        # Create visualization
        viz_path = create_visualization(model, x_data, t_data, u_data, losses, 
                                       equation_str, coefficients, r_squared, job_id)
        
        # Compute final error
        x_tensor = torch.tensor(x_data, dtype=torch.float32).reshape(-1, 1)
        t_tensor = torch.tensor(t_data, dtype=torch.float32).reshape(-1, 1)
        with torch.no_grad():
            u_pred = model(x_tensor, t_tensor).numpy().flatten()
        mse = np.mean((u_data - u_pred)**2)
        
        # Store results
        result = {
            "equation": equation_str,
            "coefficients": coefficients,
            "r_squared": float(r_squared),
            "mse": float(mse),
            "final_loss": float(losses[-1]),
            "epochs": len(losses),
            "terms_tested": all_terms,
            "visualization": viz_path
        }
        
        c.execute("""
            UPDATE jobs 
            SET status = 'completed', 
                completed_at = ?,
                result_data = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), json.dumps(result), job_id))
        conn.commit()
        
    except Exception as e:
        c.execute("""
            UPDATE jobs 
            SET status = 'failed', 
                error = ?,
                completed_at = ?
            WHERE id = ?
        """, (str(e), datetime.now().isoformat(), job_id))
        conn.commit()
    
    finally:
        conn.close()

# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface"""
    return FileResponse("static/index.html")

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
    
    return {
        "id": row[0],
        "status": row[1],
        "dataset_name": row[2],
        "created_at": row[3],
        "completed_at": row[4],
        "error": row[5],
        "result": result_data
    }

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

@app.get("/")
async def read_root():
    """Serve the main UI"""
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print("="*60)
    print("Starting PhysForge...")
    print("="*60)
    print(f"Open your browser to: http://localhost:{port}")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=port)
