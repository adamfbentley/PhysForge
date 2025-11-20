# PhysForge Research Edition - Quick Start

## What's New?

**Symbolic Regression with PySR**: Discover transcendental functions (sin, cos, exp, log) that sparse regression cannot find.

### Example Discovery

**Input:** Burgers' equation data (u_t = 0.01·u_xx - u·u_x)

**Output:**
- **Sparse Regression** (60s): Finds `u_t = 0.01·u_xx - 0.5·u·u_x` (linear approximation)
- **PySR** (2-3min): Discovers `u_t = 0.01·u_xx - u·u_x` (exact nonlinear term)

## 5-Minute Test Drive

### 1. Install Locally

```bash
cd app_research
pip install -r requirements.txt
python -c "import pysr; pysr.install()"  # Installs Julia (~5 min)
```

### 2. Run App

```bash
python app.py
```

Open http://localhost:8000

### 3. Test with Sample Data

Use the heat equation example from `app_simplified/example_data/`:
```csv
x,t,u
0.0,0.0,1.0
0.1,0.0,0.95
...
```

Upload and watch both methods run in parallel!

## Understanding Results

### Sparse Regression (Fast Method)
- **Time:** 60-90 seconds
- **Finds:** Linear combinations (u_xx, u_x, u, u², etc.)
- **Best for:** Heat equation, wave equation, linear PDEs
- **Example:** u_t = 0.01·u_xx + 0.5·u

### PySR Symbolic (Powerful Method)
- **Time:** 2-3 minutes
- **Finds:** All functions (sin, cos, exp, log, sqrt, abs)
- **Best for:** Nonlinear systems, oscillatory behavior, exponential growth
- **Example:** u_t = 0.01·u_xx + 0.5·u·(1 - 0.1·u) (logistic growth)

### When to Use Each

| Equation Type | Sparse | PySR | Example |
|---------------|--------|------|---------|
| Linear heat equation | ✅ Perfect | ⚡ Overkill | u_t = α·u_xx |
| Nonlinear diffusion | ⚠️ Approximate | ✅ Exact | u_t = ∇·(D(u)∇u) |
| Reaction-diffusion | ❌ Misses terms | ✅ Discovers | u_t = u_xx + u·(1-u) |
| Wave equation | ✅ Works | ⚡ Overkill | u_tt = c²·u_xx |
| Burgers' equation | ⚠️ Linearizes | ✅ Exact | u_t = ν·u_xx - u·u_x |
| Allen-Cahn | ❌ Can't find | ✅ Discovers | u_t = ε²·u_xx + u - u³ |

## Deployment

### Render (Recommended)

**Cost:** $7/month Starter instance (PySR requires more memory than free tier)

```bash
# Push to GitHub
git add app_research/
git commit -m "Deploy research edition"
git push

# Deploy to Render
1. New Web Service → Connect GitHub
2. Root Directory: app_research
3. Build: pip install -r requirements.txt && python -c "import pysr; pysr.install()"
4. Start: uvicorn app:app --host 0.0.0.0 --port $PORT
5. Instance: Starter ($7/month)
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for full guide.

## Performance Tuning

### Faster PySR (Trade Accuracy)

Edit `pysr_discovery.py`:

```python
PySRDiscoverer(
    timeout=60,  # Reduce from 120s
    maxsize=10,  # Reduce complexity from 20
    populations=8  # Reduce from 15
)
```

### Slower PySR (Better Results)

```python
PySRDiscoverer(
    timeout=300,  # 5 minutes
    maxsize=30,  # More complex equations
    populations=30  # More evolutionary search
)
```

## Research Applications

### 1. Turbulence Modeling (CFD)
**Problem:** RANS equations need closure for Reynolds stress tensor  
**Method:** Train PINN on DNS data, discover τ_ij = f(∇u)  
**Value:** Publishable if you find better closure than standard k-ε

### 2. Climate Parametrization
**Problem:** Sub-grid cloud physics not resolved  
**Method:** Train on high-res simulations, discover parametrization  
**Value:** Improve climate model accuracy

### 3. Materials Constitutive Laws
**Problem:** Stress-strain relationship unknown for new materials  
**Method:** Train on mechanical test data, discover σ = f(ε, ε̇)  
**Value:** Predictive model for material design

### 4. Biological Systems
**Problem:** Growth kinetics for bacteria/cancer  
**Method:** Train on time-series data, discover r(t) = f(N, nutrients)  
**Value:** Optimize bioreactor design or treatment

## Citing PhysForge

If you use PhysForge Research Edition in a publication:

```bibtex
@software{physforge_research_2024,
  title = {PhysForge Research Edition: PINN-Based PDE Discovery with Symbolic Regression},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/physforge},
  note = {AI-powered physics discovery combining Physics-Informed Neural Networks with PySR symbolic regression}
}
```

Also cite PySR:

```bibtex
@article{cranmer2023interpretable,
  title={Interpretable Machine Learning for Science with PySR and SymbolicRegression.jl},
  author={Cranmer, Miles},
  journal={arXiv preprint arXiv:2305.01582},
  year={2023}
}
```

## Troubleshooting

### "PySR not available"
```bash
pip install pysr
python -c "import pysr; pysr.install()"
```

### "Julia installation failed"
Download Julia manually from https://julialang.org/downloads/ and add to PATH.

### "PySR timeout"
Increase `timeout_seconds` in `pysr_discovery.py` or reduce dataset size.

### "Out of memory"
- Reduce `max_points` in `discover_with_pysr()` (default 500)
- Use Render Starter instance ($7/mo, 2GB RAM)
- Or deploy locally with more RAM

## Next Steps

1. **Try different datasets** - Heat, wave, Burgers', reaction-diffusion
2. **Compare methods** - When does PySR outperform sparse regression?
3. **Tune PySR settings** - Find optimal timeout/complexity tradeoff
4. **Deploy to Render** - Share with collaborators
5. **Write paper** - Novel contribution: PINN + sparse + PySR + web UI

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/yourusername/physforge/issues)
- Discussions: [Ask questions](https://github.com/yourusername/physforge/discussions)
- PySR Docs: https://astroautomata.com/PySR/

---

**Happy discovering! 🔬⚛️**
